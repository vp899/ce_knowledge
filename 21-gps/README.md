---
title: "GPS / GNSS"
aliases:
  - "GPS 模块总览"
tags:
  - gps
  - index
module: "21-gps"
status: active
---

# 21 - GPS / [[gps-system|GNSS]]

## 模块概述

GPS/GNSS 定位系统：接收机选型、[[gps-system|RTK]] 高精度定位、天线设计、导航算法。

## 目录结构

```
21-gps/
├── receiver/       # GNSS 接收机 (u-blox/Qualcomm/北斗)
├── rtk/            # RTK 高精度定位 (基站/移动站/差分)
├── antenna/        # GNSS 天线设计 (陶瓷/螺旋/抗多径)
└── nav/            # 组合导航 (GPS+IMU+视觉)
```
---

## 相关链接

- [[imu-system|IMU]]
- [[flight-controller-firmware|飞控]]
