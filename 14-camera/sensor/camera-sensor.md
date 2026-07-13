# 图像传感器 (CMOS Sensor)

## 1. 传感器选型

### 常用无人机/机器人图像传感器对比

| 型号 | 厂商 | 分辨率 | 像素尺寸 | 帧率 | 接口 | 动态范围 | 典型应用 |
|------|------|--------|----------|------|------|----------|----------|
| IMX377 | Sony | 12MP | 1.55μm | 4K@30 | MIPI 4-lane | 72dB | 航拍相机 |
| IMX477 | Sony | 12.3MP | 1.55μm | 4K@60 | MIPI 2/4-lane | 72.5dB | 高端航拍 |
| IMX586 | Sony | 48MP | 0.8μm | 4K@90 | MIPI 4-lane | 71dB | 手机级航拍 |
| IMX383 | Sony | 20MP | 2.4μm | 5K@30 | MIPI 4-lane | 80dB | 专业航测 |
| IMX290 | Sony | 2MP | 2.9μm | 1080p@120 | MIPI 2-lane | 86dB | 低光/夜视 |
| IMX464 | Sony | 4MP | 2.9μm | 2K@30 | MIPI 2/4-lane | 88dB | 低光增强 |
| OV7251 | OmniVision | 0.3MP | 3μm | VGA@120 | MIPI 1-lane | 80dB | 全局快门 |
| AR0234 | OnSemi | 2.3MP | 3μm | 1080p@60 | MIPI 2-lane | 73dB | 全局快门工业 |
| GC2053 | GalaxyCore | 2MP | 2.7μm | 1080p@30 | MIPI 1/2-lane | 72dB | 低成本 |

### 传感器关键参数

| 参数 | 说明 | 选型建议 |
|------|------|----------|
| 像素尺寸 | 单个像素感光面积 | 航拍 ≥1.5μm，低光 ≥2.5μm |
| 动态范围 | 最亮/最暗比值 | HDR 场景 >80dB |
| 滚动快门 | 逐行曝光 | 有果冻效应，适合慢速 |
| 全局快门 | 所有像素同时曝光 | 无果冻效应，适合高速/运动 |
| 量子效率 | 光子→电子转换率 | 越高越好，Sony 通常领先 |
| 暗电流 | 无光照时的噪声 | 长曝光必须低 |
| 信噪比 (SNR) | 信号/噪声比 | 越高画质越好 |
| MIPI Lane 数 | 数据传输通道 | 4K 至少 4-lane |

## 2. CMOS Sensor 工作原理

### 像素结构
```
入射光子
    │
    ▼
┌─────────────────────┐
│  微透镜 (Micro Lens) │  → 聚光到光电二极管
├─────────────────────┤
│  滤色片 (CFA)        │  → Bayer 阵列 (RGGB/BGGR)
├─────────────────────┤
│  光电二极管 (PD)     │  → 光子→电子 (光电效应)
├─────────────────────┤
│  浮动扩散 (FD)       │  → 电荷→电压转换
├─────────────────────┤
│  源极跟随器 (SF)     │  → 电压缓冲
├─────────────────────┤
│  行选择开关 (RS)     │  → 逐行读出
└─────────────────────┘

Bayer 阵列排列:
┌───┬───┬───┬───┐
│ R │ G │ R │ G │
├───┼───┼───┼───┤
│ G │ B │ G │ B │
├───┼───┼───┼───┤
│ R │ G │ R │ G │
├───┼───┼───┼───┤
│ G │ B │ G │ B │
└───┴───┴───┴───┘
```

### 曝光控制
```
曝光时间 (Integration Time):
- 控制快门打开时长
- 长曝光 → 更亮，更多运动模糊
- 短曝光 → 更暗，冻结运动

模拟增益 (Analog Gain):
- 在 ADC 之前放大信号
- 放大信号 + 放大噪声
- 通常 1x ~ 32x

数字增益 (Digital Gain):
- 在 ADC 之后放大数字信号
- 不增加信噪比
- 通常 1x ~ 16x

总增益 = 模拟增益 × 数字增益
ISO = 总增益 × 100 (近似)
```

### HDR 模式
```
方案 1: 交错曝光 (Interleaved HDR)
┌─────────────────────────┐
│ 长曝光 │ 短曝光 │ 长曝光 │  → 逐行交替
├─────────────────────────┤
│ 短曝光 │ 长曝光 │ 短曝光 │
└─────────────────────────┘
优点: 无延迟
缺点: 空间分辨率减半

方案 2: 顺序曝光 (Sequential HDR)
Frame N:   长曝光 ──→ 读出
Frame N+1: 短曝光 ──→ 读出
然后融合
优点: 全分辨率
缺点: 有延迟，运动伪影

方案 3: DOL (Dual Output Line) HDR
同一行同时输出长/短曝光
优点: 无空间损失，无时间延迟
缺点: 需要特殊传感器支持
```

## 3. MIPI CSI 接口

### MIPI CSI-2 协议层次
```
┌─────────────────────────────┐
│        应用层                │  原始图像数据 (RAW8/10/12/14)
├─────────────────────────────┤
│    数据包层 (Data Packet)    │  帧起始/结束 + 数据
├─────────────────────────────┤
│    字节层 (Byte Layer)       │  ECC + Payload
├─────────────────────────────┤
│    通道层 (Lane Management)  │  多 Lane 分发
├─────────────────────────────┤
│    物理层 (D-PHY / C-PHY)    │  差分信号, LP/HS 模式
└─────────────────────────────┘
```

### D-PHY 信号
```
差分对信号:
├── CLK+ / CLK-  : 时钟差分对
├── DATA0+ / DATA0- : 数据通道 0
├── DATA1+ / DATA1- : 数据通道 1
├── DATA2+ / DATA2- : 数据通道 2
└── DATA3+ / DATA3- : 数据通道 3

LP 模式 (低功耗):
- 单端信号, 1.2V 电平
- 用于配置寄存器 (I2C-like)
- 速率: 10 Mbps

HS 模式 (高速):
- 差分信号, 200mV 摆幅
- 用于图像数据传输
- 速率: 每 Lane 最高 2.5 Gbps (D-PHY 2.0)
```

### 数据包格式
```
┌────────┬────────┬────────┬─────────┬────────┬────────┐
│ SoT    │ Header │ Data   │ Payload │ CRC    │ EoT    │
│ (Start)│ (4B)   │ Type   │ (N B)   │ (2B)   │ (End)  │
└────────┴────────┴────────┴─────────┴────────┴────────┘

Header (4 字节):
┌──────────┬──────────┬──────────┐
│ Data ID  │ Word Cnt │ ECC      │
│ (1B)     │ (2B)     │ (1B)     │
└──────────┴──────────┴──────────┘

Data ID 格式:
┌────┬────────────┐
│ VC │ Data Type  │
│ 2b │ 6b         │
└────┴────────────┘

常见 Data Type:
0x2A = RAW8
0x2B = RAW10
0x2C = RAW12
0x2D = RAW14
0x1E = YUV422 8-bit
0x1F = YUV422 10-bit
```

## 4. Sensor 驱动开发 (Linux V4L2)

### V4L2 子系统架构
```
用户空间:  v4l2-ctl / 应用程序
              │
          ┌───┴───┐
          │ V4L2  │  (/dev/videoN)
          └───┬───┘
              │
          ┌───┴───┐
          │ v4l2  │  subdev 框架
          │subdev │
          └───┬───┘
              │
     ┌────────┼────────┐
     │        │        │
 ┌───┴──┐ ┌──┴───┐ ┌──┴───┐
 │Sensor│ │ CSI  │ │ ISP  │
 │驱动  │ │接收器│ │ 驱动 │
 └──────┘ └──────┘ └──────┘
```

### Sensor 驱动完整示例
```c
/* my_sensor.c - IMX477 风格的 sensor 驱动 */
#include <linux/module.h>
#include <linux/i2c.h>
#include <linux/v4l2-subdev.h>
#include <media/v4l2-subdev.h>
#include <media/v4l2-ctrls.h>
#include <media/v4l2-device.h>

/* 寄存器地址宽度 */
#define REG_ADDR_16BIT  2
#define REG_DATA_8BIT   1
#define REG_DATA_16BIT  2

/* 传感器模式定义 */
struct sensor_mode {
    const char *name;
    u32 width;
    u32 height;
    u32 hts;        // 总行宽 (像素时钟)
    u32 vts;        // 总行数 (帧长)
    u32 fps;
    u32 bpp;        // bits per pixel
    const struct reg_sequence *regs;
    int reg_count;
};

/* 寄存器序列 */
static const struct reg_sequence mode_4k30[] = {
    {0x0100, 0x00},  // Streaming off
    {0x0136, 0x18},  // EXCK_FREQ [15:8]
    {0x0137, 0x00},  // EXCK_FREQ [7:0]
    {0x0305, 0x02},  // PREPLLCK_VT_DIV
    {0x0306, 0x00},  // PLL_VT_MPY [15:8]
    {0x0307, 0x3C},  // PLL_VT_MPY [7:0]
    {0x030D, 0x02},  // PREPLLCK_OP_DIV
    {0x030E, 0x00},  // PLL_OP_MPY [15:8]
    {0x030F, 0x50},  // PLL_OP_MPY [7:0]
    {0x0340, 0x0C},  // VTS [15:8]
    {0x0341, 0x4E},  // VTS [7:0]
    {0x0342, 0x13},  // HTS [15:8]
    {0x0343, 0x90},  // HTS [7:0]
    {0x0344, 0x00},  // X_ADDR_START [15:8]
    {0x0345, 0x00},  // X_ADDR_START [7:0]
    {0x0346, 0x00},  // Y_ADDR_START [15:8]
    {0x0347, 0x00},  // Y_ADDR_START [7:0]
    {0x0348, 0x0F},  // X_ADDR_END [15:8]
    {0x0349, 0xD7},  // X_ADDR_END [7:0]
    {0x034A, 0x0B},  // Y_ADDR_END [15:8]
    {0x034B, 0xDF},  // Y_ADDR_END [7:0]
    {0x0900, 0x00},  // binning mode
    {0x0100, 0x01},  // Streaming on
};

static const struct sensor_mode supported_modes[] = {
    {
        .name = "4K 4000x3000 @30fps",
        .width = 4000,
        .height = 3000,
        .hts = 5008,
        .vts = 3150,
        .fps = 30,
        .bpp = 10,
        .regs = mode_4k30,
        .reg_count = ARRAY_SIZE(mode_4k30),
    },
    {
        .name = "1080p 1920x1080 @60fps",
        .width = 1920,
        .height = 1080,
        .hts = 5008,
        .vts = 1575,
        .fps = 60,
        .bpp = 10,
        .regs = mode_1080p60,
        .reg_count = ARRAY_SIZE(mode_1080p60),
    },
};

/* 驱动私有数据 */
struct sensor_data {
    struct v4l2_subdev sd;
    struct v4l2_ctrl_handler ctrl_handler;
    struct media_pad pad;
    struct i2c_client *client;
    struct regmap *regmap;
    struct clk *xclk;
    struct gpio_desc *reset_gpio;
    struct gpio_desc *pwdn_gpio;
    
    const struct sensor_mode *cur_mode;
    u32 exposure;
    u32 analog_gain;
    u32 digital_gain;
    bool streaming;
};

/* I2C regmap 配置 */
static const struct regmap_config sensor_regmap_config = {
    .reg_bits = 16,
    .val_bits = 8,
    .cache_type = REGCACHE_RBTREE,
};

/* 寄存器读写 */
static int sensor_write_reg(struct sensor_data *sensor, 
                             u16 reg, u8 val) {
    return regmap_write(sensor->regmap, reg, val);
}

static int sensor_read_reg(struct sensor_data *sensor,
                            u16 reg, u8 *val) {
    unsigned int tmp;
    int ret = regmap_read(sensor->regmap, reg, &tmp);
    *val = tmp & 0xFF;
    return ret;
}

static int sensor_write_reg_sequence(struct sensor_data *sensor,
                                      const struct reg_sequence *regs,
                                      int count) {
    return regmap_multi_reg_write(sensor->regmap, regs, count);
}

/* 设置曝光 */
static int sensor_set_exposure(struct sensor_data *sensor, u32 exp) {
    int ret;
    
    // 寄存器: 0x0202 (coarse integration time)
    ret = sensor_write_reg(sensor, 0x0202, (exp >> 8) & 0xFF);
    if (ret) return ret;
    ret = sensor_write_reg(sensor, 0x0203, exp & 0xFF);
    if (ret) return ret;
    
    sensor->exposure = exp;
    return 0;
}

/* 设置增益 */
static int sensor_set_gain(struct sensor_data *sensor, u32 gain) {
    int ret;
    u8 analog, digital;
    
    // 将增益转换为寄存器值
    // 典型: analog gain = 2^(reg/16)
    analog = (u8)(16 * ilog2(gain));
    
    ret = sensor_write_reg(sensor, 0x0204, analog);
    if (ret) return ret;
    
    sensor->analog_gain = gain;
    return 0;
}

/* 设置模式 */
static int sensor_set_mode(struct sensor_data *sensor,
                            const struct sensor_mode *mode) {
    int ret;
    
    // 停止 streaming
    ret = sensor_write_reg(sensor, 0x0100, 0x00);
    if (ret) return ret;
    
    // 写入模式寄存器
    ret = sensor_write_reg_sequence(sensor, mode->regs, 
                                     mode->reg_count);
    if (ret) return ret;
    
    // 启动 streaming
    ret = sensor_write_reg(sensor, 0x0100, 0x01);
    if (ret) return ret;
    
    sensor->cur_mode = mode;
    
    return 0;
}

/* V4L2 subdev ops */

/* 枚举帧大小 */
static int sensor_enum_frame_size(struct v4l2_subdev *sd,
                                   struct v4l2_subdev_frame_size_enum *fse) {
    struct sensor_data *sensor = sd_to_sensor(sd);
    
    if (fse->index >= ARRAY_SIZE(supported_modes)) {
        return -EINVAL;
    }
    
    fse->min_width = supported_modes[fse->index].width;
    fse->max_width = fse->min_width;
    fse->min_height = supported_modes[fse->index].height;
    fse->max_height = fse->min_height;
    
    return 0;
}

/* 设置帧格式 */
static int sensor_set_fmt(struct v4l2_subdev *sd,
                           struct v4l2_subdev_state *state,
                           struct v4l2_subdev_format *fmt) {
    struct sensor_data *sensor = sd_to_sensor(sd);
    const struct sensor_mode *mode;
    int i;
    
    // 查找匹配的模式
    for (i = 0; i < ARRAY_SIZE(supported_modes); i++) {
        if (supported_modes[i].width <= fmt->format.width &&
            supported_modes[i].height <= fmt->format.height) {
            mode = &supported_modes[i];
            break;
        }
    }
    
    if (i == ARRAY_SIZE(supported_modes)) {
        mode = &supported_modes[0];  // 默认最大分辨率
    }
    
    fmt->format.width = mode->width;
    fmt->format.height = mode->height;
    fmt->format.code = MEDIA_BUS_FMT_SRGGB10_1X10;
    fmt->format.field = V4L2_FIELD_NONE;
    fmt->format.colorspace = V4L2_COLORSPACE_SRGB;
    
    if (fmt->which == V4L2_SUBDEV_FORMAT_ACTIVE) {
        sensor->cur_mode = mode;
    }
    
    return 0;
}

/* 流控制 */
static int sensor_stream(struct v4l2_subdev *sd, int enable) {
    struct sensor_data *sensor = sd_to_sensor(sd);
    int ret;
    
    if (enable) {
        ret = sensor_set_mode(sensor, sensor->cur_mode);
    } else {
        ret = sensor_write_reg(sensor, 0x0100, 0x00);
    }
    
    sensor->streaming = enable;
    return ret;
}

/* V4L2 控件 */
static int sensor_s_ctrl(struct v4l2_ctrl *ctrl) {
    struct sensor_data *sensor = 
        container_of(ctrl->handler, struct sensor_data, ctrl_handler);
    
    switch (ctrl->id) {
    case V4L2_CID_EXPOSURE:
        return sensor_set_exposure(sensor, ctrl->val);
    case V4L2_CID_ANALOGUE_GAIN:
        return sensor_set_gain(sensor, ctrl->val);
    case V4L2_CID_GAIN:
        return sensor_set_gain(sensor, ctrl->val);
    }
    
    return 0;
}

static const struct v4l2_ctrl_ops sensor_ctrl_ops = {
    .s_ctrl = sensor_s_ctrl,
};

/* 控件初始化 */
static int sensor_init_controls(struct sensor_data *sensor) {
    struct v4l2_ctrl_handler *hdl = &sensor->ctrl_handler;
    
    v4l2_ctrl_handler_init(hdl, 3);
    
    v4l2_ctrl_new_std(hdl, &sensor_ctrl_ops,
                       V4L2_CID_EXPOSURE, 1, 65535, 1, 1000);
    v4l2_ctrl_new_std(hdl, &sensor_ctrl_ops,
                       V4L2_CID_ANALOGUE_GAIN, 1, 256, 1, 16);
    v4l2_ctrl_new_std(hdl, &sensor_ctrl_ops,
                       V4L2_CID_GAIN, 1, 4096, 1, 1);
    
    sensor->sd.ctrl_handler = hdl;
    
    return hdl->error;
}

/* 探测函数 */
static int sensor_probe(struct i2c_client *client) {
    struct sensor_data *sensor;
    struct v4l2_subdev *sd;
    u8 chip_id_h, chip_id_l;
    int ret;
    
    // 分配驱动数据
    sensor = devm_kzalloc(&client->dev, sizeof(*sensor), GFP_KERNEL);
    if (!sensor) return -ENOMEM;
    
    sensor->client = client;
    
    // 初始化 regmap
    sensor->regmap = devm_regmap_init_i2c(client, &sensor_regmap_config);
    if (IS_ERR(sensor->regmap)) {
        return PTR_ERR(sensor->regmap);
    }
    
    // 时钟
    sensor->xclk = devm_clk_get(&client->dev, "xclk");
    if (IS_ERR(sensor->xclk)) {
        return PTR_ERR(sensor->xclk);
    }
    clk_prepare_enable(sensor->xclk);
    
    // GPIO
    sensor->reset_gpio = devm_gpiod_get_optional(&client->dev, 
                                                   "reset", GPIOD_OUT_LOW);
    sensor->pwdn_gpio = devm_gpiod_get_optional(&client->dev,
                                                  "powerdown", GPIOD_OUT_LOW);
    
    // 复位
    if (sensor->reset_gpio) {
        gpiod_set_value_cansleep(sensor->reset_gpio, 1);
        msleep(10);
        gpiod_set_value_cansleep(sensor->reset_gpio, 0);
        msleep(10);
    }
    
    // 读取芯片 ID 验证
    ret = sensor_read_reg(sensor, 0x0016, &chip_id_h);
    ret |= sensor_read_reg(sensor, 0x0017, &chip_id_l);
    if (ret || chip_id_h != 0x04 || chip_id_l != 0x77) {
        dev_err(&client->dev, "Unknown chip ID: 0x%02X%02X\n",
                chip_id_h, chip_id_l);
        return -ENODEV;
    }
    
    // 初始化 V4L2 子设备
    sd = &sensor->sd;
    v4l2_i2c_subdev_init(sd, client, &sensor_subdev_ops);
    sd->flags |= V4L2_SUBDEV_FL_HAS_DEVNODE;
    
    // 初始化 media pad
    sensor->pad.flags = MEDIA_PAD_FL_SOURCE;
    sd->entity.function = MEDIA_ENT_F_CAM_SENSOR;
    media_entity_pads_init(&sd->entity, 1, &sensor->pad);
    
    // 初始化控件
    ret = sensor_init_controls(sensor);
    if (ret) goto err_entity;
    
    // 注册子设备
    ret = v4l2_async_register_subdev(sd);
    if (ret) goto err_ctrls;
    
    dev_info(&client->dev, "Sensor probed, chip_id=0x%04X\n",
             (chip_id_h << 8) | chip_id_l);
    
    return 0;

err_ctrls:
    v4l2_ctrl_handler_free(&sensor->ctrl_handler);
err_entity:
    media_entity_cleanup(&sd->entity);
    return ret;
}

/* 设备树匹配 */
static const struct of_device_id sensor_of_match[] = {
    { .compatible = "vendor,my-sensor" },
    { /* sentinel */ },
};

static struct i2c_driver sensor_i2c_driver = {
    .driver = {
        .name = "my-sensor",
        .of_match_table = sensor_of_match,
    },
    .probe_new = sensor_probe,
    .remove = sensor_remove,
};

module_i2c_driver(sensor_i2c_driver);

MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("CMOS Image Sensor driver");
MODULE_VERSION("1.0");
```

## 5. ISP 图像处理管线

### ISP 处理流程
```
Sensor RAW 数据 (RGGB/BGGR/GRBG/GBRG)
    │
    ▼
┌─────────────────────────────┐
│  Black Level Correction (BLC)│  → 暗电流补偿
├─────────────────────────────┤
│  Defect Pixel Correction     │  → 坏点修复
├─────────────────────────────┤
│  Lens Shading Correction     │  → 暗角补偿 (LSC)
├─────────────────────────────┤
│  White Balance (WB)          │  → 白平衡 (R/G/B 增益)
├─────────────────────────────┤
│  Demosaic                   │  → 去马赛克 (Bayer→RGB)
├─────────────────────────────┤
│  Color Correction (CCM)     │  → 色彩校正矩阵 (3x3)
├─────────────────────────────┤
│  Gamma Correction           │  → Gamma 曲线 (γ=2.2)
├─────────────────────────────┤
│  Noise Reduction (NR)       │  → 降噪 (2D/3D/时域)
├─────────────────────────────┤
│  Edge Enhancement (EE)      │  → 锐化
├─────────────────────────────┤
│  Color Space Conversion     │  → RGB→YUV (BT.601/709)
├─────────────────────────────┤
│  Auto Exposure (AE)         │  → 自动曝光
├─────────────────────────────┤
│  Auto White Balance (AWB)   │  → 自动白平衡
├─────────────────────────────┤
│  Auto Focus (AF)            │  → 自动对焦
└─────────────────────────────┘
    │
    ▼
输出: YUV422 / YUV420 / H.264 编码
```

### 3A 算法概述

#### AE (自动曝光)
```
目标: 亮度适中 (目标亮度 ~128 for 8-bit)

算法流程:
1. 统计当前帧亮度 (分区加权平均)
2. 计算亮度误差: err = target - current
3. PID 控制调整曝光:
   exposure += Kp * err + Ki * integral + Kd * derivative
4. 限制曝光范围 [min_exp, max_exp]
5. 写入 sensor 寄存器

曝光策略:
- ISO 优先: 固定增益，调曝光时间
- 快门优先: 固定快门，调增益
- 自动: 平衡增益和快门

AE 收敛时间目标: < 3 帧
```

#### AWB (自动白平衡)
```
目标: 白色物体在图像中显示为白色

色温范围: 2500K (暖) ~ 10000K (冷)

算法:
1. 统计色温区域 (灰度世界/白点检测)
2. 计算 R/G/B 通道增益
3. 应用白平衡增益:
   R' = R × gain_R
   G' = G × gain_G
   B' = B × gain_B

色温检测方法:
- 灰度世界假设
- 白点检测 (高亮度+低饱和度)
- 色温传感器辅助
```

#### AF (自动对焦)
```
对比度检测 AF (CDAF):
1. 计算图像高频分量 (拉普拉斯/梯度)
2. 移动镜头到不同位置
3. 找到高频分量最大的位置
4. 粗搜索 → 精搜索 → 爬山法

相位检测 AF (PDAF):
1. 传感器像素中嵌入相位检测像素
2. 计算左右像素相位差
3. 直接得到对焦方向和距离
4. 速度快，一次测量即可

激光/ToF 辅助:
1. 测量目标距离
2. 直接移动镜头到对应位置
3. 速度最快
```
