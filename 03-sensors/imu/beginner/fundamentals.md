---
title: "IMU 初级 - 基础原理"
tags: [imu, beginner, accelerometer, gyroscope, fundamentals]
level: beginner
---

# IMU 基础原理

## 概述

IMU 是所有运动设备的基础传感器。本文介绍加速度计/陀螺仪原理、数据读取和姿态表示。

完成本文学习后，你将能够：

- 理解加速度计和陀螺仪工作原理
- 掌握 IMU 数据读取和单位转换
- 了解姿态表示方法 (欧拉角/四元数)

## 背景知识

### 相关概念

### 前置知识

- C 语言基础 (变量/指针/函数)
- 基本电子电路知识 (电压/电流/电阻)
- 基本数学 (三角函数/向量)

### 学习建议

- 准备一块开发板进行动手实践
- 边学边做，不要只看不练
- 遇到问题先自己思考，再查资料

## 核心内容

### 1. 什么是 IMU

IMU (Inertial Measurement Unit) 惯性测量单元，是测量物体三轴加速度和三轴角速度的传感器。

```
IMU = 加速度计 (Accelerometer) + 陀螺仪 (Gyroscope)

高级 IMU 还包含:
IMU = 加速度计 + 陀螺仪 + 磁力计 (Magnetometer) → 9 轴
```

### 2. 加速度计原理

### 工作原理
```
加速度计测量的是「比力」(specific force)，即除重力外的外力产生的加速度。

弹簧-质量块模型:
                    ┌─────────────┐
    加速度 →        │  ┌───┐      │
                    │  │ m │──弹簧──│── 输出位移
                    │  └───┘      │
                    └─────────────┘

    F = m · a
    弹簧伸长量 ∝ 加速度

静止时:
    加速度计测量值 = 重力加速度 (9.8 m/s²) 方向向上
    → 所以静止时 Z 轴读数约为 1g

自由落体时:
    加速度计测量值 = 0 (失重状态)
```

### 三轴加速度计
```
          Z 轴 (向上为正)
          │
          │
          └─────── Y 轴
         ╱
        ╱
       ╱
      X 轴

各轴测量:
  ax: X 轴加速度 (左右)
  ay: Y 轴加速度 (前后)
  az: Z 轴加速度 (上下)

静止水平放置时:
  ax = 0, ay = 0, az = +1g (≈9.8 m/s²)

倾斜 45° 时:
  ax = 0, ay = sin(45°)·g ≈ 0.707g, az = cos(45°)·g ≈ 0.707g
```

### 从加速度计算倾斜角
```c
// 从加速度计计算 Roll 和 Pitch
float calc_roll(float ax, float ay, float az) {
    return atan2f(ay, az);  // 绕 X 轴倾斜
}

float calc_pitch(float ax, float ay, float az) {
    return atan2f(-ax, sqrtf(ay*ay + az*az));  // 绕 Y 轴倾斜
}

// 注意: 加速度计无法测量 Yaw (绕 Z 轴旋转)
// 因为重力方向不变，无法区分水平旋转
```

### 3. 陀螺仪原理

### 工作原理
```
MEMS 陀螺仪利用科里奥利力 (Coriolis Force) 测量角速度。

原理:
  振动质量块在旋转参考系中会受到科里奥利力:
  F_coriolis = -2m × (ω × v)

  ω = 角速度
  v = 振动速度
  m = 质量

MEMS 结构:
  ┌─────────────────────────┐
  │  ┌───────────────────┐  │
  │  │  驱动梳齿 (振动)   │  │
  │  │  ←→ ←→ ←→ ←→     │  │
  │  └───────────────────┘  │
  │         ↓ 科里奥利力     │
  │  ┌───────────────────┐  │
  │  │  感应梳齿 (检测)   │  │
  │  │  ↕ ↕ ↕ ↕          │  │
  │  └───────────────────┘  │
  └─────────────────────────┘

输出: 角速度 (°/s 或 rad/s)
```

### 三轴陀螺仪
```
测量绕三个轴的旋转角速度:

  gx: 绕 X 轴角速度 (Roll rate)
  gy: 绕 Y 轴角速度 (Pitch rate)
  gz: 绕 Z 轴角速度 (Yaw rate)

单位转换:
  1°/s = π/180 rad/s ≈ 0.01745 rad/s
  1 rad/s = 180/π °/s ≈ 57.3 °/s
```

### 4. 常见 IMU 模块

| 模块 | 轴数 | 接口 | 价格 | 适用 |
|------|------|------|------|------|
| MPU6050 | 6 轴 | I2C | ¥5 | 入门学习 |
| GY-521 | 6 轴 | I2C | ¥8 | Arduino |
| BMI160 | 6 轴 | SPI/I2C | ¥15 | 穿戴 |
| ICM-42688-P | 6 轴 | SPI | ¥25 | 无人机 |
| BNO055 | 9 轴 | I2C | ¥60 | 内置融合 |

### 5. 第一个 IMU 程序

```c
// MPU6050 读取示例 (I2C)
#include <Wire.h>

#define MPU6050_ADDR 0x68

void setup() {
    Serial.begin(115200);
    Wire.begin();
    
    // 唤醒 MPU6050
    Wire.beginTransmission(MPU6050_ADDR);
    Wire.write(0x6B);  // PWR_MGMT_1
    Wire.write(0x00);  // 唤醒
    Wire.endTransmission();
    
    // 设置量程
    Wire.beginTransmission(MPU6050_ADDR);
    Wire.write(0x1B);  // GYRO_CONFIG
    Wire.write(0x08);  // ±500°/s
    Wire.endTransmission();
    
    Wire.beginTransmission(MPU6050_ADDR);
    Wire.write(0x1C);  // ACCEL_CONFIG
    Wire.write(0x08);  // ±4g
    Wire.endTransmission();
}

void loop() {
    Wire.beginTransmission(MPU6050_ADDR);
    Wire.write(0x3B);  // 从加速度计数据开始
    Wire.endTransmission(false);
    Wire.requestFrom(MPU6050_ADDR, 14, true);
    
    int16_t ax = Wire.read() << 8 | Wire.read();
    int16_t ay = Wire.read() << 8 | Wire.read();
    int16_t az = Wire.read() << 8 | Wire.read();
    int16_t temp = Wire.read() << 8 | Wire.read();
    int16_t gx = Wire.read() << 8 | Wire.read();
    int16_t gy = Wire.read() << 8 | Wire.read();
    int16_t gz = Wire.read() << 8 | Wire.read();
    
    // 转换为物理单位
    float accel_x = ax / 8192.0;  // ±4g → 8192 LSB/g
    float accel_y = ay / 8192.0;
    float accel_z = az / 8192.0;
    float gyro_x = gx / 65.5;     // ±500°/s → 65.5 LSB/(°/s)
    float gyro_y = gy / 65.5;
    float gyro_z = gz / 65.5;
    float temperature = temp / 340.0 + 36.53;
    
    Serial.printf("Accel: %.2f %.2f %.2f g\n", accel_x, accel_y, accel_z);
    Serial.printf("Gyro:  %.2f %.2f %.2f °/s\n", gyro_x, gyro_y, gyro_z);
    Serial.printf("Temp:  %.1f °C\n", temperature);
    
    delay(100);
}
```

### 6. 关键术语

| 术语 | 含义 | 典型值 |
|------|------|--------|
| 量程 (Range) | 最大测量范围 | ±2g~±16g, ±250~±2000°/s |
| 灵敏度 (Sensitivity) | LSB/单位 | 16384 LSB/g (±2g) |
| 零偏 (Bias) | 零输入时的输出 | ±20~100 mg, ±0.5~5 °/s |
| 噪声密度 | 每√Hz 噪声 | 40~200 μg/√Hz |
| 温漂 | 温度引起的零偏变化 | ±0.01 °/s/°C |
| 带宽 | 有效频率范围 | 5~250 Hz |

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

1. 从简单示例开始，逐步增加复杂度
2. 充分利用厂商提供的示例代码
3. 建立良好的代码规范和注释习惯

## 常见问题

### Q1: 为什么静止时加速度计 Z 轴读数不是 0？

**A**: 加速度计测量的是「比力」(specific force)，包含重力。静止时重力加速度约 9.8 m/s² 向上，所以 Z 轴读数约为 +1g。

### Q2: 陀螺仪数据单位是什么？

**A**: 通常输出原始值 (LSB)，需要除以灵敏度转换为 °/s 或 rad/s。例如 MPU6050 在 ±250°/s 模式下，灵敏度为 131 LSB/(°/s)。

## 总结

本文介绍了基础概念和入门知识：

- 理解了核心原理和工作机制
- 掌握了基本的工具和方法
- 通过简单示例验证了学习效果

下一步建议进入中级内容，深入学习算法和实现细节。

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

**下一步**：建议学习 [[imu/intermediate/|中级内容]]
