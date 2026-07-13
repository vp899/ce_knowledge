level: beginner
---
title: "通信协议详解"
aliases:
  - "协议详解"
tags:
  - communication
  - mqtt
  - ble
  - wifi
  - uart
  - spi
module: "06-communication"
status: active
---

# 通信协议详解

## 概述

本文介绍 protocols 领域的 beginner 级别知识。

完成本文学习后，你将能够：

- 理解核心概念和基本原理
- 掌握关键技术和实现方法
- 应用到实际产品开发中

## 背景知识

### 相关概念

> 占位 - 待补充前置概念

## 核心内容

### 1. MQTT 协议

### MQTT 消息格式
```
固定头 (2 字节):
┌────────┬───────────────────────┐
│ Byte 1 │ Byte 2+               │
├────────┼───────────────────────┤
│ 类型   │ 剩余长度 (1-4 字节)   │
│ +标志   │ (Variable Length)     │
└────────┴───────────────────────┘

消息类型:
0x1 - CONNECT     (客户端连接请求)
0x2 - CONNACK     (连接确认)
0x3 - PUBLISH     (发布消息)
0x4 - PUBACK      (发布确认)
0x8 - SUBSCRIBE   (订阅主题)
0x9 - SUBACK      (订阅确认)
0xE - DISCONNECT  (断开连接)
```

### MQTT 客户端实现 (嵌入式)
```c
/* mqtt_client.c */
#include "mqtt_client.h"
#include "tcp_socket.h"
#include "tls.h"

#define MQTT_KEEPALIVE    60   // 心跳间隔 (秒)
#define MQTT_TX_BUF_SIZE  2048
#define MQTT_RX_BUF_SIZE  4096

typedef struct {
    int sock;
    TLSContext *tls;
    uint8_t tx_buf[MQTT_TX_BUF_SIZE];
    uint8_t rx_buf[MQTT_RX_BUF_SIZE];
    uint16_t packet_id;
    char client_id[32];
    char username[32];
    char password[64];
    MqttCallback callback;
    void *user_data;
    bool connected;
} MqttClient;

/* 构建 CONNECT 报文 */
static int mqtt_build_connect(MqttClient *client, uint8_t *buf) {
    int pos = 0;
    
    // 固定头
    buf[pos++] = 0x10;  // CONNECT
    
    // 可变头 + 有效载荷长度
    int remaining = 10 + 2 + strlen(client->client_id) + 2;
    if (client->username[0]) {
        remaining += 2 + strlen(client->username);
    }
    if (client->password[0]) {
        remaining += 2 + strlen(client->password);
    }
    
    // 剩余长度编码
    do {
        uint8_t encoded = remaining % 128;
        remaining /= 128;
        if (remaining > 0) encoded |= 0x80;
        buf[pos++] = encoded;
    } while (remaining > 0);
    
    // 可变头 - 协议名
    buf[pos++] = 0x00; buf[pos++] = 0x04;  // 长度
    buf[pos++] = 'M'; buf[pos++] = 'Q';    // "MQTT"
    buf[pos++] = 'T'; buf[pos++] = 'T';
    
    // 协议级别
    buf[pos++] = 0x04;  // MQTT 3.1.1
    
    // 连接标志
    uint8_t flags = 0x02;  // Clean Session
    if (client->username[0]) flags |= 0x80;
    if (client->password[0]) flags |= 0x40;
    buf[pos++] = flags;
    
    // 保活时间
    buf[pos++] = (MQTT_KEEPALIVE >> 8) & 0xFF;
    buf[pos++] = MQTT_KEEPALIVE & 0xFF;
    
    // 有效载荷 - Client ID
    int len = strlen(client->client_id);
    buf[pos++] = (len >> 8) & 0xFF;
    buf[pos++] = len & 0xFF;
    memcpy(buf + pos, client->client_id, len);
    pos += len;
    
    // 用户名
    if (client->username[0]) {
        len = strlen(client->username);
        buf[pos++] = (len >> 8) & 0xFF;
        buf[pos++] = len & 0xFF;
        memcpy(buf + pos, client->username, len);
        pos += len;
    }
    
    // 密码
    if (client->password[0]) {
        len = strlen(client->password);
        buf[pos++] = (len >> 8) & 0xFF;
        buf[pos++] = len & 0xFF;
        memcpy(buf + pos, client->password, len);
        pos += len;
    }
    
    return pos;
}

/* 构建 PUBLISH 报文 */
static int mqtt_build_publish(MqttClient *client, const char *topic,
                               const uint8_t *payload, int payload_len,
                               int qos, uint8_t *buf) {
    int pos = 0;
    
    // 固定头
    uint8_t type = 0x30;  // PUBLISH
    if (qos == 1) type |= 0x02;
    if (qos == 2) type |= 0x04;
    buf[pos++] = type;
    
    // 剩余长度
    int remaining = 2 + strlen(topic) + payload_len;
    if (qos > 0) remaining += 2;  // Packet ID
    
    do {
        uint8_t encoded = remaining % 128;
        remaining /= 128;
        if (remaining > 0) encoded |= 0x80;
        buf[pos++] = encoded;
    } while (remaining > 0);
    
    // 主题名
    int topic_len = strlen(topic);
    buf[pos++] = (topic_len >> 8) & 0xFF;
    buf[pos++] = topic_len & 0xFF;
    memcpy(buf + pos, topic, topic_len);
    pos += topic_len;
    
    // Packet ID (QoS > 0)
    if (qos > 0) {
        buf[pos++] = (client->packet_id >> 8) & 0xFF;
        buf[pos++] = client->packet_id & 0xFF;
        client->packet_id++;
    }
    
    // 有效载荷
    memcpy(buf + pos, payload, payload_len);
    pos += payload_len;
    
    return pos;
}

/* 发布消息 */
int mqtt_publish(MqttClient *client, const char *topic,
                  const uint8_t *payload, int payload_len, int qos) {
    uint8_t buf[MQTT_TX_BUF_SIZE];
    
    int len = mqtt_build_publish(client, topic, payload, 
                                  payload_len, qos, buf);
    
    // 发送
    int ret = tls_send(client->tls, buf, len);
    
    // QoS 1: 等待 PUBACK
    if (qos == 1) {
        // 等待确认...
    }
    
    return ret;
}

/* 连接服务器 */
int mqtt_connect(MqttClient *client, const char *host, int port,
                  bool use_tls) {
    // 1. TCP 连接
    client->sock = tcp_connect(host, port);
    if (client->sock < 0) return -1;
    
    // 2. TLS 握手 (可选)
    if (use_tls) {
        client->tls = tls_connect(client->sock, host);
        if (!client->tls) {
            close(client->sock);
            return -2;
        }
    }
    
    // 3. 发送 CONNECT
    uint8_t buf[256];
    int len = mqtt_build_connect(client, buf);
    tls_send(client->tls, buf, len);
    
    // 4. 等待 CONNACK
    int n = tls_recv(client->tls, buf, sizeof(buf));
    if (n < 4 || buf[0] != 0x20 || buf[3] != 0x00) {
        return -3;  // 连接失败
    }
    
    client->connected = true;
    return 0;
}
```

### 2. BLE 通信

### BLE 协议栈架构
```
Application
    │
    ├── GATT (Generic Attribute Profile)
    │   ├── Service (服务)
    │   │   ├── Characteristic (特征)
    │   │   │   ├── Value (值)
    │   │   │   └── Descriptor (描述符)
    │   │   └── ...
    │   └── Client / Server
    │
    ├── GAP (Generic Access Profile)
    │   ├── Broadcaster / Observer
    │   ├── Peripheral / Central
    │   └── Advertising / Scanning / Connection
    │
    ├── ATT (Attribute Protocol)
    │   ├── MTU 协商
    │   └── Read / Write / Notify / Indicate
    │
    ├── SMP (Security Manager)
    │   ├── 配对 (Pairing)
    │   ├── 绑定 (Bonding)
    │   └── 加密 (Encryption)
    │
    ├── L2CAP (Logical Link Control)
    │   └── 信道管理
    │
    ├── HCI (Host Controller Interface)
    │   └── Host ↔ Controller 通信
    │
    ├── Link Layer
    │   ├── 状态机 (Advertising / Scanning / Connection)
    │   ├── 调度
    │   └── 数据包处理
    │
    └── Physical Layer (2.4GHz ISM)
        ├── 40 信道 (2MHz 间隔)
        ├── 跳频 (Channel Hopping)
        └── 调制 (GFSK)
```

### BLE GATT 服务设计
```c
/* BLE 传感器服务 */
#define SENSOR_SERVICE_UUID       0x1800
#define TEMP_CHAR_UUID            0x2A1C
#define HUMIDITY_CHAR_UUID        0x2A6F
#define BATTERY_CHAR_UUID         0x2A19

/* 服务定义 */
static const gatt_attr_t sensor_service[] = {
    // 服务声明
    { PRIMARY_SERVICE, SENSOR_SERVICE_UUID },
    
    // 温度特征
    { CHARACTERISTIC, TEMP_CHAR_UUID,
      GATT_NOTIFY | GATT_READ },
    { TEMP_CHAR_UUID, sizeof(float), &temperature },
    
    // 湿度特征
    { CHARACTERISTIC, HUMIDITY_CHAR_UUID,
      GATT_NOTIFY | GATT_READ },
    { HUMIDITY_CHAR_UUID, sizeof(float), &humidity },
    
    // 电池特征
    { CHARACTERISTIC, BATTERY_CHAR_UUID,
      GATT_NOTIFY | GATT_READ },
    { BATTERY_CHAR_UUID, sizeof(uint8_t), &battery_level },
};

/* 数据更新与通知 */
void update_sensor_data(float temp, float humi) {
    temperature = temp;
    humidity = humi;
    
    // 发送通知给已连接的客户端
    if (is_connected()) {
        gatt_notify(TEMP_CHAR_UUID, &temperature, sizeof(float));
        gatt_notify(HUMIDITY_CHAR_UUID, &humidity, sizeof(float));
    }
}
```

### 3. WiFi 连接管理

### WiFi 状态机
```
┌─────────┐
│  INIT   │
└────┬────┘
     │ scan()
     ▼
┌─────────┐
│ SCANNING│
└────┬────┘
     │ found AP
     ▼
┌─────────┐
│CONNECTING│ (Authentication + Association)
└────┬────┘
     │ success
     ▼
┌─────────┐    ┌──────────┐
│CONNECTED│───→│DISCONNECT│
└────┬────┘    └──────────┘
     │ DHCP
     ▼
┌─────────┐
│  READY  │
└─────────┘
```

### WiFi 管理代码
```c
/* wifi_manager.c */
#include "wifi_manager.h"
#include "lwip/dhcp.h"
#include "lwip/netif.h"

typedef enum {
    WIFI_STATE_INIT,
    WIFI_STATE_SCANNING,
    WIFI_STATE_CONNECTING,
    WIFI_STATE_CONNECTED,
    WIFI_STATE_READY,
    WIFI_STATE_DISCONNECTED,
    WIFI_STATE_ERROR,
} WiFiState_t;

typedef struct {
    WiFiState_t state;
    char ssid[33];
    char password[64];
    ip4_addr_t ip;
    ip4_addr_t gateway;
    ip4_addr_t netmask;
    struct netif *netif;
    int retry_count;
    WiFiEventCallback callback;
} WiFiManager;

static WiFiManager wifi;

/* 扫描完成回调 */
static void on_scan_done(wifi_ap_info_t *aps, int count) {
    printf("Found %d APs:\n", count);
    for (int i = 0; i < count; i++) {
        printf("  %s (RSSI: %d, CH: %d)\n",
               aps[i].ssid, aps[i].rssi, aps[i].channel);
    }
    
    // 查找目标 AP
    for (int i = 0; i < count; i++) {
        if (strcmp(aps[i].ssid, wifi.ssid) == 0) {
            // 找到目标，开始连接
            wifi.state = WIFI_STATE_CONNECTING;
            wifi_connect_ap(&aps[i], wifi.password);
            return;
        }
    }
    
    printf("Target AP not found\n");
    wifi.state = WIFI_STATE_ERROR;
}

/* 连接 WiFi */
int wifi_connect(const char *ssid, const char *password) {
    strncpy(wifi.ssid, ssid, sizeof(wifi.ssid) - 1);
    strncpy(wifi.password, password, sizeof(wifi.password) - 1);
    
    wifi.state = WIFI_STATE_SCANNING;
    wifi.retry_count = 0;
    
    // 启动扫描
    wifi_start_scan(on_scan_done);
    
    return 0;
}

/* 连接成功回调 */
static void on_connected(void) {
    wifi.state = WIFI_STATE_CONNECTED;
    printf("Connected to %s\n", wifi.ssid);
    
    // 启动 DHCP
    dhcp_start(wifi.netif);
    
    // 等待获取 IP
    // ...
}

/* DHCP 完成回调 */
static void on_dhcp_done(struct netif *netif) {
    wifi.ip = netif->ip_addr;
    wifi.gateway = netif->gw;
    wifi.netmask = netif->netmask;
    
    wifi.state = WIFI_STATE_READY;
    
    printf("IP: %s\n", ip4addr_ntoa(&wifi.ip));
    printf("GW: %s\n", ip4addr_ntoa(&wifi.gateway));
    
    if (wifi.callback) {
        wifi.callback(WIFI_EVENT_CONNECTED, &wifi.ip);
    }
}

/* 断开连接回调 */
static void on_disconnected(int reason) {
    wifi.state = WIFI_STATE_DISCONNECTED;
    
    // 自动重连
    if (wifi.retry_count < MAX_RETRY) {
        wifi.retry_count++;
        printf("Reconnecting... (%d/%d)\n", 
               wifi.retry_count, MAX_RETRY);
        wifi_connect(wifi.ssid, wifi.password);
    } else {
        printf("Connection failed\n");
        if (wifi.callback) {
            wifi.callback(WIFI_EVENT_DISCONNECTED, NULL);
        }
    }
}
```

### 4. UART 通信协议

### 串口协议状态机
```c
/* uart_protocol.c */
#include "uart_protocol.h"

#define FRAME_SOF   0xAA
#define FRAME_EOF   0x55
#define MAX_DATA_LEN 256

typedef enum {
    STATE_IDLE,
    STATE_SOF,
    STATE_CMD,
    STATE_LEN,
    STATE_DATA,
    STATE_CRC,
    STATE_EOF,
} ProtocolState_t;

static ProtocolState_t state = STATE_IDLE;
static Frame_t rx_frame;
static uint16_t data_index = 0;

/* 协议处理 */
void uart_protocol_process(uint8_t byte) {
    switch (state) {
    case STATE_IDLE:
        if (byte == FRAME_SOF) {
            state = STATE_CMD;
            rx_frame.sof = byte;
        }
        break;
        
    case STATE_CMD:
        rx_frame.cmd = byte;
        state = STATE_LEN;
        break;
        
    case STATE_LEN:
        rx_frame.len = byte;
        data_index = 0;
        if (rx_frame.len > 0) {
            state = STATE_DATA;
        } else {
            state = STATE_CRC;
        }
        break;
        
    case STATE_DATA:
        rx_frame.data[data_index++] = byte;
        if (data_index >= rx_frame.len) {
            state = STATE_CRC;
        }
        break;
        
    case STATE_CRC:
        rx_frame.crc = (rx_frame.crc << 8) | byte;
        if (data_index == rx_frame.len) {
            state = STATE_EOF;
        }
        break;
        
    case STATE_EOF:
        if (byte == FRAME_EOF) {
            rx_frame.eof = byte;
            // 验证 CRC 并处理
            if (verify_crc(&rx_frame)) {
                process_frame(&rx_frame);
            }
        }
        state = STATE_IDLE;
        break;
    }
}
```

### 5. SPI Flash 通信

### SPI Flash 驱动
```c
/* spi_flash.c */
#include "spi_flash.h"

#define CMD_READ_ID         0x9F
#define CMD_READ_DATA       0x03
#define CMD_PAGE_PROGRAM    0x02
#define CMD_SECTOR_ERASE    0x20
#define CMD_CHIP_ERASE      0xC7
#define CMD_WRITE_ENABLE    0x06
#define CMD_READ_STATUS     0x05

#define PAGE_SIZE           256
#define SECTOR_SIZE         4096

/* 读取芯片 ID */
int spi_flash_read_id(uint32_t *id) {
    uint8_t cmd = CMD_READ_ID;
    uint8_t buf[3];
    
    spi_select();
    spi_transfer(&cmd, 1, NULL);
    spi_transfer(NULL, 3, buf);
    spi_deselect();
    
    *id = (buf[0] << 16) | (buf[1] << 8) | buf[2];
    
    return 0;
}

/* 读取数据 */
int spi_flash_read(uint32_t addr, uint8_t *buf, uint32_t len) {
    uint8_t cmd[4];
    
    cmd[0] = CMD_READ_DATA;
    cmd[1] = (addr >> 16) & 0xFF;
    cmd[2] = (addr >> 8) & 0xFF;
    cmd[3] = addr & 0xFF;
    
    spi_select();
    spi_transfer(cmd, 4, NULL);
    spi_transfer(NULL, len, buf);
    spi_deselect();
    
    return 0;
}

/* 页编程 (单次最多 256 字节) */
int spi_flash_page_program(uint32_t addr, const uint8_t *buf, 
                            uint16_t len) {
    uint8_t cmd[4];
    
    // 写使能
    spi_flash_write_enable();
    
    cmd[0] = CMD_PAGE_PROGRAM;
    cmd[1] = (addr >> 16) & 0xFF;
    cmd[2] = (addr >> 8) & 0xFF;
    cmd[3] = addr & 0xFF;
    
    spi_select();
    spi_transfer(cmd, 4, NULL);
    spi_transfer((uint8_t *)buf, len, NULL);
    spi_deselect();
    
    // 等待编程完成
    spi_flash_wait_ready();
    
    return 0;
}

/* 扇区擦除 */
int spi_flash_erase_sector(uint32_t addr) {
    uint8_t cmd[4];
    
    spi_flash_write_enable();
    
    cmd[0] = CMD_SECTOR_ERASE;
    cmd[1] = (addr >> 16) & 0xFF;
    cmd[2] = (addr >> 8) & 0xFF;
    cmd[3] = addr & 0xFF;
    
    spi_select();
    spi_transfer(cmd, 4, NULL);
    spi_deselect();
    
    // 等待擦除完成
    spi_flash_wait_ready();
    
    return 0;
}

/* 等待操作完成 */
static void spi_flash_wait_ready(void) {
    uint8_t cmd = CMD_READ_STATUS;
    uint8_t status;
    
    do {
        spi_select();
        spi_transfer(&cmd, 1, NULL);
        spi_transfer(NULL, 1, &status);
        spi_deselect();
    } while (status & 0x01);  // WIP bit
}
```
---

### 相关链接

- [[linux-driver-dev|Linux 驱动]]
- [[video-transmission|图传系统]]

## 实践示例

### 示例代码

```c
// 占位 - 待补充示例代码
```

**代码说明**：
- 待补充

## 深入理解

### 原理分析

> 占位 - 待补充原理分析

### 最佳实践

1. 待补充

## 常见问题

### Q1: 待补充常见问题？

**A**: 待补充答案。

## 总结

本文核心要点：

- 待补充

## 延伸阅读

- 待补充相关文章链接

## 参考资料

1. 待补充

---

**练习题**：

1. 待补充

**下一步**：建议学习 [[protocols/intermediate/|中级内容]]
