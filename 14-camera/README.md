---
title: "相机系统"
aliases:
  - "相机模块总览"
tags:
  - camera
  - index
module: "14-camera"
status: active
---

# 14 - 相机系统

## 模块概述

消费级无人机/机器人相机系统开发：[[camera-sensor|图像传感器]]选型、[[camera-sensor|ISP]] 调优、镜头驱动、拍照/录像、图传链路。

## 目录结构

```
14-camera/
├── sensor/         # 图像传感器 (CMOS Sensor)
├── lens/           # 镜头模组与驱动 (AF/OIS)
├── isp/            # ISP 图像处理管线
├── driver/         # Sensor 驱动开发 (V4L2/MIPI)
└── tuning/         # ISP 调优 (3A/降噪/色彩)
```

## 核心知识领域

### 1. 图像传感器选型
### 2. 镜头模组与 AF/OIS
### 3. ISP 图像处理管线
### 4. V4L2 / [[camera-sensor|MIPI CSI]] 驱动
### 5. 3A 算法与画质调优
---

## 相关链接

- [[video-transmission|图传系统]]
- [[gimbal-control|云台系统]]
- [[linux-driver-dev|Linux 驱动]]
