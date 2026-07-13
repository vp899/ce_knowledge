---
title: "云台系统"
aliases:
  - "云台控制"
  - "云台驱动"
tags:
  - gimbal
  - foc
  - bldc
  - stabilization
module: "17-gimbal"
status: active
---

# 云台系统

## 1. 云台机械结构

### 三轴云台结构
```
         Pitch (俯仰轴)
            │
            ├── 相机安装架
            │
    ┌───────┼───────┐
    │       │       │
    │    Pitch      │
    │    电机       │
    │       │       │
    └───────┼───────┘
            │
    ┌───────┼───────┐
    │       │       │
    │    Roll       │  ← Roll (横滚轴)
    │    电机       │
    │       │       │
    └───────┼───────┘
            │
    ┌───────┼───────┐
    │       │       │
    │    Yaw        │  ← Yaw (偏航轴)
    │    电机       │
    │       │       │
    └───────┼───────┘
            │
        飞行器

各轴自由度:
├── Roll: ±30° ~ ±45° (抗风)
├── Pitch: -90° ~ +30° (俯仰)
└── Yaw: ±360° (无限旋转) 或 ±160° (有限)
```

### 云台电机选型
```
无刷云台电机 (BLDC Gimbal Motor):

特点:
├── 低 KV 值 (50-300 KV)
├── 大扭矩
├── 直驱 (无齿轮)
├── 低齿槽效应
└── 精密绕线

选型参数:
| 参数 | 小型云台 | 中型云台 | 大型云台 |
|------|----------|----------|----------|
| 相机重量 | <100g | 100-500g | 500-2000g |
| 电机尺寸 | 2204-2208 | 2804-2808 | 4006-4010 |
| KV 值 | 100-200 | 50-100 | 30-80 |
| 扭矩 | 0.1-0.3 Nm | 0.3-1.0 Nm | 1.0-5.0 Nm |
| 电流 | 0.5-1A | 1-3A | 3-10A |
| 重量 | 20-40g | 40-80g | 80-200g |

常用型号:
├── iFlight 2208: 小型航拍
├── T-Motor GB2804: 中型航拍
├── iPower GBM4006: 大型航拍
└── Maxon EC-i 40: 工业级
```

## 2. 云台电机驱动

### FOC (磁场定向控制) 驱动
```
FOC 控制框图:

位置设定值 → 位置环 → 电流环 → SVPWM → 三相逆变器 → 电机
    │           │        │                              │
    │           │        │                              │
    └───────────┴────────┴────────←── 编码器/霍尔 ──────┘

FOC 核心算法:
1. Clark 变换: 三相 (Ia, Ib, Ic) → 两相静止 (Iα, Iβ)
2. Park 变换: 两相静止 (Iα, Iβ) → 两相旋转 (Id, Iq)
3. PI 控制: Id 控制磁通，Iq 控制转矩
4. 反 Park 变换: (Vd, Vq) → (Vα, Vβ)
5. SVPWM: 生成三相 PWM 信号
```

### 云台驱动代码
```c
/* gimbal_motor.c */
#include "gimbal_motor.h"

/* FOC 参数 */
typedef struct {
    float id_ref, iq_ref;       // d/q 轴电流设定值
    float id_fb, iq_fb;         // d/q 轴电流反馈
    float vd, vq;               // d/q 轴电压输出
    float v_alpha, v_beta;      // α/β 轴电压
    float theta;                // 电角度
    float pid_id_kp, pid_id_ki; // d 轴 PID
    float pid_iq_kp, pid_iq_ki; // q 轴 PID
    float integral_id, integral_iq;
} FOC_State;

/* Clark 变换 */
void clarke_transform(float ia, float ib, float ic,
                       float *i_alpha, float *i_beta) {
    *i_alpha = ia;
    *i_beta = (ia + 2 * ib) * ONE_BY_SQRT3;
}

/* Park 变换 */
void park_transform(float i_alpha, float i_beta, float theta,
                     float *id, float *iq) {
    float cos_theta = cosf(theta);
    float sin_theta = sinf(theta);
    
    *id = i_alpha * cos_theta + i_beta * sin_theta;
    *iq = -i_alpha * sin_theta + i_beta * cos_theta;
}

/* 反 Park 变换 */
void inv_park_transform(float vd, float vq, float theta,
                          float *v_alpha, float *v_beta) {
    float cos_theta = cosf(theta);
    float sin_theta = sinf(theta);
    
    *v_alpha = vd * cos_theta - vq * sin_theta;
    *v_beta = vd * sin_theta + vq * cos_theta;
}

/* SVPWM (空间矢量脉宽调制) */
void svpwm(float v_alpha, float v_beta, float v_dc,
            float *duty_a, float *duty_b, float *duty_c) {
    // 计算扇区
    float v1 = v_beta;
    float v2 = SQRT3_BY_2 * v_alpha - 0.5f * v_beta;
    float v3 = -SQRT3_BY_2 * v_alpha - 0.5f * v_beta;
    
    int sector = 0;
    if (v1 > 0) sector += 1;
    if (v2 > 0) sector += 2;
    if (v3 > 0) sector += 4;
    
    // 计算占空比
    float t1, t2, t0;
    float ts = 1.0f / PWM_FREQ;
    
    switch (sector) {
    case 1:
        t1 = SQRT3 * ts / v_dc * (SQRT3_BY_2 * v_alpha - 0.5f * v_beta);
        t2 = SQRT3 * ts / v_dc * v_beta;
        break;
    case 2:
        t1 = SQRT3 * ts / v_dc * (-SQRT3_BY_2 * v_alpha + 0.5f * v_beta);
        t2 = SQRT3 * ts / v_dc * (SQRT3_BY_2 * v_alpha + 0.5f * v_beta);
        break;
    // ... 其他扇区
    }
    
    t0 = ts - t1 - t2;
    
    // 零矢量均匀分配
    float ta = t0 / 2 + t1 + t2;
    float tb = t0 / 2 + t2;
    float tc = t0 / 2;
    
    *duty_a = ta / ts;
    *duty_b = tb / ts;
    *duty_c = tc / ts;
}

/* 电流环控制 (10kHz) */
void current_loop_update(FOC_State *foc, 
                          float ia, float ib, float ic,
                          float theta) {
    float i_alpha, i_beta;
    
    // Clark 变换
    clarke_transform(ia, ib, ic, &i_alpha, &i_beta);
    
    // Park 变换
    park_transform(i_alpha, i_beta, theta, &foc->id_fb, &foc->iq_fb);
    
    // d 轴 PI 控制 (目标: id = 0)
    float error_id = foc->id_ref - foc->id_fb;
    foc->integral_id += error_id * DT;
    foc->vd = foc->pid_id_kp * error_id + 
              foc->pid_id_ki * foc->integral_id;
    
    // q 轴 PI 控制 (控制转矩)
    float error_iq = foc->iq_ref - foc->iq_fb;
    foc->integral_iq += error_iq * DT;
    foc->vq = foc->pid_iq_kp * error_iq + 
              foc->pid_iq_ki * foc->integral_iq;
    
    // 反 Park 变换
    inv_park_transform(foc->vd, foc->vq, theta, 
                        &foc->v_alpha, &foc->v_beta);
    
    // SVPWM
    float duty_a, duty_b, duty_c;
    svpwm(foc->v_alpha, foc->v_beta, V_DC, 
          &duty_a, &duty_b, &duty_c);
    
    // 输出到 PWM
    set_pwm_duty(duty_a, duty_b, duty_c);
}

/* 位置环控制 (1kHz) */
void position_loop_update(GimbalAxis *axis, float angle_ref) {
    float angle_fb = read_encoder_angle(axis);
    float angle_error = angle_ref - angle_fb;
    
    // PD 控制器
    float velocity_ref = axis->kp * angle_error - 
                         axis->kd * axis->velocity_fb;
    
    // 速度环
    float velocity_error = velocity_ref - axis->velocity_fb;
    axis->iq_ref = axis->kv * velocity_error;
}
```

## 3. 云台控制算法

### 增稳控制
```
增稳原理:
├── IMU 测量云台姿态 (roll, pitch, yaw)
├── 与目标姿态比较
├── 计算修正力矩
├── 驱动电机消除误差

双环控制:
外环 (角度环, 100-400Hz):
    error_angle = target_angle - current_angle
    velocity_cmd = Kp_angle * error_angle

内环 (角速度环, 1-10kHz):
    error_velocity = velocity_cmd - current_velocity
    iq_cmd = Kp_velocity * error_velocity + Ki_velocity * integral

前馈补偿:
    - 飞行器角速度前馈 (减少跟踪延迟)
    - 重力补偿 (pitch 轴)
    - 摩擦补偿
```

### 跟随模式
```
模式 1: 锁定模式 (Lock)
├── 云台指向固定方向
├── 不随飞行器转向
├── 适用于: 固定目标拍摄

模式 2: 跟随模式 (Follow)
├── Yaw 轴跟随飞行器航向
├── Roll/Pitch 保持稳定
├── 适用于: 跟随拍摄

模式 3: FPV 模式
├── 三轴跟随飞行器姿态
├── 无增稳
├── 适用于: FPV 飞行

模式 4: 航点模式 (POI)
├── 云台指向固定兴趣点
├── 飞行器绕兴趣点飞行
├── 适用于: 环绕拍摄
```

## 4. 云台传感器

### IMU 选型
```
云台 IMU 要求:
├── 低噪声: 姿态估计精度
├── 高采样率: ≥1kHz
├── 低延迟: <1ms
├── 温漂小: 稳定性

常用型号:
├── ICM-42688-P: 6 轴, 低噪声, 高精度
├── BMI088: 6 轴, 高抗振
├── ICM-20689: 6 轴, 经济型
└── MPU6000: 6 轴, 经典 (已停产)

安装位置:
├── 安装在相机平台上 (测量相机姿态)
├── 远离电机 (减少电磁干扰)
└── 硬安装 (减少振动)
```

### 编码器
```
云台编码器类型:

磁编码器:
├── AS5048A: 14-bit, SPI 接口
├── AS5600: 12-bit, I2C 接口
├── 精度: ±0.05°
├── 分辨率: 0.022° (14-bit)
└── 优点: 非接触, 免维护

光学编码器:
├── 分辨率: 12-16 bit
├── 精度: ±0.01°
├── 优点: 高精度
└── 缺点: 贵, 怕灰尘

霍尔传感器:
├── 3 个霍尔元件 (120° 间隔)
├── 精度: ±1°
├── 分辨率: 有限
└── 优点: 便宜, 简单

无感 FOC:
├── 通过反电动势估算转子位置
├── 无需编码器
├── 低速精度差
└── 适用于低成本方案
```
---

## 相关链接

- [[camera-sensor|相机系统]]
- [[imu-system|IMU]]
- [[esc-control|ESC 控制]]
