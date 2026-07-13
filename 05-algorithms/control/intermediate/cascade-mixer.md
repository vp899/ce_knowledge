---
title: "控制算法中级 - 级联控制与混控"
tags: [control, intermediate, cascade, mixer, altitude]
level: intermediate
---

# 级联控制与电机混控

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
