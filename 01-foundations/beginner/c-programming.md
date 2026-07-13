---
title: "C 语言嵌入式编程基础"
tags: [c-programming, beginner, embedded, pointer, memory]
level: beginner
module: "01-foundations"
---

# C 语言嵌入式编程基础

## 概述

C 语言是嵌入式开发的首选语言，几乎所有 MCU/SoC 的驱动和固件都用 C 编写。本文介绍嵌入式 C 编程的核心知识，包括数据类型、指针、内存管理、位操作和中断编程。

完成本文学习后，你将能够：

- 理解 C 语言在嵌入式中的特殊用法
- 熟练使用指针访问硬件寄存器
- 掌握位操作进行寄存器配置
- 理解栈、堆、静态内存的区别

## 背景知识

### 前置知识

- 基本的 C 语言语法（变量、循环、函数）
- 了解编译和链接的概念

### 学习建议

- 在开发板上实际运行代码，观察行为
- 使用调试器单步执行，理解内存变化
- 嵌入式 C 和桌面 C 有很多不同，注意区分

## 核心内容

### 1. 嵌入式数据类型

```c
// 固定宽度整数 (stdint.h) - 嵌入式必须用
#include <stdint.h>

uint8_t   val8  = 255;        // 无符号 8 位 (0~255)
int8_t    sval8 = -128;       // 有符号 8 位 (-128~127)
uint16_t  val16 = 65535;      // 无符号 16 位
int16_t   sval16 = -32768;    // 有符号 16 位
uint32_t  val32 = 0xFFFFFFFF; // 无符号 32 位
int32_t   sval32 = -2147483648; // 有符号 32 位
uint64_t  val64 = 0;          // 无符号 64 位

// 不要在嵌入式中使用 int/long，宽度不固定！
// int 在 8 位 MCU 上是 16 位，在 32 位 MCU 上是 32 位

// 浮点数
float   f = 3.14f;   // 32 位浮点 (大多数 MCU 有硬件 FPU)
double  d = 3.14;    // 64 位浮点 (MCU 通常无硬件支持，很慢)
// 嵌入式尽量用 float，避免 double

// 布尔
#include <stdbool.h>
bool flag = true;     // 实际是 uint8_t
```

### 2. 指针与内存

```c
// 指针 = 存储内存地址的变量
int x = 42;
int *p = &x;    // p 指向 x 的地址
*p = 100;       // 通过指针修改 x 的值 → x = 100

// 指针类型决定了解引用时读取多少字节
uint8_t  *p8  = (uint8_t  *)0x20000000;  // 读 1 字节
uint16_t *p16 = (uint16_t *)0x20000000;  // 读 2 字节
uint32_t *p32 = (uint32_t *)0x20000000;  // 读 4 字节

// 函数指针 (回调函数)
void (*callback)(uint8_t event);

void register_callback(void (*cb)(uint8_t)) {
    callback = cb;
}

void trigger_event(uint8_t event) {
    if (callback) callback(event);
}
```

### 3. 内存布局

```
┌─────────────────────┐ 高地址
│       栈 (Stack)     │ ← 局部变量, 函数调用
│         ↓           │
│                     │
│         ↑           │
│       堆 (Heap)     │ ← malloc 动态分配
├─────────────────────┤
│    BSS (未初始化)    │ ← 全局变量 (初始为0)
├─────────────────────┤
│    Data (已初始化)   │ ← 全局变量 (有初始值)
├─────────────────────┤
│    Text (代码段)     │ ← 程序代码
└─────────────────────┘ 低地址

嵌入式注意事项:
├── 栈大小有限 (通常 1-8KB)
├── 避免递归 (栈溢出)
├── 避免大数组放在栈上
├── malloc 在嵌入式中慎用 (碎片化)
└── 用 static 替代全局变量 (减少 BSS)
```

### 4. 位操作

```c
// 位操作是嵌入式的核心技能

// 设置位 (置 1)
REG |= (1 << BIT_POS);

// 清除位 (置 0)
REG &= ~(1 << BIT_POS);

// 翻转位
REG ^= (1 << BIT_POS);

// 检查位
if (REG & (1 << BIT_POS)) {
    // 位为 1
}

// 多位操作
REG = (REG & ~MASK) | (VALUE << SHIFT);

// 实际例子: 配置 GPIO
// 设置 PA5 为输出模式
GPIOA->MODER &= ~(3 << (5 * 2));  // 清除 MODER5
GPIOA->MODER |= (1 << (5 * 2));   // 设置为 01 (输出)

// 设置 PA5 输出高电平
GPIOA->BSRR = (1 << 5);           // 置位

// 设置 PA5 输出低电平
GPIOA->BSRR = (1 << (5 + 16));    // 复位
```

### 5. volatile 关键字

```c
// 告诉编译器: 这个变量可能被硬件/中断修改，不要优化

// 错误 (编译器可能优化掉循环):
while (flag == 0) {
    // 等待 flag 被中断设置
}

// 正确:
while (volatile_flag == 0) {
    // 编译器每次都从内存读取
}

// 用于硬件寄存器:
volatile uint32_t *reg = (volatile uint32_t *)0x40021000;
*reg = 0x01;  // 确保写入操作不被优化掉

// 用于中断共享变量:
volatile uint8_t rx_flag = 0;

void USART1_IRQHandler(void) {
    rx_flag = 1;  // 中断中设置
}

int main(void) {
    while (1) {
        if (rx_flag) {  // 主循环中检查
            rx_flag = 0;
            process_data();
        }
    }
}
```

### 6. 结构体与对齐

```c
// 结构体用于组织相关数据
typedef struct {
    uint16_t x;         // 2 字节
    uint16_t y;         // 2 字节
    uint16_t z;         // 2 字节
    uint32_t timestamp; // 4 字节
    uint8_t  status;    // 1 字节
    // 编译器可能插入 1 字节填充 (对齐到 4 字节)
} __attribute__((packed)) SensorData_t;  // packed 取消填充

// packed 可能导致性能下降 (非对齐访问)
// 仅在需要精确内存布局时使用 (如协议解析)

// 位域 (节省内存)
typedef struct {
    uint8_t enable   : 1;  // 1 位
    uint8_t mode     : 2;  // 2 位
    uint8_t priority : 3;  // 3 位
    uint8_t reserved : 2;  // 2 位
} ConfigReg_t;
```

## 实践示例

### 示例1：寄存器操作

```c
// STM32 GPIO 配置
#include "stm32f4xx.h"

void led_init(void) {
    // 使能 GPIOA 时钟
    RCC->AHB1ENR |= RCC_AHB1ENR_GPIOAEN;
    
    // 配置 PA5 为输出模式
    GPIOA->MODER &= ~(3 << (5 * 2));   // 清除
    GPIOA->MODER |= (1 << (5 * 2));    // 输出模式
    
    // 配置推挽输出
    GPIOA->OTYPER &= ~(1 << 5);        // 推挽
    
    // 配置速度
    GPIOA->OSPEEDR &= ~(3 << (5 * 2));
    GPIOA->OSPEEDR |= (2 << (5 * 2));  // 高速
    
    // 无上下拉
    GPIOA->PUPDR &= ~(3 << (5 * 2));
}

void led_on(void) {
    GPIOA->BSRR = (1 << 5);    // 置位 → 高电平
}

void led_off(void) {
    GPIOA->BSRR = (1 << 21);   // 复位 → 低电平
}

void led_toggle(void) {
    GPIOA->ODR ^= (1 << 5);    // 翻转
}
```

**代码说明**：
- 第 4 行：使能 GPIOA 的时钟（不使能无法使用）
- 第 7-8 行：先清除再设置，避免影响其他位
- 第 17 行：BSRR 寄存器，低 16 位置位，高 16 位复位

### 示例2：环形缓冲区

```c
// 串口接收环形缓冲区
#define BUF_SIZE 256

typedef struct {
    uint8_t data[BUF_SIZE];
    volatile uint16_t head;  // 写入位置
    volatile uint16_t tail;  // 读取位置
} RingBuffer_t;

static RingBuffer_t rx_buf;

void ringbuf_init(RingBuffer_t *buf) {
    buf->head = 0;
    buf->tail = 0;
}

int ringbuf_put(RingBuffer_t *buf, uint8_t byte) {
    uint16_t next = (buf->head + 1) % BUF_SIZE;
    if (next == buf->tail) return -1;  // 满
    buf->data[buf->head] = byte;
    buf->head = next;
    return 0;
}

int ringbuf_get(RingBuffer_t *buf, uint8_t *byte) {
    if (buf->head == buf->tail) return -1;  // 空
    *byte = buf->data[buf->tail];
    buf->tail = (buf->tail + 1) % BUF_SIZE;
    return 0;
}

uint16_t ringbuf_count(RingBuffer_t *buf) {
    return (buf->head - buf->tail + BUF_SIZE) % BUF_SIZE;
}

// 使用: 中断接收
void USART1_IRQHandler(void) {
    if (USART1->SR & USART_SR_RXNE) {
        uint8_t byte = USART1->DR;
        ringbuf_put(&rx_buf, byte);
    }
}

// 使用: 主循环处理
void process_uart_data(void) {
    uint8_t byte;
    while (ringbuf_get(&rx_buf, &byte) == 0) {
        process_byte(byte);
    }
}
```

**代码说明**：
- 环形缓冲区是嵌入式中最常用的数据结构
- 用于中断和主循环之间的数据传递
- head/tail 用 volatile 修饰，因为会被中断修改
- 单生产者单消费者不需要锁

## 深入理解

### 原理分析

编译器优化可能导致意外行为：
```c
// 问题代码
uint8_t *reg = (uint8_t *)0x40000000;
while (*reg == 0) {
    // 等待寄存器变为非零
}
// 编译器可能优化为: 只读一次，然后死循环

// 正确代码
volatile uint8_t *reg = (volatile uint8_t *)0x40000000;
while (*reg == 0) {
    // 每次都从硬件读取
}
```

### 最佳实践

1. 始终使用 stdint.h 的固定宽度类型
2. 硬件寄存器必须用 volatile
3. 中断共享变量必须用 volatile
4. 避免在栈上分配大数组
5. 避免在中断中使用 malloc
6. 结构体用 packed 处理协议数据
7. 位操作用宏或内联函数封装

## 常见问题

### Q1: 为什么不能用 printf？

**A**: 标准库的 printf 需要操作系统支持（文件系统），嵌入式中需要重定向到串口：
```c
int fputc(int ch, FILE *f) {
    while (!(USART1->SR & USART_SR_TXE));
    USART1->DR = ch;
    return ch;
}
```

### Q2: 栈溢出怎么检测？

**A**: 方法一：在栈底部填充特定模式（如 0xDEADBEEF），定期检查是否被覆盖。方法二：使用 FreeRTOS 的 uxTaskGetStackHighWaterMark()。方法三：MPU 硬件保护。

## 总结

本文涵盖了嵌入式 C 编程的核心知识：

- 固定宽度数据类型的使用
- 指针和内存布局
- 位操作和寄存器访问
- volatile 关键字的重要性
- 环形缓冲区等实用数据结构

建议继续学习中级内容，掌握状态机和驱动框架。

## 延伸阅读

- [[stm32-basics|STM32 基础]] - MCU 入门
- [[freertos-drivers|FreeRTOS 基础]] - RTOS 入门
- [[linux-basics|Linux 基础]] - Linux 入门

## 参考资料

1. 《C Primer Plus》- Stephen Prata
2. 《嵌入式 C 编程》- Michael J. Pont
3. ARM Cortex-M 编程手册

---

**练习题**：

1. 编写函数，将一个 32 位整数的第 N 位置 1、清 0、取反
2. 实现一个容量为 64 字节的环形缓冲区，支持中断和主循环访问
3. 定义一个表示 UART 寄存器的结构体，使用位域

**下一步**：建议学习 [[stm32-basics|STM32 基础]]
