---
title: "控制算法初级 - PID 基础"
tags: [control, beginner, pid, motor, basics]
level: beginner
---

# PID 控制基础

## 概述

本文介绍 control 领域的 beginner 级别知识。

完成本文学习后，你将能够：

- 理解核心概念和基本原理
- 掌握关键技术和实现方法
- 应用到实际产品开发中

## 背景知识

### 相关概念

> 占位 - 待补充前置概念

## 核心内容

### 1. 什么是 PID

```
PID = Proportional (比例) + Integral (积分) + Derivative (微分)

生活类比: 开车保持车道
├── P: 偏离车道越多, 打方向越大 (比例于误差)
├── I: 持续偏离时逐渐加大修正 (消除稳态误差)
└── D: 偏离速度越快, 修正越猛 (预测趋势, 减少超调)
```

### 2. PID 公式

```
u(t) = Kp·e(t) + Ki·∫e(τ)dτ + Kd·de(t)/dt

  e(t) = 设定值 - 实际值 (误差)
  Kp: 比例增益
  Ki: 积分增益
  Kd: 微分增益
  u(t): 控制输出
```

### 3. 各项作用

```
P (比例):
  输出 = Kp × 误差
  作用: 快速响应误差
  问题: 有稳态误差 (无法完全消除)

I (积分):
  输出 = Ki × 误差累积
  作用: 消除稳态误差
  问题: 积分饱和 (windup), 响应慢

D (微分):
  输出 = Kd × 误差变化率
  作用: 预测趋势, 减少超调
  问题: 对噪声敏感
```

### 4. 最简单的 PID 代码

```c
float pid_update(float error, float dt) {
    static float integral = 0;
    static float prev_error = 0;
    
    // P 项
    float p = Kp * error;
    
    // I 项 (累积)
    integral += error * dt;
    float i = Ki * integral;
    
    // D 项 (变化率)
    float d = Kd * (error - prev_error) / dt;
    prev_error = error;
    
    return p + i + d;
}
```

### 5. 调参口诀

```
先 P 后 I 最后 D:
1. Ki=0, Kd=0, 增大 Kp 直到系统振荡
2. 减小 Kp 到振荡消失的 60%
3. 逐渐增大 Ki 消除稳态误差
4. 适当增大 Kd 减少超调
5. 反复微调
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

**下一步**：建议学习 [[control/intermediate/|中级内容]]
