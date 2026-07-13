#!/usr/bin/env python3
"""Convert knowledge base to Obsidian format with wiki-links and frontmatter."""

import os
import re
from pathlib import Path

KB_ROOT = Path(".")

# ──────────────────────────────────────────────
# 1. 定义所有文件的元数据 (用于 frontmatter + 链接)
# ──────────────────────────────────────────────

FILE_META = {
    # ── 01 Android ──
    "01-android/README.md": {
        "title": "Android 开发",
        "tags": ["android", "index"],
        "aliases": ["Android 模块总览"],
    },
    "01-android/frameworks/framework-customization.md": {
        "title": "Android Framework 定制开发",
        "tags": ["android", "framework", "system-server", "hal"],
        "aliases": ["Framework 定制"],
    },
    "01-android/system/system-internals.md": {
        "title": "Android 系统层开发",
        "tags": ["android", "init", "native", "selinux"],
        "aliases": ["系统层"],
    },
    "01-android/build/build-system.md": {
        "title": "Android 构建系统",
        "tags": ["android", "soong", "ota", "treble"],
        "aliases": ["Soong 构建"],
    },
    "01-android/security/android-security.md": {
        "title": "Android 安全机制",
        "tags": ["android", "security", "selinux", "keymaster"],
        "aliases": ["Android 安全"],
    },
    # ── 02 STM32 ──
    "02-stm32/README.md": {
        "title": "STM32 升级",
        "tags": ["stm32", "index"],
        "aliases": ["STM32 模块总览"],
    },
    "02-stm32/upgrade/firmware-upgrade.md": {
        "title": "STM32 固件升级方案",
        "tags": ["stm32", "ota", "firmware", "upgrade"],
        "aliases": ["固件升级", "OTA 升级"],
    },
    "02-stm32/bootloader/bootloader-design.md": {
        "title": "STM32 Bootloader 开发",
        "tags": ["stm32", "bootloader", "flash"],
        "aliases": ["Bootloader"],
    },
    # ── 03 Hardware ──
    "03-hardware/README.md": {
        "title": "硬件设计",
        "tags": ["hardware", "index"],
        "aliases": ["硬件模块总览"],
    },
    "03-hardware/schematic/schematic-design.md": {
        "title": "硬件原理图设计",
        "tags": ["hardware", "schematic", "power", "esd"],
        "aliases": ["原理图设计"],
    },
    "03-hardware/pcb/pcb-layout.md": {
        "title": "PCB Layout 设计",
        "tags": ["hardware", "pcb", "layout", "emc"],
        "aliases": ["PCB 设计"],
    },
    "03-hardware/manufacturing/pcba-process.md": {
        "title": "PCBA 制造流程",
        "tags": ["hardware", "smt", "manufacturing", "bom"],
        "aliases": ["打板制造"],
    },
    # ── 04 Security ──
    "04-security/README.md": {
        "title": "安全启动",
        "tags": ["security", "index"],
        "aliases": ["安全模块总览"],
    },
    "04-security/secure-boot/secure-boot-impl.md": {
        "title": "安全启动实现",
        "tags": ["security", "secure-boot", "rsa", "trust-chain"],
        "aliases": ["Secure Boot"],
    },
    "04-security/key-management/key-mgmt.md": {
        "title": "密钥管理",
        "tags": ["security", "key-management", "hsm", "efuse"],
        "aliases": ["密钥生命周期"],
    },
    # ── 05 Drivers ──
    "05-drivers/README.md": {
        "title": "驱动开发",
        "tags": ["drivers", "index"],
        "aliases": ["驱动模块总览"],
    },
    "05-drivers/linux/linux-driver-dev.md": {
        "title": "Linux 驱动开发",
        "tags": ["drivers", "linux", "v4l2", "i2c", "platform"],
        "aliases": ["Linux 驱动"],
    },
    "05-drivers/rtos/rtos-drivers.md": {
        "title": "RTOS 驱动开发",
        "tags": ["drivers", "rtos", "freertos", "rt-thread"],
        "aliases": ["RTOS 驱动"],
    },
    # ── 06 Communication ──
    "06-communication/README.md": {
        "title": "通信协议",
        "tags": ["communication", "index"],
        "aliases": ["通信模块总览"],
    },
    "06-communication/protocols/protocol-details.md": {
        "title": "通信协议详解",
        "tags": ["communication", "mqtt", "ble", "wifi", "uart", "spi"],
        "aliases": ["协议详解"],
    },
    # ── 07 Reliability ──
    "07-reliability/README.md": {
        "title": "可靠性测试",
        "tags": ["reliability", "index"],
        "aliases": ["可靠性模块总览"],
    },
    "07-reliability/environmental/env-testing.md": {
        "title": "可靠性测试标准",
        "tags": ["reliability", "environmental", "emc", "temperature"],
        "aliases": ["环境测试"],
    },
    "07-reliability/mechanical/mechanical-testing.md": {
        "title": "产品可靠性测试",
        "tags": ["reliability", "mechanical", "drop", "vibration"],
        "aliases": ["机械测试"],
    },
    # ── 08 Proposal ──
    "08-proposal/README.md": {
        "title": "产品提案",
        "tags": ["proposal", "index"],
        "aliases": ["提案模块总览"],
    },
    "08-proposal/templates/proposal-template.md": {
        "title": "产品提案模板",
        "tags": ["proposal", "template", "market", "business"],
        "aliases": ["提案模板"],
    },
    # ── 09 Architecture ──
    "09-architecture/README.md": {
        "title": "架构设计",
        "tags": ["architecture", "index"],
        "aliases": ["架构模块总览"],
    },
    "09-architecture/system-design/architecture-template.md": {
        "title": "产品架构设计文档模板",
        "tags": ["architecture", "design", "template"],
        "aliases": ["架构设计文档"],
    },
    # ── 10 Risk ──
    "10-risk/README.md": {
        "title": "风险管理",
        "tags": ["risk", "index"],
        "aliases": ["风险模块总览"],
    },
    "10-risk/assessment/risk-management.md": {
        "title": "产品风险评估与管理",
        "tags": ["risk", "assessment", "mitigation"],
        "aliases": ["风险评估"],
    },
    # ── 11 Project Management ──
    "11-project-management/README.md": {
        "title": "项目管理",
        "tags": ["project-management", "index"],
        "aliases": ["项目管理模块总览"],
    },
    "11-project-management/planning/dev-process.md": {
        "title": "项目管理流程",
        "tags": ["project-management", "agile", "stage-gate", "quality"],
        "aliases": ["开发流程"],
    },
    # ── 12 Marketing ──
    "12-marketing/README.md": {
        "title": "市场宣传",
        "tags": ["marketing", "index"],
        "aliases": ["市场模块总览"],
    },
    "12-marketing/campaigns/marketing-strategy.md": {
        "title": "市场宣传策略",
        "tags": ["marketing", "brand", "content", "channels"],
        "aliases": ["营销策略"],
    },
    # ── 13 Website ──
    "13-website/README.md": {
        "title": "产品网站",
        "tags": ["website", "index"],
        "aliases": ["网站模块总览"],
    },
    "13-website/development/web-dev.md": {
        "title": "产品网站开发",
        "tags": ["website", "nextjs", "seo", "performance"],
        "aliases": ["网站开发"],
    },
    # ── 14 Camera ──
    "14-camera/README.md": {
        "title": "相机系统",
        "tags": ["camera", "index"],
        "aliases": ["相机模块总览"],
    },
    "14-camera/sensor/camera-sensor.md": {
        "title": "图像传感器",
        "tags": ["camera", "sensor", "imx", "isp", "mipi", "v4l2"],
        "aliases": ["CMOS Sensor", "图像传感器"],
    },
    # ── 15 Image Transmission ──
    "15-image-transmission/README.md": {
        "title": "图传系统",
        "tags": ["image-transmission", "index"],
        "aliases": ["图传模块总览"],
    },
    "15-image-transmission/encoding/video-transmission.md": {
        "title": "图传系统（视频传输链路）",
        "tags": ["image-transmission", "h264", "h265", "fec", "antenna"],
        "aliases": ["视频传输", "图传链路"],
    },
    # ── 16 Flight Controller ──
    "16-flight-controller/README.md": {
        "title": "飞控系统",
        "tags": ["flight-controller", "index"],
        "aliases": ["飞控模块总览"],
    },
    "16-flight-controller/firmware/flight-controller-firmware.md": {
        "title": "飞控系统",
        "tags": ["flight-controller", "pid", "ekf", "failsafe", "rtl"],
        "aliases": ["飞控固件", "飞控算法"],
    },
    # ── 17 Gimbal ──
    "17-gimbal/README.md": {
        "title": "云台系统",
        "tags": ["gimbal", "index"],
        "aliases": ["云台模块总览"],
    },
    "17-gimbal/control/gimbal-control.md": {
        "title": "云台系统",
        "tags": ["gimbal", "foc", "bldc", "stabilization"],
        "aliases": ["云台控制", "云台驱动"],
    },
    # ── 18 Vision ──
    "18-vision/README.md": {
        "title": "视觉系统",
        "tags": ["vision", "index"],
        "aliases": ["视觉模块总览"],
    },
    "18-vision/slam/visual-slam.md": {
        "title": "视觉系统",
        "tags": ["vision", "slam", "obstacle-avoidance", "tracking", "depth"],
        "aliases": ["视觉 SLAM", "避障"],
    },
    # ── 19 Compass ──
    "19-compass/README.md": {
        "title": "指南针（磁力计）",
        "tags": ["compass", "index"],
        "aliases": ["指南针模块总览"],
    },
    "19-compass/calibration/compass-system.md": {
        "title": "指南针（磁力计）",
        "tags": ["compass", "magnetometer", "calibration", "heading"],
        "aliases": ["磁力计", "电子罗盘"],
    },
    # ── 20 IMU ──
    "20-imu/README.md": {
        "title": "IMU（惯性测量单元）",
        "tags": ["imu", "index"],
        "aliases": ["IMU 模块总览"],
    },
    "20-imu/sensor/imu-system.md": {
        "title": "IMU（惯性测量单元）",
        "tags": ["imu", "sensor", "mahony", "ekf", "vibration", "calibration"],
        "aliases": ["惯性测量", "姿态融合"],
    },
    # ── 21 GPS ──
    "21-gps/README.md": {
        "title": "GPS / GNSS",
        "tags": ["gps", "index"],
        "aliases": ["GPS 模块总览"],
    },
    "21-gps/receiver/gps-system.md": {
        "title": "GPS / GNSS 定位系统",
        "tags": ["gps", "gnss", "rtk", "navigation"],
        "aliases": ["GNSS", "RTK 定位"],
    },
    # ── 22 ESC ──
    "22-esc/README.md": {
        "title": "动力电调 (ESC)",
        "tags": ["esc", "index"],
        "aliases": ["电调模块总览"],
    },
    "22-esc/algorithm/esc-control.md": {
        "title": "动力电调 (ESC)",
        "tags": ["esc", "bldc", "foc", "dshot"],
        "aliases": ["ESC 控制", "无刷电调"],
    },
    # ── 23 LiDAR ──
    "23-lidar/README.md": {
        "title": "激光雷达 (LiDAR)",
        "tags": ["lidar", "index"],
        "aliases": ["LiDAR 模块总览"],
    },
    "23-lidar/tof/lidar-system.md": {
        "title": "激光雷达 (LiDAR)",
        "tags": ["lidar", "tof", "slam", "point-cloud"],
        "aliases": ["激光雷达", "LiDAR 测距"],
    },
}

# ──────────────────────────────────────────────
# 2. 定义交叉引用映射
# ──────────────────────────────────────────────

# 关键词 → 文件路径 (用于自动插入 wiki-link)
CROSS_REF_MAP = {
    # 安全相关
    "安全启动": "04-security/secure-boot/secure-boot-impl.md",
    "Secure Boot": "04-security/secure-boot/secure-boot-impl.md",
    "密钥管理": "04-security/key-management/key-mgmt.md",
    "SELinux": "01-android/security/android-security.md",
    "签名体系": "01-android/security/android-security.md",
    "dm-verity": "01-android/security/android-security.md",
    "Keymaster": "01-android/security/android-security.md",
    "eFuse": "04-security/key-management/key-mgmt.md",

    # STM32 相关
    "Bootloader": "02-stm32/bootloader/bootloader-design.md",
    "固件升级": "02-stm32/upgrade/firmware-upgrade.md",
    "OTA": "02-stm32/upgrade/firmware-upgrade.md",
    "Flash 分区": "02-stm32/bootloader/bootloader-design.md",

    # 硬件相关
    "原理图": "03-hardware/schematic/schematic-design.md",
    "PCB": "03-hardware/pcb/pcb-layout.md",
    "去耦电容": "03-hardware/schematic/schematic-design.md",
    "ESD": "03-hardware/schematic/schematic-design.md",
    "SMT": "03-hardware/manufacturing/pcba-process.md",
    "BOM": "03-hardware/manufacturing/pcba-process.md",
    "DFM": "03-hardware/manufacturing/pcba-process.md",

    # 驱动相关
    "V4L2": "14-camera/sensor/camera-sensor.md",
    "I2C 驱动": "05-drivers/linux/linux-driver-dev.md",
    "Platform 驱动": "05-drivers/linux/linux-driver-dev.md",
    "FreeRTOS": "05-drivers/rtos/rtos-drivers.md",
    "RT-Thread": "05-drivers/rtos/rtos-drivers.md",

    # 通信相关
    "MQTT": "06-communication/protocols/protocol-details.md",
    "BLE": "06-communication/protocols/protocol-details.md",
    "DShot": "22-esc/algorithm/esc-control.md",
    "PWM": "22-esc/algorithm/esc-control.md",

    # 可靠性相关
    "EMC": "07-reliability/environmental/env-testing.md",
    "跌落测试": "07-reliability/mechanical/mechanical-testing.md",
    "温度循环": "07-reliability/environmental/env-testing.md",
    "MTBF": "07-reliability/mechanical/mechanical-testing.md",

    # 产品管理
    "产品提案": "08-proposal/templates/proposal-template.md",
    "架构设计": "09-architecture/system-design/architecture-template.md",
    "风险评估": "10-risk/assessment/risk-management.md",
    "项目管理": "11-project-management/planning/dev-process.md",
    "EVT": "11-project-management/planning/dev-process.md",
    "DVT": "11-project-management/planning/dev-process.md",
    "PVT": "11-project-management/planning/dev-process.md",

    # 相机相关
    "ISP": "14-camera/sensor/camera-sensor.md",
    "MIPI CSI": "14-camera/sensor/camera-sensor.md",
    "图像传感器": "14-camera/sensor/camera-sensor.md",
    "自动曝光": "14-camera/sensor/camera-sensor.md",
    "自动白平衡": "14-camera/sensor/camera-sensor.md",
    "自动对焦": "14-camera/sensor/camera-sensor.md",

    # 图传相关
    "H.264": "15-image-transmission/encoding/video-transmission.md",
    "H.265": "15-image-transmission/encoding/video-transmission.md",
    "FEC": "15-image-transmission/encoding/video-transmission.md",
    "链路预算": "15-image-transmission/encoding/video-transmission.md",

    # 飞控相关
    "PID": "16-flight-controller/firmware/flight-controller-firmware.md",
    "姿态控制": "16-flight-controller/firmware/flight-controller-firmware.md",
    "失联保护": "16-flight-controller/firmware/flight-controller-firmware.md",
    "返航": "16-flight-controller/firmware/flight-controller-firmware.md",
    "电机混控": "16-flight-controller/firmware/flight-controller-firmware.md",

    # 云台相关
    "FOC": "17-gimbal/control/gimbal-control.md",
    "云台": "17-gimbal/control/gimbal-control.md",
    "SVPWM": "17-gimbal/control/gimbal-control.md",

    # 视觉相关
    "SLAM": "18-vision/slam/visual-slam.md",
    "避障": "18-vision/slam/visual-slam.md",
    "目标跟踪": "18-vision/slam/visual-slam.md",
    "VIO": "18-vision/slam/visual-slam.md",
    "双目视觉": "18-vision/slam/visual-slam.md",

    # 指南针相关
    "磁力计": "19-compass/calibration/compass-system.md",
    "航向": "19-compass/calibration/compass-system.md",
    "磁校准": "19-compass/calibration/compass-system.md",

    # IMU 相关
    "互补滤波": "20-imu/sensor/imu-system.md",
    "Mahony": "20-imu/sensor/imu-system.md",
    "Madgwick": "20-imu/sensor/imu-system.md",
    "EKF": "20-imu/sensor/imu-system.md",
    "四元数": "20-imu/sensor/imu-system.md",
    "陷波滤波器": "20-imu/sensor/imu-system.md",

    # GPS 相关
    "RTK": "21-gps/receiver/gps-system.md",
    "GNSS": "21-gps/receiver/gps-system.md",
    "NMEA": "21-gps/receiver/gps-system.md",
    "组合导航": "21-gps/receiver/gps-system.md",

    # ESC 相关
    "BLDC": "22-esc/algorithm/esc-control.md",
    "无刷电机": "22-esc/algorithm/esc-control.md",
    "电调": "22-esc/algorithm/esc-control.md",
    "ESC": "22-esc/algorithm/esc-control.md",

    # LiDAR 相关
    "激光雷达": "23-lidar/tof/lidar-system.md",
    "LiDAR": "23-lidar/tof/lidar-system.md",
    "点云": "23-lidar/tof/lidar-system.md",
    "ICP": "23-lidar/tof/lidar-system.md",
    "LIO-SAM": "23-lidar/tof/lidar-system.md",
}


def make_link_target(filepath: str) -> str:
    """从文件路径生成 Obsidian 链接目标 (不含 .md)"""
    p = filepath.replace(".md", "")
    # 用文件名部分作为链接 (Obsidian 自动解析)
    return Path(p).stem


def build_frontmatter(meta: dict, filepath: str) -> str:
    """生成 YAML frontmatter"""
    lines = ["---"]
    lines.append(f'title: "{meta["title"]}"')
    lines.append(f'aliases:')
    for alias in meta.get("aliases", []):
        lines.append(f'  - "{alias}"')
    lines.append(f'tags:')
    for tag in meta.get("tags", []):
        lines.append(f'  - {tag}')
    # 确定所属模块
    module = filepath.split("/")[0]
    lines.append(f'module: "{module}"')
    lines.append(f'status: active')
    lines.append("---")
    return "\n".join(lines) + "\n\n"


def add_wiki_links(content: str, current_file: str) -> str:
    """在内容中插入 wiki-links (仅首次出现)"""
    # 按关键词长度降序排列，避免短关键词先匹配
    sorted_refs = sorted(CROSS_REF_MAP.keys(), key=len, reverse=True)

    linked_terms = set()

    for term in sorted_refs:
        target_file = CROSS_REF_MAP[term]
        # 不链接自己
        if target_file == current_file:
            continue
        # 已经链接过的跳过
        if term in linked_terms:
            continue

        link_name = make_link_target(target_file)

        # 只替换第一次出现，且不在代码块中
        # 使用简单的字符串替换，替换第一次出现
        # 先检查是否存在
        if term in content:
            # 找到第一次出现的位置
            idx = content.find(term)
            # 检查是否在代码块内 (简单的启发式检查)
            before = content[:idx]
            # 计算前面的 ``` 数量
            fence_count = before.count("```")
            if fence_count % 2 == 1:
                # 在代码块内，跳过
                linked_terms.add(term)
                continue

            # 替换第一次出现
            replacement = f"[[{link_name}|{term}]]"
            content = content[:idx] + replacement + content[idx + len(term):]
            linked_terms.add(term)

    return content


def add_see_also(content: str, current_file: str) -> str:
    """在文件末尾添加相关链接区"""
    # 根据模块确定相关链接
    module = current_file.split("/")[0] if "/" in current_file else ""

    related = []

    # 定义模块间关联
    module_relations = {
        "01-android": [
            ("05-drivers/linux/linux-driver-dev.md", "Linux 驱动"),
            ("04-security/secure-boot/secure-boot-impl.md", "安全启动"),
            ("02-stm32/upgrade/firmware-upgrade.md", "固件升级"),
        ],
        "02-stm32": [
            ("04-security/secure-boot/secure-boot-impl.md", "安全启动"),
            ("04-security/key-management/key-mgmt.md", "密钥管理"),
            ("22-esc/algorithm/esc-control.md", "ESC 控制"),
        ],
        "03-hardware": [
            ("07-reliability/environmental/env-testing.md", "可靠性测试"),
            ("03-hardware/manufacturing/pcba-process.md", "PCBA 制造"),
        ],
        "04-security": [
            ("02-stm32/bootloader/bootloader-design.md", "Bootloader"),
            ("01-android/security/android-security.md", "Android 安全"),
        ],
        "05-drivers": [
            ("01-android/frameworks/framework-customization.md", "Android Framework"),
            ("06-communication/protocols/protocol-details.md", "通信协议"),
        ],
        "06-communication": [
            ("05-drivers/linux/linux-driver-dev.md", "Linux 驱动"),
            ("15-image-transmission/encoding/video-transmission.md", "图传系统"),
        ],
        "07-reliability": [
            ("03-hardware/schematic/schematic-design.md", "原理图设计"),
            ("11-project-management/planning/dev-process.md", "项目管理"),
        ],
        "08-proposal": [
            ("10-risk/assessment/risk-management.md", "风险评估"),
            ("12-marketing/campaigns/marketing-strategy.md", "市场宣传"),
        ],
        "09-architecture": [
            ("08-proposal/templates/proposal-template.md", "产品提案"),
            ("16-flight-controller/firmware/flight-controller-firmware.md", "飞控架构"),
        ],
        "10-risk": [
            ("11-project-management/planning/dev-process.md", "项目管理"),
            ("08-proposal/templates/proposal-template.md", "产品提案"),
        ],
        "11-project-management": [
            ("10-risk/assessment/risk-management.md", "风险评估"),
            ("09-architecture/system-design/architecture-template.md", "架构设计"),
        ],
        "12-marketing": [
            ("08-proposal/templates/proposal-template.md", "产品提案"),
            ("13-website/development/web-dev.md", "产品网站"),
        ],
        "13-website": [
            ("12-marketing/campaigns/marketing-strategy.md", "市场宣传"),
        ],
        "14-camera": [
            ("15-image-transmission/encoding/video-transmission.md", "图传系统"),
            ("17-gimbal/control/gimbal-control.md", "云台系统"),
            ("05-drivers/linux/linux-driver-dev.md", "Linux 驱动"),
        ],
        "15-image-transmission": [
            ("14-camera/sensor/camera-sensor.md", "相机系统"),
            ("06-communication/protocols/protocol-details.md", "通信协议"),
        ],
        "16-flight-controller": [
            ("20-imu/sensor/imu-system.md", "IMU"),
            ("21-gps/receiver/gps-system.md", "GPS"),
            ("19-compass/calibration/compass-system.md", "指南针"),
            ("22-esc/algorithm/esc-control.md", "ESC"),
            ("17-gimbal/control/gimbal-control.md", "云台"),
        ],
        "17-gimbal": [
            ("14-camera/sensor/camera-sensor.md", "相机系统"),
            ("20-imu/sensor/imu-system.md", "IMU"),
            ("22-esc/algorithm/esc-control.md", "ESC 控制"),
        ],
        "18-vision": [
            ("14-camera/sensor/camera-sensor.md", "相机系统"),
            ("23-lidar/tof/lidar-system.md", "激光雷达"),
            ("20-imu/sensor/imu-system.md", "IMU"),
        ],
        "19-compass": [
            ("20-imu/sensor/imu-system.md", "IMU"),
            ("16-flight-controller/firmware/flight-controller-firmware.md", "飞控"),
        ],
        "20-imu": [
            ("19-compass/calibration/compass-system.md", "指南针"),
            ("16-flight-controller/firmware/flight-controller-firmware.md", "飞控"),
            ("17-gimbal/control/gimbal-control.md", "云台"),
        ],
        "21-gps": [
            ("20-imu/sensor/imu-system.md", "IMU"),
            ("16-flight-controller/firmware/flight-controller-firmware.md", "飞控"),
        ],
        "22-esc": [
            ("16-flight-controller/firmware/flight-controller-firmware.md", "飞控"),
            ("17-gimbal/control/gimbal-control.md", "云台"),
        ],
        "23-lidar": [
            ("18-vision/slam/visual-slam.md", "视觉系统"),
            ("20-imu/sensor/imu-system.md", "IMU"),
        ],
    }

    if module in module_relations:
        for target_path, label in module_relations[module]:
            if target_path != current_file:
                link_name = make_link_target(target_path)
                related.append(f"[[{link_name}|{label}]]")

    if not related:
        return content

    # 检查是否已有相关链接区
    if "## 相关链接" in content or "## 参见" in content:
        return content

    section = "\n---\n\n## 相关链接\n\n"
    for link in related:
        section += f"- {link}\n"

    return content.rstrip() + section


def process_file(filepath: str):
    """处理单个文件"""
    full_path = KB_ROOT / filepath

    if not full_path.exists():
        print(f"  SKIP (not found): {filepath}")
        return

    content = full_path.read_text(encoding="utf-8")

    # 获取元数据
    meta = FILE_META.get(filepath)
    if not meta:
        print(f"  SKIP (no meta): {filepath}")
        return

    # 检查是否已经有 frontmatter
    if content.startswith("---"):
        # 已经有 frontmatter，跳过
        print(f"  SKIP (has frontmatter): {filepath}")
        return

    # 1. 生成 frontmatter
    frontmatter = build_frontmatter(meta, filepath)

    # 2. 插入 wiki-links
    content_with_links = add_wiki_links(content, filepath)

    # 3. 添加相关链接
    content_with_related = add_see_also(content_with_links, filepath)

    # 4. 组合
    final_content = frontmatter + content_with_related

    # 5. 写回
    full_path.write_text(final_content, encoding="utf-8")
    print(f"  DONE: {filepath}")


def create_master_moc():
    """创建主 MOC (Map of Content)"""
    moc = """---
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
"""

    (KB_ROOT / "MOC.md").write_text(moc, encoding="utf-8")
    print("  DONE: MOC.md")


def create_tags_index():
    """创建标签索引页"""
    content = """---
title: "标签索引"
aliases:
  - "Tags"
  - "标签"
tags:
  - index
status: active
---

# 🏷️ 标签索引

## 按技术栈

```dataview
TABLE length(rows) AS "文件数"
FROM #android OR #stm32 OR #hardware OR #security
GROUP BY tags
SORT length(rows) DESC
```

## 按无人机子系统

```dataview
TABLE length(rows) AS "文件数"
FROM #flight-controller OR #camera OR #gimbal OR #vision OR #imu OR #gps OR #esc OR #lidar OR #compass OR #image-transmission
GROUP BY tags
SORT length(rows) DESC
```

## 热门标签

#android #stm32 #hardware #security #drivers #communication #reliability #flight-controller #camera #gimbal #vision #imu #gps #esc #lidar #compass #image-transmission #pid #foc #slam #ekf #rtk #ota #bootloader #isp #mipi #v4l2 #mqtt #ble #wifi #emc #selinux #efuse #hsm #bldc #dshot #h264 #h265 #fec #mimo
"""

    (KB_ROOT / "tags.md").write_text(content, encoding="utf-8")
    print("  DONE: tags.md")


# ──────────────────────────────────────────────
# 主函数
# ──────────────────────────────────────────────

if __name__ == "__main__":
    print("=== 转换知识库为 Obsidian 格式 ===\n")

    # 处理所有文件
    for filepath in sorted(FILE_META.keys()):
        process_file(filepath)

    # 创建 MOC
    print("\n=== 创建 MOC ===")
    create_master_moc()

    # 创建标签索引
    print("\n=== 创建标签索引 ===")
    create_tags_index()

    print("\n=== 完成 ===")
