---
title: "ESC 高级 - 无感控制"
tags: [esc, advanced, sensorless, bemf, observer]
level: advanced
---

# 无感 FOC 控制

## 概述

无感控制省去传感器。本文涵盖滑模观测器、高频注入和启动策略。

完成本文学习后，你将能够：

- 能够实现无感 FOC 和滑模观测器
- 掌握高频注入低速控制
- 能够进行电机参数辨识和自适应控制

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

### 1. 无感控制原理

```
有感 vs 无感:
├── 有感: 编码器/霍尔传感器测量转子位置
├── 无感: 通过反电动势/观测器估算转子位置
└── 无感优势: 成本低, 可靠性高, 无传感器故障

反电动势 (BEMF):
  电机旋转时, 线圈切割磁力线产生反电动势
  BEMF = Ke × ω (Ke: 反电动势常数, ω: 角速度)

  低速: BEMF 弱, 难以检测
  高速: BEMF 强, 容易检测
```

### 2. 滑模观测器 (SMO)

```c
// 滑模观测器估算反电动势
typedef struct {
    float alpha_est, beta_est;  // 电流估计值
    float bemf_alpha, bemf_beta; // 反电动势估计
    float Ls;   // 电感
    float Rs;   // 电阻
    float k;    // 滑模增益
    float dt;
} SMO;

void smo_update(SMO *smo,
                 float ialpha, float ibeta,
                 float valpha, float vbeta) {
    // 电流估计误差
    float err_alpha = smo->alpha_est - ialpha;
    float err_beta = smo->beta_est - ibeta;
    
    // 滑模切换函数 (sigmoid)
    float sw_alpha = smo->k * err_alpha / (fabsf(err_alpha) + 0.01f);
    float sw_beta = smo->k * err_beta / (fabsf(err_beta) + 0.01f);
    
    // 电流观测器
    float dialpha = (valpha - smo->Rs*ialpha - smo->bemf_alpha
                     - sw_alpha) / smo->Ls;
    float dibeta = (vbeta - smo->Rs*ibeta - smo->bemf_beta
                    - sw_beta) / smo->Ls;
    
    smo->alpha_est += dialpha * smo->dt;
    smo->beta_est += dibeta * smo->dt;
    
    // 反电动势估计 (低通滤波滑模输出)
    float fc = 500.0f;  // 截止频率
    float alpha = smo->dt * 2 * 3.14159f * fc;
    smo->bemf_alpha += alpha * (sw_alpha - smo->bemf_alpha);
    smo->bemf_beta += alpha * (sw_beta - smo->bemf_beta);
}

// 从反电动势估算电角度
float smo_get_angle(SMO *smo) {
    return atan2f(-smo->bemf_alpha, smo->bemf_beta);
}

// 从反电动势估算转速
float smo_get_speed(SMO *smo) {
    float bemf_mag = sqrtf(smo->bemf_alpha*smo->bemf_alpha +
                           smo->bemf_beta*smo->bemf_beta);
    return bemf_mag / Ke;  // Ke: 反电动势常数
}
```

### 3. 高频注入 (低速无感)

```
高频注入原理:
  低速时 BEMF 弱, 无法检测位置
  → 注入高频信号, 利用凸极效应估算位置

  注入信号: vhf = Vh × sin(ωh·t) 沿 d 轴
  响应信号: ih 包含转子位置信息

  对于表贴式电机 (隐极): 不适用
  对于内嵌式电机 (凸极): 可以使用

实现:
  1. 在 d 轴注入高频电压 (500Hz~2kHz)
  2. 测量高频电流响应
  3. 带通滤波提取高频分量
  4. 解调得到转子位置

适用: 零速到中速 (0~10% 额定转速)
```

### 4. 启动策略

```c
// 无感电机启动 (开环→闭环切换)
typedef struct {
    int state;
    float freq;       // 开环频率
    float target_freq; // 目标频率
    float ramp_rate;   // 加速率
} StartupCtrl;

void startup_process(StartupCtrl *ctrl, SMO *smo,
                      float *valpha, float *vbeta) {
    switch(ctrl->state) {
    case 0: // 对齐: 固定角度, 建立初始位置
        *valpha = 1.0f; *vbeta = 0;
        ctrl->state = 1;
        break;
        
    case 1: // 开环加速
        ctrl->freq += ctrl->ramp_rate;
        *valpha = cosf(ctrl->freq);
        *vbeta = sinf(ctrl->freq);
        
        // 检测是否可以切换到闭环
        float speed = smo_get_speed(smo);
        if(speed > 0.1f * ctrl->target_freq) {
            ctrl->state = 2;  // 切换到闭环
        }
        break;
        
    case 2: // 闭环运行 (无感 FOC)
        // 使用 SMO 估算的角度
        // 正常 FOC 控制流程
        break;
    }
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

### Q1: 如何保证生产一致性？

**A**: 建立校准流程 (每台设备校准)；使用统计过程控制 (SPC)；自动化测试覆盖关键参数；建立来料检验标准。

### Q2: 如何处理边界情况？

**A**: 使用看门狗防止死机；实现故障检测和恢复机制；记录崩溃日志用于分析；进行长时间压力测试。

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
