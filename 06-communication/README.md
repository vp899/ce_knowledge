# 06 - 通信协议

## 模块概述

消费电子产品中涉及的有线/无线通信协议、组网方案与协议栈实现。

## 目录结构

```
06-communication/
├── protocols/      # 通信协议标准与规范
├── wireless/       # 无线通信 (BLE / WiFi / LoRa / NB-IoT)
├── wired/          # 有线通信 (UART / SPI / I2C / USB / Ethernet)
└── stack/          # 协议栈实现与移植
```

## 核心知识领域

### 1. 无线通信

#### 无线技术对比
| 技术 | 速率 | 距离 | 功耗 | 适用场景 |
|------|------|------|------|----------|
| BLE 5.0 | 2Mbps | 100m | 极低 | 穿戴、配件 |
| WiFi 6 | 9.6Gbps | 100m | 中 | 视频、大数据 |
| Zigbee | 250kbps | 100m | 低 | 智能家居 |
| Thread | 250kbps | 100m | 低 | 智能家居 |
| Matter | 基于IP | - | - | 统一标准 |
| LoRa | 50kbps | 15km | 极低 | 远程监测 |
| NB-IoT | 200kbps | 10km | 低 | 资产追踪 |
| 4G/5G | Gbps | 蜂窝 | 高 | 移动宽带 |
| UWB | 27Mbps | 100m | 中 | 精确定位 |
| NFC | 424kbps | 10cm | 极低 | 支付、配对 |

#### BLE 协议栈层次
```
Application (GATT Profile)
    │
├── GATT (Generic Attribute Profile)
├── ATT (Attribute Protocol)
├── SMP (Security Manager Protocol)
├── L2CAP (Logical Link Control)
├── HCI (Host Controller Interface)
├── Link Layer
└── Physical Layer (2.4GHz)
```

### 2. 有线通信

#### 接口对比
| 接口 | 速率 | 线数 | 距离 | 特点 |
|------|------|------|------|------|
| UART | 1Mbps | 2 | 1.5m | 简单异步 |
| SPI | 50MHz+ | 4 | 板级 | 全双工、高速 |
| I2C | 3.4MHz | 2 | 板级 | 多从设备 |
| USB 2.0 | 480Mbps | 2/4 | 5m | 通用 |
| USB 3.0 | 5Gbps | 2/4/9 | 3m | 高速 |
| Ethernet | 10Gbps | 4/8 | 100m | 网络 |
| CAN | 1Mbps | 2 | 1km | 汽车/工业 |
| RS-485 | 10Mbps | 2 | 1.2km | 工业总线 |
| MIPI DSI | 4Gbps | 差分 | 板级 | 显示 |
| MIPI CSI | 2.5Gbps | 差分 | 板级 | 摄像头 |

### 3. 应用层协议

| 协议 | 传输 | 特点 | 适用 |
|------|------|------|------|
| MQTT | TCP | 轻量发布订阅 | IoT |
| CoAP | UDP | RESTful、低功耗 | 受限设备 |
| HTTP/HTTPS | TCP | 通用 | Web 服务 |
| WebSocket | TCP | 全双工、持久 | 实时推送 |
| gRPC | HTTP/2 | 高性能 RPC | 微服务 |
| LwM2M | CoAP | 设备管理 | IoT 管理 |

### 4. 协议栈移植

#### LwIP 移植要点
- 网络接口驱动 (netif) 实现
- 内存池配置 (`lwipopts.h`)
- 中断 vs 轮询模式选择
- TCP/UDP 性能调优
- DHCP/DNS 客户端集成

#### mbed TLS / WolfSSL
- TLS 1.2/1.3 支持
- 证书管理 (X.509)
- 硬件加密加速 (AES、SHA)
- PSK 模式 (无证书)

## 设计决策模板

```
## 通信方案选型

### 需求
- 数据量: ___
- 实时性: ___
- 距离: ___
- 功耗预算: ___
- 成本预算: ___

### 候选方案
| 方案 | 满足度 | 风险 | 成本 |
|------|--------|------|------|
| 方案A |        |      |      |
| 方案B |        |      |      |

### 结论
选择方案 ___，理由: ___
```
