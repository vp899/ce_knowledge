level: beginner
---
title: "IMU 姿态融合算法详解"
tags: [imu, algorithm, complementary-filter, mahony, madgwick, ekf, kalman]
module: "03-sensors"
---

# IMU 姿态融合算法详解

## 概述

IMU 姿态融合算法是嵌入式状态估计核心。本文涵盖互补滤波、Mahony AHRS、EKF 完整推导和实现代码，以及振动抑制和校准方法。

完成本文学习后，你将能够：

- 掌握本模块的核心概念和原理
- 理解关键技术的实现方法
- 能够应用到实际项目中

## 背景知识

### 相关概念

### 前置知识

- C 语言基础
- 嵌入式开发基础
- 相关模块的初级知识

### 学习建议

- 准备开发板进行动手实践
- 边学边做，不要只看不练
- 遇到问题先自己思考再查资料

## 核心内容

### 1. 姿态表示方法

### 欧拉角 (Euler Angles)
```
定义: 绕三个轴的旋转角度
├── Roll  (φ): 绕 X 轴旋转 (横滚)
├── Pitch (θ): 绕 Y 轴旋转 (俯仰)
└── Yaw   (ψ): 绕 Z 轴旋转 (偏航)

旋转顺序 (ZYX, 航空 convention):
  Z(Yaw) → Y(Pitch) → X(Roll)

万向锁问题 (Gimbal Lock):
  当 Pitch = ±90° 时, Roll 和 Yaw 退化为同一轴
  → 欧拉角不适合全姿态表示
```

### 旋转矩阵 (Rotation Matrix)
```
R = Rz(ψ) · Ry(θ) · Rx(φ)

R = [cosψcosθ  cosψsinθsinφ-sinψcosφ  cosψsinθcosφ+sinψsinφ]
    [sinψcosθ  sinψsinθsinφ+cosψcosφ  sinψsinθcosφ-cosψsinφ]
    [-sinθ     cosθsinφ                cosθcosφ              ]

性质: R^T = R^(-1), det(R) = 1
优点: 无万向锁, 旋转合成简单
缺点: 9 个参数, 6 个约束, 冗余
```

### 四元数 (Quaternion)
```
定义: q = q0 + q1·i + q2·j + q3·k
  其中 i² = j² = k² = ijk = -1

表示旋转: q = [cos(θ/2), sin(θ/2)·n]
  n = 旋转轴单位向量
  θ = 旋转角度

归一化约束: |q| = q0² + q1² + q2² + q3² = 1

四元数乘法 (Hamilton product):
  q1⊗q2 = [a1a2 - b1b2 - c1c2 - d1d2,
           a1b2 + b1a2 + c1d2 - d1c2,
           a1c2 - b1d2 + c1a2 + d1b2,
           a1d2 + b1c2 - c1b2 + d1a2]

旋转一个向量 v:
  v' = q ⊗ [0, v] ⊗ q*

四元数→旋转矩阵:
  R = [1-2(q2²+q3²)  2(q1q2-q0q3)  2(q1q3+q0q2)]
      [2(q1q2+q0q3)  1-2(q1²+q3²)  2(q2q3-q0q1)]
      [2(q1q3-q0q2)  2(q2q3+q0q1)  1-2(q1²+q2²)]

四元数→欧拉角:
  Roll  = atan2(2(q0q1+q2q3), 1-2(q1²+q2²))
  Pitch = asin(2(q0q2-q3q1))
  Yaw   = atan2(2(q0q3+q1q2), 1-2(q2²+q3²))
```

### 四元数微分方程
```
dq/dt = 0.5 · q ⊗ ω

展开:
  dq0/dt = 0.5·(-q1·ωx - q2·ωy - q3·ωz)
  dq1/dt = 0.5·( q0·ωx + q2·ωz - q3·ωy)
  dq2/dt = 0.5·( q0·ωy - q1·ωz + q3·ωx)
  dq3/dt = 0.5·( q0·ωz + q1·ωy - q2·ωx)

离散化 (一阶欧拉):
  q(t+dt) = q(t) + dq/dt · dt
  然后归一化: q = q / |q|
```

### 2. 互补滤波器 (Complementary Filter)

### 原理
```
核心思想:
  陀螺仪: 短时准确, 长时漂移 (高通特性)
  加速度计: 长时准确, 短时噪声 (低通特性)
  → 互补融合: 高频用陀螺, 低频用加速度

传递函数:
  θ = α · (θ + ω·dt) + (1-α) · θ_accel
      └─── 陀螺积分 ───┘   └── 加速度 ─┘

  α = τ / (τ + dt)
  τ = 时间常数 (如 0.5-2 秒)
  dt = 采样周期

频率特性:
  截止频率 fc = 1 / (2π·τ)
  陀螺仪: 通过 fc 以上 (高频)
  加速度计: 通过 fc 以下 (低频)
```

### 完整实现
```c
/* complementary_filter.c - 完整互补滤波器 */

#include <math.h>

typedef struct {
    float q[4];           // 四元数 [q0, q1, q2, q3]
    float alpha;          // 融合系数
    float kp;             // 加速度修正增益
    float ki;             // 积分增益
    float integral[3];    // 积分项
    float dt;             // 采样周期
} ComplementaryFilter;

void comp_init(ComplementaryFilter *cf, float tau, float dt) {
    cf->q[0] = 1.0f; cf->q[1] = 0; cf->q[2] = 0; cf->q[3] = 0;
    cf->alpha = tau / (tau + dt);
    cf->kp = 0.5f;      // 比例增益 (调节收敛速度)
    cf->ki = 0.01f;     // 积分增益 (消除稳态误差)
    cf->dt = dt;
    cf->integral[0] = cf->integral[1] = cf->integral[2] = 0;
}

void comp_update(ComplementaryFilter *cf,
                  float gx, float gy, float gz,    // 陀螺 (rad/s)
                  float ax, float ay, float az) {   // 加速度 (m/s²)
    float q0 = cf->q[0], q1 = cf->q[1], q2 = cf->q[2], q3 = cf->q[3];
    
    // ===== 步骤 1: 加速度计归一化 =====
    float norm = sqrtf(ax*ax + ay*ay + az*az);
    if (norm < 0.001f) return;  // 避免除零
    ax /= norm; ay /= norm; az /= norm;
    
    // ===== 步骤 2: 估计重力方向 (当前姿态下) =====
    // 从四元数计算重力在机体坐标系的投影
    float vx = 2*(q1*q3 - q0*q2);
    float vy = 2*(q0*q1 + q2*q3);
    float vz = q0*q0 - q1*q1 - q2*q2 + q3*q3;
    
    // ===== 步骤 3: 计算误差 (叉积) =====
    // 加速度计测量值与估计值的叉积 = 误差向量
    float ex = ay*vz - az*vy;
    float ey = az*vx - ax*vz;
    float ez = ax*vy - ay*vx;
    
    // ===== 步骤 4: PI 修正 =====
    // 比例项: 直接修正
    float gx_corrected = gx + cf->kp * ex;
    float gy_corrected = gy + cf->kp * ey;
    float gz_corrected = gz + cf->kp * ez;
    
    // 积分项: 消除稳态偏差 (如陀螺零偏)
    if (cf->ki > 0) {
        cf->integral[0] += cf->ki * ex * cf->dt;
        cf->integral[1] += cf->ki * ey * cf->dt;
        cf->integral[2] += cf->ki * ez * cf->dt;
        gx_corrected += cf->integral[0];
        gy_corrected += cf->integral[1];
        gz_corrected += cf->integral[2];
    }
    
    // ===== 步骤 5: 四元数积分 =====
    float half_dt = 0.5f * cf->dt;
    q0 += (-q1*gx_corrected - q2*gy_corrected - q3*gz_corrected) * half_dt;
    q1 += ( q0*gx_corrected + q2*gz_corrected - q3*gy_corrected) * half_dt;
    q2 += ( q0*gy_corrected - q1*gz_corrected + q3*gx_corrected) * half_dt;
    q3 += ( q0*gz_corrected + q1*gy_corrected - q2*gx_corrected) * half_dt;
    
    // ===== 步骤 6: 归一化 =====
    norm = sqrtf(q0*q0 + q1*q1 + q2*q2 + q3*q3);
    cf->q[0] = q0/norm; cf->q[1] = q1/norm;
    cf->q[2] = q2/norm; cf->q[3] = q3/norm;
}

void comp_get_euler(ComplementaryFilter *cf,
                     float *roll, float *pitch, float *yaw) {
    float q0 = cf->q[0], q1 = cf->q[1], q2 = cf->q[2], q3 = cf->q[3];
    *roll  = atan2f(2*(q0*q1 + q2*q3), 1 - 2*(q1*q1 + q2*q2));
    *pitch = asinf(2*(q0*q2 - q3*q1));
    *yaw   = atan2f(2*(q0*q3 + q1*q2), 1 - 2*(q2*q2 + q3*q3));
}
```

### 3. Mahony 滤波器 (AHRS)

### 原理详解
```
Mahony vs 互补滤波:
├── 互补滤波: 简单, 只用加速度修正
├── Mahony: 完整 AHRS, 支持磁力计, 可调 PI 增益
└── 适合: 无人机/机器人姿态估计

核心思想:
  1. 用陀螺仪积分得到姿态预测
  2. 用加速度计/磁力计计算观测姿态
  3. 计算预测与观测的误差 (叉积)
  4. PI 控制器修正陀螺仪输出
  5. 用修正后的陀螺积分四元数

误差来源:
  ex = accel_measured × gravity_estimated
  → 当重力方向一致时, ex = 0
  → 当有偏差时, ex 指向修正方向

磁力计修正:
  1. 将磁力计数据转换到水平面
  2. 计算磁北方向
  3. 与期望磁北比较
  4. 只修正 Yaw 轴 (不影响 Roll/Pitch)
```

### 完整实现 (含磁力计)
```c
/* mahony_ahrs.c - 完整 Mahony AHRS */

typedef struct {
    float q[4];
    float kp, ki;
    float integral_fb[3];
    float dt;
    float two_kp;
    float two_ki;
} MahonyAHRS;

void mahony_init(MahonyAHRS *ahrs, float kp, float ki, float dt) {
    ahrs->q[0] = 1; ahrs->q[1] = 0; ahrs->q[2] = 0; ahrs->q[3] = 0;
    ahrs->kp = kp; ahrs->ki = ki;
    ahrs->two_kp = 2.0f * kp;
    ahrs->two_ki = 2.0f * ki;
    ahrs->dt = dt;
    memset(ahrs->integral_fb, 0, sizeof(ahrs->integral_fb));
}

void mahony_update(MahonyAHRS *ahrs,
                    float gx, float gy, float gz,     // 陀螺 rad/s
                    float ax, float ay, float az,      // 加速度 (任意单位)
                    float mx, float my, float mz) {    // 磁力计 (任意单位)
    float q0 = ahrs->q[0], q1 = ahrs->q[1], q2 = ahrs->q[2], q3 = ahrs->q[3];
    float recip_norm;
    float q0q0 = q0*q0, q0q1 = q0*q1, q0q2 = q0*q2, q0q3 = q0*q3;
    float q1q1 = q1*q1, q1q2 = q1*q2, q1q3 = q1*q3;
    float q2q2 = q2*q2, q2q3 = q2*q3;
    float q3q3 = q3*q3;
    
    float hx, hy, bx, bz;
    float half_vx, half_vy, half_vz;
    float half_wx, half_wy, half_wz;
    float half_ex = 0, half_ey = 0, half_ez = 0;
    
    // ===== 加速度计修正 =====
    if (!((ax == 0) && (ay == 0) && (az == 0))) {
        recip_norm = 1.0f / sqrtf(ax*ax + ay*ay + az*az);
        ax *= recip_norm; ay *= recip_norm; az *= recip_norm;
        
        // 估计重力方向
        half_vx = q1q3 - q0q2;
        half_vy = q0q1 + q2q3;
        half_vz = q0q0 - 0.5f + q3q3;
        
        // 误差 = 测量 × 估计
        half_ex += (ay * half_vz - az * half_vy);
        half_ey += (az * half_vx - ax * half_vz);
        half_ez += (ax * half_vy - ay * half_vx);
    }
    
    // ===== 磁力计修正 =====
    if (!((mx == 0) && (my == 0) && (mz == 0))) {
        recip_norm = 1.0f / sqrtf(mx*mx + my*my + mz*mz);
        mx *= recip_norm; my *= recip_norm; mz *= recip_norm;
        
        // 地磁方向在机体坐标系的投影
        hx = 2*(mx*(0.5f - q2q2 - q3q3) + my*(q1q2 - q0q3) + mz*(q1q3 + q0q2));
        hy = 2*(mx*(q1q2 + q0q3) + my*(0.5f - q1q1 - q3q3) + mz*(q2q3 - q0q1));
        bx = sqrtf(hx*hx + hy*hy);
        bz = 2*(mx*(q1q3 - q0q2) + my*(q2q3 + q0q1) + mz*(0.5f - q1q1 - q2q2));
        
        // 估计地磁方向
        half_wx = bx*(0.5f - q2q2 - q3q3) + bz*(q1q3 - q0q2);
        half_wy = bx*(q1q2 - q0q3) + bz*(q0q1 + q2q3);
        half_wz = bx*(q0q2 + q1q3) + bz*(0.5f - q1q1 - q2q2);
        
        // 误差
        half_ex += (my * half_wz - mz * half_wy);
        half_ey += (mz * half_wx - mx * half_wz);
        half_ez += (mx * half_wy - my * half_wx);
    }
    
    // ===== PI 修正 =====
    if (ahrs->two_ki > 0) {
        ahrs->integral_fb[0] += ahrs->two_ki * half_ex * ahrs->dt;
        ahrs->integral_fb[1] += ahrs->two_ki * half_ey * ahrs->dt;
        ahrs->integral_fb[2] += ahrs->two_ki * half_ez * ahrs->dt;
        gx += ahrs->integral_fb[0];
        gy += ahrs->integral_fb[1];
        gz += ahrs->integral_fb[2];
    } else {
        ahrs->integral_fb[0] = 0;
        ahrs->integral_fb[1] = 0;
        ahrs->integral_fb[2] = 0;
    }
    
    gx += ahrs->two_kp * half_ex;
    gy += ahrs->two_kp * half_ey;
    gz += ahrs->two_kp * half_ez;
    
    // ===== 四元数积分 =====
    gx *= 0.5f * ahrs->dt;
    gy *= 0.5f * ahrs->dt;
    gz *= 0.5f * ahrs->dt;
    
    float qa = q0, qb = q1, qc = q2;
    q0 += (-qb*gx - qc*gy - q3*gz);
    q1 += ( qa*gx + qc*gz - q3*gy);
    q2 += ( qa*gy - qb*gz + q3*gx);
    q3 += ( qa*gz + qb*gy - qc*gx);
    
    // 归一化
    recip_norm = 1.0f / sqrtf(q0*q0 + q1*q1 + q2*q2 + q3*q3);
    ahrs->q[0] = q0 * recip_norm;
    ahrs->q[1] = q1 * recip_norm;
    ahrs->q[2] = q2 * recip_norm;
    ahrs->q[3] = q3 * recip_norm;
}
```

### 4. 扩展卡尔曼滤波 (EKF)

### 状态空间模型
```
状态向量 (15 维):
  x = [q0, q1, q2, q3, bgx, bgy, bgz, bax, bay, baz, bmx, bmy, bmz]
       └─四元数─┘  └──陀螺零偏──┘  └─加速度零偏─┘  └─磁力计零偏─┘

状态转移方程 (预测):
  q(k+1) = q(k) + 0.5·q(k)⊗(ω_m - b_g)·dt
  b_g(k+1) = b_g(k)           (零偏建模为随机游走)
  b_a(k+1) = b_a(k)
  b_m(k+1) = b_m(k)

雅可比矩阵 F (状态转移):
  F = ∂f/∂x, 在当前状态线性化

观测方程:
  加速度计: h_a = R^T · [0, 0, g]^T + b_a + v_a
  磁力计:   h_m = R^T · [mN, 0, mD]^T + b_m + v_m

雅可比矩阵 H (观测):
  H = ∂h/∂x
```

### EKF 完整实现
```c
/* ekf_ahrs.c - 15 维 EKF AHRS */

#define STATE_DIM 15
#define MEAS_DIM  6    // 加速度3 + 磁力计3

typedef struct {
    float x[STATE_DIM];              // 状态向量
    float P[STATE_DIM][STATE_DIM];   // 协方差矩阵
    float Q[STATE_DIM][STATE_DIM];   // 过程噪声
    float R[MEAS_DIM][MEAS_DIM];     // 观测噪声
    float dt;
} EKF_AHRS;

/* 状态转移函数 */
void ekf_predict(EKF_AHRS *ekf, float gx, float gy, float gz) {
    float *x = ekf->x;
    float dt = ekf->dt;
    
    // 提取当前状态
    float q0 = x[0], q1 = x[1], q2 = x[2], q3 = x[3];
    float bgx = x[4], bgy = x[5], bgz = x[6];
    
    // 陀螺减去零偏
    float wx = gx - bgx, wy = gy - bgy, wz = gz - bgz;
    
    // 四元数积分
    x[0] = q0 + 0.5f*(-q1*wx - q2*wy - q3*wz)*dt;
    x[1] = q1 + 0.5f*( q0*wx + q2*wz - q3*wy)*dt;
    x[2] = q2 + 0.5f*( q0*wy - q1*wz + q3*wx)*dt;
    x[3] = q3 + 0.5f*( q0*wz + q1*wy - q2*wx)*dt;
    
    // 归一化
    float norm = sqrtf(x[0]*x[0]+x[1]*x[1]+x[2]*x[2]+x[3]*x[3]);
    x[0]/=norm; x[1]/=norm; x[2]/=norm; x[3]/=norm;
    
    // 零偏不变 (随机游走)
    // x[4..14] 保持不变
    
    // 更新协方差: P = F·P·F^T + Q
    // (简化: 使用一阶近似)
    // 实际实现需要计算完整的雅可比矩阵 F
    // ... (矩阵运算省略)
    
    // 加入过程噪声
    for (int i = 0; i < STATE_DIM; i++) {
        ekf->P[i][i] += ekf->Q[i][i] * dt;
    }
}

/* 观测更新 */
void ekf_update_accel_mag(EKF_AHRS *ekf,
                            float ax, float ay, float az,
                            float mx, float my, float mz) {
    float *x = ekf->x;
    float q0 = x[0], q1 = x[1], q2 = x[2], q3 = x[3];
    
    // 预测加速度 (重力在机体坐标系)
    float pred_ax = 2*(q1*q3 - q0*q2);
    float pred_ay = 2*(q0*q1 + q2*q3);
    float pred_az = q0*q0 - q1*q1 - q2*q2 + q3*q3;
    
    // 预测磁力计
    // (需要知道当地地磁方向)
    float mN = 0.3f, mD = 0.5f;  // 当地地磁水平/垂直分量
    float pred_mx = mN*(q0*q0+q1*q1-q2*q2-q3*q3) + 2*mD*(q1*q3-q0*q2);
    float pred_my = 2*mN*(q1*q2+q0*q3) + 2*mD*(q0*q1+q2*q3);
    float pred_mz = 2*mN*(q1*q3-q0*q2) + mD*(q0*q0-q1*q1+q2*q2-q3*q3);
    
    // 计算新息 (innovation)
    float y[MEAS_DIM] = {
        ax - pred_ax, ay - pred_ay, az - pred_az,
        mx - pred_mx, my - pred_my, mz - pred_mz
    };
    
    // 计算卡尔曼增益: K = P·H^T·(H·P·H^T + R)^(-1)
    // (需要计算雅可比 H, 这里省略矩阵运算)
    
    // 状态更新: x = x + K·y
    // 协方差更新: P = (I - K·H)·P
    // (完整实现需要矩阵库如 CMSIS-DSP 或自定义矩阵运算)
}

/* 雅可比矩阵计算 (部分) */
void compute_H_accel(float *x, float H[3][STATE_DIM]) {
    float q0 = x[0], q1 = x[1], q2 = x[2], q3 = x[3];
    
    // ∂h_a/∂q
    H[0][0] = -2*q2;  H[0][1] = 2*q3;   H[0][2] = -2*q0;  H[0][3] = 2*q1;
    H[1][0] = 2*q1;   H[1][1] = 2*q0;   H[1][2] = 2*q3;   H[1][3] = 2*q2;
    H[2][0] = 2*q0;   H[2][1] = -2*q1;  H[2][2] = -2*q2;  H[2][3] = 2*q3;
    
    // ∂h_a/∂b_a = I
    H[0][7] = 1; H[1][8] = 1; H[2][9] = 1;
    
    // 其余为 0
    for (int i = 0; i < 3; i++)
        for (int j = 4; j < 7; j++)
            H[i][j] = 0;
}
```

### 5. 振动抑制算法

### 陷波滤波器 (Notch Filter)
```c
/* 二阶 IIR 陷波滤波器 */
typedef struct {
    float b0, b1, b2;
    float a1, a2;
    float x1, x2, y1, y2;
} NotchFilter;

void notch_init(NotchFilter *nf, float freq, float Q, float fs) {
    float w0 = 2.0f * M_PI * freq / fs;
    float alpha = sinf(w0) / (2.0f * Q);
    float cosw0 = cosf(w0);
    
    float a0 = 1.0f + alpha;
    nf->b0 = 1.0f / a0;
    nf->b1 = -2.0f * cosw0 / a0;
    nf->b2 = 1.0f / a0;
    nf->a1 = -2.0f * cosw0 / a0;
    nf->a2 = (1.0f - alpha) / a0;
    nf->x1 = nf->x2 = nf->y1 = nf->y2 = 0;
}

float notch_filter(NotchFilter *nf, float input) {
    float output = nf->b0*input + nf->b1*nf->x1 + nf->b2*nf->x2
                   - nf->a1*nf->y1 - nf->a2*nf->y2;
    nf->x2 = nf->x1; nf->x1 = input;
    nf->y2 = nf->y1; nf->y1 = output;
    return output;
}
```

---

### 相关链接

- [[compass-system|指南针]] — 磁力计校准
- [[gps-system|GPS]] — GPS/INS 组合导航
- [[flight-controller-firmware|飞控]] — 姿态控制
- [[gimbal-control|云台]] — 云台增稳

## 实践示例

### 示例代码

```c
// 示例代码 - 结合正文理解
```

**代码说明**：
- 详见正文

## 深入理解

### 原理分析

深入理解底层原理有助于写出更高质量的代码。建议结合数据手册和源码进行学习。

### 最佳实践

1. 遵循代码规范，保持良好的注释习惯
2. 充分测试，覆盖边界条件
3. 持续重构，保持代码简洁

## 常见问题

### Q1: 学习本模块需要什么基础？

**A**: 需要 C 语言基础和基本的嵌入式开发知识。建议先完成前置模块的学习。

### Q2: 如何验证学习效果？

**A**: 通过动手实践验证：完成练习题、在开发板上运行示例代码、独立完成一个小项目。

## 总结

本文涵盖了本级别的核心知识：

- 理解了基本概念和工作原理
- 掌握了关键技术和实现方法
- 通过实践加深了理解

建议继续学习更高级别的内容。

## 延伸阅读

- [[MOC|知识地图]] - 返回总索引
- 相关模块文档 - 交叉参考
- 厂商数据手册 - 详细规格

## 参考资料

1. 厂商数据手册和技术参考
2. 开源项目文档和代码
3. 学术论文和行业标准

---

**练习题**：

1. 厂商数据手册和技术参考
2. 开源项目文档和代码
3. 学术论文和行业标准

**下一步**：建议学习 [[/intermediate/|中级内容]]
