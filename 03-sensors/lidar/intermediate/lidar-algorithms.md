level: intermediate
---
title: "LiDAR SLAM 算法详解"
tags: [lidar, slam, icp, ndt, loam, point-cloud, algorithm]
module: "03-sensors"
---

# LiDAR SLAM 算法详解

## 概述

本文介绍 lidar 领域的 intermediate 级别知识。

完成本文学习后，你将能够：

- 理解核心概念和基本原理
- 掌握关键技术和实现方法
- 应用到实际产品开发中

## 背景知识

### 相关概念

> 占位 - 待补充前置概念

## 核心内容

### 1. ICP (Iterative Closest Point)

### 算法流程
```
输入: 源点云 P, 目标点云 Q
输出: 变换矩阵 T (R, t)

迭代:
1. 对 P 中每个点, 在 Q 中找最近点
2. 计算对应点对
3. 求解最优变换 T (最小化误差)
4. 应用变换: P' = T · P
5. 检查收敛 (误差变化 < 阈值)
6. 未收敛则回到步骤 1

误差函数:
  E = Σ ||q_i - R·p_i - t||²

最优解 (SVD):
  1. 计算质心: p̄ = mean(P), q̄ = mean(Q)
  2. 去质心: p'_i = p_i - p̄, q'_i = q_i - q̄
  3. 构造协方差矩阵: H = Σ p'_i · q'_i^T
  4. SVD 分解: H = U·Σ·V^T
  5. 旋转: R = V·U^T
  6. 平移: t = q̄ - R·p̄
```

### ICP 实现
```c
/* ICP 算法核心 */

typedef struct {
    float R[3][3];
    float t[3];
    float error;
    int iterations;
} ICP_Result;

void icp(PointCloud *source, PointCloud *target, 
         ICP_Result *result, int max_iter, float tolerance) {
    float R_total[3][3] = {{1,0,0},{0,1,0},{0,0,1}};
    float t_total[3] = {0, 0, 0};
    
    // 构建 KD 树加速最近邻搜索
    KDTree *tree = kdtree_build(target);
    
    for (int iter = 0; iter < max_iter; iter++) {
        // 1. 找最近点对
        float P_matched[MAX_POINTS][3];
        float Q_matched[MAX_POINTS][3];
        int n_matched = 0;
        
        for (int i = 0; i < source->count; i++) {
            float p[3] = {
                source->points[i].x,
                source->points[i].y,
                source->points[i].z
            };
            
            // 应用当前变换
            float p_trans[3];
            transform_point(R_total, t_total, p, p_trans);
            
            // KD 树最近邻搜索
            int nearest = kdtree_nearest(tree, p_trans);
            float dist = distance(p_trans, target->points[nearest]);
            
            // 距离阈值过滤
            if (dist < 0.5f) {  // 50cm 阈值
                P_matched[n_matched][0] = p_trans[0];
                P_matched[n_matched][1] = p_trans[1];
                P_matched[n_matched][2] = p_trans[2];
                Q_matched[n_matched][0] = target->points[nearest].x;
                Q_matched[n_matched][1] = target->points[nearest].y;
                Q_matched[n_matched][2] = target->points[nearest].z;
                n_matched++;
            }
        }
        
        // 2. 计算质心
        float p_mean[3] = {0}, q_mean[3] = {0};
        for (int i = 0; i < n_matched; i++) {
            for (int j = 0; j < 3; j++) {
                p_mean[j] += P_matched[i][j];
                q_mean[j] += Q_matched[i][j];
            }
        }
        for (int j = 0; j < 3; j++) {
            p_mean[j] /= n_matched;
            q_mean[j] /= n_matched;
        }
        
        // 3. 构造协方差矩阵 H
        float H[3][3] = {0};
        for (int i = 0; i < n_matched; i++) {
            float p_d[3], q_d[3];
            for (int j = 0; j < 3; j++) {
                p_d[j] = P_matched[i][j] - p_mean[j];
                q_d[j] = Q_matched[i][j] - q_mean[j];
            }
            // H += p_d · q_d^T
            for (int r = 0; r < 3; r++)
                for (int c = 0; c < 3; c++)
                    H[r][c] += p_d[r] * q_d[c];
        }
        
        // 4. SVD 分解
        float U[3][3], S[3], V[3][3];
        svd_3x3(H, U, S, V);
        
        // 5. 计算 R, t
        float R_iter[3][3], t_iter[3];
        // R = V · U^T
        multiply_transpose(V, U, R_iter);
        // t = q̄ - R · p̄
        multiply(R_iter, p_mean, t_iter);
        for (int j = 0; j < 3; j++) t_iter[j] = q_mean[j] - t_iter[j];
        
        // 6. 更新总变换
        float R_new[3][3], t_new[3];
        multiply(R_iter, R_total, R_new);
        multiply(R_iter, t_total, t_new);
        for (int j = 0; j < 3; j++) t_new[j] += t_iter[j];
        memcpy(R_total, R_new, sizeof(R_new));
        memcpy(t_total, t_new, sizeof(t_new));
        
        // 7. 计算误差
        float error = 0;
        for (int i = 0; i < n_matched; i++) {
            float p_trans[3];
            transform_point(R_total, t_total, source->points[i], p_trans);
            float d = distance(p_trans, Q_matched[i]);
            error += d * d;
        }
        error /= n_matched;
        
        // 8. 收敛检查
        if (fabsf(error - result->error) < tolerance) {
            break;
        }
        result->error = error;
    }
    
    memcpy(result->R, R_total, sizeof(R_total));
    memcpy(result->t, t_total, sizeof(t_total));
    kdtree_destroy(tree);
}
```

### 2. NDT (Normal Distributions Transform)

### 原理
```
NDT 将目标点云分成体素 (3D 网格)

每个体素内:
  1. 计算均值: μ = mean(points)
  2. 计算协方差: Σ = (1/N)·Σ(p-μ)·(p-μ)^T
  3. 建立正态分布: p(x) = exp(-0.5·(x-μ)^T·Σ^(-1)·(x-μ)) / Z

匹配:
  对源点云每个点, 计算其在 NDT 中的概率
  最大化总概率 = 最小化负对数似然

优化: Gauss-Newton 或 Levenberg-Marquardt

NDT vs ICP:
├── ICP: 需要最近邻搜索, 慢
├── NDT: 概率模型, 不需要点对匹配, 快
├── ICP: 对初始值敏感
└── NDT: 更鲁棒, 收敛域更大
```

### 3. LOAM (LiDAR Odometry and Mapping)

### 特征提取
```
特征点类型:
├── 边缘点 (Edge): 曲率大的点
└── 平面点 (Planar): 曲率小的点

曲率计算:
  c = (1/|S|) · Σ ||p_j - p_i||²

  S = 同一扫描线上点 i 附近的点集

选取规则:
  边缘点: 曲率最大的前 N_e 个点
  平面点: 曲率最小的前 N_p 个点
  排除: 平行于扫描方向的点 (遮挡)
```

### 帧间匹配
```
边缘点匹配:
  找目标点云中最近的边缘线 (2 个点)
  点到线距离: d = |(p - p1) × (p - p2)| / |p1 - p2|

平面点匹配:
  找目标点云中最近的平面 (3 个点)
  点到面距离: d = (p - p1) · n / |n|
  n = (p2 - p1) × (p3 - p1)

优化:
  最小化所有特征点的匹配距离
  求解 6DoF 变换 (x, y, z, roll, pitch, yaw)
```

---

### 相关链接

- [[lidar-system|激光雷达]] — 传感器
- [[visual-slam|视觉 SLAM]] — 视觉方案
- [[imu-system|IMU]] — 惯性导航
- [[robot-vacuum|扫地机器人]] — 应用

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

**下一步**：建议学习 [[lidar/advanced/|高级内容]]
