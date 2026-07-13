---
title: "视觉系统"
aliases:
  - "视觉模块总览"
tags:
  - vision
  - index
module: "18-vision"
status: active
---

# 18 - 视觉系统

## 模块概述

无人机/机器人视觉感知：[[visual-slam|SLAM]]、[[visual-slam|避障]]、[[visual-slam|目标跟踪]]、深度估计。

## 目录结构

```
18-vision/
├── slam/               # 视觉 SLAM (ORB-SLAM/VINS)
├── obstacle-avoidance/ # 避障感知 (双目/ToF/结构光)
├── tracking/           # 目标跟踪 (KCF/SiamFC/YOLO)
└── depth/              # 深度估计 (双目/单目/ToF)
```
---

## 相关链接

- [[camera-sensor|相机系统]]
- [[lidar-system|激光雷达]]
- [[imu-system|IMU]]
