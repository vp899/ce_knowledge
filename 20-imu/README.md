# 20 - IMU（惯性测量单元）

## 模块概述

六轴/九轴 IMU：传感器选型、数据融合、振动抑制、校准。

## 目录结构

```
20-imu/
├── sensor/         # IMU 传感器 (MPU6050/ICM42688/BMI088)
├── fusion/         # 姿态融合 (互补滤波/Mahony/Madgwick/EKF)
├── calibration/    # 零偏校准、温漂补偿、六面校准
└── vibration/      # 振动分析与抑制 (陷波滤波器/软安装)
```
