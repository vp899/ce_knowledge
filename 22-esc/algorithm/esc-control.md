---
title: "动力电调 (ESC)"
aliases:
  - "ESC 控制"
  - "无刷电调"
tags:
  - esc
  - bldc
  - foc
  - dshot
module: "22-esc"
status: active
---

# 动力电调 (ESC)

## 1. 无刷电机原理

### BLDC 电机结构
```
无刷直流电机 (BLDC) 结构:

外转子 (旋转):
┌─────────────────────┐
│  N  S  N  S  N  S   │  ← 永磁体 (磁极对)
│  ┌───────────────┐  │
│  │               │  │
│  │   定子线圈     │  │
│  │   (绕组)       │  │
│  │               │  │
│  └───────────────┘  │
└─────────────────────┘

定子 (固定):
├── 铁芯: 硅钢片叠压
├── 绕组: 三相 (A/B/C)
├── 星形接法 (Y) 或三角形接法 (Δ)
└── 霍尔传感器 (有感) 或反电动势检测 (无感)

磁极对数 (Pole Pairs):
├── 7 对极: 常见于小型电机
├── 12 对极: 常见于中型电机
├── 14 对极: 常见于大型电机
└── 电气周期 = 机械周期 × 极对数
```

### 电机参数
```
KV 值 (RPM/V):
├── 定义: 每伏特电压的空载转速
├── KV = RPM / V
├── 低 KV: 大扭矩, 低转速, 大桨
├── 高 KV: 小扭矩, 高转速, 小桨
└── 示例:
    ├── 100KV: 大型载重, 15-17寸桨
    ├── 300KV: 中型航拍, 10-12寸桨
    ├── 700KV: 竞速, 7-8寸桨
    ├── 1000KV: 穿越机, 5寸桨
    └── 2500KV: 微型, 3寸桨

其他关键参数:
├── 额定电压: 3S-12S (11.1V-50.4V)
├── 额定电流: 10A-100A
├── 最大功率: 100W-5000W
├── 内阻: 10-200mΩ
├── 重量: 20g-500g
└── 推力: 0.5kg-30kg (单电机)

电机选型流程:
1. 确定飞行器重量和推重比
2. 计算单电机所需推力
3. 选择合适 KV 值
4. 匹配桨叶尺寸
5. 确定电调电流等级
```

## 2. ESC 硬件设计

### ESC 拓扑结构
```
三相全桥逆变器:

        VCC (电池)
         │
    ┌────┼────┬────┐
    │    │    │    │
   Q1   Q3   Q5    │  ← 高侧 MOSFET (P-MOS 或 N-MOS)
    │    │    │    │
    ├─A──┼─B──┼─C──┤  ← 三相输出到电机
    │    │    │    │
   Q2   Q4   Q6    │  ← 低侧 MOSFET (N-MOS)
    │    │    │    │
    └────┼────┴────┘
         │
        GND

MOSFET 选型:
├── 电压等级: >电池电压×1.5
├── 电流等级: >最大电流×2
├── 导通电阻 (Rds_on): <1mΩ (大电流)
├── 栅极电荷 (Qg): 影响开关速度
└── 封装: DFN5x6, SO-8, TO-220

栅极驱动:
├── 高压侧: 需要自举电路或电荷泵
├── 低压侧: 直接驱动
├── 驱动电流: 1-3A (快速开关)
├── 死区时间: 50-200ns (防止直通)
└── 隔离: 光耦或磁隔离 (高压应用)

电流采样:
├── 分流器 (Shunt): 精度高, 成本低
├── 霍尔传感器: 无损, 精度中
├── 运放: 放大分流器信号
└── ADC: 12-bit, 同步采样
```

### 典型 ESC 电路
```
小功率 ESC (5A-30A):
├── MCU: STM32F051 / GD32E230
├── MOSFET: 内置 N-MOS (半桥集成)
├── 电流采样: 单分流器
├── 电压: 3S-6S (11.1V-22.2V)
└── 通信: PWM / DShot

中功率 ESC (30A-80A):
├── MCU: STM32G071 / AT32F421
├── MOSFET: 独立 N-MOS (并联)
├── 电流采样: 双分流器
├── 电压: 4S-8S (14.8V-33.6V)
└── 通信: DShot / CAN

大功率 ESC (80A-200A):
├── MCU: STM32G474 / STM32H743
├── MOSFET: 大封装, 多并联
├── 电流采样: 三相分流器
├── 电压: 6S-14S (22.2V-58.8V)
└── 通信: CAN (DroneCAN/Cyphal)
```

## 3. ESC 通信协议

### PWM 协议
```
标准 PWM:
├── 频率: 50Hz (20ms 周期)
├── 脉宽: 1000μs (停转) ~ 2000μs (全速)
├── 分辨率: 1000 级
├── 延迟: 20ms (一个周期)
└── 特点: 兼容性好, 延迟高

Oneshot125:
├── 频率: 与飞控同步
├── 脉宽: 125μs (停转) ~ 250μs (全速)
├── 分辨率: 1000 级
├── 延迟: <1ms
└── 特点: 低延迟

DShot:
├── DShot300: 300kbit/s
├── DShot600: 600kbit/s (常用)
├── DShot1200: 1200kbit/s
├── 帧格式: 11-bit 油门 + 1-bit 遥测 + 4-bit CRC
├── 分辨率: 2048 级
├── 延迟: <100μs
├── 无需校准
└── 支持双向 (DShot Bidir) - 回传转速

DShot 帧格式:
┌────────────────────────────────────────┐
│  11-bit 油门  │ 1-bit 遥测 │ 4-bit CRC │
│  (0-2047)     │ (请求遥测)  │           │
└────────────────────────────────────────┘

DShot 编码:
├── 0: 高电平 37.5%, 低电平 62.5%
├── 1: 高电平 75%, 低电平 25%
└── 每位 1.67μs (DShot600)
```

### BLHeli 协议
```
BLHeli_S:
├── 基于 PWM/DShot
├── 固件预置
├── 参数: 启动功率、方向、刹车等
└── 通过 BLHeliSuite 配置

BLHeli_32:
├── 32-bit MCU
├── 支持 DShot 双向
├── 支持转速回传
├── 高级功能:
│   ├── 电机刹车
│   ├── 启动功率调节
│   ├── 温度保护
│   ├── 电流限制
│   └── LED 控制
└── 通过 BLHeliSuite32 配置

DroneCAN (UAVCAN):
├── CAN 总线通信
├── 高可靠性
├── 支持遥测回传:
│   ├── 电压
│   ├── 电流
│   ├── 温度
│   ├── 转速
│   └── 累计电量
├── 支持参数配置
└── 适用于高端应用
```

## 4. BLDC 控制算法

### 六步换向 (Block Commutation)
```
六步换向序列 (有感/无感):

步骤  | A相  | B相  | C相  | 导通相
------|------|------|------|--------
1     | H    | L    | Z    | A→B
2     | H    | Z    | L    | A→C
3     | Z    | H    | L    | B→C
4     | L    | H    | Z    | B→A
5     | L    | Z    | H    | C→A
6     | Z    | L    | H    | C→B

H = 高侧导通, L = 低侧导通, Z = 悬空 (检测反电动势)

无感检测:
├── 悬空相检测反电动势过零点
├── 过零点后 30° 换向
├── 低速时反电动势弱，需要开环启动
└── 高速时反电动势强，检测容易

开环启动流程:
1. 对齐: 固定换相，让转子对齐到已知位置
2. 启动: 逐步加速换相频率
3. 切换: 速度足够后切换到闭环
```

### [[gimbal-control|FOC]] 控制 (详细)
```c
/* esc_foc.c */

/* FOC 状态 */
typedef struct {
    // 电流采样
    float ia, ib, ic;           // 三相电流
    float i_alpha, i_beta;      // α-β 轴电流
    float id, iq;               // d-q 轴电流
    
    // 设定值
    float id_ref;               // d 轴电流参考 (通常=0)
    float iq_ref;               // q 轴电流参考 (控制扭矩)
    
    // 电压输出
    float vd, vq;               // d-q 轴电压
    float v_alpha, v_beta;      // α-β 轴电压
    float va, vb, vc;           // 三相电压
    
    // 角度
    float theta;                // 电角度 (弧度)
    float speed;                // 电角速度 (rad/s)
    
    // PID 控制器
    PID id_pid;
    PID iq_pid;
    
    // 参数
    float rs;                   // 定子电阻
    float ls;                   // 定子电感
    float flux;                 // 永磁体磁链
    float pole_pairs;           // 极对数
} FOC_State;

/* FOC 主循环 (10-40kHz) */
void foc_update(FOC_State *foc, float vbus) {
    // 1. 电流采样
    sample_currents(&foc->ia, &foc->ib, &foc->ic);
    
    // 2. Clark 变换
    clarke_transform(foc->ia, foc->ib, foc->ic,
                      &foc->i_alpha, &foc->i_beta);
    
    // 3. Park 变换
    park_transform(foc->i_alpha, foc->i_beta, foc->theta,
                    &foc->id, &foc->iq);
    
    // 4. d 轴电流控制 (id = 0 策略)
    foc->vd = pid_update(&foc->id_pid, foc->id_ref - foc->id);
    
    // 5. q 轴电流控制 (扭矩控制)
    foc->vq = pid_update(&foc->iq_pid, foc->iq_ref - foc->iq);
    
    // 6. 反 Park 变换
    inv_park_transform(foc->vd, foc->vq, foc->theta,
                        &foc->v_alpha, &foc->v_beta);
    
    // 7. SVPWM
    svpwm(foc->v_alpha, foc->v_beta, vbus,
          &foc->va, &foc->vb, &foc->vc);
    
    // 8. 输出到 MOSFET
    set_pwm_duty(foc->va, foc->vb, foc->vc);
}

/* MTPA (最大扭矩电流比) 控制 */
void mtpa_control(FOC_State *foc, float torque_ref) {
    // MTPA: 在给定扭矩下，使电流最小
    // 对于表贴式电机: id = 0, iq = torque / (1.5 * pole_pairs * flux)
    
    foc->id_ref = 0;
    foc->iq_ref = torque_ref / (1.5f * foc->pole_pairs * foc->flux);
}

/* 弱磁控制 (高速运行) */
void field_weakening(FOC_State *foc, float speed_ref) {
    float max_voltage = foc->vbus / SQRT3;
    float back_emf = foc->flux * foc->speed;
    
    if (back_emf > max_voltage * 0.9f) {
        // 需要弱磁
        // 注入负 id 电流，削弱磁场
        float voltage_margin = max_voltage - back_emf;
        foc->id_ref = -foc->ls * voltage_margin / (foc->rs * DT);
        foc->id_ref = CLAMP(foc->id_ref, -foc->rated_current, 0);
    }
}
```

## 5. 电机保护

### ESC 保护功能
```
过流保护:
├── 硬件: 比较器快速响应 (<1μs)
├── 软件: ADC 采样限流
├── 阈值: 额定电流 × 1.5
└── 动作: 限制占空比或关闭输出

过温保护:
├── NTC 热敏电阻测量温度
├── 温度阈值: 80-100°C
├── 动作: 降功率或停机
└── 恢复: 温度降低后自动恢复

欠压保护:
├── 电池电压过低
├── 阈值: 3.0-3.3V/单体
├── 动作: 限制最大油门
└── 防止电池过放

堵转保护:
├── 检测: 电流大但无转速
├── 时间: 持续 1-3 秒
├── 动作: 关闭输出，等待重试
└── 防止电机和 ESC 过热

失步保护:
├── 检测: 转速突变或不稳定
├── 原因: 过载、过速、振动
├── 动作: 重新启动或降速
└── 恢复: 自动重新同步
```
---

## 相关链接

- [[flight-controller-firmware|飞控]]
- [[gimbal-control|云台]]
