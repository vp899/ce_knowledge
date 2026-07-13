level: intermediate
---
title: "控制算法详解"
tags: [control, pid, cascade, mixer, ekf, kalman, path-planning, algorithm]
module: "05-algorithms"
---

# 控制算法详解

## 概述

无人机需要级联 PID 和混控。本文详细讲解高度/位置控制和混控矩阵。

完成本文学习后，你将能够：

- 掌握级联控制和电机混控
- 能够实现高度控制和位置控制
- 理解前馈和 anti-windup 技术

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

### 1. PID 控制器

### PID 公式
```
连续域:
  u(t) = Kp·e(t) + Ki·∫e(τ)dτ + Kd·de(t)/dt

离散域 (位置式):
  u(k) = Kp·e(k) + Ki·Σe(i)·Δt + Kd·(e(k)-e(k-1))/Δt

离散域 (增量式):
  Δu(k) = Kp·(e(k)-e(k-1)) + Ki·e(k)·Δt + Kd·(e(k)-2e(k-1)+e(k-2))/Δt
  u(k) = u(k-1) + Δu(k)
```

### 完整 PID 实现
```c
/* pid_complete.c */

typedef struct {
    // 增益
    float kp, ki, kd;
    
    // 积分项
    float integral;
    float integral_limit;    // 积分限幅 (防 windup)
    
    // 微分项
    float prev_error;
    float d_filter_alpha;    // D 项低通滤波系数
    float d_filtered;
    
    // 输出限幅
    float output_min, output_max;
    
    // 死区
    float deadband;
    
    // 前馈
    float feedforward;
    
    // 时间
    float dt;
} PID;

void pid_init(PID *pid, float kp, float ki, float kd, float dt) {
    pid->kp = kp; pid->ki = ki; pid->kd = kd;
    pid->dt = dt;
    pid->integral = 0;
    pid->integral_limit = 1e6f;
    pid->prev_error = 0;
    pid->d_filter_alpha = 0.1f;  // D 项滤波
    pid->d_filtered = 0;
    pid->output_min = -1e6f;
    pid->output_max = 1e6f;
    pid->deadband = 0;
    pid->feedforward = 0;
}

float pid_update(PID *pid, float error) {
    // 死区
    if (fabsf(error) < pid->deadband) error = 0;
    
    // P 项
    float p_term = pid->kp * error;
    
    // I 项 (梯形积分 + anti-windup)
    pid->integral += 0.5f * (error + pid->prev_error) * pid->dt;
    if (pid->integral > pid->integral_limit)
        pid->integral = pid->integral_limit;
    if (pid->integral < -pid->integral_limit)
        pid->integral = -pid->integral_limit;
    float i_term = pid->ki * pid->integral;
    
    // D 项 (一阶低通滤波)
    float derivative = (error - pid->prev_error) / pid->dt;
    pid->d_filtered = pid->d_filter_alpha * derivative +
                      (1.0f - pid->d_filter_alpha) * pid->d_filtered;
    float d_term = pid->kd * pid->d_filtered;
    
    pid->prev_error = error;
    
    // 输出 = P + I + D + 前馈
    float output = p_term + i_term + d_term + pid->feedforward;
    
    // 输出限幅
    if (output > pid->output_max) output = pid->output_max;
    if (output < pid->output_min) output = pid->output_min;
    
    // Anti-windup (条件积分)
    if (output >= pid->output_max || output <= pid->output_min) {
        pid->integral -= 0.5f * (error + pid->prev_error) * pid->dt;
    }
    
    return output;
}

void pid_reset(PID *pid) {
    pid->integral = 0;
    pid->prev_error = 0;
    pid->d_filtered = 0;
}
```

### PID 调参方法 (Ziegler-Nichols)
```
Ziegler-Nichols 临界比例法:

步骤:
1. 设 Ki=0, Kd=0
2. 逐渐增大 Kp, 直到系统出现等幅振荡
3. 记录临界增益 Ku 和振荡周期 Tu
4. 按下表计算 PID 参数:

| 控制器 | Kp     | Ki      | Kd     |
|--------|--------|---------|--------|
| P      | 0.5·Ku | -       | -      |
| PI     | 0.45·Ku| 0.54·Ku/Tu | - |
| PID    | 0.6·Ku | 1.2·Ku/Tu | 0.075·Ku·Tu |

手动调参步骤:
1. 先调 P: 增大 Kp 直到响应快但不振荡
2. 再调 I: 增大 Ki 消除稳态误差, 但不要太大
3. 最后调 D: 增大 Kd 减少超调, 但注意噪声

无人机姿态 PID 参考值 (典型):
├── Roll:  Kp=0.8, Ki=0.2, Kd=0.05
├── Pitch: Kp=0.8, Ki=0.2, Kd=0.05
├── Yaw:   Kp=1.0, Ki=0.1, Kd=0.0
└── Rate:  Kp=0.15, Ki=0.05, Kd=0.003
```

### 2. 级联控制 (Cascade Control)

### 无人机姿态级联控制
```
级联结构:

位置设定值 (x,y,z)
    │
    ▼
┌──────────────────┐
│  位置控制器       │  → 速度设定值
│  (外环, 50-100Hz) │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  速度控制器       │  → 加速度/角度设定值
│  (中环, 100-400Hz)│
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  姿态控制器       │  → 角速度设定值
│  (内环, 400Hz)    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  角速度控制器     │  → 力矩/油门
│  (最内环, 1kHz)   │
└──────────────────┘

优势:
├── 内环响应快, 抗干扰
├── 外环精度高, 跟踪好
├── 各环独立调参
└── 饱和处理自然
```

### 3. 电机混控 (Mixer)

### 四旋翼混控
```
四旋翼布局 (X 型):

  M1(前左)    M2(前右)
       ╲      ╱
        ╲    ╱
         ╲  ╱
          ╲╱
          ╱╲
         ╱  ╲
        ╱    ╲
       ╱      ╲
  M3(后左)    M4(后右)

混控矩阵:
  [M1]   [ 1  +1  +1  -1 ] [油门]
  [M2] = [ 1  -1  +1  +1 ] [Roll]
  [M3]   [ 1  +1  -1  +1 ] [Pitch]
  [M4]   [ 1  -1  -1  -1 ] [Yaw]

  油门: 升力
  Roll: 横滚力矩
  Pitch: 俯仰力矩
  Yaw: 偏航力矩 (反扭矩)

归一化:
  M_total = M1 + M2 + M3 + M4
  如果 M_total > max_thrust:
    等比例缩小所有电机

油门到 PWM:
  PWM = throttle_min + (throttle_max - throttle_min) × throttle
```

### 4. EKF 状态估计

### 卡尔曼滤波原理
```
预测 (Prediction):
  x̂⁻ = F·x̂ + B·u        (状态预测)
  P⁻ = F·P·F^T + Q        (协方差预测)

更新 (Update):
  K = P⁻·H^T·(H·P⁻·H^T + R)^(-1)   (卡尔曼增益)
  x̂ = x̂⁻ + K·(z - H·x̂⁻)           (状态更新)
  P = (I - K·H)·P⁻                   (协方差更新)

其中:
  x̂ = 状态估计
  F = 状态转移矩阵
  B = 控制输入矩阵
  u = 控制输入
  P = 误差协方差
  Q = 过程噪声协方差
  H = 观测矩阵
  R = 观测噪声协方差
  K = 卡尔曼增益
  z = 观测值
```

### 5. 路径规划算法

### A* 算法
```
A* 搜索:
  f(n) = g(n) + h(n)
  
  g(n) = 从起点到 n 的实际代价
  h(n) = 从 n 到终点的启发式估计 (曼哈顿/欧几里得)

算法步骤:
1. 将起点加入 open_list
2. 从 open_list 取 f 值最小的节点 current
3. 如果 current 是终点, 回溯路径
4. 将 current 移入 closed_list
5. 遍历 current 的邻居:
   - 如果在 closed_list, 跳过
   - 计算 g_new = g(current) + cost(current, neighbor)
   - 如果 neighbor 不在 open_list 或 g_new < g(neighbor):
     更新 g, h, f, parent
     加入 open_list
6. 重复步骤 2

启发式函数:
  曼哈顿: h = |x1-x2| + |y1-y2|
  欧几里得: h = sqrt((x1-x2)² + (y1-y2)²)
  对角线: h = max(|x1-x2|, |y1-y2|)

栅格地图分辨率: 通常 0.05-0.2m
```

### DWA (Dynamic Window Approach) 避障
```
DWA 算法:
1. 在速度空间 (v, ω) 中采样
2. 前向模拟轨迹
3. 评价函数选择最优速度

评价函数:
  G(v, ω) = α·heading(v,ω) + β·dist(v,ω) + γ·velocity(v,ω)

  heading: 朝向目标的程度
  dist: 离最近障碍物的距离
  velocity: 速度大小 (鼓励快速)

速度窗口:
  Vs = [v_min, v_max] × [ω_min, ω_max]  (机器人限制)
  Vd = [v-a·dt, v+a·dt] × [ω-α·dt, ω+α·dt]  (加速度限制)
  Va = {v, ω | 避障安全}  (安全约束)
  
  Vr = Vs ∩ Vd ∩ Va  (可行速度窗口)
```

---

### 相关链接

- [[imu-system|IMU]] — 姿态估计
- [[esc-control|ESC]] — 电机控制
- [[visual-slam|视觉 SLAM]] — 视觉定位
- [[lidar-system|激光雷达]] — 点云建图

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

**下一步**：建议学习 [[control/advanced/|高级内容]]
