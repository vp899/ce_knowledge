# 消费电子软件开发知识库

> Consumer Electronics Software Development Knowledge Base

## 知识库结构

| # | 模块 | 目录 | 说明 | 文件数 | 大小 |
|---|------|------|------|--------|------|
| 01 | Android 开发 | `01-android/` | Framework、系统层、构建、安全 | 5 | 40K |
| 02 | STM32 升级 | `02-stm32/` | 固件升级、Bootloader | 3 | 37K |
| 03 | 硬件设计 | `03-hardware/` | 原理图、PCB、打板制造 | 4 | 28K |
| 04 | 安全启动 | `04-security/` | Secure Boot、加密、密钥管理 | 3 | 34K |
| 05 | 驱动开发 | `05-drivers/` | Linux/RTOS 驱动 | 3 | 32K |
| 06 | 通信协议 | `06-communication/` | MQTT/BLE/WiFi/UART | 2 | 19K |
| 07 | 可靠性测试 | `07-reliability/` | 环境/机械/EMC 测试 | 3 | 32K |
| 08 | 产品提案 | `08-proposal/` | 模板、市场分析 | 2 | 11K |
| 09 | 架构设计 | `09-architecture/` | 系统/软硬件架构 | 2 | 13K |
| 10 | 风险管理 | `10-risk/` | 风险评估、缓解 | 2 | 12K |
| 11 | 项目管理 | `11-project-management/` | 开发流程、敏捷 | 2 | 13K |
| 12 | 市场宣传 | `12-marketing/` | 品牌、内容、渠道 | 2 | 15K |
| 13 | 产品网站 | `13-website/` | 设计、开发、SEO | 2 | 22K |
| **14** | **相机系统** | `14-camera/` | **Sensor/ISP/AF/3A/MIPI** | **2** | **23K** |
| **15** | **图传系统** | `15-image-transmission/` | **H.264/H.265/FEC/天线/链路预算** | **2** | **13K** |
| **16** | **飞控系统** | `16-flight-controller/` | **PID/EKF/混控/失联保护/RTL** | **2** | **17K** |
| **17** | **云台系统** | `17-gimbal/` | **FOC/三轴控制/增稳/跟踪** | **2** | **10K** |
| **18** | **视觉系统** | `18-vision/` | **SLAM/避障/跟踪/深度** | **2** | **10K** |
| **19** | **指南针** | `19-compass/` | **磁力计/校准/干扰补偿/航向** | **2** | **9K** |
| **20** | **IMU** | `20-imu/` | **姿态融合/Mahony/EKF/振动** | **2** | **15K** |
| **21** | **GPS/GNSS** | `21-gps/` | **RTK/天线/组合导航** | **2** | **11K** |
| **22** | **动力电调** | `22-esc/` | **BLDC/FOC/DShot/保护** | **2** | **10K** |
| **23** | **激光雷达** | `23-lidar/` | **ToF/三角测距/SLAM/点云** | **2** | **15K** |

**总计: 50 个 Markdown 文件, 80 个目录, 490KB+**

## 无人机/机器人模块技术深度

| 模块 | 核心内容 |
|------|----------|
| 相机 | IMX377/477/586 选型、MIPI CSI-2 协议、V4L2 驱动完整代码、ISP 管线 (BLC→Demosaic→NR→CCM→Gamma)、3A 算法 (AE/AWB/AF) |
| 图传 | H.264/H.265 低延迟编码配置、私有协议帧格式、FEC/ARQ 纠错、MIMO 天线、FSPL 链路预算、自适应码率 |
| 飞控 | STM32H7 硬件设计、ArduPilot/PX4 架构、级联 PID 控制 (角度→角速度→混控)、失联保护状态机、RTL 返航算法 |
| 云台 | 无刷云台电机选型、FOC 磁场定向控制 (Clark/Park/SVPWM)、三轴增稳、跟随/锁定/FPV 模式、编码器选型 |
| 视觉 | VINS-Mono VIO、双目测距原理、避障传感器对比、KCF/SiamRPN 目标跟踪、MiDaS 深度估计 |
| 指南针 | QMC5883L/IST8310 选型、硬磁/软磁校准 (椭球拟合)、倾斜补偿航向解算、电流干扰检测 |
| IMU | ICM-42688/BMI088 选型、互补滤波/Mahony/EKF 姿态融合、六面校准、陷波滤波器振动抑制 |
| GPS | u-blox ZED-F9P RTK 配置、NMEA 解析、GNSS 天线设计、GPS+IMU 组合导航、GPS 中断处理 |
| 电调 | BLDC 电机原理、三相全桥逆变器、六步换向/FOC 控制、DShot/BLHeli 协议、过流/过温保护 |
| 激光雷达 | ToF/三角测距/FMCW 原理、机械/固态 LiDAR 对比、体素下采样/ICP 点云处理、LIO-SAM SLAM、UDP 驱动 |

## 使用方式

1. **查阅**: 按模块浏览，每个目录下有 `README.md` 作为入口
2. **搜索**: `grep -r "关键词" consumer-electronics-kb/` 全文检索
3. **代码**: 每个模块包含完整可参考的代码示例 (C/Python)
4. **模板**: 提案、架构设计、测试报告等可直接使用的模板
