---
title: "指南针（磁力计）"
aliases:
  - "指南针模块总览"
tags:
  - compass
  - index
module: "19-compass"
status: active
---

# 19 - 指南针（[[compass-system|磁力计]]）

## 模块概述

电子罗盘/磁力计：传感器选型、校准算法、干扰补偿、[[compass-system|航向]]解算。

## 目录结构

```
19-compass/
├── sensor/         # 磁力计传感器 (HMC5883L/QMC5883L/MMC5603)
├── calibration/    # 硬磁/软磁校准算法 (椭球拟合)
└── interference/   # 干扰检测与补偿 (电流/电机/金属)
```
---

## 相关链接

- [[imu-system|IMU]]
- [[flight-controller-firmware|飞控]]
