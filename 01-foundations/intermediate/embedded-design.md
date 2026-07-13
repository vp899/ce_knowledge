---
title: "嵌入式系统设计"
tags: [embedded, intermediate, architecture, rtos, driver]
level: intermediate
module: "01-foundations"
---

# 嵌入式系统设计

## 概述

嵌入式系统设计需要综合考虑硬件、软件、实时性和可靠性。本文介绍嵌入式系统架构设计、RTOS 原理、驱动框架和调试方法。

完成本文学习后，你将能够：

- 设计模块化的嵌入式软件架构
- 理解 RTOS 的任务调度和同步机制
- 掌握常见外设驱动的设计方法
- 使用调试工具定位嵌入式问题

## 背景知识

### 前置知识

- 完成初级内容（电子基础、C 语言、Linux 基础）
- 了解 MCU 基本外设（GPIO/UART/SPI/I2C）

### 学习建议

- 结合具体 MCU 平台学习（推荐 STM32）
- 理解原理后动手实现
- 学会阅读数据手册和参考手册

## 核心内容

### 1. 嵌入式软件架构

```
分层架构:

┌─────────────────────────────────┐
│         应用层 (Application)     │  业务逻辑
├─────────────────────────────────┤
│         中间件 (Middleware)      │  协议栈/算法/框架
├─────────────────────────────────┤
│         OS 抽象层 (OSAL)         │  RTOS API 封装
├─────────────────────────────────┤
│         驱动层 (Driver)          │  硬件驱动
├─────────────────────────────────┤
│         HAL (硬件抽象层)         │  寄存器操作
├─────────────────────────────────┤
│         硬件 (Hardware)          │  MCU + 外设
└─────────────────────────────────┘

优点:
├── 各层独立，便于测试和移植
├── 硬件变更只需修改 HAL/驱动
├── 应用逻辑与硬件解耦
└── 便于团队分工协作
```

### 2. 状态机设计

```c
// 状态机是嵌入式最常用的设计模式

typedef enum {
    STATE_IDLE,
    STATE_RUNNING,
    STATE_ERROR,
    STATE_RECOVERY,
} SystemState_t;

typedef enum {
    EVENT_START,
    EVENT_STOP,
    EVENT_ERROR,
    EVENT_TIMEOUT,
} SystemEvent_t;

typedef SystemState_t (*StateHandler)(SystemEvent_t event);

// 状态处理函数
SystemState_t handle_idle(SystemEvent_t event) {
    switch (event) {
    case EVENT_START: return STATE_RUNNING;
    case EVENT_ERROR: return STATE_ERROR;
    default: return STATE_IDLE;
    }
}

SystemState_t handle_running(SystemEvent_t event) {
    switch (event) {
    case EVENT_STOP:  return STATE_IDLE;
    case EVENT_ERROR: return STATE_ERROR;
    case EVENT_TIMEOUT: return STATE_RECOVERY;
    default: return STATE_RUNNING;
    }
}

// 状态机表
StateHandler state_table[] = {
    handle_idle,
    handle_running,
    handle_error,
    handle_recovery,
};

// 状态机运行
void state_machine_run(SystemEvent_t event) {
    static SystemState_t current_state = STATE_IDLE;
    current_state = state_table[current_state](event);
}
```

### 3. 驱动设计模式

```c
// 驱动接口定义 (面向对象思想)
typedef struct {
    int  (*init)(void);
    int  (*read)(uint8_t *buf, uint16_t len);
    int  (*write)(const uint8_t *buf, uint16_t len);
    int  (*ioctl)(uint32_t cmd, void *arg);
    void (*deinit)(void);
} DriverOps_t;

// 驱动注册
typedef struct {
    const char *name;
    const DriverOps_t *ops;
    void *priv_data;
} Device_t;

// 使用示例
static const DriverOps_t uart_ops = {
    .init = uart_init,
    .read = uart_read,
    .write = uart_write,
    .ioctl = uart_ioctl,
    .deinit = uart_deinit,
};

static Device_t uart_device = {
    .name = "uart1",
    .ops = &uart_ops,
    .priv_data = NULL,
};

// 应用层调用
uart_device.ops->init();
uart_device.ops->write(data, len);
```

### 4. 中断设计

```c
// 中断处理最佳实践

// Top Half (硬中断): 快速处理，设置标志
volatile uint8_t data_ready = 0;
volatile uint8_t rx_buffer[256];
volatile uint16_t rx_count = 0;

void USART1_IRQHandler(void) {
    if (USART1->SR & USART_SR_RXNE) {
        rx_buffer[rx_count++] = USART1->DR;
        if (rx_count >= sizeof(rx_buffer)) {
            rx_count = 0;
        }
        data_ready = 1;
    }
}

// Bottom Half (主循环): 详细处理
void process_data(void) {
    if (data_ready) {
        data_ready = 0;
        // 处理 rx_buffer 中的数据
        for (uint16_t i = 0; i < rx_count; i++) {
            parse_byte(rx_buffer[i]);
        }
        rx_count = 0;
    }
}
```

## 实践示例

### 示例：模块化项目结构

```
project/
├── app/                    # 应用层
│   ├── main.c
│   ├── state_machine.c
│   └── protocol.c
├── middleware/             # 中间件
│   ├── ring_buffer.c
│   ├── pid_controller.c
│   └── filter.c
├── drivers/                # 驱动层
│   ├── uart.c
│   ├── spi.c
│   ├── i2c.c
│   └── gpio.c
├── hal/                    # HAL 层
│   ├── hal_uart.c
│   ├── hal_spi.c
│   └── hal_gpio.c
├── bsp/                    # 板级支持
│   ├── board.c
│   ├── clock.c
│   └── pin_mux.c
└── config/                 # 配置
    ├── FreeRTOSConfig.h
    └── board_config.h
```

## 深入理解

### 最佳实践

1. 中断处理尽量快，复杂逻辑放主循环
2. 使用互斥锁保护共享资源
3. 看门狗必须在主循环中喂狗
4. 关键数据用 CRC 校验
5. 串口通信使用环形缓冲区
6. 使用 static 限制变量作用域

## 常见问题

### Q1: 中断中为什么不能用 delay？

**A**: 中断中使用 delay 会阻塞其他中断，导致系统响应变差甚至死机。中断处理应该尽可能快，复杂操作放到主循环或任务中。

### Q2: 如何调试 HardFault？

**A**: 
1. 在 HardFault_Handler 中保存寄存器现场
2. 查看 SCB->CFSR 寄存器确定故障类型
3. 查看 LR 和 PC 寄存器定位故障地址
4. 使用调试器的 Call Stack 查看调用链

## 总结

本文涵盖了嵌入式系统设计的核心知识：

- 分层架构和模块化设计
- 状态机设计模式
- 驱动框架和接口设计
- 中断处理最佳实践

建议继续学习高级内容，掌握性能优化和可靠性设计。

## 延伸阅读

- [[stm32-basics|STM32 基础]] - MCU 入门
- [[freertos-drivers|FreeRTOS 基础]] - RTOS 入门
- [[linux-driver-dev|Linux 驱动开发]] - Linux 驱动

## 参考资料

1. 《嵌入式系统设计与实践》- Elecia White
2. 《Making Embedded Systems》- Elecia White
3. ARM Cortex-M 编程指南

---

**练习题**：

1. 设计一个简单的状态机，实现串口协议解析
2. 实现一个驱动框架，支持多个 UART 设备
3. 设计一个中断驱动的按键消抖方案

**下一步**：建议学习 [[freertos-drivers|FreeRTOS 基础]]
