---
title: "无人机算法 - 路径规划与返航"
tags: [drone, path-planning, rtl, geofence, avoidance, algorithm]
module: "11-product-lines"
---

# 无人机算法详解

## 1. 航点导航

### 航点跟踪 (Line Following)
```
航点跟踪算法:

当前位置 P, 目标航点 W, 下一航点 W_next

1. 计算航点线段方向:
   d = (W_next - W) / |W_next - W|

2. 计算垂足 (最近点):
   t = (P - W) · d
   closest = W + t · d

3. 横向误差 (cross-track error):
   e_ct = |P - closest|

4. 航向误差:
   e_heading = atan2(d.y, d.x) - current_heading

5. 控制指令:
   lateral_speed = Kp_ct · e_ct + Kd_ct · d(e_ct)/dt
   forward_speed = Kp_h · cos(e_heading) · max_speed
   yaw_rate = Kp_heading · e_heading

到达判定:
   if |P - W| < arrival_radius:
       切换到下一航点
```

## 2. 地理围栏

### 多边形围栏检测
```c
/* 射线法判断点在多边形内 */

typedef struct {
    float lat, lon;
} GeoPoint;

bool point_in_polygon(GeoPoint *polygon, int n, 
                       float lat, float lon) {
    bool inside = false;
    
    for (int i = 0, j = n-1; i < n; j = i++) {
        float xi = polygon[i].lon, yi = polygon[i].lat;
        float xj = polygon[j].lon, yj = polygon[j].lat;
        
        // 射线与边相交检测
        if (((yi > lat) != (yj > lat)) &&
            (lon < (xj - xi) * (lat - yi) / (yj - yi) + xi)) {
            inside = !inside;
        }
    }
    
    return inside;
}

/* 圆形围栏检测 */
bool point_in_circle(float center_lat, float center_lon, 
                      float radius_m, float lat, float lon) {
    float dist = haversine_distance(center_lat, center_lon, lat, lon);
    return dist < radius_m;
}

/* 围栏违规处理 */
void check_geofence(float lat, float lon, float alt) {
    // 水平围栏
    if (!point_in_polygon(fence_polygon, fence_points, lat, lon)) {
        // 计算返回围栏内的方向
        float return_bearing = bearing_to_nearest_edge(lat, lon);
        
        // 限制飞行: 只允许朝围栏内飞
        limit_velocity_direction(return_bearing);
        
        // 如果严重超出 (>50m), 触发返航
        if (distance_to_fence_edge(lat, lon) > 50) {
            trigger_rtl();
        }
    }
    
    // 高度围栏
    if (alt > max_altitude) {
        limit_altitude(max_altitude);
    }
}
```

## 3. 返航 (RTL) 算法

### 智能返航 (沿航线返回)
```
记录飞行轨迹:
  轨迹点队列: P0 → P1 → P2 → P3 → ... → Pn

返航路径:
  Pn → Pn-1 → ... → P2 → P1 → P0 (起飞点)

优化:
  1. 简化轨迹 (Douglas-Peucker 算法)
     - 移除冗余中间点
     - 保持关键转向点
  
  2. 避障检查
     - 检查返航路径是否有障碍物
     - 如有, 绕行或升高
  
  3. 高度优化
     - 最后阶段缓慢下降
     - 避免直接俯冲

RTL 流程:
  1. 爬升到安全高度 (如 30m)
  2. 沿简化航线返回
  3. 到达起飞点上空
  4. 缓慢下降
  5. 着陆检测 (高度 + 加速度)
  6. 关闭电机
```

## 4. 悬停算法

### 位置保持 (GPS + 光流)
```
GPS 悬停 (室外):
  位置误差 = GPS_测量 - 目标位置
  速度指令 = Kp · 位置误差 + Kd · 速度估计
  
  水平精度: ±1.5m (单点), ±0.02m (RTK)

光流悬停 (室内):
  光流速度 = 光流传感器测量
  位置估计 += 光流速度 · dt
  速度指令 = Kp · 位置误差 + Kd · 光流速度
  
  水平精度: ±0.1m

融合悬停 (GPS + 光流):
  低空 (<5m): 主要依赖光流
  高空 (>5m): 主要依赖 GPS
  过渡区: 加权融合
```

---

## 相关链接

- [[flight-controller-firmware|飞控]] — 控制算法
- [[gps-system|GPS]] — 定位系统
- [[visual-slam|视觉]] — 视觉避障
