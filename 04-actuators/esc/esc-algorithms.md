level: beginner
---
title: "ESC 控制算法详解"
tags: [esc, bldc, foc, svpwm, six-step, sensorless, algorithm]
module: "04-actuators"
---

# ESC 控制算法详解

## 概述

ESC 控制算法从六步换向到 FOC 的完整技术栈。本文涵盖 Clark/Park/SVPWM 推导、无感控制和 MTPA/弱磁策略。

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

### 1. 六步换向 (Block Commutation)

### 原理
```
BLDC 三相反电动势波形 (梯形波):

  A相:  ┌──┐  ┌──┐  ┌──┐
        │  │  │  │  │  │
   ─────┘  └──┘  └──┘  └─────

  B相:     ┌──┐  ┌──┐  ┌──┐
           │  │  │  │  │  │
   ────────┘  └──┘  └──┘  └─

  C相:  ───┐  ┌──┐  ┌──┐  ┌
           │  │  │  │  │  │
           └──┘  └──┘  └──┘

六步换向序列:
  Step 1: A+, B-  → C 相检测过零
  Step 2: A+, C-  → B 相检测过零
  Step 3: B+, C-  → A 相检测过零
  Step 4: B+, A-  → C 相检测过零
  Step 5: C+, A-  → B 相检测过零
  Step 6: C+, B-  → A 相检测过零
```

### 无感反电动势检测
```c
/* 反电动势过零检测 */

typedef struct {
    uint8_t step;           // 当前换向步 (0-5)
    uint32_t last_zc_time;  // 上次过零时间
    uint32_t comm_period;   // 换向周期
    uint32_t advance_time;  // 提前换向时间 (30° 电角度)
    bool running;
} BLDC_Sensorless;

// 反电动势检测 (ADC 中断中调用)
bool detect_back_emf_zero_cross(BLDC_Sensorless *bldc,
                                 float va, float vb, float vc,
                                 float vneutral) {
    float bemf;
    
    switch (bldc->step) {
    case 0: case 3:  // A 相悬空
        bemf = va - vneutral;
        break;
    case 1: case 4:  // B 相悬空
        bemf = vb - vneutral;
        break;
    case 2: case 5:  // C 相悬空
        bemf = vc - vneutral;
        break;
    }
    
    // 过零检测: 反电动势穿过中性点
    static float prev_bemf = 0;
    bool zc = (prev_bemf < 0 && bemf >= 0) || (prev_bemf >= 0 && bemf < 0);
    prev_bemf = bemf;
    
    if (zc) {
        uint32_t now = micros();
        bldc->comm_period = now - bldc->last_zc_time;
        bldc->last_zc_time = now;
        bldc->advance_time = bldc->comm_period / 6;  // 30° = 周期/12
        return true;
    }
    return false;
}

// 换向执行
void bldc_commutate(BLDC_Sensorless *bldc) {
    bldc->step = (bldc->step + 1) % 6;
    
    switch (bldc->step) {
    case 0: set_pwm(A_HIGH, B_LOW, C_FLOAT); break;
    case 1: set_pwm(A_HIGH, C_LOW, B_FLOAT); break;
    case 2: set_pwm(B_HIGH, C_LOW, A_FLOAT); break;
    case 3: set_pwm(B_HIGH, A_LOW, C_FLOAT); break;
    case 4: set_pwm(C_HIGH, A_LOW, B_FLOAT); break;
    case 5: set_pwm(C_HIGH, B_LOW, A_FLOAT); break;
    }
}
```

### 2. FOC (磁场定向控制)

### 坐标变换
```
Clark 变换 (三相→两相静止):
  iα = ia
  iβ = (ia + 2·ib) / √3

Park 变换 (两相静止→两相旋转):
  id =  iα·cosθ + iβ·sinθ
  iq = -iα·sinθ + iβ·cosθ

反 Park 变换:
  vα = vd·cosθ - vq·sinθ
  vβ = vd·sinθ + vq·cosθ

Clark 逆变换 (两相静止→三相):
  va = vα
  vb = (-vα + √3·vβ) / 2
  vc = (-vα - √3·vβ) / 2
```

### SVPWM (空间矢量脉宽调制)
```
基本电压矢量:
  V0 (000): 零矢量
  V1 (100): A+        → 0°
  V2 (110): A+,B+     → 60°
  V3 (010): B+        → 120°
  V4 (011): B+,C+     → 180°
  V5 (001): C+        → 240°
  V6 (101): A+,C+     → 300°
  V7 (111): 零矢量

扇区判断:
  U1 = vβ
  U2 = √3/2·vα - 1/2·vβ
  U3 = -√3/2·vα - 1/2·vβ

  A = (U1 > 0) ? 1 : 0
  B = (U2 > 0) ? 1 : 0
  C = (U3 > 0) ? 1 : 0
  sector = A + 2*B + 4*C    (1-6)

作用时间 (以扇区 1 为例):
  T1 = √3·Ts/Vdc·(√3/2·vα - 1/2·vβ)
  T2 = √3·Ts/Vdc·vβ
  T0 = Ts - T1 - T2

PWM 占空比:
  Ta = (Ts - T1 - T2) / 2    (A 相)
  Tb = Ta + T1                (B 相)
  Tc = Tb + T2                (C 相)
```

### FOC 完整实现
```c
/* foc_complete.c - FOC 完整实现 */

#define SQRT3       1.732050808f
#define SQRT3_BY_2  0.866025404f
#define ONE_BY_SQRT3 0.577350269f
#define TWO_BY_SQRT3 1.154700538f

typedef struct {
    // 电流采样
    float ia, ib, ic;
    float ialpha, ibeta;
    float id, iq;
    
    // 设定值
    float id_ref;       // d 轴参考 (通常=0)
    float iq_ref;       // q 轴参考 (扭矩)
    
    // 电压输出
    float vd, vq;
    float valpha, vbeta;
    float duty_a, duty_b, duty_c;
    
    // 角度
    float theta;        // 电角度 (rad)
    float speed;        // 电角速度 (rad/s)
    
    // PID
    float id_kp, id_ki;
    float iq_kp, iq_ki;
    float id_integral, iq_integral;
    
    // 参数
    float vbus;         // 母线电压
    float rs;           // 定子电阻
    float ls;           // 定子电感
    float flux;         // 永磁磁链
    int pole_pairs;     // 极对数
} FOC_Controller;

// Clark 变换
void clarke(float ia, float ib, float ic, float *ialpha, float *ibeta) {
    *ialpha = ia;
    *ibeta = (ia + 2.0f * ib) * ONE_BY_SQRT3;
}

// Park 变换
void park(float ialpha, float ibeta, float theta, float *id, float *iq) {
    float c = cosf(theta), s = sinf(theta);
    *id =  ialpha * c + ibeta * s;
    *iq = -ialpha * s + ibeta * c;
}

// 反 Park 变换
void inv_park(float vd, float vq, float theta, float *valpha, float *vbeta) {
    float c = cosf(theta), s = sinf(theta);
    *valpha = vd * c - vq * s;
    *vbeta  = vd * s + vq * c;
}

// SVPWM
void svpwm(float valpha, float vbeta, float vbus,
           float *duty_a, float *duty_b, float *duty_c) {
    float ts = 1.0f;  // 归一化到 1
    
    // 扇区判断
    float u1 = vbeta;
    float u2 = SQRT3_BY_2 * valpha - 0.5f * vbeta;
    float u3 = -SQRT3_BY_2 * valpha - 0.5f * vbeta;
    
    int sector = 0;
    if (u1 > 0) sector += 1;
    if (u2 > 0) sector += 2;
    if (u3 > 0) sector += 4;
    
    // 计算作用时间
    float t1, t2;
    float vdc_inv = 1.0f / vbus;
    
    switch (sector) {
    case 1: // 扇区 I
        t1 = SQRT3 * ts * vdc_inv * (SQRT3_BY_2 * valpha - 0.5f * vbeta);
        t2 = SQRT3 * ts * vdc_inv * vbeta;
        break;
    case 2: // 扇区 II
        t1 = SQRT3 * ts * vdc_inv * (-SQRT3_BY_2 * valpha + 0.5f * vbeta);
        t2 = SQRT3 * ts * vdc_inv * (SQRT3_BY_2 * valpha + 0.5f * vbeta);
        break;
    case 3: // 扇区 III
        t1 = SQRT3 * ts * vdc_inv * vbeta;
        t2 = SQRT3 * ts * vdc_inv * (-valpha);
        break;
    case 4: // 扇区 IV
        t1 = SQRT3 * ts * vdc_inv * (-SQRT3_BY_2 * valpha - 0.5f * vbeta);
        t2 = SQRT3 * ts * vdc_inv * (-vbeta);
        break;
    case 5: // 扇区 V
        t1 = SQRT3 * ts * vdc_inv * (valpha);
        t2 = SQRT3 * ts * vdc_inv * (-SQRT3_BY_2 * valpha - 0.5f * vbeta);
        break;
    case 6: // 扇区 VI
        t1 = SQRT3 * ts * vdc_inv * (-vbeta);
        t2 = SQRT3 * ts * vdc_inv * (SQRT3_BY_2 * valpha - 0.5f * vbeta);
        break;
    default:
        t1 = t2 = 0;
        break;
    }
    
    // 过调制处理
    if (t1 + t2 > ts) {
        float ratio = ts / (t1 + t2);
        t1 *= ratio;
        t2 *= ratio;
    }
    
    float t0 = ts - t1 - t2;
    
    // 零矢量均匀分配 (七段式)
    float ta, tb, tc;
    switch (sector) {
    case 1:  ta = t0/2;       tb = ta + t1;     tc = tb + t2;  break;
    case 2:  ta = t0/2 + t1;  tb = t0/2;        tc = ta + t2;  break;
    case 3:  ta = tb + t2;    tb = t0/2;        tc = t0/2 + t1; break;
    case 4:  ta = tb + t2;    tb = t0/2 + t1;   tc = t0/2;     break;
    case 5:  ta = t0/2 + t2;  tb = tc + t1;     tc = t0/2;     break;
    case 6:  ta = t0/2;       tb = tc + t1;     tc = t0/2 + t2; break;
    default: ta = tb = tc = 0; break;
    }
    
    *duty_a = ta / ts;
    *duty_b = tb / ts;
    *duty_c = tc / ts;
}

// FOC 主循环 (10kHz)
void foc_update(FOC_Controller *foc, float theta, float vbus) {
    foc->theta = theta;
    foc->vbus = vbus;
    
    // 1. 电流采样 (已在 ADC 中断中完成)
    
    // 2. Clark 变换
    clarke(foc->ia, foc->ib, foc->ic, &foc->ialpha, &foc->ibeta);
    
    // 3. Park 变换
    park(foc->ialpha, foc->ibeta, foc->theta, &foc->id, &foc->iq);
    
    // 4. d 轴 PI (id → 0)
    float id_err = foc->id_ref - foc->id;
    foc->id_integral += id_err * foc->id_ki;
    foc->id_integral = CLAMP(foc->id_integral, -vbus, vbus);
    foc->vd = foc->id_kp * id_err + foc->id_integral;
    
    // 5. q 轴 PI (扭矩控制)
    float iq_err = foc->iq_ref - foc->iq;
    foc->iq_integral += iq_err * foc->iq_ki;
    foc->iq_integral = CLAMP(foc->iq_integral, -vbus, vbus);
    foc->vq = foc->iq_kp * iq_err + foc->iq_integral;
    
    // 6. 电压限幅 (不超过六边形)
    float v_max = vbus / SQRT3;
    float v_mag = sqrtf(foc->vd*foc->vd + foc->vq*foc->vq);
    if (v_mag > v_max) {
        foc->vd *= v_max / v_mag;
        foc->vq *= v_max / v_mag;
    }
    
    // 7. 反 Park 变换
    inv_park(foc->vd, foc->vq, foc->theta, &foc->valpha, &foc->vbeta);
    
    // 8. SVPWM
    svpwm(foc->valpha, foc->vbeta, vbus,
          &foc->duty_a, &foc->duty_b, &foc->duty_c);
    
    // 9. 输出到 PWM
    set_pwm_duty(foc->duty_a, foc->duty_b, foc->duty_c);
}
```

### 3. MTPA 与弱磁控制

### MTPA (最大扭矩电流比)
```
目标: 在给定扭矩下, 使电流最小 (效率最高)

对于表贴式电机 (Ld ≈ Lq):
  id = 0
  iq = torque / (1.5 · p · ψ_m)

对于内嵌式电机 (Ld < Lq):
  id = ψ_m/(4·(Lq-Ld)) - sqrt((ψ_m/(4·(Lq-Ld)))² + iq²/2)
  iq = torque / (1.5 · p · (ψ_m + (Ld-Lq)·id))
```

### 弱磁控制
```
当反电动势接近母线电压时, 需要弱磁:

条件: sqrt(vd² + vq²) ≥ vbus/√3

方法: 注入负 id 电流, 削弱磁场

id_fw = (vbus/√3 - sqrt(vd²+vq²)) / (ω·Ls)

限制: id_fw ≥ -ψ_m/Ld  (最大弱磁电流)
```

---

### 相关链接

- [[bldc-motor|BLDC 电机]]
- [[flight-controller-firmware|飞控]]
- [[gimbal-control|云台]]

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
