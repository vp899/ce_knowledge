# IMU（惯性测量单元）

## 1. IMU 传感器选型

### 常用 IMU 传感器对比

| 型号 | 厂商 | 类型 | 陀螺噪声 | 加速度噪声 | 采样率 | 接口 | 典型应用 |
|------|------|------|----------|-----------|--------|------|----------|
| MPU6050 | TDK | 6轴 | 0.005°/s/√Hz | 40μg/√Hz | 1kHz | I2C/SPI | 入门级 |
| MPU6500 | TDK | 6轴 | 0.005°/s/√Hz | 40μg/√Hz | 32kHz | SPI | 消费级 |
| ICM-20602 | TDK | 6轴 | 0.004°/s/√Hz | 30μg/√Hz | 32kHz | SPI | 低成本 |
| ICM-20689 | TDK | 6轴 | 0.004°/s/√Hz | 30μg/√Hz | 32kHz | SPI | 消费级 |
| ICM-42688-P | TDK | 6轴 | 0.0028°/s/√Hz | 18μg/√Hz | 32kHz | SPI | 无人机 |
| BMI088 | Bosch | 6轴 | 0.014°/s/√Hz | 175μg/√Hz | 2kHz | SPI | 高抗振 |
| BMI270 | Bosch | 6轴 | 0.014°/s/√Hz | 120μg/√Hz | 6.4kHz | SPI | 穿戴 |
| ADIS16470 | ADI | 6轴 | 0.002°/s/√Hz | 16μg/√Hz | 2kHz | SPI | 工业级 |
| ICM-42686-P | TDK | 6轴 | 0.0015°/s/√Hz | 12μg/√Hz | 64kHz | SPI | 高性能 |
| LSM6DSOX | ST | 6轴 | 0.004°/s/√Hz | 70μg/√Hz | 6.6kHz | SPI | 机器学习 |

### 传感器关键参数
```
陀螺仪:
├── 量程: ±250/500/1000/2000/4000 °/s
│   └── 无人机选 ±2000°/s, 云台选 ±250°/s
├── 零偏稳定性: <1°/h (消费级), <0.1°/h (工业级)
├── 角度随机游走 (ARW): <0.1°/√h
│   └── 积分漂移: 位置误差 ≈ ARW × √t × v
├── 噪声密度: <0.01°/s/√Hz
├── 温漂: <0.01°/s/°C
└── 带宽: >400Hz (飞控), >100Hz (云台)

加速度计:
├── 量程: ±2/4/8/16g
│   └── 飞控选 ±16g, 云台选 ±4g
├── 零偏稳定性: <50μg
├── 噪声密度: <200μg/√Hz
├── 温漂: <0.5mg/°C
└── 带宽: >400Hz
```

## 2. 姿态融合算法

### 互补滤波
```c
/* complementary_filter.c */

typedef struct {
    float q0, q1, q2, q3;  // 四元数
    float alpha;            // 融合系数 (0.96-0.99)
} ComplementaryFilter;

void complementary_filter_update(ComplementaryFilter *cf,
                                  float gx, float gy, float gz,  // 陀螺 (rad/s)
                                  float ax, float ay, float az,  // 加速度
                                  float dt) {
    // 1. 陀螺仪积分 (短时准确)
    float half_dt = 0.5f * dt;
    float q0 = cf->q0, q1 = cf->q1, q2 = cf->q2, q3 = cf->q3;
    
    cf->q0 += (-q1*gx - q2*gy - q3*gz) * half_dt;
    cf->q1 += ( q0*gx + q2*gz - q3*gy) * half_dt;
    cf->q2 += ( q0*gy - q1*gz + q3*gx) * half_dt;
    cf->q3 += ( q0*gz + q1*gy - q2*gx) * half_dt;
    
    // 2. 加速度计修正 (长时稳定)
    // 只修正 roll 和 pitch，不修正 yaw
    float norm = sqrtf(ax*ax + ay*ay + az*az);
    if (norm > 0.1f) {
        ax /= norm; ay /= norm; az /= norm;
        
        // 重力方向在当前姿态下的投影
        float vx = 2*(q1*q3 - q0*q2);
        float vy = 2*(q0*q1 + q2*q3);
        float vz = q0*q0 - q1*q1 - q2*q2 + q3*q3;
        
        // 误差 (叉积)
        float ex = ay*vz - az*vy;
        float ey = az*vx - ax*vz;
        float ez = 0;  // 不修正 yaw
        
        // PI 修正
        float kp = 0.5f;
        gx += kp * ex;
        gy += kp * ey;
        gz += kp * ez;
    }
    
    // 3. 归一化
    norm = sqrtf(cf->q0*cf->q0 + cf->q1*cf->q1 + 
                 cf->q2*cf->q2 + cf->q3*cf->q3);
    cf->q0 /= norm; cf->q1 /= norm; 
    cf->q2 /= norm; cf->q3 /= norm;
}
```

### Mahony 滤波器
```c
/* mahony_filter.c */

typedef struct {
    float q0, q1, q2, q3;
    float integral_fb_x, integral_fb_y, integral_fb_z;
    float kp, ki;
} MahonyFilter;

void mahony_update(MahonyFilter *mf,
                    float gx, float gy, float gz,
                    float ax, float ay, float az,
                    float mx, float my, float mz,  // 磁力计 (可选)
                    float dt) {
    float q0 = mf->q0, q1 = mf->q1, q2 = mf->q2, q3 = mf->q3;
    float recipNorm;
    float qa, qb, qc;
    
    // 加速度计归一化
    recipNorm = sqrtf(ax*ax + ay*ay + az*az);
    if (recipNorm < 0.001f) return;
    ax /= recipNorm; ay /= recipNorm; az /= recipNorm;
    
    // 磁力计归一化 (如有)
    if (mx != 0 || my != 0 || mz != 0) {
        recipNorm = sqrtf(mx*mx + my*my + mz*mz);
        mx /= recipNorm; my /= recipNorm; mz /= recipNorm;
    }
    
    // 估计重力方向
    float vx = 2*(q1*q3 - q0*q2);
    float vy = 2*(q0*q1 + q2*q3);
    float vz = q0*q0 - q1*q1 - q2*q2 + q3*q3;
    
    // 加速度误差
    float ex = (ay*vz - az*vy);
    float ey = (az*vx - ax*vz);
    float ez = (ax*vy - ay*vx);
    
    // 磁力计修正 (如有)
    if (mx != 0 || my != 0 || mz != 0) {
        // 估计地磁方向
        float hx = 2*(mx*(0.5 - q2*q2 - q3*q3) + my*(q1*q2 - q0*q3) + mz*(q1*q3 + q0*q2));
        float hy = 2*(mx*(q1*q2 + q0*q3) + my*(0.5 - q1*q1 - q3*q3) + mz*(q2*q3 - q0*q1));
        float bx = sqrtf(hx*hx + hy*hy);
        float bz = 2*(mx*(q1*q3 - q0*q2) + my*(q2*q3 + q0*q1) + mz*(0.5 - q1*q1 - q2*q2));
        
        // 地磁误差
        float wx = 2*(bx*(0.5 - q2*q2 - q3*q3) + bz*(q1*q3 - q0*q2));
        float wy = 2*(bx*(q1*q2 - q0*q3) + bz*(q0*q1 + q2*q3));
        float wz = 2*(bx*(q0*q2 + q1*q3) + bz*(0.5 - q1*q1 - q2*q2));
        
        ex += (my*wz - mz*wy);
        ey += (mz*wx - mx*wz);
        ez += (mx*wy - my*wx);
    }
    
    // PI 控制器
    if (mf->ki > 0) {
        mf->integral_fb_x += mf->ki * ex * dt;
        mf->integral_fb_y += mf->ki * ey * dt;
        mf->integral_fb_z += mf->ki * ez * dt;
        gx += mf->integral_fb_x;
        gy += mf->integral_fb_y;
        gz += mf->integral_fb_z;
    }
    
    gx += mf->kp * ex;
    gy += mf->kp * ey;
    gz += mf->kp * ez;
    
    // 四元数积分
    gx *= 0.5f * dt;
    gy *= 0.5f * dt;
    gz *= 0.5f * dt;
    
    qa = q0; qb = q1; qc = q2;
    q0 += (-qb*gx - qc*gy - q3*gz);
    q1 += ( qa*gx + qc*gz - q3*gy);
    q2 += ( qa*gy - qb*gz + q3*gx);
    q3 += ( qa*gz + qb*gy - qc*gx);
    
    // 归一化
    recipNorm = sqrtf(q0*q0 + q1*q1 + q2*q2 + q3*q3);
    mf->q0 = q0/recipNorm; mf->q1 = q1/recipNorm;
    mf->q2 = q2/recipNorm; mf->q3 = q3/recipNorm;
}
```

### EKF (扩展卡尔曼滤波)
```
状态向量 (15 维):
x = [q0, q1, q2, q3, bgx, bgy, bgz, bax, bay, baz]
     四元数     陀螺零偏        加速度零偏

状态转移:
x(k+1) = f(x(k), u(k)) + w(k)
u(k) = [gx, gy, gz, ax, ay, az]  (IMU 测量)

观测模型:
z(k) = h(x(k)) + v(k)
z(k) = [ax, ay, az, mx, my, mz]  (加速度+磁力计)

EKF 步骤:
1. 预测: 使用陀螺仪积分
   x_pred = f(x, u)
   P_pred = F * P * F' + Q

2. 更新: 使用加速度计/磁力计修正
   K = P_pred * H' * (H * P_pred * H' + R)^(-1)
   x = x_pred + K * (z - h(x_pred))
   P = (I - K * H) * P_pred

优点:
├── 最优估计 (最小方差)
├── 可估计零偏
├── 可融合多传感器
└── 理论上最准确

缺点:
├── 计算量大 (矩阵运算)
├── 需要调参 (Q, R 矩阵)
├── 可能发散
└── 需要线性化
```

## 3. IMU 校准

### 零偏校准
```c
/* imu_calibration.c */

/* 静态零偏校准 */
typedef struct {
    float gyro_bias[3];     // 陀螺零偏
    float accel_bias[3];    // 加速度零偏
    float gyro_scale[3];    // 陀螺比例因子
    float accel_scale[3];   // 加速度比例因子
    float accel_rot[3][3];  // 加速度安装误差矩阵
} IMU_Calibration;

int calibrate_gyro_bias(IMU_Calibration *cal, 
                         const float *gyro_samples, int count) {
    // 静态时陀螺输出应为 0
    // 零偏 = 平均值
    
    float sum[3] = {0, 0, 0};
    
    for (int i = 0; i < count; i++) {
        sum[0] += gyro_samples[i * 3 + 0];
        sum[1] += gyro_samples[i * 3 + 1];
        sum[2] += gyro_samples[i * 3 + 2];
    }
    
    cal->gyro_bias[0] = sum[0] / count;
    cal->gyro_bias[1] = sum[1] / count;
    cal->gyro_bias[2] = sum[2] / count;
    
    return 0;
}

/* 六面校准 (加速度计) */
int calibrate_accel_six_face(IMU_Calibration *cal,
                               const float accel_data[6][3]) {
    // 6 个面: +x, -x, +y, -y, +z, -z
    // 每个面的理论值: ±1g 在对应轴
    
    // 计算比例因子和零偏
    // scale = (max - min) / 2
    // bias = (max + min) / 2
    
    for (int axis = 0; axis < 3; axis++) {
        float max_val = accel_data[axis * 2][axis];      // + 面
        float min_val = accel_data[axis * 2 + 1][axis];  // - 面
        
        cal->accel_scale[axis] = (max_val - min_val) / 2.0f;
        cal->accel_bias[axis] = (max_val + min_val) / 2.0f;
    }
    
    return 0;
}

/* 应用校准 */
void apply_imu_calibration(const IMU_Calibration *cal,
                            float raw_gyro[3], float raw_accel[3],
                            float corrected_gyro[3], float corrected_accel[3]) {
    // 陀螺校准 (零偏)
    corrected_gyro[0] = (raw_gyro[0] - cal->gyro_bias[0]) * cal->gyro_scale[0];
    corrected_gyro[1] = (raw_gyro[1] - cal->gyro_bias[1]) * cal->gyro_scale[1];
    corrected_gyro[2] = (raw_gyro[2] - cal->gyro_bias[2]) * cal->gyro_scale[2];
    
    // 加速度校准 (零偏 + 比例因子 + 安装误差)
    float temp[3];
    temp[0] = (raw_accel[0] - cal->accel_bias[0]) / cal->accel_scale[0];
    temp[1] = (raw_accel[1] - cal->accel_bias[1]) / cal->accel_scale[1];
    temp[2] = (raw_accel[2] - cal->accel_bias[2]) / cal->accel_scale[2];
    
    // 应用安装误差矩阵
    corrected_accel[0] = cal->accel_rot[0][0]*temp[0] + 
                         cal->accel_rot[0][1]*temp[1] + 
                         cal->accel_rot[0][2]*temp[2];
    corrected_accel[1] = cal->accel_rot[1][0]*temp[0] + 
                         cal->accel_rot[1][1]*temp[1] + 
                         cal->accel_rot[1][2]*temp[2];
    corrected_accel[2] = cal->accel_rot[2][0]*temp[0] + 
                         cal->accel_rot[2][1]*temp[1] + 
                         cal->accel_rot[2][2]*temp[2];
}
```

## 4. 振动分析与抑制

### 振动来源
```
无人机振动来源:
├── 电机振动
│   ├── 电机不平衡
│   ├── 轴承磨损
│   └── KV 值差异
│
├── 桨叶振动
│   ├── 桨叶不平衡
│   ├── 桨叶变形
│   └── 桨叶损坏
│
├── 结构共振
│   ├── 机架刚度不足
│   ├── 电机座松动
│   └── 安装方式不当
│
└── 气动振动
    ├── 涡流
    └── 乱流

振动频率分析:
├── 1P: 电机旋转频率 (100-300Hz)
├── 2P: 二倍频 (200-600Hz)
├── NP: 桨叶通过频率 (N × 1P)
└── 宽带: 气动噪声
```

### 陷波滤波器
```c
/* notch_filter.c */

/* 二阶 IIR 陷波滤波器 */
typedef struct {
    float b0, b1, b2;  // 分子系数
    float a1, a2;       // 分母系数
    float x1, x2;       // 输入历史
    float y1, y2;       // 输出历史
} NotchFilter;

/* 初始化陷波滤波器 */
void notch_filter_init(NotchFilter *nf, float freq, float q, float fs) {
    /*
     * 陷波滤波器传递函数:
     * H(z) = (1 - 2*cos(w0)*z^(-1) + z^(-2)) / 
     *        (1 - 2*r*cos(w0)*z^(-1) + r^2*z^(-2))
     * 
     * w0 = 2*pi*freq/fs
     * r = 1 - pi*freq/(q*fs)
     */
    
    float w0 = 2.0f * M_PI * freq / fs;
    float cos_w0 = cosf(w0);
    float r = 1.0f - M_PI * freq / (q * fs);
    
    nf->b0 = 1.0f;
    nf->b1 = -2.0f * cos_w0;
    nf->b2 = 1.0f;
    nf->a1 = -2.0f * r * cos_w0;
    nf->a2 = r * r;
    
    nf->x1 = nf->x2 = 0;
    nf->y1 = nf->y2 = 0;
}

/* 滤波处理 */
float notch_filter_process(NotchFilter *nf, float input) {
    float output = nf->b0 * input + nf->b1 * nf->x1 + nf->b2 * nf->x2
                   - nf->a1 * nf->y1 - nf->a2 * nf->y2;
    
    nf->x2 = nf->x1;
    nf->x1 = input;
    nf->y2 = nf->y1;
    nf->y1 = output;
    
    return output;
}

/* 动态陷波滤波器 (自动跟踪振动频率) */
typedef struct {
    NotchFilter filters[3];  // X/Y/Z 轴
    float peak_freq;         // 检测到的峰值频率
    float fft_buffer[256];   // FFT 缓冲区
    int buffer_index;
} DynamicNotchFilter;

void dynamic_notch_update(DynamicNotchFilter *dnf, float sample) {
    // 1. 收集样本
    dnf->fft_buffer[dnf->buffer_index++] = sample;
    
    if (dnf->buffer_index >= 256) {
        // 2. FFT 分析
        fft_256(dnf->fft_buffer);
        
        // 3. 找到峰值频率
        float max_power = 0;
        int max_bin = 0;
        for (int i = 2; i < 128; i++) {
            float power = dnf->fft_buffer[i] * dnf->fft_buffer[i];
            if (power > max_power) {
                max_power = power;
                max_bin = i;
            }
        }
        
        float peak_freq = (float)max_bin * SAMPLE_RATE / 256.0f;
        
        // 4. 更新陷波滤波器频率
        if (fabsf(peak_freq - dnf->peak_freq) > 5.0f) {
            dnf->peak_freq = peak_freq;
            for (int i = 0; i < 3; i++) {
                notch_filter_init(&dnf->filters[i], peak_freq, 5.0f, 
                                   SAMPLE_RATE);
            }
        }
        
        dnf->buffer_index = 0;
    }
}
```

### 软安装减振
```
软安装方案:
┌─────────────────────────────────────┐
│                                      │
│  IMU 板                              │
│  ┌────────────────────────────────┐ │
│  │  IMU + 配重                    │ │
│  └────────────────────────────────┘ │
│         │ │ │ │                      │
│       减振垫 (硅胶/泡棉)             │
│         │ │ │ │                      │
│  ┌────────────────────────────────┐ │
│  │  飞控板                        │ │
│  └────────────────────────────────┘ │
│                                      │
└─────────────────────────────────────┘

减振垫选型:
├── 硅胶垫: 硬度 20-40A, 适合轻载
├── 泡棉垫: 密度 30-60kg/m³, 适合中载
├── O 型圈: 简单有效
└── 3M 双面胶: 方便但效果一般

安装注意事项:
├── IMU 板自由悬浮 (不要刚性连接)
├── 配重增加惯性 (提高减振效果)
├── 避免线缆刚性连接 (使用软线)
└── 避免共振频率匹配
```
