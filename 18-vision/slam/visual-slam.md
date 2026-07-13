---
title: "视觉系统"
aliases:
  - "视觉 SLAM"
  - "避障"
tags:
  - vision
  - slam
  - obstacle-avoidance
  - tracking
  - depth
module: "18-vision"
status: active
---

# 视觉系统

## 1. 视觉 SLAM

### VIO (视觉惯性里程计)
```
VIO 系统架构:

Camera (图像) ──→ 特征提取 ──→ 特征匹配 ──→ 位姿估计
                                              │
IMU (加速度/角速度) ──→ 预积分 ─────────────→ 融合
                                              │
                                              ▼
                                        位姿输出 (6DoF)
                                        地图点云

常用 VIO 框架:
├── VINS-Mono/Mobile: 单目 VIO, 港科大开源
├── ORB-SLAM3: 单目/双目/RGB-D + IMU
├── MSCKF: 滤波方法, 低计算量
├── OpenVINS: 模块化 VIO
├── ARKit/ARCore: 商用方案
└── T265 (Intel): 硬件 VIO 模块

VINS-Mono 核心流程:
1. 初始化
   ├── 单目 SfM 恢复初始结构
   ├── 视觉惯性对齐 (尺度、重力方向)
   └── 三角化初始地图点

2. 前端 (视觉里程计)
   ├── KLT 光流跟踪特征点
   ├── 关键帧选择
   └── 5-point RANSAC 外点剔除

3. 后端 (滑动窗口优化)
   ├── 边缘化旧帧
   ├── 视觉重投影误差
   ├── IMU 预积分约束
   └── 先验约束

4. 回环检测
   ├── DBoW2 词袋检索
   ├── 回环验证
   └── 位姿图优化
```

### 双目视觉
```
双目测距原理:

左相机        右相机
  │             │
  │  基线 B     │
  │←───────────→│
  │             │
  ▼             ▼
┌───┐         ┌───┐
│   │         │   │
└───┘         └───┘

视差 (disparity) d = x_left - x_right
深度 Z = f × B / d

其中:
f = 焦距 (像素)
B = 基线长度 (米)
d = 视差 (像素)

示例:
├── f = 700 pixels
├── B = 0.12m (12cm)
├── d = 35 pixels (10m 处物体)
└── Z = 700 × 0.12 / 35 = 2.4m (错误!应该是 10m)

修正: d = 700 × 0.12 / 10 = 8.4 pixels (10m 处)

深度分辨率:
ΔZ = Z² / (f × B)
├── 1m 处:  ΔZ = 1 / (700×0.12) = 0.012m = 1.2cm
├── 5m 处:  ΔZ = 25 / (700×0.12) = 0.30m = 30cm
├── 10m 处: ΔZ = 100 / (700×0.12) = 1.19m = 119cm
└── 20m 处: ΔZ = 400 / (700×0.12) = 4.76m = 476cm

结论: 双目测距精度随距离平方增长, 近距离精度高
```

## 2. 避障系统

### 避障传感器对比
| 传感器 | 测距范围 | 精度 | FOV | 帧率 | 功耗 | 成本 | 适用 |
|--------|----------|------|-----|------|------|------|------|
| 双目相机 | 0.5-30m | 1-5% | 90° | 30fps | 中 | 中 | 通用避障 |
| ToF 相机 | 0.1-5m | 1% | 60° | 60fps | 中 | 中 | 近距避障 |
| 结构光 | 0.2-10m | 0.5% | 60° | 30fps | 中 | 高 | 精细建图 |
| 超声波 | 0.02-5m | 3% | 30° | 10Hz | 低 | 低 | 近距测距 |
| 毫米波雷达 | 0.5-200m | 5% | 120° | 20Hz | 中 | 中 | 全天候 |
| [[lidar-system|LiDAR]] | 0.3-200m | 2cm | 360° | 10Hz | 高 | 高 | 精确建图 |

### 双目避障算法
```c
/* stereo_obstacle_avoidance.c */

/* 视差图转深度图 */
void disparity_to_depth(const float *disparity, float *depth,
                         int width, int height,
                         float focal_length, float baseline) {
    for (int i = 0; i < width * height; i++) {
        if (disparity[i] > 0) {
            depth[i] = focal_length * baseline / disparity[i];
        } else {
            depth[i] = INFINITY;
        }
    }
}

/* 障碍物检测 */
typedef struct {
    float x, y, z;       // 障碍物位置 (机体坐标系)
    float distance;       // 距离
    float size;           // 尺寸
    float confidence;     // 置信度
} Obstacle;

int detect_obstacles(const float *depth, int width, int height,
                      Obstacle *obstacles, int max_count,
                      float min_dist, float max_dist) {
    int count = 0;
    
    // 将深度图分成网格
    int grid_w = 8, grid_h = 6;
    int cell_w = width / grid_w;
    int cell_h = height / grid_h;
    
    for (int gy = 0; gy < grid_h && count < max_count; gy++) {
        for (int gx = 0; gx < grid_w && count < max_count; gx++) {
            // 统计网格内的最小深度
            float min_depth = INFINITY;
            int valid_count = 0;
            float sum_x = 0, sum_y = 0, sum_z = 0;
            
            for (int y = gy * cell_h; y < (gy + 1) * cell_h; y++) {
                for (int x = gx * cell_w; x < (gx + 1) * cell_w; x++) {
                    float d = depth[y * width + x];
                    if (d > min_dist && d < max_dist) {
                        if (d < min_depth) min_depth = d;
                        valid_count++;
                        sum_x += x;
                        sum_y += y;
                        sum_z += d;
                    }
                }
            }
            
            // 如果有足够的有效像素，认为有障碍物
            if (valid_count > cell_w * cell_h * 0.3 && 
                min_depth < max_dist) {
                Obstacle *obs = &obstacles[count];
                obs->x = (gx - grid_w / 2.0f) * min_depth / focal;
                obs->y = (gy - grid_h / 2.0f) * min_depth / focal;
                obs->z = min_depth;
                obs->distance = min_depth;
                obs->size = cell_w * min_depth / focal;
                obs->confidence = (float)valid_count / 
                                  (cell_w * cell_h);
                count++;
            }
        }
    }
    
    return count;
}

/* 避障决策 */
typedef enum {
    AVOID_NONE,
    AVOID_SLOW_DOWN,
    AVOID_STOP,
    AVOID_ALTITUDE,
    AVOID_SIDESTEP,
    AVOID_RETURN,
} AvoidanceAction;

AvoidanceAction plan_avoidance(const Obstacle *obstacles, 
                                 int count,
                                 float flight_speed) {
    float min_front_dist = INFINITY;
    
    // 找前方最近障碍物
    for (int i = 0; i < count; i++) {
        if (fabsf(obstacles[i].x) < 1.0f &&  // 前方 ±1m
            obstacles[i].z > 0) {              // 正前方
            if (obstacles[i].distance < min_front_dist) {
                min_front_dist = obstacles[i].distance;
            }
        }
    }
    
    // 决策
    if (min_front_dist < 1.0f) {
        return AVOID_STOP;           // <1m: 紧急停止
    } else if (min_front_dist < 3.0f) {
        return AVOID_SIDESTEP;       // 1-3m: 侧移避障
    } else if (min_front_dist < 5.0f) {
        return AVOID_SLOW_DOWN;      // 3-5m: 减速
    } else if (min_front_dist < 10.0f) {
        return AVOID_ALTITUDE;       // 5-10m: 调整高度
    }
    
    return AVOID_NONE;
}
```

## 3. 目标跟踪

### 跟踪算法
```
传统方法:
├── KCF (Kernel Correlation Filter)
│   ├── 基于相关滤波
│   ├── 速度快 (>100fps)
│   └── 对遮挡敏感
│
├── MOSSE (Minimum Output Sum of Squared Error)
│   ├── 最简单相关滤波
│   ├── 速度极快 (>700fps)
│   └── 精度一般
│
└── CSRT (Discriminative Correlation Filter with SR)
    ├── 空间可靠性权重
    ├── 精度高
    └── 速度中等 (~50fps)

深度学习方法:
├── SiamFC (Siamese Fully Convolutional)
│   ├── 端到端学习
│   ├── 精度高
│   └── ~50fps (GPU)
│
├── SiamRPN / SiamRPN++
│   ├── 区域建议网络
│   ├── 尺度自适应
│   └── ~30fps (GPU)
│
├── TransT / STARK
│   ├── Transformer 架构
│   ├── 精度最高
│   └── ~30fps (GPU)
│
└── YOLO + DeepSORT
    ├── 检测 + 多目标跟踪
    ├── 处理遮挡
    └── ~30fps (GPU)
```

### [[gimbal-control|云台]]跟踪控制
```c
/* gimbal_tracking.c */

typedef struct {
    float target_x, target_y;    // 目标在图像中的位置 (像素)
    float image_center_x, image_center_y;  // 图像中心
    float focal_length;          // 焦距 (像素)
    float tracking_gain;         // 跟踪增益
    float filter_alpha;          // 低通滤波系数
    float filtered_vx, filtered_vy;  // 滤波后的速度
} TrackingState;

/* 跟踪云台控制 */
void gimbal_tracking_update(TrackingState *ts,
                             float target_x, float target_y,
                             float dt,
                             float *yaw_cmd, float *pitch_cmd) {
    // 计算目标偏离中心的像素误差
    float error_x = target_x - ts->image_center_x;
    float error_y = target_y - ts->image_center_y;
    
    // 转换为角度误差
    float angle_error_x = atan2f(error_x, ts->focal_length);
    float angle_error_y = atan2f(error_y, ts->focal_length);
    
    // 计算目标速度 (用于前馈)
    float vx = angle_error_x / dt;
    float vy = angle_error_y / dt;
    
    // 低通滤波
    ts->filtered_vx = ts->filter_alpha * vx + 
                      (1 - ts->filter_alpha) * ts->filtered_vx;
    ts->filtered_vy = ts->filter_alpha * vy + 
                      (1 - ts->filter_alpha) * ts->filtered_vy;
    
    // PID + 前馈
    *yaw_cmd = ts->tracking_gain * angle_error_x + 
               0.3f * ts->filtered_vx;   // 前馈
    *pitch_cmd = ts->tracking_gain * angle_error_y + 
                 0.3f * ts->filtered_vy;
    
    // 限幅
    *yaw_cmd = CLAMP(*yaw_cmd, -2.0f, 2.0f);    // rad/s
    *pitch_cmd = CLAMP(*pitch_cmd, -2.0f, 2.0f);
}
```

## 4. 深度估计

### 单目深度估计
```
方法 1: MiDaS (深度学习)
├── 输入: 单张 RGB 图像
├── 输出: 相对深度图
├── 优点: 无需标定
└── 缺点: 相对深度，需后处理

方法 2: 结构从运动 (SfM)
├── 多视图几何
├── 需要相机运动
└── 恢复绝对深度

方法 3: 深度学习 + IMU
├── 单目深度网络
├── IMU 提供尺度信息
└── 绝对深度估计
```
---

## 相关链接

- [[camera-sensor|相机系统]]
- [[lidar-system|激光雷达]]
- [[imu-system|IMU]]
