---
title: "视觉算法初级 - 图像基础"
tags: [vision, beginner, image, color, filter]
level: beginner
---

# 视觉算法基础

## 概述

本文介绍 vision 领域的 beginner 级别知识。

完成本文学习后，你将能够：

- 理解核心概念和基本原理
- 掌握关键技术和实现方法
- 应用到实际产品开发中

## 背景知识

### 相关概念

> 占位 - 待补充前置概念

## 核心内容

### 1. 数字图像基础

```
数字图像 = 像素矩阵

灰度图: 每个像素 1 个值 (0-255)
  ┌───┬───┬───┬───┐
  │ 0 │ 50│100│255│
  ├───┼───┼───┼───┤
  │ 30│ 80│150│200│
  └───┴───┴───┴───┘

彩色图: 每个像素 3 个值 (R, G, B)
  ┌─────────────┐
  │ (255,0,0)   │ 红色
  │ (0,255,0)   │ 绿色
  │ (0,0,255)   │ 蓝色
  │ (255,255,0) │ 黄色
  └─────────────┘

分辨率: 1920×1080 = 200 万像素
```

### 2. 颜色空间

```
RGB: 红绿蓝 (最常用)
  R: 0-255 (红色分量)
  G: 0-255 (绿色分量)
  B: 0-255 (蓝色分量)

HSV: 色相-饱和度-明度
  H: 0-360° (颜色类型)
  S: 0-100% (颜色纯度)
  V: 0-100% (亮度)

  HSV 更适合颜色检测:
  例: 检测红色物体
  → H 在 0-30° 或 330-360°

YUV: 亮度-色度
  Y: 亮度 (灰度)
  U: 蓝色色度
  V: 红色色度

  YUV 用于视频编码 (压缩时丢弃 U/V)
```

### 3. 基本图像操作

```c
// 灰度化
void rgb_to_gray(uint8_t *rgb, uint8_t *gray, int w, int h) {
    for(int i = 0; i < w*h; i++) {
        int r = rgb[i*3], g = rgb[i*3+1], b = rgb[i*3+2];
        gray[i] = (uint8_t)(0.299*r + 0.587*g + 0.114*b);
    }
}

// 二值化 (阈值分割)
void threshold(uint8_t *gray, uint8_t *binary,
               int w, int h, int thresh) {
    for(int i = 0; i < w*h; i++) {
        binary[i] = gray[i] > thresh ? 255 : 0;
    }
}

// 图像翻转
void flip_horizontal(uint8_t *src, uint8_t *dst, int w, int h) {
    for(int y = 0; y < h; y++) {
        for(int x = 0; x < w; x++) {
            dst[y*w + x] = src[y*w + (w-1-x)];
        }
    }
}
```

### 4. 滤波

```c
// 均值滤波 (模糊/降噪)
void blur_3x3(uint8_t *src, uint8_t *dst, int w, int h) {
    for(int y = 1; y < h-1; y++) {
        for(int x = 1; x < w-1; x++) {
            int sum = 0;
            for(int dy = -1; dy <= 1; dy++) {
                for(int dx = -1; dx <= 1; dx++) {
                    sum += src[(y+dy)*w + (x+dx)];
                }
            }
            dst[y*w + x] = sum / 9;
        }
    }
}

// 边缘检测 (Sobel)
void sobel(uint8_t *src, uint8_t *dst, int w, int h) {
    for(int y = 1; y < h-1; y++) {
        for(int x = 1; x < w-1; x++) {
            int gx = -src[(y-1)*w+(x-1)] + src[(y-1)*w+(x+1)]
                     -2*src[y*w+(x-1)] + 2*src[y*w+(x+1)]
                     -src[(y+1)*w+(x-1)] + src[(y+1)*w+(x+1)];
            int gy = -src[(y-1)*w+(x-1)] - 2*src[(y-1)*w+x] - src[(y-1)*w+(x+1)]
                     +src[(y+1)*w+(x-1)] + 2*src[(y+1)*w+x] + src[(y+1)*w+(x+1)];
            dst[y*w + x] = CLAMP(abs(gx) + abs(gy), 0, 255);
        }
    }
}
```

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

**下一步**：建议学习 [[vision/intermediate/|中级内容]]
