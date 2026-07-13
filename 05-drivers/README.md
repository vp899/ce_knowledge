# 05 - 驱动开发

## 模块概述

嵌入式 Linux 与 RTOS 设备驱动开发、BSP 移植与测试。

## 目录结构

```
05-drivers/
├── linux/          # Linux 内核驱动
├── rtos/           # RTOS 驱动 (FreeRTOS / RT-Thread)
├── bsp/            # Board Support Package
└── testing/        # 驱动测试与验证
```

## 核心知识领域

### 1. Linux 驱动开发

#### 驱动框架
```
用户空间:  应用程序
               │
          ┌────┴────┐
          │ VFS 层  │   (open/read/write/ioctl)
          └────┬────┘
               │
          ┌────┴────┐
          │ 驱动层  │   (file_operations / platform_driver)
          └────┬────┘
               │
          ┌────┴────┐
          │ 总线层  │   (I2C / SPI / USB / PCI)
          └────┬────┘
               │
          ┌────┴────┐
          │ 硬件层  │   (寄存器操作 / DMA / 中断)
          └─────────┘
```

#### 常用驱动类型
| 类型 | 子系统 | 示例 |
|------|--------|------|
| 字符设备 | misc / char | GPIO、LED、按键 |
| 块设备 | block | eMMC、Flash、SD |
| 网络设备 | net | WiFi、以太网、BLE |
| 输入设备 | input | 触摸屏、键盘、传感器 |
| 显示设备 | drm / fb | LCD、HDMI、MIPI DSI |
| 音频设备 | alsa / asoc | Codec、I2S、DMIC |
| 电源管理 | regulator / power | PMIC、充电IC |
| 传感器 | iio | 加速度计、陀螺仪、温湿度 |

#### 设备树 (Device Tree)
```dts
/* 示例：I2C 传感器节点 */
&i2c1 {
    status = "okay";
    clock-frequency = <400000>;

    sensor@68 {
        compatible = "vendor,sensor-name";
        reg = <0x68>;
        interrupt-parent = <&gpio1>;
        interrupts = <5 IRQ_TYPE_EDGE_FALLING>;
        vdd-supply = <&ldo3>;
        vddio-supply = <&ldo5>;
    };
};
```

### 2. RTOS 驱动开发

#### FreeRTOS vs RT-Thread
| 特性 | FreeRTOS | RT-Thread |
|------|----------|-----------|
| 内核 | 微内核 | 微内核 + 组件 |
| 生态 | AWS 联盟 | 国产社区活跃 |
| 驱动框架 | 需自建 | 设备框架完善 |
| 包管理 | 无 | Env 工具 |
| GUI | 无 | LVGL 集成 |
| 适用 | 简单任务 | 复杂 IoT |

### 3. BSP 移植

#### BSP 移植清单
- [ ] 启动代码（汇编初始化、C 运行环境）
- [ ] 时钟配置（PLL、分频、外设时钟）
- [ ] 内存配置（SRAM、SDRAM、Flash 映射）
- [ ] 中断控制器（NVIC 优先级配置）
- [ ] GPIO 配置（引脚复用、上下拉）
- [ ] 调试串口（UART printf 重定向）
- [ ] 定时器（SysTick、硬件定时器）
- [ ] DMA 控制器配置
- [ ] 电源管理（低功耗模式）

### 4. 驱动测试

#### 测试层次
```
Level 1: 单元测试 (单个函数/模块)
Level 2: 集成测试 (驱动 + 硬件)
Level 3: 压力测试 (并发、高频调用)
Level 4: 异常测试 (错误注入、边界条件)
Level 5: 长稳测试 (72h+ 连续运行)
```

## 常用调试技巧

```bash
# Linux 内核调试
echo 8 > /proc/sys/kernel/print_loglevel   # 打开内核日志
cat /proc/interrupts                         # 查看中断统计
cat /sys/kernel/debug/gpio                   # GPIO 状态
i2cdetect -y 1                              # I2C 设备扫描
devmem2 0x48000000 w                        # 寄存器读取
```
