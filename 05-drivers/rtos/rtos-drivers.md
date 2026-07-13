---
title: "RTOS 驱动开发"
aliases:
  - "RTOS 驱动"
tags:
  - drivers
  - rtos
  - freertos
  - rt-thread
module: "05-drivers"
status: active
---

# RTOS 驱动开发

## 1. FreeRTOS 驱动框架

### FreeRTOS 任务管理
```c
/* freertos_tasks.c */
#include "FreeRTOS.h"
#include "task.h"
#include "queue.h"
#include "semphr.h"

/* 任务句柄 */
TaskHandle_t sensor_task_handle;
TaskHandle_t comm_task_handle;
TaskHandle_t storage_task_handle;

/* 队列句柄 */
QueueHandle_t sensor_data_queue;
QueueHandle_t comm_cmd_queue;

/* 信号量句柄 */
SemaphoreHandle_t spi_mutex;
SemaphoreHandle_t uart_sem;

/* 传感器任务 */
void sensor_task(void *pvParameters) {
    SensorData_t data;
    TickType_t xLastWakeTime;
    const TickType_t xPeriod = pdMS_TO_TICKS(100);  // 100ms
    
    xLastWakeTime = xTaskGetTickCount();
    
    while (1) {
        // 读取传感器
        if (sensor_read(&data) == 0) {
            // 发送到队列
            xQueueSend(sensor_data_queue, &data, 0);
        }
        
        // 精确周期延时
        vTaskDelayUntil(&xLastWakeTime, xPeriod);
    }
}

/* 通信任务 */
void comm_task(void *pvParameters) {
    CommCmd_t cmd;
    
    while (1) {
        // 等待命令
        if (xQueueReceive(comm_cmd_queue, &cmd, portMAX_DELAY)) {
            // 处理命令
            process_comm_cmd(&cmd);
        }
    }
}

/* 存储任务 */
void storage_task(void *pvParameters) {
    SensorData_t data;
    
    while (1) {
        // 从队列获取数据
        if (xQueueReceive(sensor_data_queue, &data, portMAX_DELAY)) {
            // 获取 SPI 互斥锁
            if (xSemaphoreTake(spi_mutex, pdMS_TO_TICKS(100))) {
                // 写入 Flash
                flash_write_data(&data);
                
                // 释放互斥锁
                xSemaphoreGive(spi_mutex);
            }
        }
    }
}

/* 系统初始化 */
void system_init(void) {
    // 创建队列
    sensor_data_queue = xQueueCreate(32, sizeof(SensorData_t));
    comm_cmd_queue = xQueueCreate(16, sizeof(CommCmd_t));
    
    // 创建互斥锁
    spi_mutex = xSemaphoreCreateMutex();
    uart_sem = xSemaphoreCreateBinary();
    
    // 创建任务
    xTaskCreate(sensor_task, "Sensor", 256, NULL, 
                configMAX_PRIORITIES - 2, &sensor_task_handle);
    xTaskCreate(comm_task, "Comm", 512, NULL,
                configMAX_PRIORITIES - 3, &comm_task_handle);
    xTaskCreate(storage_task, "Storage", 256, NULL,
                configMAX_PRIORITIES - 4, &storage_task_handle);
    
    // 启动调度器
    vTaskStartScheduler();
}
```

### FreeRTOS 中断处理
```c
/* freertos_interrupt.c */

/* 中断优先级配置 */
#define IRQ_PRIORITY_HIGH    5   // 高优先级中断
#define IRQ_PRIORITY_NORMAL  10  // 普通中断
#define IRQ_PRIORITY_LOW     15  // 低优先级中断

/* 中断安全的队列操作 */
void UART_IRQHandler(void) {
    BaseType_t xHigherPriorityTaskWoken = pdFALSE;
    uint8_t data;
    
    if (UART_GetITStatus(UART1, UART_IT_RXNE)) {
        data = UART_ReceiveData(UART1);
        
        // 中断中发送到队列
        xQueueSendFromISR(comm_cmd_queue, &data, 
                          &xHigherPriorityTaskWoken);
        
        UART_ClearITPendingBit(UART1, UART_IT_RXNE);
    }
    
    // 如果有更高优先级任务被唤醒，触发上下文切换
    portYIELD_FROM_ISR(xHigherPriorityTaskWoken);
}

/* 中断安全的信号量操作 */
void DMA_IRQHandler(void) {
    BaseType_t xHigherPriorityTaskWoken = pdFALSE;
    
    if (DMA_GetITStatus(DMA1_IT_TC3)) {
        // 释放信号量
        xSemaphoreGiveFromISR(dma_complete_sem, 
                              &xHigherPriorityTaskWoken);
        
        DMA_ClearITPendingBit(DMA1_IT_TC3);
    }
    
    portYIELD_FROM_ISR(xHigherPriorityTaskWoken);
}
```

## 2. RT-Thread 驱动框架

### RT-Thread 设备驱动
```c
/* rt_device_driver.c */
#include <rtthread.h>
#include <rtdevice.h>

/* 设备结构体 */
struct my_sensor_device {
    struct rt_device parent;
    struct rt_i2c_bus_device *i2c;
    rt_mutex_t lock;
    rt_uint16_t temperature;
    rt_uint16_t humidity;
};

/* 设备操作函数 */
static rt_err_t my_sensor_init(rt_device_t dev) {
    struct my_sensor_device *sensor = (struct my_sensor_device *)dev;
    
    // 初始化 I2C 设备
    sensor->i2c = rt_i2c_bus_device_find("i2c1");
    if (sensor->i2c == RT_NULL) {
        return -RT_ERROR;
    }
    
    // 初始化传感器
    rt_uint8_t cmd = 0x01;
    rt_i2c_master_send(sensor->i2c, 0x48, 0, &cmd, 1);
    
    return RT_EOK;
}

static rt_err_t my_sensor_open(rt_device_t dev, rt_uint16_t oflag) {
    return RT_EOK;
}

static rt_err_t my_sensor_close(rt_device_t dev) {
    return RT_EOK;
}

static rt_size_t my_sensor_read(rt_device_t dev, rt_off_t pos,
                                 void *buffer, rt_size_t size) {
    struct my_sensor_device *sensor = (struct my_sensor_device *)dev;
    rt_uint16_t *data = (rt_uint16_t *)buffer;
    
    rt_mutex_take(sensor->lock, RT_WAITING_FOREVER);
    
    data[0] = sensor->temperature;
    data[1] = sensor->humidity;
    
    rt_mutex_release(sensor->lock);
    
    return size;
}

static rt_err_t my_sensor_control(rt_device_t dev, int cmd, void *args) {
    struct my_sensor_device *sensor = (struct my_sensor_device *)dev;
    
    switch (cmd) {
    case 0x1000:  // 校准
        // 执行校准
        break;
    case 0x1001:  // 设置采样率
        // 设置采样率
        break;
    }
    
    return RT_EOK;
}

/* 设备操作结构体 */
static struct rt_device_ops my_sensor_ops = {
    .init = my_sensor_init,
    .open = my_sensor_open,
    .close = my_sensor_close,
    .read = my_sensor_read,
    .write = RT_NULL,
    .control = my_sensor_control,
};

/* 注册设备 */
int my_sensor_register(void) {
    struct my_sensor_device *sensor;
    
    sensor = rt_calloc(1, sizeof(struct my_sensor_device));
    if (sensor == RT_NULL) {
        return -RT_ENOMEM;
    }
    
    sensor->parent.type = RT_Device_Class_Sensor;
    sensor->parent.ops = &my_sensor_ops;
    
    sensor->lock = rt_mutex_create("sensor_lock", RT_IPC_FLAG_FIFO);
    
    rt_device_register(&sensor->parent, "my_sensor", 
                       RT_DEVICE_FLAG_RDWR);
    
    return RT_EOK;
}
INIT_DEVICE_EXPORT(my_sensor_register);
```

### RT-Thread 线程管理
```c
/* rt_thread.c */

/* 线程栈 */
#define SENSOR_THREAD_STACK_SIZE    512
#define COMM_THREAD_STACK_SIZE      1024

static rt_uint8_t sensor_thread_stack[SENSOR_THREAD_STACK_SIZE];
static rt_uint8_t comm_thread_stack[COMM_THREAD_STACK_SIZE];

static struct rt_thread sensor_thread;
static struct rt_thread comm_thread;

/* 传感器线程入口 */
void sensor_thread_entry(void *parameter) {
    rt_device_t dev;
    rt_uint16_t data[2];
    
    dev = rt_device_find("my_sensor");
    if (dev == RT_NULL) {
        rt_kprintf("Sensor device not found\n");
        return;
    }
    
    rt_device_open(dev, RT_DEVICE_FLAG_RDWR);
    
    while (1) {
        rt_device_read(dev, 0, data, sizeof(data));
        
        rt_kprintf("Temp: %d, Humi: %d\n", data[0], data[1]);
        
        rt_thread_mdelay(1000);
    }
}

/* 初始化线程 */
int thread_init(void) {
    rt_err_t result;
    
    result = rt_thread_init(&sensor_thread, "sensor",
                            sensor_thread_entry, RT_NULL,
                            sensor_thread_stack,
                            SENSOR_THREAD_STACK_SIZE,
                            10, 10);
    
    if (result == RT_EOK) {
        rt_thread_startup(&sensor_thread);
    }
    
    return 0;
}
INIT_APP_EXPORT(thread_init);
```

## 3. 常用外设驱动

### GPIO 驱动
```c
/* gpio_driver.c */

/* GPIO 配置结构体 */
typedef struct {
    GPIO_TypeDef *port;
    uint16_t pin;
    uint32_t mode;
    uint32_t pull;
    uint32_t speed;
} GPIO_Config_t;

/* GPIO 初始化 */
void gpio_init(const GPIO_Config_t *config) {
    GPIO_InitTypeDef gpio;
    
    gpio.Pin = config->pin;
    gpio.Mode = config->mode;
    gpio.Pull = config->pull;
    gpio.Speed = config->speed;
    
    HAL_GPIO_Init(config->port, &gpio);
}

/* LED 控制 */
void led_on(GPIO_TypeDef *port, uint16_t pin) {
    HAL_GPIO_WritePin(port, pin, GPIO_PIN_SET);
}

void led_off(GPIO_TypeDef *port, uint16_t pin) {
    HAL_GPIO_WritePin(port, pin, GPIO_PIN_RESET);
}

void led_toggle(GPIO_TypeDef *port, uint16_t pin) {
    HAL_GPIO_TogglePin(port, pin);
}

/* 按键读取 */
uint8_t button_read(GPIO_TypeDef *port, uint16_t pin) {
    return HAL_GPIO_ReadPin(port, pin) == GPIO_PIN_SET ? 1 : 0;
}

/* 按键消抖 */
uint8_t button_read_debounce(GPIO_TypeDef *port, uint16_t pin) {
    static uint8_t last_state = 0;
    static uint8_t debounce_count = 0;
    
    uint8_t current = button_read(port, pin);
    
    if (current != last_state) {
        debounce_count++;
        if (debounce_count >= 5) {  // 5 次采样一致
            last_state = current;
            debounce_count = 0;
            return current;
        }
    } else {
        debounce_count = 0;
    }
    
    return last_state;
}
```

### ADC 驱动
```c
/* adc_driver.c */

/* ADC 配置 */
void adc_init(void) {
    ADC_HandleTypeDef hadc;
    
    hadc.Instance = ADC1;
    hadc.Init.ClockPrescaler = ADC_CLOCK_SYNC_PCLK_DIV4;
    hadc.Init.Resolution = ADC_RESOLUTION_12B;
    hadc.Init.ScanConvMode = DISABLE;
    hadc.Init.ContinuousConvMode = DISABLE;
    hadc.Init.DiscontinuousConvMode = DISABLE;
    hadc.Init.ExternalTrigConvEdge = ADC_EXTERNALTRIGCONVEDGE_NONE;
    hadc.Init.DataAlign = ADC_DATAALIGN_RIGHT;
    hadc.Init.NbrOfConversion = 1;
    
    HAL_ADC_Init(&hadc);
}

/* 单次 ADC 读取 */
uint16_t adc_read(ADC_HandleTypeDef *hadc, uint32_t channel) {
    ADC_ChannelConfTypeDef config;
    
    config.Channel = channel;
    config.Rank = 1;
    config.SamplingTime = ADC_SAMPLETIME_84CYCLES;
    
    HAL_ADC_ConfigChannel(hadc, &config);
    HAL_ADC_Start(hadc);
    HAL_ADC_PollForConversion(hadc, 100);
    
    return HAL_ADC_GetValue(hadc);
}

/* 多通道 ADC 扫描 */
void adc_scan_channels(ADC_HandleTypeDef *hadc, 
                        uint32_t *channels, 
                        uint16_t *results, 
                        uint8_t count) {
    ADC_ChannelConfTypeDef config;
    
    for (int i = 0; i < count; i++) {
        config.Channel = channels[i];
        config.Rank = i + 1;
        config.SamplingTime = ADC_SAMPLETIME_84CYCLES;
        
        HAL_ADC_ConfigChannel(hadc, &config);
    }
    
    HAL_ADC_Start(hadc);
    HAL_ADC_PollForConversion(hadc, 100 * count);
    
    for (int i = 0; i < count; i++) {
        results[i] = HAL_ADC_GetValue(hadc);
    }
}

/* ADC 值转换 */
float adc_to_voltage(uint16_t adc_value, float vref) {
    return (float)adc_value / 4096.0f * vref;
}
```

### [[esc-control|PWM]] 驱动
```c
/* pwm_driver.c */

/* PWM 初始化 */
void pwm_init(TIM_HandleTypeDef *htim, uint32_t channel,
              uint32_t frequency, uint32_t duty) {
    TIM_OC_InitTypeDef config;
    
    // 计算预分频和周期
    uint32_t timer_clock = HAL_RCC_GetPCLK1Freq() * 2;
    uint32_t prescaler = 0;
    uint32_t period = timer_clock / frequency;
    
    while (period > 65535) {
        prescaler++;
        period = timer_clock / (frequency * (prescaler + 1));
    }
    
    htim->Init.Prescaler = prescaler;
    htim->Init.Period = period - 1;
    htim->Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
    htim->Init.CounterMode = TIM_COUNTERMODE_UP;
    
    HAL_TIM_PWM_Init(htim);
    
    config.OCMode = TIM_OCMODE_PWM1;
    config.Pulse = period * duty / 100;
    config.OCPolarity = TIM_OCPOLARITY_HIGH;
    config.OCFastMode = TIM_OCFAST_DISABLE;
    
    HAL_TIM_PWM_ConfigChannel(htim, &config, channel);
    HAL_TIM_PWM_Start(htim, channel);
}

/* 设置占空比 */
void pwm_set_duty(TIM_HandleTypeDef *htim, uint32_t channel,
                   uint32_t duty) {
    uint32_t period = htim->Init.Period + 1;
    uint32_t pulse = period * duty / 100;
    
    __HAL_TIM_SET_COMPARE(htim, channel, pulse);
}
```
---

## 相关链接

- [[framework-customization|Android Framework]]
- [[protocol-details|通信协议]]
