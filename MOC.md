---
title: "消费电子知识库 - 总索引"
aliases:
  - "MOC"
  - "知识地图"
  - "Home"
tags: [moc, index, root]
status: active
---

# 🗺️ 消费电子产品开发知识库

> 面向企业培训 · 覆盖无人机/手持云台/扫地机/3D打印机 · 产品级完整知识

---

## 📖 快速导航

### 按角色
| 我是... | 从这里开始 |
|---------|-----------|
| 🆕 新入职工程师 | [[learning-paths\|学习路径]] |
| 💻 嵌入式开发 | [[stm32\|STM32]] → [[linux-driver-dev\|Linux 驱动]] → [[ci-cd-pipeline\|CI/CD]] |
| 📷 算法工程师 | [[imu-system\|IMU 融合]] → [[visual-slam\|视觉 SLAM]] → [[lidar-system\|激光雷达]] |
| 🔧 硬件工程师 | [[schematic-design\|原理图]] → [[pcb-layout\|PCB]] → [[product-design\|产品设计]] |
| 🧪 测试工程师 | [[testing-system\|测试体系]] → [[env-testing\|环境测试]] → [[it-infrastructure\|实验室]] |
| 📋 产品经理 | [[proposal-template\|产品提案]] → [[architecture-template\|架构设计]] → [[dev-process\|项目管理]] |
| 🚀 DevOps | [[ci-cd-pipeline\|CI/CD]] → [[ota-system\|OTA]] → [[it-infrastructure\|IT 架构]] |

### 按产品
| 产品 | 核心模块 |
|------|----------|
| 🚁 无人机 | [[flight-controller-firmware\|飞控]] → [[camera-sensor\|相机]] → [[video-transmission\|图传]] |
| 📱 手持云台 | [[gimbal-control\|云台]] → [[imu-system\|IMU]] → [[camera-sensor\|相机]] |
| 🤖 扫地机器人 | [[lidar-system\|LiDAR]] → [[visual-slam\|SLAM]] → [[esc-control\|电机]] |
| 🖨️ 3D打印机 | [[esc-control\|步进驱动]] → [[firmware-upgrade\|固件]] → [[pcb-layout\|PCB]] |

---

## 🏗️ 知识体系 (16 层)

### L1 基础能力
| 模块 | 内容 | 入口 |
|------|------|------|
| ⚡ 电子基础 | 电路/运放/电源/数字电路 | 01-foundations |
| 💻 C 语言 | 指针/内存/状态机/Makefile | 01-foundations |
| 🐧 Linux 基础 | 内核/驱动/设备树/构建 | 01-foundations |
| ⏱️ RTOS | FreeRTOS/RT-Thread/任务调度 | 01-foundations |

### L2 平台技术
| 模块 | 内容 | 入口 |
|------|------|------|
| 🤖 Android | Framework/HAL/系统/安全/构建 | [[framework-customization\|Android]] |
| ⚡ STM32 | MCU 驱动/Bootloader/OTA | [[firmware-upgrade\|STM32]] |
| 🐧 Linux SoC | 驱动/设备树/系统定制 | [[linux-driver-dev\|Linux 驱动]] |
| ⏱️ FreeRTOS | 任务/队列/信号量/中断 | [[freertos-drivers\|RTOS]] |

### L3 传感器
| 模块 | 内容 | 入口 |
|------|------|------|
| 📷 相机 | Sensor/ISP/AF/3A/V4L2 | [[camera-sensor\|相机]] |
| 📐 IMU | 传感器/姿态融合/校准/振动 | [[imu-system\|IMU]] |
| 📍 GPS | GNSS/RTK/天线/组合导航 | [[gps-system\|GPS]] |
| 🧭 指南针 | 磁力计/校准/干扰/航向 | [[compass-system\|指南针]] |
| 📡 激光雷达 | ToF/点云/SLAM/驱动 | [[lidar-system\|LiDAR]] |

### L4 执行器
| 模块 | 内容 | 入口 |
|------|------|------|
| ⚡ ESC | BLDC/FOC/DShot/保护 | [[esc-control\|ESC]] |
| 🎥 云台 | 三轴控制/增稳/跟踪 | [[gimbal-control\|云台]] |

### L5 算法
| 模块 | 内容 | 入口 |
|------|------|------|
| 👁️ 视觉 | SLAM/避障/跟踪/深度 | [[visual-slam\|视觉]] |
| 🎯 控制 | PID/EKF/混控/失联保护 | [[flight-controller-firmware\|飞控]] |

### L6 通信
| 模块 | 内容 | 入口 |
|------|------|------|
| 📡 协议 | MQTT/BLE/WiFi/UART/SPI | [[protocol-details\|协议]] |
| 📡 图传 | H.264/H.265/FEC/天线/链路 | [[video-transmission\|图传]] |

### L7 硬件设计
| 模块 | 内容 | 入口 |
|------|------|------|
| 📐 原理图 | 电源/时钟/复位/ESD | [[schematic-design\|原理图]] |
| 🔲 PCB | 叠层/阻抗/布线/EMC | [[pcb-layout\|PCB]] |
| 🏭 制造 | SMT/DIP/组装/DFM | [[pcba-process\|制造]] |

### L8 软件工程
| 模块 | 内容 | 入口 |
|------|------|------|
| 🔄 CI/CD | GitLab CI/Jenkins/自动化 | [[ci-cd-pipeline\|CI/CD]] |
| 🧪 测试 | 单元/HIL/自动化/Robot | [[testing-system\|测试]] |

### L9 安全
| 模块 | 内容 | 入口 |
|------|------|------|
| 🔒 安全启动 | 信任链/RSA/防回滚 | [[secure-boot-impl\|安全启动]] |
| 🔑 密钥管理 | 生成/存储/轮换/销毁 | [[key-mgmt\|密钥]] |

### L10 可靠性
| 模块 | 内容 | 入口 |
|------|------|------|
| 🌡️ 环境测试 | 温湿度/盐雾/防水/EMC | [[env-testing\|环境测试]] |
| 🔨 机械测试 | 跌落/振动/按键寿命 | [[mechanical-testing\|机械测试]] |

### L11 产品线
| 产品 | 核心技术 | 入口 |
|------|----------|------|
| 📱 手持云台 | FOC增稳/人脸跟踪/低功耗 | [[handheld-gimbal\|手持云台]] |
| 🤖 扫地机器人 | LDS SLAM/全覆盖/AI避障 | [[robot-vacuum\|扫地机]] |
| 🖨️ 3D打印机 | 步进控制/温控/切片 | [[3d-printer\|3D打印机]] |

### L12 后台系统
| 模块 | 内容 | 入口 |
|------|------|------|
| 🔄 OTA | 升级管理/灰度/回滚/统计 | [[ota-system\|OTA]] |

### L13 IT 基础设施
| 模块 | 内容 | 入口 |
|------|------|------|
| 🛠️ 研发工具 | GitLab/Jenkins/实验室/监控 | [[it-infrastructure\|IT 架构]] |

### L14 产品管理
| 模块 | 内容 | 入口 |
|------|------|------|
| 📋 提案 | 市场/竞品/商业论证 | [[proposal-template\|提案]] |
| 🏗️ 架构 | 系统/软硬件/接口 | [[architecture-template\|架构]] |
| ⚠️ 风险 | 评估/缓解/跟踪 | [[risk-management\|风险]] |
| 📊 项目 | 流程/敏捷/质量 | [[dev-process\|项目管理]] |
| 🚀 发布 | DFM/热设计/检查清单 | [[product-design\|产品设计]] |

### L15 培训体系
| 级别 | 内容 | 入口 |
|------|------|------|
| L0 入门 | 电子/C语言/Linux (4周) | [[learning-paths\|学习路径]] |
| L1 核心 | STM32/驱动/硬件 (8周) | [[learning-paths\|学习路径]] |
| L2 产品线 | 无人机/扫地机/打印机 (6周) | [[learning-paths\|学习路径]] |
| L3 实战 | 定义/架构/量产/发布 (4周) | [[learning-paths\|学习路径]] |

### L16 市场与网站
| 模块 | 内容 | 入口 |
|------|------|------|
| 📣 市场 | 品牌/内容/渠道/发布会 | [[marketing-strategy\|市场]] |
| 🌐 网站 | 设计/开发/SEO/分析 | [[web-dev\|网站]] |

---

## 🔗 技术全景图

```
┌─────────────────────────────────────────────────────────────┐
│  产品线:  无人机 │ 手持云台 │ 扫地机器人 │ 3D打印机          │
├─────────────────────────────────────────────────────────────┤
│  传感器:  相机 │ IMU │ GPS │ 指南针 │ LiDAR                 │
│  执行器:  ESC │ 云台 │ 电机                                  │
│  算法:    控制 │ 视觉 │ SLAM │ 融合                         │
│  通信:    协议 │ 图传 │ 遥测                                │
├─────────────────────────────────────────────────────────────┤
│  平台:    STM32 │ Linux │ Android │ FreeRTOS                 │
│  硬件:    原理图 │ PCB │ 制造 │ 热设计                      │
│  软件:    CI/CD │ 测试 │ DevOps                             │
│  安全:    安全启动 │ 密钥管理                                │
├─────────────────────────────────────────────────────────────┤
│  后台:    OTA │ 云架构 │ 设备管理                            │
│  IT:      GitLab │ Jenkins │ 实验室 │ 监控                   │
│  管理:    提案 │ 架构 │ 风险 │ 项目 │ 发布                   │
│  培训:    L0→L1→L2→L3→L4                                    │
└─────────────────────────────────────────────────────────────┘
```
