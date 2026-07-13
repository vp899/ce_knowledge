# GPS / GNSS 定位系统

## 1. GNSS 接收机选型

### 常用 GNSS 模块对比

| 型号 | 厂商 | 频段 | 系统 | 精度 (CEP) | 首次定位 | 更新率 | 接口 | 功耗 |
|------|------|------|------|-----------|----------|--------|------|------|
| NEO-M9N | u-blox | L1 | GPS+GLO+BDS+GAL | 1.5m | 26s | 25Hz | UART/SPI | 31mA |
| MAX-M10S | u-blox | L1 | GPS+GLO+BDS+GAL | 1.5m | 11s | 25Hz | UART | 25mA |
| ZED-F9P | u-blox | L1+L5 | RTK 多频 | 1cm+1ppm | 25s | 20Hz | UART/USB | 68mA |
| LC29H | Quectel | L1+L5 | RTK 多频 | 1cm+1ppm | 30s | 20Hz | UART | 50mA |
| UM982 | Unicore | L1+L2 | RTK 双频 | 1cm+1ppm | 30s | 20Hz | UART | 120mA |
| AT3620 | Allystar | L1+L5 | RTK 双频 | 1cm+1ppm | 25s | 20Hz | UART | 60mA |
| SIM8800 | SIMCOM | L1+L5 | RTK + 4G | 1cm+1ppm | 20s | 20Hz | UART | 200mA |

### 接收机关键参数
```
定位精度:
├── 单点定位: 1.5-2.5m (CEP 50%)
├── SBAS 辅助: 1-2m
├── RTK 固定: 1cm + 1ppm × 距离
├── RTK 浮点: 20-50cm
└── PPP: 10-30cm

首次定位时间 (TTFF):
├── 冷启动: 30-60s (无辅助)
├── 温启动: 10-30s (有历书)
├── 热启动: 1-5s (有星历)
└── AGPS: 5-15s (网络辅助)

更新率:
├── 普通: 1-10Hz
├── 高速: 20-50Hz
└── 特殊: 100Hz (航空)

灵敏度:
├── 捕获: -148 ~ -160dBm
├── 跟踪: -155 ~ -167dBm
└── 重捕: -155 ~ -160dBm
```

## 2. RTK 高精度定位

### RTK 原理
```
差分定位原理:

基站 (已知精确坐标)           移动站 (待求坐标)
    │                            │
    ├── 接收卫星信号              ├── 接收卫星信号
    ├── 计算观测值                ├── 计算观测值
    ├── 发送差分数据 ──────────→  ├── 接收差分数据
    │   ( RTCM 格式)             ├── 计算差分改正
    │                            └── 输出精确坐标
    │
    └── 基站坐标精度: mm 级

差分类型:
├── 位置差分: 直接改正坐标 (精度低)
├── 伪距差分 (DGPS): 改正伪距 (亚米级)
├── 载波相位差分 (RTK): 改正载波相位 (厘米级)
└── 网络 RTK (NRTK): 多基站网络 (厘米级)

RTK 固定解:
├── 浮点解: 20-50cm, 可靠性一般
├── 固定解: 1-2cm, 可靠性高
└── 固定率: >95% (良好环境)
```

### RTK 数据链路
```
基站 → 移动站 数据链路:

方案 1: 电台 (UHF)
├── 频率: 430-470MHz
├── 速率: 9600-19200bps
├── 距离: 5-20km
├── 延迟: <100ms
└── 优点: 独立, 不依赖网络

方案 2: 4G/5G 网络
├── 使用 NTRIP 协议
├── 距离: 无限制
├── 延迟: 50-500ms
├── 优点: 距离远, 覆盖广
└── 缺点: 依赖网络, 有延迟

方案 3: WiFi
├── 距离: <100m
├── 延迟: <10ms
├── 适用: 室内/近距离
└── 优点: 低延迟

RTCM 3.x 消息类型:
├── 1005: 基站坐标
├── 1077: GPS 观测值
├── 1087: GLONASS 观测值
├── 1097: Galileo 观测值
├── 1127: BeiDou 观测值
└── 更新率: 1Hz (通常)
```

### u-blox ZED-F9P 配置
```c
/* ublox_f9p.c */

/* UBX 协议命令 */
#define UBX_SYNC1      0xB5
#define UBX_SYNC2      0x62

/* 配置消息 */
static const uint8_t enable_rtcm3[] = {
    UBX_SYNC1, UBX_SYNC2,
    0x06, 0x8A,           // UBX-CFG-VALSET
    // ... 配置 RTCM3 输入
};

/* 配置 RTK 基站模式 */
int config_base_station(int update_rate_hz) {
    // 1. 设置输出频率
    uint8_t rate_cmd[] = {
        UBX_SYNC1, UBX_SYNC2,
        0x06, 0x08, 0x06, 0x00,
        (1000 / update_rate_hz) & 0xFF,  // 测量周期 ms
        (1000 / update_rate_hz) >> 8,
        0x01, 0x00,  // 测量比
        0x01, 0x00,  // 参考时间
    };
    send_ubx(rate_cmd, sizeof(rate_cmd));
    
    // 2. 启用 RTCM3 输出
    enable_message(UBX_CLASS_RTCM3, 0x05, 1);  // 1005 基站坐标
    enable_message(UBX_CLASS_RTCM3, 0x4D, 1);  // 1077 GPS MSM7
    enable_message(UBX_CLASS_RTCM3, 0x57, 1);  // 1087 GLO MSM7
    enable_message(UBX_CLASS_RTCM3, 0x61, 1);  // 1097 GAL MSM7
    enable_message(UBX_CLASS_RTCM3, 0x7F, 1);  // 1127 BDS MSM7
    
    // 3. 设置为基准站模式
    // 使用 SURVEY-IN 模式自动确定基站位置
    uint8_t tmode_cmd[] = {
        UBX_SYNC1, UBX_SYNC2,
        0x06, 0x71, 0x28, 0x00,
        0x00, 0x00, 0x00, 0x00,  // version
        0x01, 0x00, 0x00, 0x00,  // mode: survey-in
        0x80, 0x38, 0x01, 0x00,  // 80000 秒
        0xE8, 0x03, 0x00, 0x00,  // 1000 秒
        0x00, 0x00, 0x00, 0x00,  // 固定纬度
        0x00, 0x00, 0x00, 0x00,  // 固定经度
        0x00, 0x00, 0x00, 0x00,  // 固定高度
        0x00, 0x00, 0x00, 0x00,  // 固定高度精度
        0x00, 0x00, 0x00, 0x00,  // 固定纬度
        0x00, 0x00, 0x00, 0x00,  // 固定经度
        0x00, 0x00, 0x00, 0x00,  // 固定高度
    };
    send_ubx(tmode_cmd, sizeof(tmode_cmd));
    
    return 0;
}

/* 解析 NMEA 语句 */
int parse_nmea_gga(const char *nmea, GPS_Fix *fix) {
    // $GPGGA,hhmmss.ss,llll.ll,a,yyyyy.yy,a,x,xx,x.x,x.x,M,x.x,M,x.x,xxxx*hh
    
    char *token;
    char buf[128];
    strncpy(buf, nmea, sizeof(buf));
    
    token = strtok(buf, ",");
    
    // 时间
    token = strtok(NULL, ",");
    if (token) {
        fix->hour = (token[0]-'0')*10 + (token[1]-'0');
        fix->min = (token[2]-'0')*10 + (token[3]-'0');
        fix->sec = (token[4]-'0')*10 + (token[5]-'0');
    }
    
    // 纬度
    token = strtok(NULL, ",");
    if (token) fix->latitude = nmea_to_decimal(token);
    token = strtok(NULL, ",");  // N/S
    
    // 经度
    token = strtok(NULL, ",");
    if (token) fix->longitude = nmea_to_decimal(token);
    token = strtok(NULL, ",");  // E/W
    
    // 定位质量
    token = strtok(NULL, ",");
    if (token) fix->fix_quality = atoi(token);
    // 0=无效, 1=GPS, 2=DGPS, 4=RTK固定, 5=RTK浮动
    
    // 使用卫星数
    token = strtok(NULL, ",");
    if (token) fix->num_satellites = atoi(token);
    
    // HDOP
    token = strtok(NULL, ",");
    if (token) fix->hdop = atof(token);
    
    // 海拔
    token = strtok(NULL, ",");
    if (token) fix->altitude = atof(token);
    
    return 0;
}
```

## 3. GNSS 天线设计

### 天线类型
```
陶瓷贴片天线:
├── 尺寸: 18×18mm, 25×25mm
├── 增益: 3-5dBi
├── 带宽: L1 (1575.42MHz)
├── 极化: 右旋圆极化 (RHCP)
├── 优点: 小型化, 低成本
└── 缺点: 增益有限

螺旋天线:
├── 增益: 5-8dBi
├── 带宽: L1+L2+L5
├── 极化: 圆极化
├── 优点: 多频段, 高增益
└── 缺点: 体积较大

四臂螺旋天线 (QFH):
├── 增益: 4-6dBi
├── 半球覆盖
├── 低仰角增益好
└── 无人机常用

天线性能指标:
├── 增益: >3dBi
├── 轴比: <3dB (圆极化纯度)
├── 相位中心稳定性: <1mm
├── 多径抑制: >15dB
└── 带宽: 覆盖 L1+L5
```

### 天线安装
```
无人机 GNSS 天线安装:

最佳安装:
┌─────────────────────────────────┐
│                                  │
│         GNSS 天线                │
│         ┌─────┐                 │
│         │     │                 │
│         └──┬──┘                 │
│            │                    │
│     ┌──────┴──────┐            │
│     │  高架杆     │  ← 远离机身 │
│     │  5-10cm     │            │
│     └──────┬──────┘            │
│     ┌──────┴──────┐            │
│     │  飞控板     │            │
│     └─────────────┘            │
│                                  │
└─────────────────────────────────┘

安装注意事项:
├── 天线朝上 (面向天空)
├── 远离金属物体 (至少 λ/2 = 9.5cm)
├── 远离电机和 ESC (电磁干扰)
├── 遮挡最小化
├── 地平面 (反射板) 增强增益
└── 多频天线需要更大净空
```

## 4. 组合导航

### GPS + IMU 融合
```
松耦合 (Loosely Coupled):
GPS 提供位置/速度 ──→ EKF ──→ 最优位置/速度
IMU 提供加速度/角速度 ──→ EKF

紧耦合 (Tightly Coupled):
GPS 伪距/载波相位 ──→ EKF ──→ 最优位置/速度/姿态
IMU 加速度/角速度 ──→ EKF

松耦合实现:
状态向量: [x, y, z, vx, vy, vz, roll, pitch, yaw, bax, bay, baz, bgx, bgy, bgz]

预测 (IMU):
├── 使用加速度和角速度积分
├── 传播协方差
└── 频率: 100-400Hz

更新 (GPS):
├── 使用 GPS 位置/速度修正
├── 计算卡尔曼增益
└── 频率: 1-10Hz

融合优势:
├── GPS: 绝对位置, 无漂移
├── IMU: 高频, 短时精度高
├── 互补: GPS 修正 IMU 漂移, IMU 补充 GPS 间隙
└── 可估计传感器零偏
```

### GPS 中断处理
```c
/* gps_outage_handling.c */

typedef struct {
    float position[3];
    float velocity[3];
    float covariance[15][15];
    uint32_t last_gps_time;
    bool gps_valid;
    float predicted_position[3];
} NavigationState;

void handle_gps_outage(NavigationState *nav, uint32_t current_time) {
    uint32_t outage_duration = current_time - nav->last_gps_time;
    
    if (outage_duration < 1000) {
        // <1s: 短暂中断, 继续用 IMU 推算
        // 协方差缓慢增长
        return;
    }
    
    if (outage_duration < 10000) {
        // 1-10s: 中等中断
        // 增大过程噪声, 允许更快漂移
        for (int i = 0; i < 3; i++) {
            nav->covariance[i][i] *= 1.1f;  // 位置协方差增长
        }
        return;
    }
    
    if (outage_duration < 60000) {
        // 10-60s: 长中断
        // 切换到纯 IMU 推算模式
        // 协方差快速增长
        for (int i = 0; i < 6; i++) {
            nav->covariance[i][i] *= 1.5f;
        }
        
        // 检查协方差是否过大
        if (nav->covariance[0][0] > 100.0f) {
            // 位置不确定度 >10m, 警告
            set_warning(WARNING_NAV_DEGRADED);
        }
        return;
    }
    
    // >60s: 严重中断
    // 位置信息不可信
    set_warning(WARNING_GPS_LOST);
    
    // 可选: 使用视觉里程计补充
    if (vision_available()) {
        // 融合视觉里程计
        fuse_vio(nav);
    }
}
```
