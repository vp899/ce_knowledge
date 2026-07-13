---
title: "STM32 固件升级方案"
tags: [stm32, ota, firmware, upgrade]
module: "02-platforms"
---
# STM32 固件升级方案

## 核心内容
- A/B 升级架构
- Bootloader 设计 (启动流程/Flash 分区/签名验证)
- 通信协议 (帧格式/命令/状态机)
- BLE OTA 无线升级
- Flash 驱动 (擦除/写入/读取)
- 固件打包工具 (Python)

## 相关链接
- [[bootloader-design|Bootloader]]
- [[secure-boot-impl|安全启动]]
- [[ota-system|OTA 后台]]
- [[esc-control|ESC 控制]]
