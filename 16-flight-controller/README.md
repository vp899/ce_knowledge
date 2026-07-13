---
title: "飞控系统"
aliases:
  - "飞控模块总览"
tags:
  - flight-controller
  - index
module: "16-flight-controller"
status: active
---

# 16 - 飞控系统

## 模块概述

无人机飞控硬件设计、固件架构、姿态/位置控制算法、安全保护机制。

## 目录结构

```
16-flight-controller/
├── hardware/       # 飞控硬件设计 (MCU/接口/PCB)
├── firmware/       # 飞控固件架构 (RTOS/模块/通信)
├── algorithm/      # 控制算法 (PID/EKF/路径规划)
└── safety/         # 安全保护 (失联保护/低电量/地理围栏)
```

## 核心知识领域

### 1. 飞控硬件
### 2. 固件架构
### 3. 控制算法
### 4. 安全保护
---

## 相关链接

- [[imu-system|IMU]]
- [[gps-system|GPS]]
- [[compass-system|指南针]]
- [[esc-control|ESC]]
- [[gimbal-control|云台]]
