---
title: "嵌入式系统高级设计"
tags: [embedded, advanced, optimization, reliability, production]
level: advanced
module: "01-foundations"
---

# 嵌入式系统高级设计

## 概述

产品级嵌入式系统需要考虑性能优化、可靠性设计、低功耗和可维护性。本文介绍生产级嵌入式系统的设计方法和最佳实践。

完成本文学习后，你将能够：

- 进行嵌入式系统性能分析和优化
- 设计可靠的故障检测和恢复机制
- 实现低功耗管理策略
- 掌握生产级代码规范和测试方法

## 背景知识

### 前置知识

- 完成中级内容（嵌入式系统设计）
- 有实际项目开发经验

### 学习建议

- 结合实际项目需求学习
- 关注可靠性和可维护性
- 阅读开源项目源码（如 ArduPilot、Marlin）

## 核心内容

### 1. 性能优化

```c
// 优化策略

// 1. 查找表替代实时计算
// 慢: float y = sinf(x);
// 快: float y = sin_table[x >> 8];  // 预计算 256 点

// 2. 定点数替代浮点数
// 慢: float value = 3.14f * sensor_data;
// 快: int32_t value = (314 * sensor_data) / 100;

// 3. DMA 替代 CPU 搬运
// 慢: for(i=0; i<len; i++) buf[i] = SPI->DR;
// 快: DMA_transfer(SPI, buf, len);

// 4. 内联函数减少调用开销
static inline uint16_t swap_bytes(uint16_t val) {
    return (val >> 8) | (val << 8);
}

// 5. 编译器优化
// -O2 优化级别
// __attribute__((optimize("O2"))) 单函数优化
```

### 2. 可靠性设计

```c
// 看门狗
void watchdog_init(void) {
    IWDG->KR = 0x5555;      // 允许写入
    IWDG->PR = 4;           // 分频 64
    IWDG->RLR = 625;        // 超时 1s
    IWDG->KR = 0xCCCC;      // 启动看门狗
}

void watchdog_feed(void) {
    IWDG->KR = 0xAAAA;      // 喂狗
}

// 故障检测
typedef struct {
    uint32_t error_code;
    uint32_t timestamp;
    uint32_t count;
} ErrorRecord_t;

void record_error(uint32_t code) {
    ErrorRecord_t record = {
        .error_code = code,
        .timestamp = get_tick(),
        .count = error_count[code]++,
    };
    flash_write(ERROR_LOG_ADDR, &record, sizeof(record));
}

// 自恢复机制
void system_recovery(void) {
    // 1. 保存关键数据
    save_critical_data();
    
    // 2. 关闭外设
    deinit_peripherals();
    
    // 3. 重置到已知状态
    NVIC_SystemReset();
}
```

### 3. 低功耗设计

```c
// 功耗模式管理
typedef enum {
    POWER_MODE_RUN,       // 全速运行
    POWER_MODE_IDLE,      // 空闲 (CPU 停, 外设运行)
    POWER_MODE_SLEEP,     // 睡眠 (仅唤醒源工作)
    POWER_MODE_DEEPSLEEP, // 深度睡眠 (RAM 保持)
    POWER_MODE_OFF,       // 关机
} PowerMode_t;

void enter_sleep_mode(void) {
    // 配置唤醒源
    configure_wakeup_pin();
    configure_rtc_alarm();
    
    // 关闭不需要的外设
    disable_unused_peripherals();
    
    // 进入睡眠
    SCB->SCR |= SCB_SCR_SLEEPDEEP_Msk;
    __WFI();  // Wait For Interrupt
}

// 功耗预算
// 运行: 50mA
// 睡眠: 10μA
// 电池: 1000mAh
// 运行续航: 1000/50 = 20h
// 睡眠续航: 1000/0.01 = 100000h ≈ 11年
```

### 4. 代码规范

```c
// 命名规范
// 变量: 小写+下划线
uint16_t sensor_value;
float target_temperature;

// 函数: 模块_动词_名词
void sensor_init(void);
int sensor_read(SensorData_t *data);
float pid_calculate(PID_t *pid, float error);

// 宏: 大写+下划线
#define MAX_BUFFER_SIZE  256
#define SENSOR_SAMPLE_RATE 100

// 类型: 驼峰+后缀
typedef struct {
    float kp, ki, kd;
    float integral;
} PID_Controller_t;

// 错误处理
int function_that_can_fail(void) {
    int ret;
    
    ret = step1();
    if (ret != 0) goto error_step1;
    
    ret = step2();
    if (ret != 0) goto error_step2;
    
    return 0;

error_step2:
    undo_step1();
error_step1:
    return ret;
}
```

## 实践示例

### 示例：生产级主循环

```c
// 带看门狗和错误处理的主循环
int main(void) {
    // 系统初始化
    system_init();
    watchdog_init();
    
    // 自检
    if (self_test() != 0) {
        enter_safe_mode();
    }
    
    // 主循环
    while (1) {
        watchdog_feed();
        
        // 周期性任务
        if (tick_1ms()) {
            sensor_process();
        }
        
        if (tick_10ms()) {
            control_process();
            communication_process();
        }
        
        if (tick_100ms()) {
            monitor_process();
            log_process();
        }
        
        if (tick_1s()) {
            health_check();
            power_management();
        }
        
        // 空闲时进入低功耗
        enter_idle_mode();
    }
}
```

## 深入理解

### 最佳实践

1. 每个函数只做一件事，函数长度 < 50 行
2. 使用 assert 进行开发阶段检查
3. 关键路径代码要有注释说明为什么
4. 版本号遵循语义化版本 (SemVer)
5. 变更日志记录每次修改
6. 代码评审发现问题及时修复

## 常见问题

### Q1: 如何保证固件升级不砖？

**A**: 使用 A/B 分区，升级写入非活动分区，验证后切换。Bootloader 检查启动成功标志，失败自动回滚。配合看门狗，确保不会死机。

### Q2: Flash 写入寿命有限怎么办？

**A**: 
1. 使用磨损均衡算法
2. 减少不必要的写入
3. RAM 缓存 + 定时批量写入
4. 监控写入次数，提前预警

## 总结

本文涵盖了生产级嵌入式系统设计：

- 性能优化策略（查找表、定点数、DMA）
- 可靠性设计（看门狗、故障检测、自恢复）
- 低功耗管理（睡眠模式、唤醒源）
- 代码规范和最佳实践

这些知识是将原型产品推向量产的关键。

## 延伸阅读

- [[firmware-upgrade|固件升级]] - OTA 方案
- [[secure-boot-impl|安全启动]] - 安全设计
- [[env-testing|环境测试]] - 可靠性验证

## 参考资料

1. 《嵌入式系统设计与实践》- Elecia White
2. MISRA-C 编码规范
3. IEC 61508 功能安全标准

---

**练习题**：

1. 实现一个带看门狗保护的主循环框架
2. 设计一个简单的磨损均衡算法
3. 实现一个功耗管理系统，支持多种睡眠模式

**下一步**：建议学习 [[firmware-upgrade|固件升级方案]]
