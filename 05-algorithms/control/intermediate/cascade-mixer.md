---
title: "控制算法中级 - 级联控制与混控"
tags: [control, intermediate, cascade, mixer, altitude]
level: intermediate
---

# 级联控制与电机混控

## 概述

本文介绍 control 领域的 intermediate 级别知识。

完成本文学习后，你将能够：

- 理解核心概念和基本原理
- 掌握关键技术和实现方法
- 应用到实际产品开发中

## 背景知识

### 相关概念

> 占位 - 待补充前置概念

## 核心内容

### 1. 级联控制结构

```
无人机姿态级联控制 (四环):

位置设定值 (x,y,z)
    │
    ▼
┌──────────────────┐
│  位置控制器       │  → 速度设定值
│  (外环, 50Hz)     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  速度控制器       │  → 角度设定值
│  (100Hz)         │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  姿态控制器       │  → 角速度设定值
│  (400Hz)         │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  角速度控制器     │  → 力矩输出
│  (最内环, 1kHz)   │
└──────────────────┘

为什么用级联?
├── 内环快, 抗干扰 (角速度 1kHz)
├── 外环慢, 跟踪好 (位置 50Hz)
├── 各环独立调参
└── 饱和处理自然
```

### 2. 高度控制

```c
// 高度控制器 (气压计 + 超声波融合)
typedef struct {
    float target_alt;
    float kp, ki, kd;
    float integral;
    float prev_error;
    float dt;
} AltController;

float alt_control_update(AltController *c,
                          float baro_alt,    // 气压计高度
                          float sonar_alt,   // 超声波高度
                          float vz) {        // 垂直速度
    
    // 融合高度: 低空用超声波, 高空用气压计
    float alt;
    if(sonar_alt > 0 && sonar_alt < 5.0f) {
        alt = sonar_alt;  // 5m 以下用超声波
    } else {
        alt = baro_alt;   // 5m 以上用气压计
    }
    
    float error = c->target_alt - alt;
    
    // PID
    c->integral += error * c->dt;
    c->integral = CLAMP(c->integral, -2.0f, 2.0f);
    float derivative = -vz;  // 用速度代替微分
    
    float throttle = c->kp * error
                   + c->ki * c->integral
                   + c->kd * derivative;
    
    // 加上悬停油门 (补偿重力)
    throttle += HOVER_THROTTLE;
    
    return CLAMP(throttle, 0, 1.0f);
}
```

### 3. 电机混控

```c
// 四旋翼 X 型混控
void mixer_quad_x(float throttle, float roll, float pitch,
                   float yaw, float *motor) {
    // M1(前左)  M2(前右)
    //      ╲  ╱
    //       ╲╱
    //       ╱╲
    //      ╱  ╲
    // M3(后左)  M4(后右)
    
    motor[0] = throttle + roll + pitch - yaw;  // 前左
    motor[1] = throttle - roll + pitch + yaw;  // 前右
    motor[2] = throttle + roll - pitch + yaw;  // 后左
    motor[3] = throttle - roll - pitch - yaw;  // 后右
    
    // 归一化: 如果任何电机超限, 等比例缩小
    float max_motor = 0;
    for(int i=0; i<4; i++) {
        if(motor[i] > max_motor) max_motor = motor[i];
    }
    
    if(max_motor > 1.0f) {
        float scale = 1.0f / max_motor;
        for(int i=0; i<4; i++) {
            motor[i] *= scale;
        }
    }
    
    // 限幅
    for(int i=0; i<4; i++) {
        motor[i] = CLAMP(motor[i], 0, 1.0f);
    }
}
```

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

**下一步**：建议学习 [[control/advanced/|高级内容]]
