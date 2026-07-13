---
title: "图传系统"
aliases:
  - "图传模块总览"
tags:
  - image-transmission
  - index
module: "15-image-transmission"
status: active
---

# 15 - 图传系统

## 模块概述

无人机图传（视频传输）链路设计：编码、调制、[[video-transmission|链路预算]]、天线、抗干扰、低延迟传输。

## 目录结构

```
15-image-transmission/
├── encoding/       # 视频编码 (H.264/H.265/编码器调优)
├── protocol/       # 传输协议 (私有协议/RTP/WebRTC)
├── antenna/        # 天线设计 (定向/全向/MIMO)
└── link-budget/    # 链路预算与信道规划
```

## 核心知识领域

### 1. 视频编码
### 2. 低延迟传输协议
### 3. 天线与射频
### 4. 链路预算
---

## 相关链接

- [[camera-sensor|相机系统]]
- [[protocol-details|通信协议]]
