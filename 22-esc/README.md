# 22 - 动力电调 (ESC)

## 模块概述

无刷电机电子调速器 (ESC)：硬件设计、BLDC 控制、通信协议、FOC 算法。

## 目录结构

```
22-esc/
├── hardware/       # ESC 硬件设计 (MOSFET/栅极驱动/电流采样)
├── protocol/       # 通信协议 (PWM/DSHOT/BLHeli_S/BLHeli_32)
├── algorithm/      # 控制算法 (六步换向/FOC/无感控制)
└── bldc/           # 无刷电机原理与选型
```
