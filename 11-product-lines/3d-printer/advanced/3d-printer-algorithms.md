level: advanced
---
title: "3D 打印机算法详解"
tags: [3d-printer, trapezoid, s-curve, input-shaper, temperature-pid, algorithm]
module: "11-product-lines"
---

# 3D 打印机算法详解

## 概述

打印质量取决于运动算法。本文涵盖 S 曲线、Input Shaper 和自动调平。

完成本文学习后，你将能够：

- 掌握本模块的核心概念和原理
- 理解关键技术的实现方法
- 能够应用到实际项目中

## 背景知识

### 相关概念

### 前置知识

- C 语言基础
- 嵌入式开发基础
- 相关模块的初级知识

### 学习建议

- 准备开发板进行动手实践
- 边学边做，不要只看不练
- 遇到问题先自己思考再查资料

## 核心内容

### 1. 运动规划算法

### 梯形加速度规划 (Trapezoid)
```
速度曲线:
  v_max ─────────────────
        ╱               ╲
       ╱                 ╲
      ╱                   ╲
  v_start                 v_end
  ─────┼─────┼─────┼─────┼─────→ t
       t1    t2    t3    t4

  加速段: t1→t2, 加速度 a
  匀速段: t2→t3, 速度 v_max
  减速段: t3→t4, 减速度 -a

加速段时间: t_accel = (v_max - v_start) / a
匀速段时间: t_cruise = (distance - s_accel - s_decel) / v_max
减速段时间: t_decel = (v_max - v_end) / a

每步时间计算 (Bresenham 风格):
  step_n 的时间间隔:
    Δt_n = Δt_0 / (1 + 2·n·a·Δt_0²)
  
  Δt_0 = 初始时间间隔 (第一步)
```

### S 曲线加速度规划
```
S 曲线: 加速度平滑变化 (减少振动)

加速度曲线:
  a_max    ╭──────╮
          ╱        ╲
         ╱          ╲
  0 ─────╱            ╲─────
        │              │
        j_max       -j_max  (加加速度)

优点:
├── 振动小 (无加速度突变)
├── 噪音低
├── 精度高 (减少过冲)
└── 适合高速打印

实现:
  加速段分为 7 段:
  1. 加加速 (jerk > 0)
  2. 匀加速
  3. 减加速 (jerk < 0)
  4. 匀速
  5. 加减速 (jerk > 0)
  6. 匀减速
  7. 减减速 (jerk < 0)
```

### 2. 输入整形 (Input Shaper)

### 振动抑制
```
原理: 将单个运动命令分解为多个延迟的脉冲
      使脉冲产生的振动相互抵消

ZV (Zero Vibration) 整形器:
  脉冲: [A1, A2] = [K, 1-K]
  延迟: [0, T/2]
  K = exp(-π·ζ/√(1-ζ²))
  T = 1/fn (固有频率)

MZV 整形器:
  脉冲: [A1, A2, A3] = [K², 2K(1-K), (1-K)²]
  延迟: [0, T/2, T]

EI (Extra Insensitive) 整形器:
  容忍频率误差 ±5%
  适合频率不确定的情况

配置 (Klipper):
  [input_shaper]
  shaper_type = mzv
  shaper_freq_x = 57.0   # X 轴固有频率 (Hz)
  shaper_freq_y = 48.0   # Y 轴固有频率 (Hz)
```

### 3. 温度 PID 控制

### 挤出头温控
```c
/* 温度 PID 控制器 */

typedef struct {
    float kp, ki, kd;
    float integral;
    float prev_error;
    float output_min, output_max;
    float dt;
} TempPID;

float temp_pid_update(TempPID *pid, float target, float current) {
    float error = target - current;
    
    // P 项
    float p = pid->kp * error;
    
    // I 项 (带 anti-windup)
    pid->integral += error * pid->dt;
    if (pid->integral > pid->output_max / pid->ki)
        pid->integral = pid->output_max / pid->ki;
    if (pid->integral < pid->output_min / pid->ki)
        pid->integral = pid->output_min / pid->ki;
    float i = pid->ki * pid->integral;
    
    // D 项 (对测量值微分, 避免设定值突变引起的冲击)
    float d = -pid->kd * (current - pid->prev_error) / pid->dt;
    pid->prev_error = current;
    
    // 输出
    float output = p + i + d;
    output = CLAMP(output, pid->output_min, pid->output_max);
    
    return output;
}

// PID 自整定 (Ziegler-Nichols)
void auto_tune_temp(TempPID *pid, float target) {
    // 1. 仅 P 控制, 逐渐增大 Kp
    // 2. 直到温度出现等幅振荡
    // 3. 记录 Ku (临界增益) 和 Tu (振荡周期)
    // 4. 计算: Kp=0.6Ku, Ki=2Kp/Tu, Kd=Kp·Tu/8
}
```

### 热床温控
```
热床温度曲线:
  PLA: 50-60°C
  ABS: 100-110°C
  PETG: 70-80°C
  TPU: 50-60°C

PID 参数 (典型):
  热端: Kp=20, Ki=0.5, Kd=300
  热床: Kp=100, Ki=5, Kd=500

Bang-Bang 控制 (简单方案):
  if (current < target - 2):
      heater ON
  elif (current > target + 2):
      heater OFF
  → 精度差 (±2°C), 但简单可靠
```

### 4. 自动调平算法

### 探测网格拟合
```c
/* 自动调平 - 网格补偿 */

typedef struct {
    float z_offset[16][16];  // Z 偏移网格
    int grid_w, grid_h;
    float bed_size_x, bed_size_y;
} BedLevel;

void bed_level_probe(BedLevel *bl, int probe_points) {
    float step_x = bl->bed_size_x / (bl->grid_w - 1);
    float step_y = bl->bed_size_y / (bl->grid_h - 1);
    
    for (int y = 0; y < bl->grid_h; y++) {
        for (int x = 0; x < bl->grid_w; x++) {
            float px = x * step_x;
            float py = y * step_y;
            
            // 移动到探测点
            move_to(px, py, 5.0);
            
            // 下探
            float z = probe_z();  // 触发时的 Z 高度
            bl->z_offset[y][x] = z;
        }
    }
}

float bed_level_get_z(BedLevel *bl, float x, float y) {
    // 双线性插值
    float step_x = bl->bed_size_x / (bl->grid_w - 1);
    float step_y = bl->bed_size_y / (bl->grid_h - 1);
    
    int ix = (int)(x / step_x);
    int iy = (int)(y / step_y);
    ix = CLAMP(ix, 0, bl->grid_w - 2);
    iy = CLAMP(iy, 0, bl->grid_h - 2);
    
    float fx = (x / step_x) - ix;
    float fy = (y / step_y) - iy;
    
    float z00 = bl->z_offset[iy][ix];
    float z10 = bl->z_offset[iy][ix+1];
    float z01 = bl->z_offset[iy+1][ix];
    float z11 = bl->z_offset[iy+1][ix+1];
    
    // 双线性插值
    float z = z00*(1-fx)*(1-fy) + z10*fx*(1-fy) +
              z01*(1-fx)*fy + z11*fx*fy;
    
    return z;
}
```

---

### 相关链接

- [[esc-control|电机控制]] — 步进驱动
- [[firmware-upgrade|固件]] — Marlin/Klipper
- [[pcb-layout|PCB]] — 主控板

## 实践示例

### 示例代码

```c
// 示例代码 - 结合正文理解
```

**代码说明**：
- 详见正文

## 深入理解

### 原理分析

深入理解底层原理有助于写出更高质量的代码。建议结合数据手册和源码进行学习。

### 最佳实践

1. 遵循代码规范，保持良好的注释习惯
2. 充分测试，覆盖边界条件
3. 持续重构，保持代码简洁

## 常见问题

### Q1: 学习本模块需要什么基础？

**A**: 需要 C 语言基础和基本的嵌入式开发知识。建议先完成前置模块的学习。

### Q2: 如何验证学习效果？

**A**: 通过动手实践验证：完成练习题、在开发板上运行示例代码、独立完成一个小项目。

## 总结

本文涵盖了本级别的核心知识：

- 理解了基本概念和工作原理
- 掌握了关键技术和实现方法
- 通过实践加深了理解

建议继续学习更高级别的内容。

## 延伸阅读

- [[MOC|知识地图]] - 返回总索引
- 相关模块文档 - 交叉参考
- 厂商数据手册 - 详细规格

## 参考资料

1. 厂商数据手册和技术参考
2. 开源项目文档和代码
3. 学术论文和行业标准

---

**练习题**：

1. 厂商数据手册和技术参考
2. 开源项目文档和代码
3. 学术论文和行业标准

**下一步**：建议学习 [[MOC|返回知识地图]]
