---
title: "云台系统"
aliases:
  - "云台模块总览"
tags:
  - gimbal
  - index
module: "17-gimbal"
status: active
---

# 17 - [[gimbal-control|云台]]系统

## 模块概述

相机云台（Gimbal）设计：[[esc-control|无刷电机]]驱动、姿态传感器、三轴控制算法、机械结构。

## 目录结构

```
17-gimbal/
├── mechanical/     # 机械结构设计
├── motor/          # 无刷云台电机驱动
├── sensor/         # IMU/编码器
└── control/        # 三轴控制算法 (PID/前馈/自适应)
```
---

## 相关链接

- [[camera-sensor|相机系统]]
- [[imu-system|IMU]]
- [[esc-control|ESC 控制]]
