level: advanced
---
title: "通信协议算法详解"
tags: [communication, fec, arq, reed-solomon, adaptive-rate, algorithm]
module: "06-communication"
---

# 通信协议算法详解

## 概述

本文介绍 06-communication 领域的 advanced 级别知识。

完成本文学习后，你将能够：

- 理解核心概念和基本原理
- 掌握关键技术和实现方法
- 应用到实际产品开发中

## 背景知识

### 相关概念

> 占位 - 待补充前置概念

## 核心内容

### 1. FEC 前向纠错

### Reed-Solomon 编码
```
RS(N, K) 码:
  K = 数据符号数
  N = 总符号数 (数据 + 冗余)
  N-K = 冗余符号数
  可纠正 t = (N-K)/2 个符号错误

RS(255, 223):
  223 个数据符号 + 32 个校验符号
  可纠正 16 个符号错误
  每个符号 8-bit (GF(2^8))

编码过程:
  1. 将数据看作 GF(2^8) 上的多项式
  2. 生成多项式: g(x) = Π(x - α^i), i=0..2t-1
  3. 数据多项式乘以 x^(N-K)
  4. 除以生成多项式, 取余数
  5. 编码结果 = 数据 + 余数

解码过程:
  1. 计算伴随式 (syndrome)
  2. 用 Berlekamp-Massey 算法求错误定位多项式
  3. 用 Chien 搜索找错误位置
  4. 用 Forney 算法求错误值
  5. 纠正错误
```

### 卷积编码 + Viterbi 译码
```
卷积编码器 (1/2 码率, K=7):
  生成多项式: g1 = 171(八进制), g2 = 133(八进制)
  
  输入比特 → 移位寄存器 → 2 个输出比特

Viterbi 译码:
  1. 构造网格图 (trellis)
  2. 计算每个状态的路径度量
  3. 选择幸存路径 (最小汉明距离)
  4. 回溯得到译码结果

编码增益:
  硬判决: 3-4 dB
  软判决: 5-6 dB
```

### 2. ARQ 协议

### 选择性重传 (SR-ARQ)
```c
/* 选择性重传 ARQ */

#define WINDOW_SIZE    16
#define MAX_SEQ        256

typedef struct {
    uint8_t seq;           // 序列号
    uint8_t data[1024];    // 数据
    uint16_t len;          // 长度
    uint32_t timestamp;    // 发送时间
    bool acked;            // 是否已确认
    int retry_count;       // 重试次数
} ARQ_Packet;

typedef struct {
    ARQ_Packet tx_window[WINDOW_SIZE];
    int base;              // 窗口基序号
    int next_seq;          // 下一个待发序列号
    uint32_t timeout_ms;   // 超时时间
    int max_retries;       // 最大重试
} SR_ARQ;

// 发送
int arq_send(SR_ARQ *arq, uint8_t *data, uint16_t len) {
    int idx = arq->next_seq % WINDOW_SIZE;
    
    ARQ_Packet *pkt = &arq->tx_window[idx];
    pkt->seq = arq->next_seq;
    memcpy(pkt->data, data, len);
    pkt->len = len;
    pkt->timestamp = millis();
    pkt->acked = false;
    pkt->retry_count = 0;
    
    // 发送
    send_packet(pkt);
    
    arq->next_seq = (arq->next_seq + 1) % MAX_SEQ;
    return 0;
}

// 接收 ACK
void arq_process_ack(SR_ARQ *arq, uint8_t ack_seq) {
    int idx = ack_seq % WINDOW_SIZE;
    arq->tx_window[idx].acked = true;
    
    // 滑动窗口
    while (arq->tx_window[arq->base % WINDOW_SIZE].acked) {
        arq->base = (arq->base + 1) % MAX_SEQ;
    }
}

// 超时检查
void arq_check_timeout(SR_ARQ *arq) {
    uint32_t now = millis();
    
    for (int i = arq->base; i != arq->next_seq; i = (i+1) % MAX_SEQ) {
        int idx = i % WINDOW_SIZE;
        ARQ_Packet *pkt = &arq->tx_window[idx];
        
        if (!pkt->acked && (now - pkt->timestamp > arq->timeout_ms)) {
            if (pkt->retry_count < arq->max_retries) {
                send_packet(pkt);  // 重传
                pkt->timestamp = now;
                pkt->retry_count++;
            } else {
                // 超过最大重试, 放弃
                arq->base = (i + 1) % MAX_SEQ;
            }
        }
    }
}
```

### 3. 自适应码率

### 信道质量估计
```c
/* 自适应码率控制 */

typedef struct {
    int current_rate;       // 当前码率 (kbps)
    int min_rate;           // 最低码率
    int max_rate;           // 最高码率
    float snr_estimate;     // 信噪比估计
    float ber_estimate;     // 误码率估计
    float packet_loss;      // 丢包率
    int rssi;               // 接收信号强度
} AdaptiveRate;

void adaptive_rate_update(AdaptiveRate *ar, int rssi, 
                           float loss_rate, float snr) {
    ar->rssi = rssi;
    ar->packet_loss = loss_rate;
    ar->snr_estimate = snr;
    
    // Shannon 容量: C = B · log2(1 + SNR)
    // 实际码率取 50-80% Shannon 容量
    
    float shannon_capacity = BANDWIDTH * log2f(1.0f + powf(10, snr/10));
    int optimal_rate = (int)(shannon_capacity * 0.6f / 1000);  // kbps
    
    // 基于丢包率调整
    if (loss_rate > 0.1f) {
        optimal_rate *= 0.5f;  // 丢包严重, 大幅降低
    } else if (loss_rate > 0.05f) {
        optimal_rate *= 0.8f;
    }
    
    // 平滑过渡
    ar->current_rate = ar->current_rate * 0.7f + optimal_rate * 0.3f;
    
    // 限幅
    ar->current_rate = CLAMP(ar->current_rate, ar->min_rate, ar->max_rate);
}

// SNR 估计
float estimate_snr(int16_t *samples, int n, float signal_power) {
    float noise_power = 0;
    for (int i = 0; i < n; i++) {
        noise_power += samples[i] * samples[i];
    }
    noise_power /= n;
    noise_power -= signal_power;
    
    if (noise_power <= 0) return 30.0f;  // 上限
    
    return 10.0f * log10f(signal_power / noise_power);
}
```

---

### 相关链接

- [[video-transmission|图传系统]] — 视频传输
- [[protocol-details|通信协议]] — 协议详解

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

**下一步**：建议学习 [[MOC|返回知识地图]]
