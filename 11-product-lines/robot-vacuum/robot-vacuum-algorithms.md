---
title: "产品线算法 - 扫地机器人"
tags: [robot-vacuum, slam, path-planning, coverage, dock, algorithm]
module: "11-product-lines"
---

# 扫地机器人算法详解

## 1. 全覆盖路径规划

### Boustrophedon (牛耕式) 分解
```
将自由空间分解为多个 cell:

┌─────┬───────────┐
│     │           │
│  A  │     B     │
│     │           │
├─────┤           │
│     │           │
│  C  ├───────────┤
│     │     D     │
│     │           │
└─────┴───────────┘

每个 cell 内做弓字形清扫:
  A: →→→→→→
      ←←←←←←
      →→→→→→

cell 间用最短路径连接:
  A → C → D → B (或用 TSP 优化)

覆盖率计算:
  coverage = 已清扫面积 / 总自由面积 × 100%
  目标: >98%
```

### 路径生成算法
```c
/* 弓字形路径生成 */

typedef struct {
    float x, y;
} Point;

typedef struct {
    Point *points;
    int count;
} Path;

void generate_boustrophedon_path(
    uint8_t *occupancy_grid, int grid_w, int grid_h,
    float resolution, float robot_radius,
    float start_x, float start_y,
    Path *path) {
    
    int r_cells = (int)(robot_radius / resolution);
    path->count = 0;
    
    // 从下往上逐行扫描
    for (int y = r_cells; y < grid_h - r_cells; y++) {
        if (y % 2 == 0) {
            // 从左到右
            for (int x = r_cells; x < grid_w - r_cells; x++) {
                if (is_free(occupancy_grid, x, y, r_cells)) {
                    path->points[path->count].x = x * resolution;
                    path->points[path->count].y = y * resolution;
                    path->count++;
                }
            }
        } else {
            // 从右到左
            for (int x = grid_w - r_cells - 1; x >= r_cells; x--) {
                if (is_free(occupancy_grid, x, y, r_cells)) {
                    path->points[path->count].x = x * resolution;
                    path->points[path->count].y = y * resolution;
                    path->count++;
                }
            }
        }
    }
}
```

## 2. 回充对接算法

### 红外信标定位
```
充电座红外信标:
  发射 38kHz 调制红外信号
  覆盖角度: ±30°

机器人接收:
  左/中/右 三个红外接收器
  根据信号强度判断方向

对接流程:
  1. 检测到红外信号 → 粗对准
  2. 转向信号最强方向
  3. 缓慢前进, 持续调整方向
  4. 接近充电座 → 微调
  5. 物理接触 → 充电开始

PID 方向控制:
  error = left_signal - right_signal
  steering = Kp · error + Kd · d(error)/dt
```

## 3. 尘盒/水箱检测

### 霍尔传感器检测
```c
/* 霍尔传感器检测附件 */

typedef enum {
    ATTACH_NONE = 0,
    ATTACH_DUST_BIN,      // 尘盒
    ATTACH_WATER_TANK,    // 水箱
    ATTACH_MOP,           // 拖布
} AttachmentType;

AttachmentType detect_attachment(int adc_value) {
    // 不同附件内置不同强度磁铁
    // ADC 值对应不同范围
    
    if (adc_value < 500) {
        return ATTACH_NONE;
    } else if (adc_value >= 500 && adc_value < 1500) {
        return ATTACH_DUST_BIN;
    } else if (adc_value >= 1500 && adc_value < 2500) {
        return ATTACH_WATER_TANK;
    } else {
        return ATTACH_MOP;
    }
}
```

## 4. 拖地控制算法

### 出水量控制
```c
/* 自适应出水量控制 */

typedef struct {
    int base_flow_rate;     // 基础出水量 (ml/min)
    int max_flow_rate;      // 最大出水量
    float dirt_level;       // 脏污程度 (0-1)
    float floor_type;       // 地板类型系数
} MopController;

int calculate_flow_rate(MopController *mc, 
                         float dirt_level,
                         int floor_type) {
    // 地板类型系数
    float floor_coeff[] = {1.0, 0.8, 1.2, 1.5};  // 瓷砖/木地板/大理石/地毯
    
    // 出水量 = 基础 × 脏污系数 × 地板系数
    int flow = mc->base_flow_rate * (1.0f + dirt_level) * floor_coeff[floor_type];
    
    return CLAMP(flow, 0, mc->max_flow_rate);
}
```

---

## 相关链接

- [[lidar-system|激光雷达]] — LDS SLAM
- [[visual-slam|视觉 SLAM]] — 视觉避障
- [[esc-control|电机控制]] — 驱动系统
