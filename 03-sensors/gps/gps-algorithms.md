---
title: "GPS/GNSS 算法详解"
tags: [gps, gnss, nmea, rtk, kalman, fusion, algorithm]
module: "03-sensors"
---

# GPS/GNSS 算法详解

## 1. NMEA 解析

### GGA 语句解析
```c
/* NMEA GGA 解析 */
// $GPGGA,hhmmss.ss,llll.ll,a,yyyyy.yy,a,x,xx,x.x,x.x,M,x.x,M,x.x,xxxx*hh

typedef struct {
    int hour, min, sec, msec;
    double latitude;      // 度 (正=北, 负=南)
    double longitude;     // 度 (正=东, 负=西)
    int fix_quality;      // 0=无效, 1=GPS, 2=DGPS, 4=RTK固定, 5=RTK浮动
    int num_satellites;
    float hdop;
    float altitude;       // 海拔 (米)
    float geoid_sep;      // 大地水准面差距
} GGA_Data;

int parse_gga(const char *nmea, GGA_Data *data) {
    char buf[128];
    strncpy(buf, nmea, sizeof(buf));
    
    char *token = strtok(buf, ",");
    int field = 0;
    
    while (token && field < 14) {
        switch (field) {
        case 1: // 时间
            data->hour = (token[0]-'0')*10 + (token[1]-'0');
            data->min = (token[2]-'0')*10 + (token[3]-'0');
            data->sec = (token[4]-'0')*10 + (token[5]-'0');
            break;
        case 2: // 纬度 (ddmm.mmmm)
            data->latitude = nmea_to_decimal(token);
            break;
        case 3: // N/S
            if (token[0] == 'S') data->latitude = -data->latitude;
            break;
        case 4: // 经度 (dddmm.mmmm)
            data->longitude = nmea_to_decimal(token);
            break;
        case 5: // E/W
            if (token[0] == 'W') data->longitude = -data->longitude;
            break;
        case 6: // 定位质量
            data->fix_quality = atoi(token);
            break;
        case 7: // 卫星数
            data->num_satellites = atoi(token);
            break;
        case 8: // HDOP
            data->hdop = atof(token);
            break;
        case 9: // 海拔
            data->altitude = atof(token);
            break;
        }
        token = strtok(NULL, ",");
        field++;
    }
    return 0;
}

double nmea_to_decimal(const char *nmea_coord) {
    // ddmm.mmmm → dd.ddddd
    double raw = atof(nmea_coord);
    int degrees = (int)(raw / 100);
    double minutes = raw - degrees * 100;
    return degrees + minutes / 60.0;
}
```

## 2. GPS/INS 组合导航 (EKF)

### 状态空间模型
```
状态向量 (15 维):
  x = [px, py, pz, vx, vy, vz, roll, pitch, yaw, bax, bay, baz, bgx, bgy, bgz]
       └──位置──┘  └──速度──┘  └──姿态──┘  └──加速度零偏──┘  └──陀螺零偏──┘

预测 (IMU):
  p(k+1) = p(k) + v·dt + 0.5·(R·a_m - g)·dt²
  v(k+1) = v(k) + (R·a_m - g)·dt
  q(k+1) = q(k) ⊗ exp(ω_m·dt)
  b(k+1) = b(k)  (零偏随机游走)

更新 (GPS):
  z_gps = [px, py, pz, vx, vy, vz]
  h_gps = [p, v]  (直接观测位置和速度)

协方差:
  Q = IMU 噪声协方差 (由传感器参数决定)
  R_gps = GPS 噪声协方差 (由 HDOP 和卫星数决定)
```

### GPS 精度估计
```c
/* GPS 精度因子 (DOP) */

typedef struct {
    float gdop;  // 几何精度因子
    float pdop;  // 位置精度因子
    float hdop;  // 水平精度因子
    float vdop;  // 垂直精度因子
    float tdop;  // 时间精度因子
} DOP_Factors;

// 从卫星几何计算 DOP
void calculate_dop(float (*sat_pos)[3], int n_sats,
                    float receiver_pos[3], DOP_Factors *dop) {
    // 构造几何矩阵 G
    // G = [dx1/r1  dy1/r1  dz1/r1  1]
    //     [dx2/r2  dy2/r2  dz2/r2  1]
    //     ...
    
    float G[12][4];  // 最多 12 颗卫星
    for (int i = 0; i < n_sats; i++) {
        float dx = sat_pos[i][0] - receiver_pos[0];
        float dy = sat_pos[i][1] - receiver_pos[1];
        float dz = sat_pos[i][2] - receiver_pos[2];
        float r = sqrtf(dx*dx + dy*dy + dz*dz);
        G[i][0] = dx / r;
        G[i][1] = dy / r;
        G[i][2] = dz / r;
        G[i][3] = 1.0f;
    }
    
    // Q = (G^T · G)^(-1)
    // DOP = sqrt(diag(Q))
    
    // GDOP = sqrt(q11 + q22 + q33 + q44)
    // PDOP = sqrt(q11 + q22 + q33)
    // HDOP = sqrt(q11 + q22)
    // VDOP = sqrt(q33)
}

// GPS 精度估计 (米)
// 水平精度 ≈ HDOP × UERE (用户等效测距误差)
// UERE 典型值: 1-3m (单点), 0.01-0.03m (RTK)
```

## 3. RTK 差分算法

### 载波相位差分
```
双差观测方程:

  ∇Δφ = ∇Δρ + λ·∇ΔN + ∇Δε

  ∇Δφ = 双差载波相位观测值
  ∇Δρ = 双差几何距离
  λ = 载波波长 (L1: 19cm)
  ∇ΔN = 双差整周模糊度
  ∇Δε = 双差误差

求解步骤:
1. 建立双差方程
2. 用伪距求解初始位置
3. 求解整周模糊度 (LAMBDA 算法)
4. 用载波相位精化位置
5. 输出 RTK 固定解 (cm 级)

LAMBDA 算法 (整周模糊度求解):
1. 浮点解: 最小二乘求解
2. 整周搜索: 在浮点解附近搜索整数组合
3. 验证: 比率检验确认最优解
```

---

## 相关链接

- [[imu-system|IMU]] — 惯性导航
- [[compass-system|指南针]] — 航向
- [[flight-controller-firmware|飞控]] — 导航控制
