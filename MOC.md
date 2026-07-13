---
title: "消费电子知识库 - 总索引"
aliases:
  - "MOC"
  - "知识地图"
  - "Home"
tags:
  - moc
  - index
  - root
module: root
status: active
---

# 🗺️ 消费电子软件开发知识库

> 无人机 · 机器人 · 消费电子 · 全栈知识

---

## 📚 基础模块

```dataview
TABLE title AS "模块", tags AS "标签"
FROM #index
SORT file.name ASC
```

| 模块 | 说明 | 入口 |
|------|------|------|
| 🤖 Android | 系统定制、Framework、构建、安全 | [[README|Android 开发]] |
| ⚡ STM32 | 固件升级、Bootloader、外设 | [[README|STM32 升级]] |
| 🔧 硬件 | 原理图、PCB、打板、BOM | [[README|硬件设计]] |
| 🔒 安全启动 | Secure Boot、加密、密钥 | [[README|安全启动]] |
| 🖥️ 驱动 | Linux/RTOS 驱动开发 | [[README|驱动开发]] |
| 📡 通信 | MQTT/BLE/WiFi/UART | [[README|通信协议]] |
| 🧪 可靠性 | 环境/机械/EMC 测试 | [[README|可靠性测试]] |
| 📋 产品提案 | 模板、市场分析、商业论证 | [[README|产品提案]] |
| 🏗️ 架构 | 系统/软硬件架构设计 | [[README|架构设计]] |
| ⚠️ 风险 | 风险评估、缓解、跟踪 | [[README|风险管理]] |
| 📊 项目管理 | 开发流程、敏捷、质量 | [[README|项目管理]] |
| 📣 市场 | 品牌、内容、渠道、活动 | [[README|市场宣传]] |
| 🌐 网站 | 设计、开发、SEO、分析 | [[README|产品网站]] |

---

## 🚁 无人机/机器人模块

```dataview
TABLE title AS "模块", tags AS "标签"
FROM #index
WHERE contains(module, "14-") OR contains(module, "15-") OR contains(module, "16-") OR contains(module, "17-") OR contains(module, "18-") OR contains(module, "19-") OR contains(module, "20-") OR contains(module, "21-") OR contains(module, "22-") OR contains(module, "23-")
SORT file.name ASC
```

| 模块 | 核心内容 | 入口 |
|------|----------|------|
| 📷 相机 | Sensor/ISP/AF/3A/MIPI/V4L2 | [[README|相机系统]] |
| 📡 图传 | H.264/H.265/FEC/天线/链路 | [[README|图传系统]] |
| 🚁 飞控 | PID/EKF/混控/失联保护/RTL | [[README|飞控系统]] |
| 🎥 云台 | FOC/三轴控制/增稳/跟踪 | [[README|云台系统]] |
| 👁️ 视觉 | SLAM/避障/跟踪/深度 | [[README|视觉系统]] |
| 🧭 指南针 | 磁力计/校准/干扰/航向 | [[README|指南针]] |
| 📐 IMU | 传感器/融合/校准/振动 | [[README|IMU]] |
| 📍 GPS | RTK/天线/组合导航 | [[README|GPS/GNSS]] |
| ⚡ 电调 | BLDC/FOC/DShot/保护 | [[README|动力电调]] |
| 📡 激光雷达 | ToF/SLAM/点云/驱动 | [[README|激光雷达]] |

---

## 🔗 无人机系统架构图

```
                    ┌─────────────┐
                    │   飞控系统   │
                    │  (Flight    │
                    │  Controller)│
                    └──────┬──────┘
                           │
        ┌──────────┬───────┼───────┬──────────┐
        │          │       │       │          │
   ┌────┴────┐┌────┴────┐┌─┴──┐┌───┴───┐┌────┴────┐
   │  IMU    ││  GPS    ││ESC ││ 云台  ││ 指南针  │
   │(姿态)   ││(定位)   ││(动力)││(相机) ││(航向)   │
   └────┬────┘└────┬────┘└─┬──┘└───┬───┘└────┬────┘
        │          │       │       │          │
        └──────────┴───────┼───────┴──────────┘
                           │
                    ┌──────┴──────┐
                    │   视觉系统   │
                    │ (SLAM/避障)  │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
         ┌────┴────┐ ┌─────┴─────┐ ┌────┴────┐
         │  相机   │ │ 激光雷达   │ │   图传   │
         │(图像)   │ │(点云)     │ │(下行链路)│
         └─────────┘ └───────────┘ └─────────┘
```

---

## 🏷️ 标签索引

### 按技术领域
- `#android` - Android 系统开发
- `#stm32` - STM32 微控制器
- `#hardware` - 硬件设计
- `#security` - 安全机制
- `#drivers` - 驱动开发
- `#communication` - 通信协议

### 按无人机子系统
- `#flight-controller` - 飞控
- `#camera` - 相机
- `#gimbal` - 云台
- `#vision` - 视觉
- `#imu` - 惯性测量
- `#gps` - 定位
- `#esc` - 电调
- `#lidar` - 激光雷达
- `#compass` - 指南针
- `#image-transmission` - 图传

### 按文档类型
- `#index` - 索引/入口
- `#template` - 模板
- `#code` - 代码示例

---

## 📖 阅读路径

### 🚀 无人机新手入门
1. [[README|飞控系统]] → 了解飞控架构
2. [[imu-system|IMU]] → 理解姿态感知
3. [[gps-system|GPS]] → 理解定位
4. [[esc-control|ESC]] → 理解动力系统
5. [[flight-controller-firmware|飞控固件]] → 深入控制算法

### 📷 相机系统开发
1. [[camera-sensor|图像传感器]] → Sensor 选型与驱动
2. [[video-transmission|图传系统]] → 编码与传输
3. [[gimbal-control|云台系统]] → 增稳与控制
4. [[visual-slam|视觉系统]] → SLAM 与避障

### 🔒 安全体系
1. [[secure-boot-impl|安全启动]] → 信任链设计
2. [[key-mgmt|密钥管理]] → 密钥生命周期
3. [[android-security|Android 安全]] → 系统安全

### 📋 产品全流程
1. [[proposal-template|产品提案]] → 市场与商业
2. [[architecture-template|架构设计]] → 技术方案
3. [[dev-process|项目管理]] → 执行与管控
4. [[risk-management|风险管理]] → 风险控制
