---
title: "指南针校准算法详解"
tags: [compass, magnetometer, calibration, ellipsoid, hard-iron, soft-iron, algorithm]
module: "03-sensors"
---

# 指南针校准算法详解

## 1. 磁力计误差模型

### 误差来源
```
测量模型:
  m_meas = A · (m_true + b_hard) + b_soft + noise

  m_meas = 磁力计测量值
  m_true = 真实磁场
  A = 软磁矩阵 (3×3)
  b_hard = 硬磁偏移 (3×1)
  b_soft = 软磁偏移 (通常合并到 A)
  noise = 噪声

简化模型:
  m_meas = A · m_true + b

  A = 包含软磁和比例因子
  b = 硬磁偏移

无干扰时:
  |m_true| = 常数 (地球磁场强度)
  → 测量点在球面上

有硬磁干扰:
  |m_meas - b| = 常数
  → 测量点在偏移球面上

有软磁干扰:
  → 测量点在椭球面上
```

## 2. 椭球拟合校准

### 最小二乘椭球拟合
```c
/* 椭球拟合校准 */

// 椭球方程: ax² + by² + cz² + 2dxy + 2exz + 2fyz + 2gx + 2hy + 2kz = 1
// 矩阵形式: [x² y² z² 2xy 2xz 2yz 2x 2y 2z] · [a b c d e f g h k]^T = 1

typedef struct {
    float offset[3];       // 椭球中心 (硬磁偏移)
    float scale[3];        // 各轴比例因子
    float rotation[3][3];  // 旋转矩阵 (软磁)
} CompassCalibration;

int calibrate_compass_ellipsoid(float (*samples)[3], int n,
                                  CompassCalibration *cal) {
    // 构造最小二乘矩阵: D · v = e
    // D = [x² y² z² 2xy 2xz 2yz 2x 2y 2z]  (n×9)
    // e = [1 1 ... 1]^T  (n×1)
    
    double D[9][9] = {0};
    double d[9] = {0};
    
    for (int i = 0; i < n; i++) {
        double x = samples[i][0], y = samples[i][1], z = samples[i][2];
        double row[9] = {x*x, y*y, z*z, 2*x*y, 2*x*z, 2*y*z, 2*x, 2*y, 2*z};
        
        for (int j = 0; j < 9; j++) {
            for (int k = 0; k < 9; k++) {
                D[j][k] += row[j] * row[k];
            }
            d[j] += row[j];
        }
    }
    
    // 求解 D·v = d (Cholesky 分解或 LU 分解)
    double v[9];
    solve_linear(D, d, v, 9);
    
    // 从椭球参数提取校准矩阵
    // 椭球中心: offset = -A^(-1) · [g h k]^T
    // 其中 A = [a d e; d b f; e f c]
    
    double A[3][3] = {
        {v[0], v[3], v[4]},
        {v[3], v[1], v[5]},
        {v[4], v[5], v[2]}
    };
    double g_vec[3] = {v[6], v[7], v[8]};
    
    // 中心 = -A^(-1) · g
    double A_inv[3][3];
    matrix_inverse_3x3(A, A_inv);
    cal->offset[0] = -(A_inv[0][0]*g_vec[0] + A_inv[0][1]*g_vec[1] + A_inv[0][2]*g_vec[2]);
    cal->offset[1] = -(A_inv[1][0]*g_vec[0] + A_inv[1][1]*g_vec[1] + A_inv[1][2]*g_vec[2]);
    cal->offset[2] = -(A_inv[2][0]*g_vec[0] + A_inv[2][1]*g_vec[1] + A_inv[2][2]*g_vec[2]);
    
    // 特征值分解得到比例因子和旋转
    // A = R · diag(1/a², 1/b², 1/c²) · R^T
    eigen_decomposition_3x3(A, cal->scale, cal->rotation);
    
    // 归一化比例因子
    float avg_radius = (cal->scale[0] + cal->scale[1] + cal->scale[2]) / 3.0f;
    for (int i = 0; i < 3; i++) {
        cal->scale[i] = avg_radius / cal->scale[i];
    }
    
    return 0;
}

// 应用校准
void apply_compass_calibration(CompassCalibration *cal,
                                float raw[3], float corrected[3]) {
    // 1. 去除硬磁偏移
    float temp[3];
    temp[0] = raw[0] - cal->offset[0];
    temp[1] = raw[1] - cal->offset[1];
    temp[2] = raw[2] - cal->offset[2];
    
    // 2. 应用软磁校正 (旋转 + 缩放)
    corrected[0] = cal->rotation[0][0]*temp[0] + cal->rotation[0][1]*temp[1] + cal->rotation[0][2]*temp[2];
    corrected[1] = cal->rotation[1][0]*temp[0] + cal->rotation[1][1]*temp[1] + cal->rotation[1][2]*temp[2];
    corrected[2] = cal->rotation[2][0]*temp[0] + cal->rotation[2][1]*temp[1] + cal->rotation[2][2]*temp[2];
    
    // 3. 应用比例因子
    corrected[0] *= cal->scale[0];
    corrected[1] *= cal->scale[1];
    corrected[2] *= cal->scale[2];
}
```

## 3. 倾斜补偿航向解算

### 三维航向计算
```c
/* 倾斜补偿航向 */

float calculate_heading_tilt_compensated(
    float mx, float my, float mz,   // 磁力计 (已校准)
    float roll, float pitch) {        // 姿态角 (来自 IMU)
    
    float cos_roll = cosf(roll);
    float sin_roll = sinf(roll);
    float cos_pitch = cosf(pitch);
    float sin_pitch = sinf(pitch);
    
    // 将磁力计数据从机体坐标系转换到水平坐标系
    float mx_h = mx * cos_pitch + my * sin_roll * sin_pitch + mz * cos_roll * sin_pitch;
    float my_h = my * cos_roll - mz * sin_roll;
    
    // 计算磁航向
    float heading = atan2f(-my_h, mx_h);
    
    // 转换到 0-2π
    if (heading < 0) heading += 2 * M_PI;
    
    return heading;  // 弧度
}

// 真航向 = 磁航向 + 磁偏角
float magnetic_to_true_heading(float magnetic_heading, float declination) {
    float true_h = magnetic_heading + declination;
    if (true_h > 2*M_PI) true_h -= 2*M_PI;
    if (true_h < 0) true_h += 2*M_PI;
    return true_h;
}
```

---

## 相关链接

- [[imu-system|IMU]] — 姿态融合
- [[compass-system|指南针]] — 传感器选型
- [[flight-controller-firmware|飞控]] — 航向控制
