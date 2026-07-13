---
title: "STM32 升级"
aliases:
  - "STM32 模块总览"
tags:
  - stm32
  - index
module: "02-stm32"
status: active
---

# 02 - STM32 升级

## 模块概述

STM32 微控制器[[firmware-upgrade|固件升级]]方案设计、[[bootloader-design|Bootloader]] 开发、[[firmware-upgrade|OTA]] 实现。

## 目录结构

```
02-stm32/
├── upgrade/        # 升级方案设计（OTA、有线、SD卡）
├── bootloader/     # Bootloader 开发
├── firmware/       # 固件工程与构建
└── peripherals/    # 外设驱动与通信接口
```

## 核心知识领域

### 1. 固件升级方案

#### 升级方式对比
| 方式 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| UART 串口 | 简单可靠 | 速度慢、需连线 | 开发调试、产线 |
| USB DFU | 速度快 | 需 USB 连接 | 产线烧录 |
| OTA ([[protocol-details|BLE]]/WiFi) | 无线便捷 | 复杂度高 | 量产产品 |
| SD 卡 | 无需连接 | 用户操作 | 离线升级 |
| A/B 分区 | 无缝回滚 | Flash 占用大 | 高可靠性产品 |

#### OTA 升级流程
```
[服务器] --推送升级包--> [手机APP] --BLE/WiFi--> [设备Bootloader]
                                                        |
                                                   [校验签名]
                                                        |
                                                   [擦除Flash]
                                                        |
                                                   [写入新固件]
                                                        |
                                                   [校验CRC/SHA]
                                                        |
                                                   [跳转运行]
```

### 2. Bootloader 设计
- 启动流程：Boot0 → Bootloader → Application
- [[bootloader-design|Flash 分区]]布局设计
- 固件完整性校验（CRC32、SHA256、RSA 签名）
- 回滚机制与看门狗保护
- 双 Bank 升级（STM32L4/H7 支持）

### 3. Flash 管理
- Flash 读写保护 (RDP/WRP)
- Option Bytes 配置
- EEPROM 模拟（Flash 存储参数）
- 断电保护与掉电恢复策略

### 4. 常用 STM32 系列选型

| 系列 | 主频 | Flash | 特点 | 典型应用 |
|------|------|-------|------|----------|
| STM32F1 | 72MHz | 64-512K | 入门经典 | 简单控制 |
| STM32F4 | 168MHz | 512K-2M | 高性能 | 音频、图形 |
| STM32L4 | 80MHz | 256K-1M | 低功耗 | 穿戴、IoT |
| STM32H7 | 480MHz | 1-2M | 旗舰 | HMI、AI |
| STM32G4 | 170MHz | 128-512K | 混合信号 | 电机控制 |
| STM32U5 | 160MHz | 1-4M | 超低功耗 | 可穿戴 |

## 关键工具链

| 工具 | 用途 |
|------|------|
| STM32CubeMX | 引脚配置与代码生成 |
| STM32CubeIDE | 集成开发环境 |
| STM32CubeProgrammer | 烧录与 Option Bytes |
| OpenOCD | 开源调试器 |
| J-Link | SEGGER 调试探针 |
| ST-Link | ST 官方调试器 |

## 通信接口

- **UART**：调试串口、AT 指令
- **SPI**：Flash、显示屏、传感器
- **I2C**：EEPROM、RTC、传感器
- **CAN**：汽车电子、工业控制
- **USB**：HID、CDC、MSC、DFU
---

## 相关链接

- [[secure-boot-impl|安全启动]]
- [[key-mgmt|密钥管理]]
- [[esc-control|ESC 控制]]
