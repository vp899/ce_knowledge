# 23 - 激光雷达 (LiDAR)

## 模块概述

激光雷达系统：测距原理、扫描机构、点云处理、SLAM 建图。

## 目录结构

```
23-lidar/
├── mechanical/     # 机械式 LiDAR (旋转机构/电机驱动)
├── tof/            # 测距原理 (ToF/三角测距/FMCW)
├── slam-mapping/   # SLAM 建图 (Cartographer/LOAM/LIO-SAM)
└── driver/         # 驱动与协议 (串口/以太网/点云解析)
```
