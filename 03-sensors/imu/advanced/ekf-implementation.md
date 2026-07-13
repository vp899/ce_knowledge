---
title: "IMU 高级 - EKF 完整实现"
tags: [imu, advanced, ekf, kalman, state-estimation]
level: advanced
---

# IMU 高级 - EKF 完整实现

## 概述

生产级 IMU 需要精确状态估计。本文涵盖 15 维 EKF、振动抑制和多传感器融合。

完成本文学习后，你将能够：

- 能够设计 15 维 EKF 状态估计器
- 掌握多传感器融合和零偏估计
- 能够进行实时性优化和抗振设计

## 背景知识

### 相关概念

### 前置知识

- 完成中级内容的学习
- 有实际项目开发经验
- 熟悉系统级设计方法

### 学习建议

- 结合实际项目需求学习
- 关注生产级的可靠性设计
- 阅读开源项目源码

## 核心内容

### 1. 状态空间模型

### 15 维状态向量
```
x = [q0, q1, q2, q3, bgx, bgy, bgz, bax, bay, baz]
     └──四元数──┘   └──陀螺零偏──┘   └──加速度零偏──┘

物理含义:
├── q0-q3: 描述姿态 (4 维, 3 自由度)
├── bgx-bgy-bgz: 陀螺仪零偏 (估计后补偿)
└── bax-bay-baz: 加速度计零偏 (估计后补偿)
```

### 状态转移方程
```
预测模型 (IMU 驱动):

  q(k+1) = q(k) + 0.5·q(k)⊗(ω_m - b_g)·dt
  b_g(k+1) = b_g(k)     (随机游走)
  b_a(k+1) = b_a(k)     (随机游走)

其中:
  ω_m = 陀螺仪测量值
  b_g = 陀螺零偏估计
  ⊗ = 四元数乘法
```

### 雅可比矩阵
```c
// 计算状态转移雅可比 F (15×15)
void compute_F(float *x, float *gyro, float dt, float F[15][15]) {
    float q0=x[0], q1=x[1], q2=x[2], q3=x[3];
    float bgx=x[4], bgy=x[5], bgz=x[6];
    
    // 修正后的角速度
    float wx = gyro[0]-bgx, wy = gyro[1]-bgy, wz = gyro[2]-bgz;
    float h = 0.5f*dt;
    
    // 初始化为单位矩阵
    memset(F, 0, sizeof(float)*15*15);
    for(int i=0; i<15; i++) F[i][i] = 1.0f;
    
    // ∂q/∂q (四元数对自身的偏导)
    F[0][0] = 1;           F[0][1] = -h*wx;      F[0][2] = -h*wy;      F[0][3] = -h*wz;
    F[1][0] = h*wx;        F[1][1] = 1;           F[1][2] = h*wz;       F[1][3] = -h*wy;
    F[2][0] = h*wy;        F[2][1] = -h*wz;       F[2][2] = 1;          F[2][3] = h*wx;
    F[3][0] = h*wz;        F[3][1] = h*wy;        F[3][2] = -h*wx;      F[3][3] = 1;
    
    // ∂q/∂bg (四元数对陀螺零偏的偏导)
    F[0][4] = h*q1;        F[0][5] = h*q2;        F[0][6] = h*q3;
    F[1][4] = -h*q0;       F[1][5] = h*q3;        F[1][6] = -h*q2;
    F[2][4] = -h*q3;       F[2][5] = -h*q0;       F[2][6] = h*q1;
    F[3][4] = h*q2;        F[3][5] = -h*q1;       F[3][6] = -h*q0;
}

// 计算过程噪声协方差 Q
void compute_Q(float *x, float dt, float Q[15][15]) {
    float gyro_noise = 0.01f;   // rad/s/√Hz
    float accel_noise = 0.1f;   // m/s²/√Hz
    float gyro_bias_noise = 1e-6f;
    float accel_bias_noise = 1e-6f;
    
    memset(Q, 0, sizeof(float)*15*15);
    
    // 四元数噪声 (从陀螺噪声传播)
    float q_noise = gyro_noise * dt;
    Q[0][0] = Q[1][1] = Q[2][2] = Q[3][3] = q_noise*q_noise;
    
    // 零偏噪声 (随机游走)
    Q[4][4] = Q[5][5] = Q[6][6] = gyro_bias_noise*gyro_bias_noise*dt;
    Q[7][7] = Q[8][8] = Q[9][9] = accel_bias_noise*accel_bias_noise*dt;
}
```

### 2. EKF 完整实现

```c
// EKF 主循环
void ekf_predict(float *x, float P[15][15],
                  float *gyro, float *accel, float dt) {
    float F[15][15], Q[15][15];
    
    // 1. 状态预测
    float q0=x[0], q1=x[1], q2=x[2], q3=x[3];
    float wx = gyro[0]-x[4], wy = gyro[1]-x[5], wz = gyro[2]-x[6];
    float h = 0.5f*dt;
    
    x[0] = q0 + (-q1*wx-q2*wy-q3*wz)*h;
    x[1] = q1 + ( q0*wx+q2*wz-q3*wy)*h;
    x[2] = q2 + ( q0*wy-q1*wz+q3*wx)*h;
    x[3] = q3 + ( q0*wz+q1*wy-q2*wx)*h;
    // 零偏不变
    
    // 归一化四元数
    float norm = sqrtf(x[0]*x[0]+x[1]*x[1]+x[2]*x[2]+x[3]*x[3]);
    x[0]/=norm; x[1]/=norm; x[2]/=norm; x[3]/=norm;
    
    // 2. 计算雅可比
    compute_F(x, gyro, dt, F);
    compute_Q(x, dt, Q);
    
    // 3. 协方差预测: P = F·P·F^T + Q
    float FP[15][15], FPFt[15][15];
    mat_mul(F, P, FP, 15, 15, 15);
    mat_mul_transpose(FP, F, FPFt, 15, 15, 15);
    mat_add(FPFt, Q, P, 15, 15);
}

void ekf_update_accel(float *x, float P[15][15],
                       float *accel) {
    // 观测: 加速度计测量值
    // 预测: 重力在机体坐标系的投影
    
    float q0=x[0], q1=x[1], q2=x[2], q3=x[3];
    
    // 预测加速度
    float pred[3];
    pred[0] = 2*(q1*q3-q0*q2);
    pred[1] = 2*(q0*q1+q2*q3);
    pred[2] = q0*q0-q1*q1-q2*q2+q3*q3;
    
    // 新息
    float y[3] = {accel[0]-pred[0], accel[1]-pred[1], accel[2]-pred[2]};
    
    // 观测雅可比 H (3×15)
    float H[3][15] = {0};
    H[0][0]=-2*q2; H[0][1]=2*q3;  H[0][2]=-2*q0; H[0][3]=2*q1;
    H[1][0]=2*q1;  H[1][1]=2*q0;  H[1][2]=2*q3;  H[1][3]=2*q2;
    H[2][0]=2*q0;  H[2][1]=-2*q1; H[2][2]=-2*q2; H[2][3]=2*q3;
    
    // 观测噪声
    float R[3][3] = {0};
    float accel_noise = 0.5f;
    R[0][0]=R[1][1]=R[2][2] = accel_noise*accel_noise;
    
    // 卡尔曼增益: K = P·H^T·(H·P·H^T + R)^(-1)
    // ... (矩阵运算省略, 实际使用 CMSIS-DSP 或自定义矩阵库)
    
    // 状态更新: x = x + K·y
    // 协方差更新: P = (I - K·H)·P
}
```

### 3. 调参指南

### Q/R 矩阵调参
```
Q (过程噪声):
├── 陀螺噪声: 0.001~0.1 rad/s/√Hz
│   → 越大: 越信任加速度计, 响应快但噪声大
│   → 越小: 越信任陀螺仪, 平滑但响应慢
├── 零偏噪声: 1e-8~1e-4
│   → 越大: 零偏估计变化快
│   → 越小: 零偏估计稳定
└── 调参方法: 从大到小, 观察响应

R (观测噪声):
├── 加速度噪声: 0.1~10 m/s²
│   → 越大: 越不信任加速度计
│   → 越小: 越信任加速度计
└── 调参方法: 静态采集, 计算标准差

实际调参步骤:
1. 先设 Q=R=I
2. 增大 R → 姿态更平滑, 但响应慢
3. 减小 R → 响应快, 但振动大
4. 增大 Q 中零偏项 → 零偏收敛快
5. 反复微调, 找到平衡点
```

### 4. 振动环境优化

### 陷波滤波器
```c
// 级联陷波滤波器 (消除多个振动频率)
typedef struct {
    float b0, b1, b2, a1, a2;
    float x1, x2, y1, y2;
} NotchFilter;

float notch_filter(NotchFilter *f, float x) {
    float y = f->b0*x + f->b1*f->x1 + f->b2*f->x2
              - f->a1*f->y1 - f->a2*f->y2;
    f->x2=f->x1; f->x1=x;
    f->y2=f->y1; f->y1=y;
    return y;
}

// 无人机典型配置: 3 级陷波
// 1P 电机频率 (如 120Hz)
// 2P 倍频 (如 240Hz)
// 桨叶频率 (如 480Hz)
```

### 自适应增益
```c
// 根据加速度大小自适应调整 EKF 增益
float adaptive_gain(float *accel) {
    float norm = sqrtf(accel[0]*accel[0] + accel[1]*accel[1] + accel[2]*accel[2]);
    float error = fabsf(norm - 9.81f);
    
    // 加速度偏差大时, 降低对加速度计的信任
    if(error > 2.0f) return 0.1f;   // 高机动, 低信任
    if(error > 1.0f) return 0.5f;   // 中等机动
    return 1.0f;                     // 正常, 全信任
}

## 实践示例

### 示例代码

```c
// 示例代码 - 结合正文理解
```

**代码说明**：
- 详见正文

## 深入理解

### 原理分析

请参考核心内容部分的详细讲解。

### 最佳实践

1. 关注可靠性和可维护性
2. 建立自动化测试和 CI/CD
3. 文档先行，代码即文档

## 常见问题

### Q1: EKF 发散怎么办？

**A**: 检查 Q/R 矩阵是否合理，增大 R (更信任模型)；检查数值稳定性 (四元数归一化)；加入发散检测和重置机制。

### Q2: 如何处理高振动环境？

**A**: 使用陷波滤波器消除特定频率振动；降低加速度计权重 (增大 R)；使用软安装减少机械传递。

## 总结

本文涵盖了生产级的高级技术：

- 能够进行系统级架构设计
- 掌握了性能优化和可靠性设计
- 具备独立解决复杂工程问题的能力

建议结合实际项目进行综合实践。

## 延伸阅读

- [[MOC|知识地图]] - 返回总索引
- 相关模块文档 - 交叉参考
- 厂商数据手册 - 详细规格

## 参考资料

- 厂商数据手册和技术参考
- 开源项目文档和代码
- 学术论文和行业标准

---

**练习题**：

- 厂商数据手册和技术参考
- 开源项目文档和代码
- 学术论文和行业标准

**下一步**：建议学习 [[MOC|返回知识地图]]
