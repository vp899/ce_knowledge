---
title: "IMU 中级 - 姿态融合算法"
tags: [imu, intermediate, complementary, mahony, quaternion]
level: intermediate
---

# IMU 始态融合算法

## 概述

本文介绍 imu 领域的 intermediate 级别知识。

完成本文学习后，你将能够：

- 掌握互补滤波和 Mahony 姿态融合
- 能够实现 IMU 校准算法
- 理解振动对 IMU 的影响和抑制方法

## 背景知识

### 相关概念

### 前置知识

- 完成初级内容的学习
- 熟悉嵌入式开发流程
- 掌握基本的数据结构和算法

### 学习建议

- 理解原理后动手实现
- 对比不同算法的优缺点
- 关注工程实践中的细节

## 核心内容

### 1. 为什么需要融合

```
单独使用加速度计的问题:
├── 噪声大 (振动环境)
├── 无法测量 Yaw
└── 动态时测量不准 (含运动加速度)

单独使用陀螺仪的问题:
├── 积分漂移 (零偏累积)
├── 长时间后姿态完全错误
└── 需要初始对准

融合的目的:
  结合两者优点:
  ├── 陀螺仪: 短时准确, 响应快
  └── 加速度计: 长时稳定, 无漂移
```

### 2. 互补滤波器

### 原理
```
互补滤波 = 低通滤波(加速度计) + 高通滤波(陀螺仪)

  θ = α × (θ + ω×dt) + (1-α) × θ_accel
      └──── 陀螺积分 ────┘   └─ 加速度 ─┘

  α = τ / (τ + dt)
  τ = 时间常数 (如 0.5-2 秒)
  dt = 采样周期

频率特性:
  截止频率 fc = 1/(2πτ)
  
  τ = 1s → fc = 0.16 Hz
  τ = 0.5s → fc = 0.32 Hz

  陀螺仪: 通过 fc 以上 (高频, 快速变化)
  加速度计: 通过 fc 以下 (低频, 稳态)
```

### 完整实现
```c
typedef struct {
    float q[4];      // 四元数
    float kp;        // 比例增益
    float ki;        // 积分增益
    float integral[3];
    float dt;
} CompFilter;

void comp_init(CompFilter *f, float kp, float ki, float dt) {
    f->q[0]=1; f->q[1]=f->q[2]=f->q[3]=0;
    f->kp = kp; f->ki = ki; f->dt = dt;
    f->integral[0]=f->integral[1]=f->integral[2]=0;
}

void comp_update(CompFilter *f,
                  float gx, float gy, float gz,
                  float ax, float ay, float az) {
    float q0=f->q[0], q1=f->q[1], q2=f->q[2], q3=f->q[3];
    
    // 归一化加速度
    float norm = sqrtf(ax*ax + ay*ay + az*az);
    if(norm < 0.001f) return;
    ax/=norm; ay/=norm; az/=norm;
    
    // 估计重力方向
    float vx = 2*(q1*q3 - q0*q2);
    float vy = 2*(q0*q1 + q2*q3);
    float vz = q0*q0 - q1*q1 - q2*q2 + q3*q3;
    
    // 误差 = 测量 × 估计 (叉积)
    float ex = ay*vz - az*vy;
    float ey = az*vx - ax*vz;
    float ez = ax*vy - ay*vx;
    
    // PI 修正
    f->integral[0] += f->ki * ex * f->dt;
    f->integral[1] += f->ki * ey * f->dt;
    f->integral[2] += f->ki * ez * f->dt;
    
    gx += f->kp*ex + f->integral[0];
    gy += f->kp*ey + f->integral[1];
    gz += f->kp*ez + f->integral[2];
    
    // 四元数积分
    float h = 0.5f * f->dt;
    q0 += (-q1*gx - q2*gy - q3*gz)*h;
    q1 += ( q0*gx + q2*gz - q3*gy)*h;
    q2 += ( q0*gy - q1*gz + q3*gx)*h;
    q3 += ( q0*gz + q1*gy - q2*gx)*h;
    
    norm = sqrtf(q0*q0+q1*q1+q2*q2+q3*q3);
    f->q[0]=q0/norm; f->q[1]=q1/norm;
    f->q[2]=q2/norm; f->q[3]=q3/norm;
}
```

### 3. Mahony AHRS

### 与互补滤波的区别
```
Mahony 改进:
├── 支持磁力计 (完整 9 轴 AHRS)
├── 自适应增益 (根据加速度大小调整)
├── 更好的抗振性能
└── 可估计陀螺零偏 (积分项)
```

### 完整实现 (含磁力计)
```c
void mahony_update(float gx, float gy, float gz,
                    float ax, float ay, float az,
                    float mx, float my, float mz,
                    float dt) {
    static float q0=1, q1=0, q2=0, q3=0;
    static float ix=0, iy=0, iz=0;
    float kp = 2.0f, ki = 0.005f;
    
    // 加速度归一化
    float norm = sqrtf(ax*ax+ay*ay+az*az);
    if(norm < 0.001f) return;
    ax/=norm; ay/=norm; az/=norm;
    
    // 磁力计归一化
    norm = sqrtf(mx*mx+my*my+mz*mz);
    if(norm < 0.001f) goto skip_mag;
    mx/=norm; my/=norm; mz/=norm;
    
    // 磁力计辅助方向估计
    float q0q0=q0*q0, q0q1=q0*q1, q0q2=q0*q2, q0q3=q0*q3;
    float q1q1=q1*q1, q1q2=q1*q2, q1q3=q1*q3;
    float q2q2=q2*q2, q2q3=q2*q3, q3q3=q3*q3;
    
    float hx = 2*(mx*(0.5f-q2q2-q3q3) + my*(q1q2-q0q3) + mz*(q1q3+q0q2));
    float hy = 2*(mx*(q1q2+q0q3) + my*(0.5f-q1q1-q3q3) + mz*(q2q3-q0q1));
    float bx = sqrtf(hx*hx+hy*hy);
    float bz = 2*(mx*(q1q3-q0q2) + my*(q2q3+q0q1) + mz*(0.5f-q1q1-q2q2));
    
    // 估计方向
    float vx = q1q3-q0q2,  vy = q0q1+q2q3,  vz = q0q0-0.5f+q3q3;
    float wx = bx*(0.5f-q2q2-q3q3)+bz*(q1q3-q0q2);
    float wy = bx*(q1q2-q0q3)+bz*(q0q1+q2q3);
    float wz = bx*(q0q2+q1q3)+bz*(0.5f-q1q1-q2q2);
    
    // 误差 = 加速度误差 + 磁力计误差
    float ex = (ay*vz-az*vy) + (my*wz-mz*wy);
    float ey = (az*vx-ax*vz) + (mz*wx-mx*wz);
    float ez = (ax*vy-ay*vx) + (mx*wy-my*wx);
    goto compute;
    
skip_mag:
    // 无磁力计时只用加速度修正
    float vx2 = 2*(q1*q3-q0*q2);
    float vy2 = 2*(q0*q1+q2*q3);
    float vz2 = q0*q0-q1*q1-q2*q2+q3*q3;
    ex = ay*vz2-az*vy2;
    ey = az*vx2-ax*vz2;
    ez = ax*vy2-ay*vx2;
    
compute:
    // PI 修正
    if(ki > 0) {
        ix += ki*ex*dt; iy += ki*ey*dt; iz += ki*ez*dt;
        gx += ix; gy += iy; gz += iz;
    }
    gx += kp*ex; gy += kp*ey; gz += kp*ez;
    
    // 四元数积分
    float h = 0.5f*dt;
    float qa=q0, qb=q1, qc=q2;
    q0 += (-qb*gx-qc*gy-q3*gz)*h;
    q1 += ( qa*gx+qc*gz-q3*gy)*h;
    q2 += ( qa*gy-qb*gz+q3*gx)*h;
    q3 += ( qa*gz+qb*gy-qc*gx)*h;
    
    norm = sqrtf(q0*q0+q1*q1+q2*q2+q3*q3);
    q0/=norm; q1/=norm; q2/=norm; q3/=norm;
}
```

### 4. 四元数深入

### 万向锁问题
```
欧拉角的万向锁:
  当 Pitch = ±90° 时:
  Roll 和 Yaw 退化为同一轴
  → 丢失一个自由度

四元数无万向锁:
  4 个参数表示 3 个自由度
  始终有冗余约束 (|q|=1)
```

### 四元数插值 (SLERP)
```
球面线性插值 (Slerp):
  用于两个姿态之间的平滑过渡

  q(t) = q0 × sin((1-t)θ)/sinθ + q1 × sin(tθ)/sinθ
  
  θ = acos(q0 · q1)  (两四元数夹角)
  t ∈ [0, 1]
```

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

1. 模块化设计，接口清晰
2. 充分的错误处理和边界检查
3. 编写可测试的代码

## 常见问题

### Q1: 互补滤波和 Mahony 有什么区别？

**A**: 互补滤波只用加速度计修正，实现简单；Mahony 支持磁力计、自适应增益、可估计零偏，适合完整 AHRS。

### Q2: 如何选择 kp 和 ki 参数？

**A**: kp 控制收敛速度 (典型 0.5-5.0)，ki 消除零偏 (典型 0.001-0.01)。从小值开始，逐渐增大观察响应。

## 总结

本文深入讲解了核心技术和实现方法：

- 掌握了关键算法的原理和实现
- 能够独立完成模块级开发
- 理解了工程实践中的优化技巧

下一步建议进入高级内容，学习系统级设计和生产级优化。

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

**下一步**：建议学习 [[imu/advanced/|高级内容]]
