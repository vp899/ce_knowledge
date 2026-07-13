level: intermediate
---
title: "相机 ISP 算法详解"
tags: [camera, isp, ae, awb, af, demosaic, denoise, algorithm]
module: "03-sensors"
---

# 相机 ISP 算法详解

## 概述

ISP 决定画质。本文详细讲解去马赛克、AE/AWB/AF 算法原理和实现。

完成本文学习后，你将能够：

- 掌握 ISP 管线各步骤算法
- 能够实现 AE/AWB/AF 三大算法
- 理解 V4L2 驱动框架

## 背景知识

### 相关概念

### 前置知识

- 完成初级内容的学习
- 熟悉嵌入式开发流程
- 掌握基本的数据结构和算法

### 学习建议

- 理解原理后动手实现
- 对比不同算法的优缺点
- 关注工程实践中的细节

## 核心内容

### 1. ISP 管线各步骤算法

### 黑电平校正 (BLC)
```
原理: CMOS sensor 无光时输出不为 0 (暗电流)
公式: I_out(x,y) = I_in(x,y) - BLC_offset

典型值: 64-128 (10-bit ADC)
分通道: R/Gr/Gb/B 各自独立校正
```

### 坏点校正 (DPC)
```c
/* 中值滤波检测坏点 */
void detect_bad_pixel(uint16_t *raw, int w, int h, 
                       int threshold, uint8_t *bad_map) {
    for (int y = 1; y < h-1; y++) {
        for (int x = 1; x < w-1; x++) {
            uint16_t center = raw[y*w + x];
            
            // 取周围同色像素 (Bayer pattern)
            uint16_t neighbors[4];
            // 根据 Bayer 位置选择邻居
            if ((y%2==0 && x%2==0) || (y%2==1 && x%2==1)) { // R or B
                neighbors[0] = raw[(y-2)*w + x];
                neighbors[1] = raw[(y+2)*w + x];
                neighbors[2] = raw[y*w + x-2];
                neighbors[3] = raw[y*w + x+2];
            } else { // G
                neighbors[0] = raw[(y-1)*w + x-1];
                neighbors[1] = raw[(y-1)*w + x+1];
                neighbors[2] = raw[(y+1)*w + x-1];
                neighbors[3] = raw[(y+1)*w + x+1];
            }
            
            // 排序取中值
            sort4(neighbors);
            uint16_t median = (neighbors[1] + neighbors[2]) / 2;
            
            // 判断坏点
            if (abs(center - median) > threshold) {
                bad_map[y*w + x] = 1;
                raw[y*w + x] = median;  // 替换
            }
        }
    }
}
```

### Demosaic (去马赛克)
```
双线性插值 (Bilinear):

Bayer 阵列:
  R  G  R  G
  G  B  G  B
  R  G  R  G
  G  B  G  B

R 位置插值 G:
  G = (G_left + G_right + G_up + G_down) / 4

R 位置插值 B:
  B = (B↖ + B↗ + B↙ + B↘) / 4

G 位置插值 R (在 R 行):
  R = (R_left + R_right) / 2

G 位置插值 B (在 B 行):
  B = (B_up + B_down) / 2

B 位置类似 R 位置的镜像

进阶算法:
├── Malvar-He-Cutler: 边缘感知, 利用梯度方向
├── AHD (Adaptive Homogeneity): 自适应同质性
└── VNG (Variable Number of Gradients): 变梯度数
```

### 自动曝光 (AE)
```c
/* AE 算法 - 目标亮度控制 */

typedef struct {
    float target_brightness;   // 目标亮度 (0-255)
    float kp, ki;              // PI 增益
    float integral;
    float min_exp, max_exp;    // 曝光范围
    float min_gain, max_gain;  // 增益范围
    float current_exp;
    float current_gain;
} AE_Controller;

void ae_update(AE_Controller *ae, uint8_t *image, int w, int h) {
    // 1. 计算当前亮度 (加权平均)
    float brightness = 0;
    float total_weight = 0;
    
    for (int y = 0; y < h; y += 2) {
        for (int x = 0; x < w; x += 2) {
            // 中心权重高, 边缘权重低
            float cx = (x - w/2.0f) / (w/2.0f);
            float cy = (y - h/2.0f) / (h/2.0f);
            float weight = 1.0f - 0.5f*(cx*cx + cy*cy);
            
            brightness += image[y*w + x] * weight;
            total_weight += weight;
        }
    }
    brightness /= total_weight;
    
    // 2. PI 控制
    float error = ae->target_brightness - brightness;
    ae->integral += error * ae->ki;
    ae->integral = CLAMP(ae->integral, -50, 50);
    
    float correction = ae->kp * error + ae->integral;
    
    // 3. 调整曝光 (优先调增益, 再调曝光时间)
    if (correction > 0) {
        // 需要更亮
        if (ae->current_gain < ae->max_gain) {
            ae->current_gain *= (1.0f + correction * 0.01f);
        } else {
            ae->current_exp *= (1.0f + correction * 0.01f);
        }
    } else {
        // 需要更暗
        if (ae->current_exp > ae->min_exp) {
            ae->current_exp *= (1.0f + correction * 0.01f);
        } else {
            ae->current_gain *= (1.0f + correction * 0.01f);
        }
    }
    
    // 4. 限幅
    ae->current_exp = CLAMP(ae->current_exp, ae->min_exp, ae->max_exp);
    ae->current_gain = CLAMP(ae->current_gain, ae->min_gain, ae->max_gain);
    
    // 5. 写入 sensor
    sensor_set_exposure(ae->current_exp);
    sensor_set_gain(ae->current_gain);
}
```

### 自动白平衡 (AWB)
```
灰度世界假设:
  假设场景平均颜色为灰色
  R_avg = G_avg = B_avg

算法:
  1. 统计图像 R/G/B 通道平均值
  2. 计算增益:
     gain_R = G_avg / R_avg
     gain_G = 1.0
     gain_B = G_avg / B_avg
  3. 应用增益:
     R' = R × gain_R
     G' = G × gain_G
     B' = B × gain_B

白点检测 (改进):
  1. 选择高亮度 + 低饱和度的像素
  2. 这些像素应该是白色/灰色
  3. 用这些像素计算色温
  4. 查找对应增益表

色温范围:
  2500K (暖/蜡烛) → 6500K (日光) → 10000K (冷/阴天)
```

### 自动对焦 (AF)
```c
/* 对比度检测 AF (CDAF) */

typedef struct {
    float focus_value;      // 对焦值 (高频能量)
    float best_focus;       // 最佳焦距位置
    float best_value;       // 最佳对焦值
    int state;              // 状态机
    float current_pos;      // 当前镜头位置
    float step;             // 搜索步长
} AF_Controller;

float calculate_focus_value(uint8_t *image, int w, int h) {
    // 拉普拉斯算子计算高频能量
    float sum = 0;
    for (int y = 1; y < h-1; y++) {
        for (int x = 1; x < w-1; x++) {
            int laplacian = -4 * image[y*w + x]
                          + image[(y-1)*w + x]
                          + image[(y+1)*w + x]
                          + image[y*w + x-1]
                          + image[y*w + x+1];
            sum += abs(laplacian);
        }
    }
    return sum / (w * h);
}

void af_update(AF_Controller *af, uint8_t *image, int w, int h) {
    af->focus_value = calculate_focus_value(image, w, h);
    
    switch (af->state) {
    case 0: // 粗搜索
        if (af->focus_value > af->best_value) {
            af->best_value = af->focus_value;
            af->best_focus = af->current_pos;
        }
        af->current_pos += af->step;
        lens_move_to(af->current_pos);
        
        if (af->current_pos > LENS_MAX) {
            // 粗搜索完成, 进入精搜索
            af->current_pos = af->best_focus - af->step * 2;
            af->step = af->step / 4;
            af->state = 1;
        }
        break;
        
    case 1: // 精搜索 (爬山法)
        if (af->focus_value > af->best_value) {
            af->best_value = af->focus_value;
            af->best_focus = af->current_pos;
            af->current_pos += af->step;
        } else {
            // 已过峰值, 回到最佳位置
            lens_move_to(af->best_focus);
            af->state = 2;
        }
        break;
        
    case 2: // 跟踪 (持续监测)
        if (fabsf(af->focus_value - af->best_value) > 10) {
            // 场景变化, 重新搜索
            af->best_value = 0;
            af->step = 10;
            af->state = 0;
        }
        break;
    }
}
```

---

### 相关链接

- [[camera-sensor|图像传感器]] — Sensor 选型与驱动
- [[video-transmission|图传系统]] — 编码与传输
- [[visual-slam|视觉 SLAM]] — 视觉算法

## 实践示例

### 示例代码

```c
// 示例代码 - 结合正文理解
```

**代码说明**：
- 详见正文

## 深入理解

### 原理分析

请参考核心内容部分的详细讲解。

### 最佳实践

1. 模块化设计，接口清晰
2. 充分的错误处理和边界检查
3. 编写可测试的代码

## 常见问题

### Q1: 如何调试复杂问题？

**A**: 使用逻辑分析仪/示波器抓取信号；添加日志输出关键变量；使用 GDB 在线调试；分模块隔离问题。

### Q2: 性能不够怎么办？

**A**: 使用 DMA 减少 CPU 负担；优化中断处理 (Top/Bottom Half)；使用硬件加速器；降低采样率或简化算法。

## 总结

本文深入讲解了核心技术和实现方法：

- 掌握了关键算法的原理和实现
- 能够独立完成模块级开发
- 理解了工程实践中的优化技巧

下一步建议进入高级内容，学习系统级设计和生产级优化。

## 延伸阅读

- [[MOC|知识地图]] - 返回总索引
- 相关模块文档 - 交叉参考
- 厂商数据手册 - 详细规格

## 参考资料

- 厂商数据手册和技术参考
- 开源项目文档和代码
- 学术论文和行业标准

---

**练习题**：

- 厂商数据手册和技术参考
- 开源项目文档和代码
- 学术论文和行业标准

**下一步**：建议学习 [[camera/advanced/|高级内容]]
