level: beginner
---
title: "IT 基础设施支撑研发"
aliases:
  - "研发 IT"
  - "IT 架构"
  - "研发工具链"
tags:
  - it-infra
  - dev-tools
  - lab
  - build-farm
  - monitoring
module: "13-it-infra"
status: active
---

# IT 基础设施支撑研发体系

## 概述

本文介绍 dev-tools 领域的 beginner 级别知识。

完成本文学习后，你将能够：

- 掌握本模块的核心概念和原理
- 理解关键技术的实现方法
- 能够应用到实际项目中

## 背景知识

### 相关概念

### 前置知识

- C 语言基础
- 嵌入式开发基础
- 相关模块的初级知识

### 学习建议

- 准备开发板进行动手实践
- 边学边做，不要只看不练
- 遇到问题先自己思考再查资料

## 核心内容

### 1. 研发 IT 架构全景

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     研发 IT 架构全景                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │                        研发人员                                    │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐             │ │
│  │  │ 硬件组   │ │ 固件组   │ │ 算法组   │ │ 测试组   │             │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘             │ │
│  └───────────────────────────────┬───────────────────────────────────┘ │
│                                  │                                      │
│  ┌───────────────────────────────┴───────────────────────────────────┐ │
│  │                        研发工具层                                   │ │
│  │                                                                    │ │
│  │  代码管理      构建系统       测试系统       文档系统               │ │
│  │  ┌────────┐   ┌────────┐    ┌────────┐    ┌────────┐             │ │
│  │  │ GitLab │   │Jenkins │    │ Robot  │    │Confluence│            │ │
│  │  │ Server │   │ CI/CD  │    │Framework│   │ Wiki    │            │ │
│  │  └────────┘   └────────┘    └────────┘    └────────┘             │ │
│  │                                                                    │ │
│  │  项目管理      制品管理       代码质量       通信协作               │ │
│  │  ┌────────┐   ┌────────┐    ┌────────┐    ┌────────┐             │ │
│  │  │  Jira  │   │ Nexus  │    │SonarQube│   │Slack/飞书│            │ │
│  │  │        │   │ Artifactory│ │        │    │        │             │ │
│  │  └────────┘   └────────┘    └────────┘    └────────┘             │ │
│  └───────────────────────────────┬───────────────────────────────────┘ │
│                                  │                                      │
│  ┌───────────────────────────────┴───────────────────────────────────┐ │
│  │                        基础设施层                                   │ │
│  │                                                                    │ │
│  │  代码托管        构建农场         测试农场          制品存储        │ │
│  │  ┌────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐      │ │
│  │  │ GitLab │    │ Jenkins  │    │ HIL 测试台│    │ MinIO    │      │ │
│  │  │ Server │    │ Agent ×N │    │ 设备池   │    │ S3 兼容  │      │ │
│  │  └────────┘    └──────────┘    └──────────┘    └──────────┘      │ │
│  │                                                                    │ │
│  │  容器平台        镜像仓库         监控告警          日志中心        │ │
│  │  ┌────────┐    ┌────────┐    ┌──────────┐    ┌──────────┐      │ │
│  │  │  K8s   │    │Harbor  │    │Prometheus│    │ ELK      │      │ │
│  │  │        │    │        │    │ Grafana  │    │ Stack    │      │ │
│  │  └────────┘    └────────┘    └──────────┘    └──────────┘      │ │
│  └───────────────────────────────┬───────────────────────────────────┘ │
│                                  │                                      │
│  ┌───────────────────────────────┴───────────────────────────────────┐ │
│  │                        实验室设备层                                 │ │
│  │                                                                    │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐             │ │
│  │  │ 测试机台 │ │ 烧录设备 │ │ 测量仪器 │ │ 环境设备 │             │ │
│  │  │ (无人机) │ │ (J-Link) │ │ (示波器) │ │ (温箱)   │             │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘             │ │
│  └───────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2. 工具链部署方案

### 服务器规划
```
研发服务器资源规划 (30 人团队):

┌──────────────┬──────────────┬────────────┬───────────────────┐
│  服务器       │  配置         │  用途       │  服务              │
├──────────────┼──────────────┼────────────┼───────────────────┤
│  git-server  │ 8C 16G 500G  │ 代码托管    │ GitLab CE         │
│  ci-server   │ 16C 32G 1T   │ 构建        │ Jenkins + Agent   │
│  art-server  │ 4C 8G 2T     │ 制品存储    │ Nexus + Harbor    │
│  doc-server  │ 4C 8G 500G   │ 文档        │ Confluence        │
│  monitor     │ 4C 8G 200G   │ 监控        │ Prometheus+Grafana│
│  dev-server  │ 32C 64G 2T   │ 开发环境    │ VS Code Server    │
├──────────────┼──────────────┼────────────┼───────────────────┤
│  总计         │ 70C 136G 6.2T│            │                   │
│  云服务器年费  │ ~¥50,000/年  │            │                   │
└──────────────┴──────────────┴────────────┴───────────────────┘

小团队替代方案 (5-10 人):
├── GitLab CE: 免费, 自托管
├── Jenkins: 免费开源
├── Gitea: 轻量 Git (<100MB)
├── MinIO: 免费 S3 兼容
├── Grafana Cloud: 免费监控
└── 1 台服务器: 16C 32G 1T (~¥10,000/年)
```

### GitLab 部署
```yaml
# docker-compose.yml - GitLab CE
version: '3.8'
services:
  gitlab:
    image: gitlab/gitlab-ce:16.8-ce.0
    container_name: gitlab
    hostname: gitlab.example.com
    ports:
      - "80:80"
      - "443:443"
      - "22:22"
    volumes:
      - ./config:/etc/gitlab
      - ./logs:/var/log/gitlab
      - ./data:/var/opt/gitlab
    environment:
      GITLAB_OMNIBUS_CONFIG: |
        # 基础配置
        external_url 'https://gitlab.example.com'
        gitlab_rails['gitlab_shell_ssh_port'] = 22
        
        # 邮件配置
        gitlab_rails['smtp_enable'] = true
        gitlab_rails['smtp_address'] = "smtp.example.com"
        gitlab_rails['smtp_port'] = 587
        
        # LFS 配置 (大文件)
        gitlab_rails['lfs_enabled'] = true
        gitlab_rails['lfs_storage_path'] = "/var/opt/gitlab/lfs"
        
        # Container Registry
        registry['enable'] = true
        registry_external_url 'https://registry.example.com'
        
        # 备份
        gitlab_rails['backup_path'] = "/var/opt/gitlab/backups"
        gitlab_rails['backup_keep_time'] = 604800  # 7 天
        
        # 性能
        puma['worker_processes'] = 4
        sidekiq['max_concurrency'] = 10
    restart: always
    shm_size: '256m'
```

### Jenkins 部署
```yaml
# docker-compose.yml - Jenkins
version: '3.8'
services:
  jenkins:
    image: jenkins/jenkins:lts
    container_name: jenkins
    ports:
      - "8080:8080"
      - "50000:50000"
    volumes:
      - ./jenkins_home:/var/jenkins_home
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      JAVA_OPTS: "-Xmx4g -Xms2g"
    restart: always

  # ARM 编译 Agent
  build-agent-arm:
    image: ghcr.io/arm-none-eabi/gcc:12.2
    container_name: build-agent-arm
    volumes:
      - ./workspace:/workspace
    environment:
      JENKINS_URL: http://jenkins:8080
      JENKINS_AGENT_NAME: arm-builder
      JENKINS_SECRET: ${AGENT_SECRET}
    restart: always

  # Android 编译 Agent
  build-agent-android:
    image: ubuntu:22.04
    container_name: build-agent-android
    volumes:
      - ./android-srv:/srv
      - ./workspace:/workspace
    environment:
      JENKINS_URL: http://jenkins:8080
      JENKINS_AGENT_NAME: android-builder
      JENKINS_SECRET: ${AGENT_SECRET}
    restart: always
```

### 3. 实验室基础设施

### 测试设备管理
```
实验室设备管理系统:

┌─────────────────────────────────────────────────────────────┐
│                    设备管理平台                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  设备注册 → 设备预约 → 远程控制 → 测试执行 → 报告生成       │
│                                                              │
│  设备清单:                                                   │
│  ├── 飞控测试台 ×10                                         │
│  │   ├── Pixhawk 飞控板                                     │
│  │   ├── 电源 (可调)                                        │
│  │   ├── 示波器 (远程)                                      │
│  │   ├── 逻辑分析仪                                         │
│  │   └── J-Link 调试器                                      │
│  │                                                          │
│  ├── 云台测试台 ×5                                          │
│  │   ├── 云台模组                                           │
│  │   ├── IMU 校准夹具                                       │
│  │   └── 振动台                                             │
│  │                                                          │
│  ├── 环境测试设备 ×3                                        │
│  │   ├── 高低温箱 (-40~150°C)                               │
│  │   ├── 恒温恒湿箱                                         │
│  │   └── 盐雾箱                                             │
│  │                                                          │
│  ├── EMC 预测试 ×1                                          │
│  │   ├── 频谱分析仪                                         │
│  │   ├── 近场探头                                           │
│  │   ├── ESD 枪                                             │
│  │   └── 屏蔽箱                                             │
│  │                                                          │
│  └── 烧录/调试设备 ×20                                      │
│      ├── J-Link Ultra+                                      │
│      ├── ST-Link V3                                         │
│      ├── USB-UART 转换器                                    │
│      └── 逻辑分析仪 (Saleae)                                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 远程调试系统
```
远程调试架构:

研发人员 (远程)
    │
    ├── VPN 连接
    │
    ▼
实验室网关 (Raspberry Pi / x86 Mini PC)
    │
    ├── USB Hub → J-Link / ST-Link / USB-UART
    │
    ├── 网络摄像头 (观察设备状态)
    │
    └── 电源控制 (远程开关电源)

远程操作:
├── 固件烧录 (J-Link Remote Server)
├── 串口调试 (ser2net)
├── 示波器控制 (SCPI over TCP)
├── 电源控制 (智能插座 / 继电器)
└── 视频监控 (摄像头实时画面)

工具:
├── ser2net: 串口转网络
├── J-Link Remote Server: 远程调试
├── OpenOCD + GDB: 远程调试
├── Tailscale/ZeroTier: VPN
└── OctoPrint: 远程管理 (3D 打印机)
```

### 4. 开发环境标准化

### 开发容器 (Dev Container)
```json
// .devcontainer/devcontainer.json
{
    "name": "Embedded Dev",
    "build": {
        "dockerfile": "Dockerfile",
        "context": ".."
    },
    "runArgs": [
        "--privileged",
        "--network=host"
    ],
    "customizations": {
        "vscode": {
            "extensions": [
                "ms-vscode.cpptools",
                "ms-vscode.cmake-tools",
                "marus25.cortex-debug",
                "mcu-debug.memory-view",
                "ms-vscode.hexeditor",
                "zixuanwang.linkerscript",
                "trond-sneknes.gnu-linker-map"
            ],
            "settings": {
                "terminal.integrated.defaultProfile.linux": "bash"
            }
        }
    },
    "mounts": [
        "source=/dev/bus/usb,target=/dev/bus/usb,type=bind",
        "source=${localWorkspaceFolder},target=/workspace,type=bind"
    ],
    "postCreateCommand": "pip install -r requirements.txt && cmake -B build"
}
```

```dockerfile
# .devcontainer/Dockerfile
FROM ubuntu:22.04

# 基础工具
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    ninja-build \
    git \
    curl \
    wget \
    python3 \
    python3-pip \
    usbutils \
    && rm -rf /var/lib/apt/lists/*

# ARM 工具链
RUN wget -qO- https://developer.arm.com/-/media/Files/downloads/gnu/12.2.rel1/binrel/arm-gnu-toolchain-12.2.rel1-x86_64-arm-none-eabi.tar.xz | \
    tar -xJ -C /opt/
ENV PATH="/opt/arm-gnu-toolchain-12.2.rel1-x86_64-arm-none-eabi/bin:${PATH}"

# OpenOCD
RUN apt-get update && apt-get install -y openocd && rm -rf /var/lib/apt/lists/*

# Python 工具
RUN pip3 install \
    pyserial \
    pyocd \
    intelhex \
    cryptography \
    pytest \
    robotframework

# 代码质量
RUN apt-get update && apt-get install -y \
    cppcheck \
    clang-format \
    clang-tidy \
    valgrind \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
```

### 5. 监控与告警

### 研发效能监控
```
研发效能指标:

代码质量:
├── 代码评审覆盖率: >90%
├── 单元测试覆盖率: >80%
├── 静态分析 Bug 密度: <5/KLOC
├── 技术债务比率: <10%
└── SonarQube Quality Gate: Pass

构建效率:
├── 构建成功率: >95%
├── 平均构建时间: <10min
├── 构建排队时间: <5min
├── 日构建次数: 50-200
└── 构建资源利用率: 60-80%

测试效率:
├── 测试用例通过率: >98%
├── 自动化测试比例: >70%
├── 缺陷逃逸率: <5%
├── 测试执行时间: <30min
└── 测试环境可用率: >95%

交付效率:
├── 需求交付周期: <2 周
├── 部署频率: 每周
├── 变更失败率: <10%
├── 故障恢复时间: <1h
└── 发布成功率: >95%
```

### Grafana Dashboard
```json
{
    "dashboard": {
        "title": "研发效能仪表板",
        "panels": [
            {
                "title": "构建成功率",
                "type": "stat",
                "targets": [{
                    "expr": "jenkins_build_success_rate",
                    "format": "percent"
                }],
                "thresholds": {
                    "steps": [
                        {"value": 0, "color": "red"},
                        {"value": 90, "color": "yellow"},
                        {"value": 95, "color": "green"}
                    ]
                }
            },
            {
                "title": "代码覆盖率趋势",
                "type": "timeseries",
                "targets": [{
                    "expr": "sonarqube_coverage",
                    "legendFormat": "覆盖率"
                }]
            },
            {
                "title": "测试用例通过率",
                "type": "gauge",
                "targets": [{
                    "expr": "test_pass_rate",
                    "format": "percent"
                }]
            },
            {
                "title": "设备在线状态",
                "type": "table",
                "targets": [{
                    "expr": "device_online_status"
                }]
            }
        ]
    }
}
```

---

### 相关链接

- [[ci-cd-pipeline|CI/CD 流水线]]
- [[ota-system|OTA 升级系统]]
- [[dev-process|项目管理]]
- [[product-design|产品设计]]

## 实践示例

### 示例代码

```c
// 示例代码 - 结合正文理解
```

**代码说明**：
- 详见正文

## 深入理解

### 原理分析

深入理解底层原理有助于写出更高质量的代码。建议结合数据手册和源码进行学习。

### 最佳实践

1. 遵循代码规范，保持良好的注释习惯
2. 充分测试，覆盖边界条件
3. 持续重构，保持代码简洁

## 常见问题

### Q1: 学习本模块需要什么基础？

**A**: 需要 C 语言基础和基本的嵌入式开发知识。建议先完成前置模块的学习。

### Q2: 如何验证学习效果？

**A**: 通过动手实践验证：完成练习题、在开发板上运行示例代码、独立完成一个小项目。

## 总结

本文涵盖了本级别的核心知识：

- 理解了基本概念和工作原理
- 掌握了关键技术和实现方法
- 通过实践加深了理解

建议继续学习更高级别的内容。

## 延伸阅读

- [[MOC|知识地图]] - 返回总索引
- 相关模块文档 - 交叉参考
- 厂商数据手册 - 详细规格

## 参考资料

1. 厂商数据手册和技术参考
2. 开源项目文档和代码
3. 学术论文和行业标准

---

**练习题**：

1. 厂商数据手册和技术参考
2. 开源项目文档和代码
3. 学术论文和行业标准

**下一步**：建议学习 [[dev-tools/intermediate/|中级内容]]
