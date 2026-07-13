level: beginner
---
title: "可靠性统计算法详解"
tags: [reliability, weibull, mtbf, arrhenius, acceleration, algorithm]
module: "10-reliability"
---

# 可靠性统计算法详解

## 概述

可靠性算法量化产品寿命。本文涵盖威布尔分布、Arrhenius 加速模型和 MTBF 预测。

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

### 1. 威布尔分布 (Weibull Distribution)

### 威布尔模型
```
累积失效概率:
  F(t) = 1 - exp(-(t/η)^β)

  t = 时间
  η = 尺度参数 (特征寿命, 63.2% 失效时间)
  β = 形状参数 (失效率变化趋势)

失效率函数:
  λ(t) = (β/η) · (t/η)^(β-1)

  β < 1: 失效率递减 (早期失效, 浴盆曲线左侧)
  β = 1: 失效率恒定 (随机失效, 指数分布)
  β > 1: 失效率递增 (磨损失效, 浴盆曲线右侧)

可靠性函数:
  R(t) = exp(-(t/η)^β)

MTBF (平均故障间隔):
  MTBF = η · Γ(1 + 1/β)

B10 寿命 (10% 失效时间):
  B10 = η · (-ln(0.9))^(1/β)
```

### 威布尔参数估计
```python
import numpy as np
from scipy import stats
from scipy.special import gamma as gamma_func

def weibull_mle(failure_times):
    """最大似然估计威布尔参数"""
    n = len(failure_times)
    t = np.array(failure_times)
    
    # 对数似然函数
    def neg_log_likelihood(params):
        beta, eta = params
        if beta <= 0 or eta <= 0:
            return 1e10
        ll = n * np.log(beta/eta) + (beta-1) * np.sum(np.log(t/eta)) - np.sum((t/eta)**beta)
        return -ll
    
    # 优化求解
    from scipy.optimize import minimize
    result = minimize(neg_log_likelihood, [2.0, np.mean(t)], method='Nelder-Mead')
    beta, eta = result.x
    
    return beta, eta

def weibull_rank_regression(failure_times):
    """秩回归法 (中位秩)"""
    t = np.sort(failure_times)
    n = len(t)
    
    # 中位秩
    F = (np.arange(1, n+1) - 0.3) / (n + 0.4)
    
    # 线性回归: ln(-ln(1-F)) = β·ln(t) - β·ln(η)
    x = np.log(t)
    y = np.log(-np.log(1 - F))
    
    slope, intercept, r, p, se = stats.linregress(x, y)
    
    beta = slope
    eta = np.exp(-intercept / beta)
    
    return beta, eta, r**2

# 使用示例
failure_times = [100, 250, 420, 580, 710, 950]
beta, eta, r2 = weibull_rank_regression(failure_times)
print(f"β = {beta:.2f}, η = {eta:.0f}h, R² = {r2:.4f}")
print(f"MTBF = {eta * gamma_func(1 + 1/beta):.0f}h")
print(f"B10 = {eta * (-np.log(0.9))**(1/beta):.0f}h")
```

### 2. Arrhenius 加速模型

### 加速因子计算
```
Arrhenius 模型:
  失效率 λ = A · exp(-Ea / (k·T))

  A = 常数
  Ea = 活化能 (eV), 典型 0.3-1.0 eV
  k = 玻尔兹曼常数 (8.617×10⁻⁵ eV/K)
  T = 绝对温度 (K)

加速因子:
  AF = λ_test / λ_use = exp[(Ea/k) · (1/T_use - 1/T_test)]

示例:
  使用温度: 25°C (298K)
  测试温度: 85°C (358K)
  活化能: 0.7 eV

  AF = exp[(0.7/8.617e-5) · (1/298 - 1/358)]
     = exp[8122 · 0.000564]
     = exp[4.58]
     = 97.5

  含义: 85°C 测试 1 小时 ≈ 25°C 使用 97.5 小时
```

### 多应力加速
```
Arrhenius + 湿度 + 电压:

  AF = AF_temp × AF_humidity × AF_voltage

  AF_temp = exp[(Ea/k) · (1/T_use - 1/T_test)]
  AF_humidity = (RH_test/RH_use)^n    (n ≈ 2-3)
  AF_voltage = (V_test/V_use)^m       (m ≈ 1-2)

HALT (高加速寿命测试):
  温度: 极端温度循环 (-60°C ~ 150°C)
  振动: 逐步增加直到失效
  电压: 超压/欠压
  → 快速发现设计薄弱点
```

### 3. MTBF 预测

### 元器件计数法
```
系统 MTBF 预测 (MIL-HDBK-217F):

  λ_system = Σ (N_i × λ_i × π_i)

  N_i = 第 i 种元器件数量
  λ_i = 基本失效率 (查表)
  π_i = 环境因子 (地面/车载/航空/航天)

典型失效率 (FIT = failures per 10⁹ hours):
  电阻:     1-10 FIT
  电容:     5-50 FIT
  IC:       10-100 FIT
  连接器:   1-10 FIT
  焊点:     0.1-1 FIT
  晶振:     5-20 FIT

MTBF = 10⁹ / λ_system (小时)

示例 (飞控板):
  MCU:      1 × 50 FIT = 50
  IMU:      2 × 30 FIT = 60
  电阻:     100 × 2 FIT = 200
  电容:     50 × 10 FIT = 500
  连接器:   10 × 5 FIT = 50
  焊点:     500 × 0.5 FIT = 250
  ─────────────────────────
  总计:     1110 FIT
  
  MTBF = 10⁹ / 1110 ≈ 900,900h ≈ 103 年
```

---

### 相关链接

- [[env-testing|环境测试]] — 测试标准
- [[mechanical-testing|机械测试]] — 机械可靠性
- [[product-design|产品设计]] — 可靠性设计

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
