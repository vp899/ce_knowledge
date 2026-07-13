---
title: "激光雷达 (LiDAR)"
aliases:
  - "激光雷达"
  - "LiDAR 测距"
tags:
  - lidar
  - tof
  - slam
  - point-cloud
module: "23-lidar"
status: active
---

# 激光雷达 (LiDAR)

## 1. 测距原理

### ToF (飞行时间) 测距
```
脉冲式 ToF:
发射器 ──→ 激光脉冲 ──→ 目标 ──→ 反射 ──→ 接收器
                                        │
                                    计算时间差
                                        │
                                    距离 = c × t / 2

精度: ±1-3cm
范围: 0.1-200m
频率: 10kHz-1MHz (单点)
优点: 测距远, 精度高
缺点: 受环境光影响

相位式 ToF:
发射器 ──→ 连续波调制 ──→ 目标 ──→ 反射 ──→ 接收器
                                        │
                                    测量相位差
                                        │
                                    距离 = c × φ / (4π × f)

精度: ±1mm-1cm
范围: 0.01-50m
频率: 100kHz-100MHz (调制频率)
优点: 精度高, 可靠
缺点: 多路径干扰
```

### 三角测距
```
三角测距原理:

激光器        接收透镜
  │              │
  │     d        │
  │←────────────→│
  │              │
  ▼              ▼
  ╲              │
   ╲  θ          │
    ╲            │ f (焦距)
     ╲          │
      ╲        │
       ╲      │
        ╲    │
         ╲  │
          ╲│
           │←── x (像面上的位置)
           │

目标距离 D = f × d / x

精度: ±0.1-1mm (近距离)
范围: 0.01-30m
优点: 精度极高 (近距离)
缺点: 距离远精度下降, 体积较大
```

### FMCW (调频连续波)
```
FMCW 测距原理:

发射信号: 频率线性调频 (锯齿波)
接收信号: 延迟的发射信号

频率
  │    ╱╱╱
  │   ╱╱╱  ← 发射
  │  ╱╱╱
  │ ╱╱╱
  │╱╱╱───────────
  │╱  ╱╱╱
  │  ╱╱╱  ← 接收
  │ ╱╱╱
  │╱╱╱
  └──────────────→ 时间
      │
      │←──→│
         Δt (延迟)

差频: fb = Δf × 2D / (c × T)
距离: D = fb × c × T / (2 × Δf)

FMCW 优势:
├── 同时测距和测速
├── 抗环境光干扰
├── 抗多径干扰
└── 精度高 (mm 级)
```

## 2. LiDAR 系统类型

### 机械旋转式 LiDAR
```
结构:
┌─────────────────────────────────┐
│          旋转部分                │
│  ┌──────────────────────────┐  │
│  │  激光器 + 接收器          │  │
│  │  (16/32/64 线)           │  │
│  └──────────────────────────┘  │
│         │                       │
│     旋转电机 (600-1200 RPM)     │
│         │                       │
│  ┌──────────────────────────┐  │
│  │  固定底座                 │  │
│  │  (电源/通信/处理)         │  │
│  └──────────────────────────┘  │
└─────────────────────────────────┘

典型产品:
├── Velodyne VLP-16: 16线, 100m, 300k点/秒
├── Velodyne VLP-32C: 32线, 200m, 600k点/秒
├── Hesai Pandar40P: 40线, 200m, 800k点/秒
├── Robosense RS-LiDAR-16: 16线, 150m, 300k点/秒
└── Livox Mid-70: 非重复扫描, 70m, 100k点/秒

参数:
├── 线数: 1/4/16/32/64/128
├── 测距范围: 0.3-200m
├── 精度: ±1-3cm
├── 角分辨率: 0.1-0.4°
├── 垂直 FOV: 15-40°
├── 水平 FOV: 360°
├── 帧率: 5-20Hz
└── 点云密度: 100k-3M 点/秒
```

### 固态 LiDAR
```
MEMS 振镜式:
├── 微机电振镜扫描
├── 无旋转部件
├── 体积小, 可靠性高
├── FOV: 60-120° (水平)
└── 代表: Innoviz One, Livox Horizon

OPA (光学相控阵):
├── 电子束偏转
├── 无机械运动
├── 响应极快
├── 技术尚不成熟
└── 代表: Quanergy S3

Flash LiDAR:
├── 面阵探测 (类似相机)
├── 一次闪光获取整帧深度
├── 距离有限 (30m)
├── 分辨率有限
└── 代表: Intel RealSense L515

FMCW LiDAR:
├── 调频连续波
├── 同时测距和测速
├── 抗干扰强
├── 精度高 (mm 级)
└── 代表: Aeva, SiLC
```

## 3. 点云处理

### 点云数据格式
```c
/* 点云数据结构 */
typedef struct {
    float x, y, z;        // 3D 坐标 (米)
    float intensity;       // 反射强度 (0-255)
    uint16_t ring;         // 线号 (0-15 for 16线)
    double timestamp;      // 时间戳 (秒)
} PointXYZI;

typedef struct {
    PointXYZI *points;
    int count;
    int capacity;
    double start_time;
    double end_time;
} PointCloud;

/* 解析 Livox 数据包 */
int parse_livox_packet(const uint8_t *data, int len, 
                        PointCloud *cloud) {
    LivoxPacketHeader *header = (LivoxPacketHeader *)data;
    
    int point_count = header->dot_num;
    LivoxPoint *raw_points = (LivoxPoint *)(data + 
                              sizeof(LivoxPacketHeader));
    
    for (int i = 0; i < point_count; i++) {
        PointXYZI *p = &cloud->points[cloud->count];
        
        // 坐标转换 (极坐标 → 直角坐标)
        float range = raw_points[i].depth / 1000.0f;  // mm → m
        float theta = raw_points[i].theta * DEG_TO_RAD;
        float phi = raw_points[i].phi * DEG_TO_RAD;
        
        p->x = range * cosf(phi) * cosf(theta);
        p->y = range * cosf(phi) * sinf(theta);
        p->z = range * sinf(phi);
        p->intensity = raw_points[i].reflectivity;
        p->timestamp = header->timestamp;
        
        cloud->count++;
    }
    
    return 0;
}
```

### 点云滤波
```c
/* 点云滤波算法 */

/* 体素下采样 (Voxel Grid) */
void voxel_grid_downsample(PointCloud *input, PointCloud *output,
                            float voxel_size) {
    // 建立体素网格
    int grid_x = (int)((input->max_x - input->min_x) / voxel_size) + 1;
    int grid_y = (int)((input->max_y - input->min_y) / voxel_size) + 1;
    int grid_z = (int)((input->max_z - input->min_z) / voxel_size) + 1;
    
    // 哈希表存储体素
    HashMap *voxel_map = hashmap_create();
    
    for (int i = 0; i < input->count; i++) {
        PointXYZI *p = &input->points[i];
        
        int gx = (int)((p->x - input->min_x) / voxel_size);
        int gy = (int)((p->y - input->min_y) / voxel_size);
        int gz = (int)((p->z - input->min_z) / voxel_size);
        
        uint64_t key = ((uint64_t)gx << 40) | 
                       ((uint64_t)gy << 20) | gz;
        
        // 累加到体素中心
        VoxelAccum *acc = hashmap_get(voxel_map, key);
        if (acc == NULL) {
            acc = malloc(sizeof(VoxelAccum));
            acc->x = p->x; acc->y = p->y; acc->z = p->z;
            acc->count = 1;
            hashmap_put(voxel_map, key, acc);
        } else {
            acc->x += p->x; acc->y += p->y; acc->z += p->z;
            acc->count++;
        }
    }
    
    // 计算体素中心
    hashmap_foreach(voxel_map, key, acc) {
        PointXYZI *out = &output->points[output->count];
        out->x = acc->x / acc->count;
        out->y = acc->y / acc->count;
        out->z = acc->z / acc->count;
        output->count++;
    }
    
    hashmap_destroy(voxel_map);
}

/* 统计离群点去除 */
void statistical_outlier_removal(PointCloud *input, PointCloud *output,
                                   int k_neighbors, float std_threshold) {
    // 对每个点，找 k 个最近邻
    // 计算平均距离
    // 移除距离大于 mean + std_threshold × std 的点
    
    KDTree *tree = kdtree_build(input);
    
    float *mean_distances = malloc(input->count * sizeof(float));
    float total_mean = 0;
    
    for (int i = 0; i < input->count; i++) {
        float *distances = kdtree_knn(tree, &input->points[i], 
                                       k_neighbors);
        mean_distances[i] = 0;
        for (int j = 0; j < k_neighbors; j++) {
            mean_distances[i] += distances[j];
        }
        mean_distances[i] /= k_neighbors;
        total_mean += mean_distances[i];
    }
    
    total_mean /= input->count;
    
    // 计算标准差
    float variance = 0;
    for (int i = 0; i < input->count; i++) {
        float diff = mean_distances[i] - total_mean;
        variance += diff * diff;
    }
    float std = sqrtf(variance / input->count);
    
    // 过滤
    float threshold = total_mean + std_threshold * std;
    for (int i = 0; i < input->count; i++) {
        if (mean_distances[i] < threshold) {
            output->points[output->count++] = input->points[i];
        }
    }
    
    free(mean_distances);
    kdtree_destroy(tree);
}
```

## 4. [[visual-slam|SLAM]] 建图

### LiDAR SLAM 算法
```
经典 LiDAR SLAM:

1. ICP (Iterative Closest Point)
   ├── 最近点匹配
   ├── 计算变换矩阵
   ├── 迭代直到收敛
   └── 精度高, 但容易陷入局部最优

2. NDT (Normal Distributions Transform)
   ├── 点云分成体素
   ├── 每个体素拟合正态分布
   ├── 用概率模型匹配
   └── 比 ICP 更鲁棒

3. LOAM (LiDAR Odometry and Mapping)
   ├── 特征提取 (边缘点 + 平面点)
   ├── 帧间匹配 (里程计)
   ├── 帧到地图匹配 (建图)
   └── 实时性好

4. LeGO-LOAM (Lightweight and Ground-Optimized LOAM)
   ├── 地面分割
   ├── 聚类
   ├── 特征提取
   └── 适合地面机器人

5. LIO-SAM (LiDAR-Inertial Odometry via Smoothing and Mapping)
   ├── LiDAR + IMU 紧耦合
   ├── 因子图优化
   ├── 回环检测
   └── 精度最高

Cartographer:
├── Google 开源
├── 2D/3D SLAM
├── 子图 + 全局优化
├── 实时性好
└── 适合室内建图
```

### LIO-SAM 核心流程
```
LIO-SAM 系统架构:

LiDAR 扫描 ──→ 去畸变 ──→ 特征提取 ──→ 帧到地图匹配
                                              │
IMU 数据 ──→ IMU 预积分 ──→ 因子图优化 ←────┘
                                              │
GPS 数据 ──→ GPS 因子 ───→ 因子图优化 ←────┘
                                              │
                                              ▼
                                        位姿输出
                                        点云地图

因子图:
┌─────────────────────────────────────────┐
│                                          │
│  X0 ── X1 ── X2 ── X3 ── X4            │
│  │      │      │      │      │           │
│  IMU    IMU    IMU    IMU    IMU         │
│  │      │      │      │      │           │
│  L0     L1     L2     L3     L4         │
│  │             │             │           │
│  GPS           GPS           GPS        │
│                                          │
│  X = 位姿节点                            │
│  IMU = IMU 预积分因子                    │
│  L = LiDAR 匹配因子                     │
│  GPS = GPS 位置因子                      │
│                                          │
└─────────────────────────────────────────┘
```

## 5. LiDAR 驱动开发

### 串口驱动示例
```c
/* lidar_serial_driver.c */

/* Livox LiDAR 协议 */
#define LIVOX_HEADER_SIZE    24
#define LIVOX_POINT_SIZE     14
#define LIVOX_MAX_POINTS     100

typedef struct {
    uint8_t version;
    uint8_t length;
    uint16_t time_interval;
    uint16_t dot_num;
    uint16_t udp_cnt;
    uint8_t frame_cnt;
    uint8_t data_type;
    uint8_t time_type;
    uint8_t pack_info;
    uint8_t padding[2];
    double timestamp;
} __attribute__((packed)) LivoxPacketHeader;

typedef struct {
    int32_t x;           // mm
    int32_t y;           // mm
    int32_t z;           // mm
    uint8_t reflectivity;
    uint8_t tag;
} __attribute__((packed)) LivoxPointRaw;

/* 数据解析线程 */
void *lidar_rx_thread(void *arg) {
    LidarDriver *drv = (LidarDriver *)arg;
    uint8_t buffer[1500];
    
    while (drv->running) {
        int len = udp_recv(drv->sock, buffer, sizeof(buffer), 100);
        if (len < LIVOX_HEADER_SIZE) continue;
        
        LivoxPacketHeader *header = (LivoxPacketHeader *)buffer;
        LivoxPointRaw *raw = (LivoxPointRaw *)(buffer + LIVOX_HEADER_SIZE);
        
        // 转换点云
        for (int i = 0; i < header->dot_num; i++) {
            PointXYZI *p = &drv->cloud.points[drv->cloud.count];
            
            p->x = raw[i].x / 1000.0f;  // mm → m
            p->y = raw[i].y / 1000.0f;
            p->z = raw[i].z / 1000.0f;
            p->intensity = raw[i].reflectivity;
            p->timestamp = header->timestamp + 
                           i * header->time_interval / 1000000.0f;
            
            drv->cloud.count++;
        }
        
        // 帧结束检查
        if (header->frame_cnt != drv->last_frame_cnt) {
            // 新帧开始，回调处理
            if (drv->callback) {
                drv->callback(&drv->cloud, drv->user_data);
            }
            drv->cloud.count = 0;
            drv->last_frame_cnt = header->frame_cnt;
        }
    }
    
    return NULL;
}

/* 以太网驱动 (高速 LiDAR) */
int lidar_ethernet_init(LidarDriver *drv, const char *ip, int port) {
    // 创建 UDP socket
    drv->sock = socket(AF_INET, SOCK_DGRAM, 0);
    
    struct sockaddr_in addr;
    addr.sin_family = AF_INET;
    addr.sin_port = htons(port);
    inet_pton(AF_INET, ip, &addr.sin_addr);
    
    bind(drv->sock, (struct sockaddr *)&addr, sizeof(addr));
    
    // 设置接收缓冲区
    int buf_size = 4 * 1024 * 1024;  // 4MB
    setsockopt(drv->sock, SOL_SOCKET, SO_RCVBUF, 
               &buf_size, sizeof(buf_size));
    
    // 启动接收线程
    drv->running = true;
    pthread_create(&drv->rx_thread, NULL, lidar_rx_thread, drv);
    
    return 0;
}
```
---

## 相关链接

- [[visual-slam|视觉系统]]
- [[imu-system|IMU]]
