level: intermediate
---
title: "图传系统（视频传输链路）"
aliases:
  - "视频传输"
  - "图传链路"
tags:
  - image-transmission
  - h264
  - h265
  - fec
  - antenna
module: "15-image-transmission"
status: active
---

# 图传系统（视频传输链路）

## 概述

本文介绍 06-communication 领域的 intermediate 级别知识。

完成本文学习后，你将能够：

- 理解核心概念和基本原理
- 掌握关键技术和实现方法
- 应用到实际产品开发中

## 背景知识

### 相关概念

> 占位 - 待补充前置概念

## 核心内容

### 1. 视频编码

### H.264/H.265 编码对比

| 特性 | H.264 (AVC) | H.265 (HEVC) |
|------|-------------|--------------|
| 压缩效率 | 基准 | 提升 40-50% |
| 块大小 | 4×4 ~ 16×16 | 4×4 ~ 64×64 |
| 帧内预测模式 | 9 种 | 35 种 |
| 运动补偿 | 1/4 像素 | 1/4 像素 |
| 熵编码 | CAVLC / CABAC | CABAC |
| 并行处理 | Slice 级 | Tile / WPP |
| 编码复杂度 | 中 | 高 (2-3x) |
| 解码复杂度 | 低 | 中 |
| 延迟 | 低 | 中 |
| 适用 | 实时图传 | 高压缩需求 |

### 低延迟编码配置
```c
/* x264 低延迟编码参数 */
x264_param_t param;

x264_param_default_preset(&param, "ultrafast", "zerolatency");

// 关键低延迟参数
param.i_threads = 1;                    // 单线程减少延迟
param.i_bframe = 0;                     // 禁用 B 帧
param.b_vfr_input = 0;                  // 固定帧率
param.b_repeat_headers = 1;             // 每帧带 SPS/PPS
param.i_slice_max_size = 1400;          // 限制 slice 大小 (MTU)
param.i_keyint_max = 30;                // 每 30 帧一个 IDR
param.i_keyint_min = 30;
param.rc.i_rc_method = X264_RC_CRF;    // 恒定质量
param.rc.i_bitrate = 8000;              // 8 Mbps
param.rc.f_rf_constant = 23;            // CRF 值
param.i_fps_num = 60;                   // 60fps
param.i_fps_den = 1;

// Profile & Level
param.i_level_idc = 41;                 // Level 4.1
param.i_profile_idc = HIGH;

x264_t *encoder = x264_encoder_open(&param);
```

### 硬件编码器 (VPU)
```
常用硬件编码器:
├── Ambarella H22/H32: 4K@60, H.264/H.265, 航拍专用
├── HiSilicon Hi3559A: 4K@120, 8K@30, 双核编码
├── Qualcomm Spectra: 4K@60, 高通平台
├── Rockchip RV1126: 4K@30, AI+编码, 机器人
├── Allwinner V853: 4K@30, 低成本
└── NVIDIA Jetson: GPU 编码, 通用

编码延迟对比:
| 编码器 | 延迟 (ms) | 功耗 (W) |
|--------|-----------|----------|
| x264 (ultrafast) | 5-15 | CPU 高 |
| x265 (fast) | 10-30 | CPU 很高 |
| Ambarella VPU | 2-5 | 0.5-1 |
| HiSilicon VPU | 3-8 | 0.3-0.8 |
| Jetson NVENC | 3-10 | 2-5 |
```

### 2. 低延迟传输协议

### 私有图传协议设计
```
协议栈:
┌─────────────────────────────────────┐
│  应用层: 视频帧 (H.264/H.265 NALU) │
├─────────────────────────────────────┤
│  分片层: NALU 分片 + FEC            │
├─────────────────────────────────────┤
│  传输层: UDP + ARQ (选择性重传)     │
├─────────────────────────────────────┤
│  链路层: 自定义 MAC (TDMA/FHSS)    │
├─────────────────────────────────────┤
│  物理层: OFDM / SC-FDMA            │
└─────────────────────────────────────┘
```

### 帧格式
```
┌─────────────────────────────────────────────────┐
│  Packet Header (16 字节)                         │
├──────┬──────┬──────┬──────┬──────┬──────┬───────┤
│ Sync │ Type │ Frame│ Frag │ Frag │ Total│ CRC   │
│ 2B   │ 1B   │ ID   │ ID   │ Cnt  │ Len  │ 2B    │
│ 0xAA55│     │ 4B   │ 2B   │ 2B   │ 4B   │       │
├──────┴──────┴──────┴──────┴──────┴──────┴───────┤
│  Payload (变长, 最大 1400 字节)                   │
├─────────────────────────────────────────────────┤
│  FEC 冗余数据 (可选)                             │
└─────────────────────────────────────────────────┘

Packet Types:
0x01 = I-Frame (关键帧)
0x02 = P-Frame (预测帧)
0x03 = B-Frame (双向帧)
0x10 = SPS/PPS 参数集
0x11 = SEI 补充信息
0x20 = FEC 冗余包
0x80 = ACK 确认
0x81 = NACK 重传请求
```

### FEC (前向纠错)
```
Reed-Solomon FEC:
- 每 K 个数据包生成 N-K 个冗余包
- 接收端可恢复丢失的包，无需重传
- 参数: RS(N, K), 如 RS(12, 10) 可恢复 2 个丢包

XOR FEC:
- 简单高效
- 每 N 个包生成 1 个 XOR 校验包
- 可恢复 1 个丢包

交织 (Interleaving):
- 将连续的包分散到不同的 FEC 块
- 抗突发丢包
- 增加延迟 (块大小 × 帧时间)

推荐配置:
├── 短距离 (<1km): RS(12,10), 延迟低
├── 中距离 (1-5km): RS(14,10), 均衡
└── 长距离 (>5km): RS(16,10), 更强纠错
```

### ARQ (选择性重传)
```
发送端:
1. 发送数据包，启动超时计时器
2. 收到 ACK → 清除计时器，发送下一包
3. 收到 NACK → 重传指定包
4. 超时未收到 ACK → 重传

接收端:
1. 收到包 → 校验 CRC
2. CRC 正确 → 缓存，发送 ACK
3. CRC 错误 → 发送 NACK
4. 检测到丢包 (序列号跳跃) → 发送 NACK

重传策略:
├── 快速重传: 收到 3 个重复 ACK 立即重传
├── 选择性重传: 只重传丢失的包
└── 限制重传次数: 最多重传 3 次

延迟分析:
单向延迟: ~5ms (近距离)
重传延迟: 2 × 单向延迟 + 处理时间 ≈ 15ms
最大重传延迟: 3 × 15ms = 45ms
```

### 3. 天线设计

### 无人机图传天线类型
```
全向天线:
├── 偶极子天线: 增益 2dBi, 全向
├── PCB 天线: 增益 1-3dBi, 紧凑
├── 螺旋天线: 增益 3-5dBi, 圆极化
└── 芯片天线: 增益 1-2dBi, 超小

定向天线:
├── 八木天线: 增益 10-15dBi, 窄波束
├── 平板天线: 增益 12-18dBi, 中等波束
├── 抛物面天线: 增益 20-30dBi, 极窄波束
└── 相控阵天线: 增益 15-25dFi, 电子扫描

波束宽度与增益关系:
增益(dBi) ≈ 10 × log10(41253 / (θ_az × θ_el))
θ_az: 水平波束宽度 (度)
θ_el: 垂直波束宽度 (度)

示例:
├── 全向 (360°×90°): G ≈ 3dBi
├── 中等 (60°×60°):  G ≈ 13dBi
├── 窄波束 (15°×15°): G ≈ 23dBi
└── 极窄 (5°×5°):    G ≈ 31dBi
```

### MIMO 天线
```
2×2 MIMO:
┌─────────────┐      ┌─────────────┐
│  TX1  TX2   │ ───→ │  RX1  RX2   │
│  (水平/垂直) │      │  (水平/垂直) │
└─────────────┘      └─────────────┘

MIMO 增益:
- 分集增益: 抗多径衰落
- 空间复用增益: 2×MIMO 容量翻倍
- 阵列增益: 波束成形

天线间距要求:
- ≥ λ/2 (半波长)
- 2.4GHz: ≥ 6.25cm
- 5.8GHz: ≥ 2.58cm
```

### 4. 链路预算

### 自由空间路径损耗 (FSPL)
```
FSPL(dB) = 20×log10(d) + 20×log10(f) + 20×log10(4π/c)
简化公式 (f in GHz, d in km):
FSPL(dB) = 92.45 + 20×log10(d) + 20×log10(f)

示例:
| 频率 | 距离 | FSPL |
|------|------|------|
| 2.4GHz | 1km | 100dB |
| 2.4GHz | 5km | 114dB |
| 2.4GHz | 10km | 120dB |
| 5.8GHz | 1km | 108dB |
| 5.8GHz | 5km | 122dB |
| 5.8GHz | 10km | 128dB |
```

### 链路预算计算
```
链路预算 = TX功率 + TX增益 - 线缆损耗 - FSPL + RX增益 - 灵敏度余量

示例 (5.8GHz, 5km):
├── TX 功率: 30dBm (1W)
├── TX 天线增益: 5dBi (全向)
├── 线缆损耗: 2dB
├── FSPL: 122dB
├── RX 天线增益: 5dBi (全向)
├── RX 灵敏度: -95dBm
│
链路预算 = 30 + 5 - 2 - 122 + 5 = -84dBm
余量 = -84 - (-95) = 11dB

余量分析:
├── < 6dB: 不可靠
├── 6-10dB: 基本可用
├── 10-20dB: 良好
└── > 20dB: 优秀

增加链路余量的方法:
├── 增加 TX 功率 (法规限制)
├── 使用高增益天线
├── 降低编码码率
├── 使用更强的 FEC
└── 降低调制阶数 (QPSK vs 16QAM)
```

### 动态码率自适应
```c
/* 自适应码率控制 */
typedef struct {
    int current_bitrate;    // 当前码率 (kbps)
    int min_bitrate;        // 最低码率
    int max_bitrate;        // 最高码率
    float rssi_threshold;   // RSSI 阈值
    float packet_loss_rate; // 丢包率
    int adapt_interval;     // 自适应间隔 (ms)
} AdaptiveRateCtrl;

void adaptive_rate_update(AdaptiveRateCtrl *ctrl, 
                           float rssi, float loss_rate) {
    int new_rate = ctrl->current_bitrate;
    
    // 基于 RSSI 调整
    if (rssi < -85) {
        new_rate = ctrl->min_bitrate;       // 强制最低码率
    } else if (rssi < -75) {
        new_rate *= 0.7;                     // 降低 30%
    } else if (rssi > -60 && loss_rate < 0.01) {
        new_rate *= 1.1;                     // 增加 10%
    }
    
    // 基于丢包率调整
    if (loss_rate > 0.1) {
        new_rate *= 0.5;                     // 丢包严重，大幅降低
    } else if (loss_rate > 0.05) {
        new_rate *= 0.8;                     // 丢包中等
    }
    
    // 限制范围
    new_rate = CLAMP(new_rate, ctrl->min_bitrate, ctrl->max_bitrate);
    
    ctrl->current_bitrate = new_rate;
}
```

### 5. 延迟优化

### 端到端延迟分解
```
┌─────────────────────────────────────────────────────┐
│  端到端延迟分解                                       │
├─────────────────────────────────────────────────────┤
│                                                      │
│  传感器曝光:     1/fps = 16.7ms (60fps)              │
│  传感器读出:     5-15ms (取决于分辨率)                │
│  ISP 处理:       3-10ms                              │
│  编码:           2-8ms (硬件) / 5-20ms (软件)        │
│  打包+FEC:       1-2ms                               │
│  传输:           1-5ms (近距离)                       │
│  解包+FEC恢复:   1-2ms                               │
│  解码:           2-5ms (硬件) / 5-15ms (软件)        │
│  显示:           1-5ms                               │
│                                                      │
│  总延迟:         约 35-85ms (优化后)                  │
│                  约 100-300ms (未优化)                │
│                                                      │
└─────────────────────────────────────────────────────┘

延迟优化技巧:
├── 传感器: 选择低读出延迟的 sensor
├── ISP: 流水线处理，减少帧缓冲
├── 编码: 硬件编码器，禁用 B 帧
├── 传输: 减小 FEC 块大小，降低交织深度
├── 解码: 硬件解码器，零拷贝显示
└── 整体: 减少每个环节的缓冲
```
---

### 相关链接

- [[camera-sensor|相机系统]]
- [[protocol-details|通信协议]]

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

**下一步**：建议学习 [[06-communication/advanced/|高级内容]]
