# 飞控系统

## 1. 飞控硬件设计

### 飞控主控芯片选型

| 芯片 | 厂商 | 主频 | RAM | Flash | PWM | ADC | 特点 | 典型飞控 |
|------|------|------|-----|-------|-----|-----|------|----------|
| STM32F405 | ST | 168MHz | 192K | 1M | 14 | 16 | 经典选择 | Pixhawk 1 |
| STM32F765 | ST | 216MHz | 512K | 2M | 18 | 24 | 高性能 | Pixhawk 4 |
| STM32H743 | ST | 480MHz | 1M | 2M | 20 | 36 | 旗舰 | Pixhawk 6X |
| STM32F427 | ST | 180MHz | 256K | 2M | 14 | 24 | 双冗余 | Pixhawk 2 |
| AT32F435 | Artery | 288MHz | 448K | 4M | 16 | 16 | 国产替代 | - |
| ESP32-S3 | Espressif | 240MHz | 512K | - | 8 | 20 | WiFi/BT 集成 | 轻量飞控 |

### 飞控接口定义
```
┌─────────────────────────────────────────────────────┐
│                   飞控板接口布局                      │
├─────────────────────────────────────────────────────┤
│                                                      │
│  传感器接口:                                         │
│  ├── SPI1: IMU (ICM42688) - 高速主传感器            │
│  ├── SPI2: IMU (BMI088) - 冗余传感器                │
│  ├── SPI3: 气压计 (MS5611 / BMP388)                 │
│  ├── I2C1: 指南针 (QMC5883L / IST8310)              │
│  ├── I2C2: 距离传感器 / 光流                         │
│  └── UART5: GPS (u-blox M10)                        │
│                                                      │
│  执行器接口:                                         │
│  ├── PWM1-8: 电调信号输出 (400Hz / DShot)           │
│  ├── PWM9-14: 云台/辅助通道                          │
│  └── GPIO: LED / 蜂鸣器 / 安全开关                   │
│                                                      │
│  通信接口:                                           │
│  ├── UART1: 遥控器接收 (SBUS/CRSF)                  │
│  ├── UART2: 数传 (MAVLink)                           │
│  ├── UART3: 图传 (串口控制)                          │
│  ├── UART4: 备用                                     │
│  ├── CAN1: ESC / 云台 (DroneCAN / Cyphal)          │
│  ├── CAN2: 备用 CAN                                  │
│  └── USB: 调试/参数配置                               │
│                                                      │
│  存储接口:                                           │
│  ├── SDIO: SD 卡 (日志记录)                          │
│  └── SPI Flash: 参数存储                              │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### 电源设计
```
飞控电源树:

电池 (3S-6S LiPo, 11.1V-22.2V)
    │
    ├── 高压降压 (Buck, 5V/3A)
    │       │
    │       ├── 5V Rail: GPS, 数传, 外设
    │       │
    │       └── 3.3V LDO (500mA)
    │               │
    │               ├── MCU 核心供电
    │               ├── IMU 供电 (独立 LDO，低噪声)
    │               ├── 气压计供电
    │               └── 指南针供电
    │
    └── ADC 分压采样 (电池电压监测)

电压监测:
├── 电池电压: 分压 1:10 → ADC 量程 0-3.3V
├── 5V 电压: 分压 1:2 → ADC 量程 0-3.3V
└── 电流传感器: 分流器 + 运放 → ADC

功耗预算:
├── MCU: 100-200mA
├── IMU ×2: 10mA
├── 气压计: 5mA
├── 指南针: 5mA
├── GPS: 50-100mA
├── 数传: 100-300mA
├── LED: 50mA
└── 总计: ~500mA @ 3.3V ≈ 1.65W
```

## 2. 飞控固件架构

### ArduPilot / PX4 架构概览
```
ArduPilot 架构:
┌─────────────────────────────────────────────────────┐
│                    应用层 (AP_Arming, AP_Mission)     │
├─────────────────────────────────────────────────────┤
│  控制层 (AC_AttitudeControl, AC_PosControl)          │
├─────────────────────────────────────────────────────┤
│  导航层 (AP_Navigation, AP_WPNav, AP_Landing)       │
├─────────────────────────────────────────────────────┤
│  传感器驱动 (AP_IMU, AP_Compass, AP_GPS, AP_Baro)   │
├─────────────────────────────────────────────────────┤
│  HAL 抽象层 (AP_HAL)                                 │
│  ├── ChibiOS (STM32)                                │
│  ├── Linux (Linux 飞控)                              │
│  └── SITL (软件仿真)                                 │
├─────────────────────────────────────────────────────┤
│  硬件 (STM32 + 传感器 + 电调)                        │
└─────────────────────────────────────────────────────┘

PX4 架构:
┌─────────────────────────────────────────────────────┐
│  应用层 (Commander, Navigator, Mission)              │
├─────────────────────────────────────────────────────┤
│  控制层 (mc_pos_control, mc_att_control)            │
├─────────────────────────────────────────────────────┤
│  传感器驱动 (drivers/)                               │
├─────────────────────────────────────────────────────┤
│  uORB 消息总线                                       │
├─────────────────────────────────────────────────────┤
│  NuttX RTOS                                          │
├─────────────────────────────────────────────────────┤
│  硬件                                               │
└─────────────────────────────────────────────────────┘
```

### 飞控任务调度
```c
/* 飞控主循环 (1kHz) */
void flight_controller_loop(void) {
    static uint32_t loop_count = 0;
    uint32_t start_time = micros();
    
    // 1kHz 任务 - 每次执行
    read_imu();                     // 读取 IMU 数据
    update_attitude_estimate();     // 姿态估计 (互补/EKF)
    run_attitude_controller();      // 姿态控制 (400Hz)
    run_rate_controller();          // 角速度控制 (1kHz)
    output_motor_mixing();          // 电机混控输出
    
    // 400Hz 任务
    if (loop_count % 2 == 0) {
        run_position_controller();  // 位置控制
        run_altitude_controller();  // 高度控制
    }
    
    // 100Hz 任务
    if (loop_count % 10 == 0) {
        read_compass();             // 读取指南针
        read_barometer();           // 读取气压计
        update_ekf();               // EKF 更新
        check_battery();            // 电池检查
    }
    
    // 50Hz 任务
    if (loop_count % 20 == 0) {
        update_mission();           // 航点导航
        check_geofence();           // 地理围栏
        log_data();                 // 数据记录
    }
    
    // 10Hz 任务
    if (loop_count % 100 == 0) {
        update_gps();               // GPS 更新
        heartbeat_check();          // 心跳检测
        failsafe_check();           // 失联保护检查
    }
    
    // 1Hz 任务
    if (loop_count % 1000 == 0) {
        status_report();            // 状态上报
        parameter_save();           // 参数保存
    }
    
    loop_count++;
    
    // 检查循环时间
    uint32_t elapsed = micros() - start_time;
    if (elapsed > 1000) {
        // 超时告警
        log_warning("Loop overrun: %dus", elapsed);
    }
    
    // 等待下一个周期
    while (micros() - start_time < 1000) {
        // busy wait
    }
}
```

## 3. 控制算法

### PID 控制器
```c
/* PID 控制器实现 */
typedef struct {
    float kp, ki, kd;       // PID 增益
    float integral;          // 积分累积
    float prev_error;        // 上次误差
    float integral_limit;    // 积分限幅
    float output_limit;      // 输出限幅
    float dt;               // 控制周期
    float filter_alpha;     // D 项滤波系数
    float d_filtered;       // 滤波后的 D 项
} PID_Controller;

float pid_update(PID_Controller *pid, float error) {
    // P 项
    float p_term = pid->kp * error;
    
    // I 项 (带限幅)
    pid->integral += error * pid->dt;
    pid->integral = CLAMP(pid->integral, 
                          -pid->integral_limit, 
                           pid->integral_limit);
    float i_term = pid->ki * pid->integral;
    
    // D 项 (低通滤波)
    float derivative = (error - pid->prev_error) / pid->dt;
    pid->d_filtered = pid->filter_alpha * derivative + 
                      (1 - pid->filter_alpha) * pid->d_filtered;
    float d_term = pid->kd * pid->d_filtered;
    
    pid->prev_error = error;
    
    // 输出限幅
    float output = p_term + i_term + d_term;
    output = CLAMP(output, -pid->output_limit, pid->output_limit);
    
    return output;
}

void pid_reset(PID_Controller *pid) {
    pid->integral = 0;
    pid->prev_error = 0;
    pid->d_filtered = 0;
}
```

### 姿态控制 (四旋翼)
```
级联控制结构:

角度设定值 (roll/pitch/yaw)
    │
    ▼
┌──────────────────┐
│  角度控制器       │  → 角速度设定值
│  (外环, 100-400Hz)│
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  角速度控制器     │  → 力矩输出
│  (内环, 1kHz)     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  电机混控         │  → 各电机 PWM
│  (Mixer)         │
└──────────────────┘

四旋翼混控矩阵:
M1 (前左)  = throttle + roll + pitch - yaw
M2 (前右)  = throttle - roll + pitch + yaw
M3 (后左)  = throttle + roll - pitch + yaw
M4 (后右)  = throttle - roll - pitch - yaw

其中:
- throttle: 油门 (升力)
- roll: 横滚力矩
- pitch: 俯仰力矩
- yaw: 偏航力矩 (反扭力矩)
```

### 高度控制
```
气压计 + 超声波 + GPS 融合高度:

传感器融合:
├── 气压计: 大范围高度 (0-10000m), 低频 (10-50Hz)
│   ├── 精度: ±1m
│   ├── 漂移: 有 (温度相关)
│   └── 噪声: 低
│
├── 超声波/ToF: 近地面 (0.1-50m), 中频 (10-50Hz)
│   ├── 精度: ±2cm
│   ├── 无漂移
│   └── 噪声: 中
│
└── GPS: 大范围 (0-10000m+), 低频 (1-10Hz)
    ├── 精度: ±1.5m (单点) / ±2cm (RTK)
    ├── 垂直精度较差
    └── 更新率低

融合方法:
- 互补滤波: 气压计低频 + 加速度计高频
- EKF: 所有传感器融合
- 高度切换: 近地面用超声波，高处用气压计/GPS
```

## 4. 安全保护

### 失联保护 (Failsafe)
```c
/* 失联保护状态机 */
typedef enum {
    FS_NONE = 0,
    FS_RADIO_LOST,          // 遥控器失联
    FS_GPS_LOST,            // GPS 丢失
    FS_BATTERY_LOW,         // 电池低电量
    FS_BATTERY_CRITICAL,    // 电池危急
    FS_GEOFENCE,            // 地理围栏突破
    FS_EKF_FAIL,            // EKF 故障
    FS_MOTOR_FAIL,          // 电机故障
} FailsafeType;

/* 遥控器失联处理 */
void handle_radio_failsafe(void) {
    static uint32_t lost_time = 0;
    
    if (!radio_connected()) {
        if (lost_time == 0) {
            lost_time = millis();
        }
        
        uint32_t lost_duration = millis() - lost_time;
        
        if (lost_duration > 5000) {
            // 失联超过 5 秒
            switch (fs_config.radio_lost_action) {
            case FS_ACTION_LAND:
                // 原地降落
                set_mode(MODE_LAND);
                break;
            case FS_ACTION_RTL:
                // 返航
                set_mode(MODE_RTL);
                break;
            case FS_ACTION_CONTINUE:
                // 继续任务
                break;
            case FS_ACTION_SMART_RTL:
                // 沿航线返回
                set_mode(MODE_SMART_RTL);
                break;
            }
        }
    } else {
        lost_time = 0;
    }
}

/* 电池失联处理 */
void handle_battery_failsafe(void) {
    float voltage = get_battery_voltage();
    float remaining = get_battery_remaining();
    
    if (remaining < 10.0f) {
        // 电量 < 10%，紧急降落
        set_mode(MODE_LAND);
        buzzer_alarm(BUZZER_BATTERY_CRITICAL);
        led_set(LED_RED_FLASH);
    } else if (remaining < 20.0f) {
        // 电量 < 20%，返航
        set_mode(MODE_RTL);
        buzzer_alarm(BUZZER_BATTERY_LOW);
        led_set(LED_RED);
    }
}

/* 地理围栏 */
typedef struct {
    float home_lat, home_lon;    // 起飞点
    float max_radius;            // 最大半径 (m)
    float max_altitude;          // 最大高度 (m)
    float min_altitude;          // 最小高度 (m)
    bool enabled;
} GeofenceConfig;

bool check_geofence(GeofenceConfig *fence, 
                     float lat, float lon, float alt) {
    if (!fence->enabled) return true;
    
    // 检查半径
    float distance = calculate_distance(
        fence->home_lat, fence->home_lon, lat, lon);
    
    if (distance > fence->max_radius) {
        return false;  // 超出范围
    }
    
    // 检查高度
    if (alt > fence->max_altitude || alt < fence->min_altitude) {
        return false;  // 超出高度限制
    }
    
    return true;
}
```

### 返航 (RTL) 算法
```
返航流程:

1. 记录起飞点 (Home Position)
   ├── GPS 坐标
   ├── 高度
   └── 航向

2. 返航决策
   ├── 爬升到安全高度 (默认 30m)
   ├── 避障检测 (前方障碍物)
   └── 路径规划

3. 返航路径
   ├── 直线返航 (简单)
   ├── 沿航线返航 (Smart RTL)
   └── 避障绕行 (有避障系统)

4. 到达起飞点上空
   ├── 对准起飞点
   ├── 缓慢下降
   └── 着陆检测

5. 着陆完成
   ├── 关闭电机
   ├── 记录日志
   └── 解锁保护
```
