---
title: "指南针（磁力计）"
aliases:
  - "磁力计"
  - "电子罗盘"
tags:
  - compass
  - magnetometer
  - calibration
  - heading
module: "19-compass"
status: active
---

# 指南针（磁力计）

## 1. 磁力计传感器

### 常用磁力计对比

| 型号 | 厂商 | 量程 | 分辨率 | 噪声 | 采样率 | 接口 | 特点 |
|------|------|------|--------|------|--------|------|------|
| QMC5883L | QST | ±8G | 0.73mG | 2mG | 200Hz | I2C | 经济型 |
| HMC5883L | Honeywell | ±8G | 0.73mG | 2mG | 160Hz | I2C | 经典 (停产) |
| IST8310 | Isentek | ±16G | 0.3μT | 0.6μT | 200Hz | I2C | 无人机常用 |
| MMC5603NJ | Memsic | ±30G | 0.0625mG | 0.4mG | 1000Hz | I2C | 高精度 |
| AK09918 | AKM | ±49G | 0.15μT | 1.2μT | 100Hz | I2C | 9轴 IMU 内置 |
| LIS3MDL | ST | ±16G | 0.14mG | 1mG | 1000Hz | SPI/I2C | 低功耗 |
| RM3100 | PNI | ±800μT | 13nT | <20nT | 200Hz | SPI | 最高精度 |

### 传感器关键参数
```
量程: ±2G ~ ±16G
├── 地球磁场: ~0.5G (50μT)
├── 无人机: ±8G 足够
└── 强干扰环境: ±16G

分辨率: ADC 位数决定
├── 12-bit: 0.73mG @±8G
├── 14-bit: 0.18mG @±8G
├── 16-bit: 0.045mG @±8G
└── 越高越好, 影响航向精度

噪声: 影响航向稳定性
├── <1mG: 高精度
├── 1-3mG: 普通
├── >3mG: 需要滤波

采样率: 飞控需要 ≥50Hz
├── 10Hz: 低速应用
├── 50-100Hz: 飞控
└── 200Hz+: 快速响应
```

## 2. 磁力计校准

### 硬磁干扰与软磁干扰
```
硬磁干扰 (Hard Iron):
├── 来源: 永磁体、直流电流
├── 表现: 磁场偏移 (椭球中心偏移)
├── 校准: 加减常数偏移
└── 特点: 不随传感器朝向变化

软磁干扰 (Soft Iron):
├── 来源: 铁磁材料、交流电流
├── 表现: 磁场变形 (椭球变成椭球)
├── 校准: 乘以校准矩阵
└── 特点: 随传感器朝向变化

理想 vs 实际磁力计输出:
理想: 圆形 (无干扰)
┌───────────┐
│     ○     │  → 标准圆
│           │
└───────────┘

硬磁干扰: 偏移的圆
┌───────────┐
│   ○       │  → 圆心偏移
│           │
└───────────┘

软磁干扰: 椭圆
┌───────────┐
│    ⬮      │  → 椭圆变形
│           │
└───────────┘

硬磁+软磁: 偏移的椭圆
┌───────────┐
│  ⬮        │  → 椭圆偏移
│           │
└───────────┘
```

### 校准算法
```c
/* compass_calibration.c */

/* 硬磁校准 (简单偏移) */
typedef struct {
    float offset[3];       // X/Y/Z 偏移
    float scale[3];        // X/Y/Z 比例因子
    float soft_iron[3][3]; // 软磁校准矩阵
} CompassCalibration;

/* 椭球拟合校准 */
int calibrate_compass_ellipsoid(CompassCalibration *cal,
                                  const float *samples, int count) {
    /*
     * 采集大量样本 (旋转传感器 360°)
     * 拟合椭球方程:
     * (x-x0)²/a² + (y-y0)²/b² + (z-z0)²/c² = 1
     * 
     * 校准后: x_cal = (x - x0) / a
     */
    
    // 1. 找到各轴最大/最小值
    float min[3] = {1e9, 1e9, 1e9};
    float max[3] = {-1e9, -1e9, -1e9};
    
    for (int i = 0; i < count; i++) {
        for (int axis = 0; axis < 3; axis++) {
            float val = samples[i * 3 + axis];
            if (val < min[axis]) min[axis] = val;
            if (val > max[axis]) max[axis] = val;
        }
    }
    
    // 2. 计算偏移 (椭球中心)
    for (int axis = 0; axis < 3; axis++) {
        cal->offset[axis] = (max[axis] + min[axis]) / 2.0f;
    }
    
    // 3. 计算比例因子 (椭球半径)
    for (int axis = 0; axis < 3; axis++) {
        cal->scale[axis] = (max[axis] - min[axis]) / 2.0f;
    }
    
    // 归一化到单位球
    float avg_radius = (cal->scale[0] + cal->scale[1] + cal->scale[2]) / 3.0f;
    for (int axis = 0; axis < 3; axis++) {
        cal->scale[axis] = avg_radius / cal->scale[axis];
    }
    
    return 0;
}

/* 应用校准 */
void apply_compass_calibration(const CompassCalibration *cal,
                                const float raw[3], float corrected[3]) {
    float temp[3];
    
    // 1. 去除硬磁偏移
    temp[0] = raw[0] - cal->offset[0];
    temp[1] = raw[1] - cal->offset[1];
    temp[2] = raw[2] - cal->offset[2];
    
    // 2. 应用比例因子
    temp[0] *= cal->scale[0];
    temp[1] *= cal->scale[1];
    temp[2] *= cal->scale[2];
    
    // 3. 应用软磁校准矩阵 (如有)
    corrected[0] = cal->soft_iron[0][0]*temp[0] + 
                   cal->soft_iron[0][1]*temp[1] + 
                   cal->soft_iron[0][2]*temp[2];
    corrected[1] = cal->soft_iron[1][0]*temp[0] + 
                   cal->soft_iron[1][1]*temp[1] + 
                   cal->soft_iron[1][2]*temp[2];
    corrected[2] = cal->soft_iron[2][0]*temp[0] + 
                   cal->soft_iron[2][1]*temp[1] + 
                   cal->soft_iron[2][2]*temp[2];
}
```

## 3. 航向解算

### 磁航向计算
```c
/* heading_calculation.c */

/* 从磁力计计算磁航向 */
float calculate_heading(float mx, float my, float mz,
                         float roll, float pitch) {
    /*
     * 将磁力计数据从机体坐标系转换到水平坐标系
     * 然后计算磁北方向
     */
    
    float cos_roll = cosf(roll);
    float sin_roll = sinf(roll);
    float cos_pitch = cosf(pitch);
    float sin_pitch = sinf(pitch);
    
    // 倾斜补偿
    float mx_h = mx * cos_pitch + my * sin_roll * sin_pitch + 
                 mz * cos_roll * sin_pitch;
    float my_h = my * cos_roll - mz * sin_roll;
    
    // 计算航向
    float heading = atan2f(-my_h, mx_h);
    
    // 转换到 0-360°
    if (heading < 0) {
        heading += 2 * M_PI;
    }
    
    return heading;  // 弧度
}

/* 真航向 = 磁航向 + 磁偏角 */
float true_heading(float magnetic_heading, float declination) {
    float true_h = magnetic_heading + declination;
    
    if (true_h > 2 * M_PI) true_h -= 2 * M_PI;
    if (true_h < 0) true_h += 2 * M_PI;
    
    return true_h;
}

/* 磁偏角查询 (需要数据库或模型) */
float get_magnetic_declination(float latitude, float longitude) {
    // 使用 WMM (World Magnetic Model) 或 IGRF
    // 简化: 使用查表或在线 API
    // 中国地区典型值: -5° ~ +10°
    
    // 示例: 北京 (39.9°N, 116.4°E) 约 -6.5°
    // 示例: 上海 (31.2°N, 121.5°E) 约 -5.8°
    // 示例: 深圳 (22.5°N, 114.1°E) 约 -3.0°
    
    return declination_db_lookup(latitude, longitude);
}
```

## 4. 干扰检测与补偿

### 电流干扰补偿
```
电机电流对磁力计的影响:

影响公式:
B_measured = B_earth + B_hard_iron + k × I_motor

其中:
├── B_measured: 磁力计测量值
├── B_earth: 地球磁场
├── B_hard_iron: 硬磁干扰
├── k: 电流-磁场系数 (与布线有关)
└── I_motor: 电机电流

补偿方法:
1. 地面校准: 测量无电流时的磁场
2. 飞行中: 测量电流和磁场的关系
3. 实时补偿: B_compensated = B_measured - k × I_motor

电流补偿系数 k 的标定:
├── 地面: 起动电机到不同油门
├── 记录: 磁力计输出 vs 电流
├── 线性拟合: k = ΔB / ΔI
└── 存储: 用于实时补偿
```

### 干扰检测
```c
/* interference_detection.c */

typedef struct {
    float field_strength;      // 磁场强度
    float expected_strength;   // 预期强度 (地球磁场)
    float strength_threshold;  // 强度阈值
    bool is_interfered;        // 是否被干扰
} InterferenceDetector;

bool check_magnetic_interference(InterferenceDetector *det,
                                   float mx, float my, float mz) {
    // 计算磁场强度
    float strength = sqrtf(mx*mx + my*my + mz*mz);
    
    det->field_strength = strength;
    
    // 与预期强度比较
    // 地球磁场: 25-65μT (取决于位置)
    float ratio = strength / det->expected_strength;
    
    // 干扰判定
    if (ratio > 1.5f || ratio < 0.5f) {
        // 磁场强度偏差 >50%，认为有干扰
        det->is_interfered = true;
        return true;
    }
    
    // 检查磁场变化率
    static float prev_strength = 0;
    float delta = fabsf(strength - prev_strength);
    prev_strength = strength;
    
    if (delta > 5.0f) {
        // 磁场突变 >5μT，可能有干扰
        det->is_interfered = true;
        return true;
    }
    
    det->is_interfered = false;
    return false;
}
```

### 安装注意事项
```
磁力计安装指南:

最佳安装位置:
├── 远离电机 (至少 10cm)
├── 远离电池 (电流产生磁场)
├── 远离金属结构 (软磁干扰)
├── 远离 ESC (开关噪声)
└── 高处安装 (远离电流集中区)

安装检查清单:
□ 远离所有电流携带导线
□ 远离永磁体 (扬声器、磁铁)
□ 远离铁磁材料 (螺丝、支架)
□ 远离大电流电调/电机
□ 软安装减少振动 (但不要影响精度)
□ 使用非磁性螺丝固定
□ 安装方向与飞控一致
□ 飞行前完成校准
```
---

## 相关链接

- [[imu-system|IMU]]
- [[flight-controller-firmware|飞控]]
