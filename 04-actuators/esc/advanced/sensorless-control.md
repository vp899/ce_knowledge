---
title: "ESC 高级 - 无感控制"
tags: [esc, advanced, sensorless, bemf, observer]
level: advanced
---

# 无感 FOC 控制

## 概述

本文介绍 esc 领域的 advanced 级别知识。

完成本文学习后，你将能够：

- 理解核心概念和基本原理
- 掌握关键技术和实现方法
- 应用到实际产品开发中

## 背景知识

### 相关概念

> 占位 - 待补充前置概念

## 核心内容

### 1. 无感控制原理

```
有感 vs 无感:
├── 有感: 编码器/霍尔传感器测量转子位置
├── 无感: 通过反电动势/观测器估算转子位置
└── 无感优势: 成本低, 可靠性高, 无传感器故障

反电动势 (BEMF):
  电机旋转时, 线圈切割磁力线产生反电动势
  BEMF = Ke × ω (Ke: 反电动势常数, ω: 角速度)

  低速: BEMF 弱, 难以检测
  高速: BEMF 强, 容易检测
```

### 2. 滑模观测器 (SMO)

```c
// 滑模观测器估算反电动势
typedef struct {
    float alpha_est, beta_est;  // 电流估计值
    float bemf_alpha, bemf_beta; // 反电动势估计
    float Ls;   // 电感
    float Rs;   // 电阻
    float k;    // 滑模增益
    float dt;
} SMO;

void smo_update(SMO *smo,
                 float ialpha, float ibeta,
                 float valpha, float vbeta) {
    // 电流估计误差
    float err_alpha = smo->alpha_est - ialpha;
    float err_beta = smo->beta_est - ibeta;
    
    // 滑模切换函数 (sigmoid)
    float sw_alpha = smo->k * err_alpha / (fabsf(err_alpha) + 0.01f);
    float sw_beta = smo->k * err_beta / (fabsf(err_beta) + 0.01f);
    
    // 电流观测器
    float dialpha = (valpha - smo->Rs*ialpha - smo->bemf_alpha
                     - sw_alpha) / smo->Ls;
    float dibeta = (vbeta - smo->Rs*ibeta - smo->bemf_beta
                    - sw_beta) / smo->Ls;
    
    smo->alpha_est += dialpha * smo->dt;
    smo->beta_est += dibeta * smo->dt;
    
    // 反电动势估计 (低通滤波滑模输出)
    float fc = 500.0f;  // 截止频率
    float alpha = smo->dt * 2 * 3.14159f * fc;
    smo->bemf_alpha += alpha * (sw_alpha - smo->bemf_alpha);
    smo->bemf_beta += alpha * (sw_beta - smo->bemf_beta);
}

// 从反电动势估算电角度
float smo_get_angle(SMO *smo) {
    return atan2f(-smo->bemf_alpha, smo->bemf_beta);
}

// 从反电动势估算转速
float smo_get_speed(SMO *smo) {
    float bemf_mag = sqrtf(smo->bemf_alpha*smo->bemf_alpha +
                           smo->bemf_beta*smo->bemf_beta);
    return bemf_mag / Ke;  // Ke: 反电动势常数
}
```

### 3. 高频注入 (低速无感)

```
高频注入原理:
  低速时 BEMF 弱, 无法检测位置
  → 注入高频信号, 利用凸极效应估算位置

  注入信号: vhf = Vh × sin(ωh·t) 沿 d 轴
  响应信号: ih 包含转子位置信息

  对于表贴式电机 (隐极): 不适用
  对于内嵌式电机 (凸极): 可以使用

实现:
  1. 在 d 轴注入高频电压 (500Hz~2kHz)
  2. 测量高频电流响应
  3. 带通滤波提取高频分量
  4. 解调得到转子位置

适用: 零速到中速 (0~10% 额定转速)
```

### 4. 启动策略

```c
// 无感电机启动 (开环→闭环切换)
typedef struct {
    int state;
    float freq;       // 开环频率
    float target_freq; // 目标频率
    float ramp_rate;   // 加速率
} StartupCtrl;

void startup_process(StartupCtrl *ctrl, SMO *smo,
                      float *valpha, float *vbeta) {
    switch(ctrl->state) {
    case 0: // 对齐: 固定角度, 建立初始位置
        *valpha = 1.0f; *vbeta = 0;
        ctrl->state = 1;
        break;
        
    case 1: // 开环加速
        ctrl->freq += ctrl->ramp_rate;
        *valpha = cosf(ctrl->freq);
        *vbeta = sinf(ctrl->freq);
        
        // 检测是否可以切换到闭环
        float speed = smo_get_speed(smo);
        if(speed > 0.1f * ctrl->target_freq) {
            ctrl->state = 2;  // 切换到闭环
        }
        break;
        
    case 2: // 闭环运行 (无感 FOC)
        // 使用 SMO 估算的角度
        // 正常 FOC 控制流程
        break;
    }
}

## 实践示例

### 示例代码

```c
// 占位 - 待补充示例代码
```

**代码说明**：
- 待补充

## 深入理解

### 原理分析

> 占位 - 待补充原理分析

### 最佳实践

1. 待补充

## 常见问题

### Q1: 待补充常见问题？

**A**: 待补充答案。

## 总结

本文核心要点：

- 待补充

## 延伸阅读

- 待补充相关文章链接

## 参考资料

1. 待补充

---

**练习题**：

1. 待补充

**下一步**：建议学习 [[MOC|返回知识地图]]
