---
title: "动力电调 (ESC)"
aliases:
  - "电调模块总览"
tags:
  - esc
  - index
module: "22-esc"
status: active
---

# 22 - 动力[[esc-control|电调]] ([[esc-control|ESC]])

## 模块概述

[[esc-control|无刷电机]]电子调速器 (ESC)：硬件设计、[[esc-control|BLDC]] 控制、通信协议、[[gimbal-control|FOC]] 算法。

## 目录结构

```
22-esc/
├── hardware/       # ESC 硬件设计 (MOSFET/栅极驱动/电流采样)
├── protocol/       # 通信协议 (PWM/DSHOT/BLHeli_S/BLHeli_32)
├── algorithm/      # 控制算法 (六步换向/FOC/无感控制)
└── bldc/           # 无刷电机原理与选型
```
---

## 相关链接

- [[flight-controller-firmware|飞控]]
- [[gimbal-control|云台]]
