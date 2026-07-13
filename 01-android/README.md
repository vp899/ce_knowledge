# 01 - Android 开发

## 模块概述

消费电子产品中 Android 系统的定制、移植、应用开发与构建。

## 目录结构

```
01-android/
├── frameworks/     # Android Framework 定制
├── system/         # 系统层（HAL、Init、Native）
├── apps/           # 系统应用与预装应用
├── build/          # 构建系统（Soong/Make、OTA）
└── security/       # Android 安全（SELinux、签名、密钥）
```

## 核心知识领域

### 1. 系统定制与移植
- AOSP 源码结构与编译流程
- Board Support Package (BSP) 集成
- Device Tree 与硬件抽象层 (HAL)
- 内核配置与驱动适配
- 分区规划（system、vendor、boot、recovery）

### 2. Framework 定制
- SystemServer 服务扩展
- WindowManager / InputManager 定制
- 电源管理（PowerManager、Suspend/Resume）
- OTA 升级框架（UpdateEngine / RecoverySystem）
- 多用户与访客模式

### 3. 应用开发
- 系统应用（Settings、Launcher、SystemUI）
- 硬件相关应用（Camera、Audio、Sensor）
- ContentProvider 与系统数据共享
- AIDL / HIDL 跨进程通信

### 4. 构建与发布
- Soong (Blueprint) 构建系统
- Makefile 规则与模块定义
- OTA 包生成与签名
- A/B 分区无缝升级
- 增量包 (Incremental OTA) 制作

### 5. 安全
- SELinux 策略配置
- 签名体系（platform、media、shared、testkey）
- Keymaster / Keymint HAL
- Verified Boot (dm-verity)
- 权限管理与隐私保护

## 关键工具链

| 工具 | 用途 |
|------|------|
| `repo` | AOSP 多仓库管理 |
| `adb` | 设备调试与文件传输 |
| `fastboot` | 刷机与分区操作 |
| `mkbootimg` | boot 镜像打包 |
| `signapk` | APK / OTA 签名 |
| `simg2img` | sparse image 转换 |

## 参考资源

- [AOSP 官方文档](https://source.android.com/)
- [Android CDD (Compatibility Definition)](https://source.android.com/docs/compatibility/cdd)
- [Treble 架构](https://source.android.com/docs/core/architecture)
