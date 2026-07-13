# STM32 Bootloader 开发

## 1. 启动模式

### STM32 启动配置 (BOOT 引脚)
| BOOT1 | BOOT0 | 启动模式 | 说明 |
|-------|-------|----------|------|
| X | 0 | 从 Flash 启动 | 正常模式 (0x08000000) |
| 0 | 1 | 从 System Memory | 内置 Bootloader (串口/USB) |
| 1 | 1 | 从 SRAM 启动 | 调试模式 (0x20000000) |

### 自定义 Bootloader 启动流程
```
上电/复位
    │
    ├── 读取 Boot 引脚
    │       │
    │       ├── Flash 启动 → 检查升级标志
    │       │       │
    │       │       ├── 无升级请求 → 验证 App → 跳转 App
    │       │       ├── 有升级请求 → 进入升级模式
    │       │       └── App 无效 → 进入恢复模式
    │       │
    │       └── System Memory → 进入内置 Bootloader
    │
    └── 超时/看门狗复位 → 重新开始
```

## 2. Flash 分区规划

### STM32F407 Flash 布局 (1MB)
```
地址范围                    用途          大小
0x08000000 - 0x08007FFF    Bootloader    32KB
0x08008000 - 0x0800BFFF    Config        16KB
0x0800C000 - 0x0800FFFF    Backup        16KB
0x08010000 - 0x0804FFFF    App Slot A    256KB
0x08050000 - 0x0808FFFF    App Slot B    256KB
0x08090000 - 0x080FFFFF    User Data     448KB
```

### STM32L476 Flash 布局 (1MB, 双 Bank)
```
Bank 1:
0x08000000 - 0x08001FFF    Bootloader    8KB
0x08002000 - 0x08003FFF    Config        8KB
0x08004000 - 0x0803FFFF    App Slot A    248KB

Bank 2:
0x08040000 - 0x0807BFFF    App Slot B    240KB
0x0807C000 - 0x0807DFFF    Backup        8KB
0x0807E000 - 0x0807FFFF    User Data     8KB
```

### Linker Script 配置
```ld
/* bootloader.ld */
MEMORY
{
    FLASH (rx)  : ORIGIN = 0x08000000, LENGTH = 32K
    RAM   (rwx) : ORIGIN = 0x20000000, LENGTH = 128K
}

/* app_slot_a.ld */
MEMORY
{
    FLASH (rx)  : ORIGIN = 0x08010000, LENGTH = 256K
    RAM   (rwx) : ORIGIN = 0x20000000, LENGTH = 128K
}

/* app_slot_b.ld */
MEMORY
{
    FLASH (rx)  : ORIGIN = 0x08050000, LENGTH = 256K
    RAM   (rwx) : ORIGIN = 0x20000000, LENGTH = 128K
}
```

## 3. 完整 Bootloader 源码

### 主文件
```c
/* bootloader/main.c */
#include "stm32f4xx_hal.h"
#include "boot_config.h"
#include "flash_driver.h"
#include "comm_interface.h"
#include "crypto_verify.h"
#include "upgrade_manager.h"

/* 看门狗初始化 */
static void IWDG_Init(void) {
    IWDG_HandleTypeDef hiwdg;
    hiwdg.Instance = IWDG;
    hiwdg.Init.Prescaler = IWDG_PRESCALER_256;
    hiwdg.Init.Reload = 4095;  // ~26s 超时
    HAL_IWDG_Init(&hiwdg);
}

/* 时钟配置 */
static void SystemClock_Config(void) {
    RCC_OscInitTypeDef osc = {0};
    osc.OscillatorType = RCC_OSCILLATORTYPE_HSE;
    osc.HSEState = RCC_HSE_ON;
    osc.PLL.PLLState = RCC_PLL_ON;
    osc.PLL.PLLSource = RCC_PLLSOURCE_HSE;
    osc.PLL.PLLM = 8;
    osc.PLL.PLLN = 336;
    osc.PLL.PLLP = RCC_PLLP_DIV2;
    osc.PLL.PLLQ = 7;
    HAL_RCC_OscConfig(&osc);

    RCC_ClkInitTypeDef clk = {0};
    clk.ClockType = RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_SYSCLK
                  | RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
    clk.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
    clk.AHBCLKDivider = RCC_SYSCLK_DIV1;
    clk.APB1CLKDivider = RCC_HCLK_DIV4;
    clk.APB2CLKDivider = RCC_HCLK_DIV2;
    HAL_RCC_ClockConfig(&clk, FLASH_LATENCY_5);
}

/* 诊断信息 */
typedef struct {
    uint32_t reset_reason;     // 复位原因
    uint32_t boot_count;       // 启动计数
    uint32_t last_error;       // 最后错误码
    uint32_t uptime;           // 运行时间
} DiagInfo_t;

static DiagInfo_t *diag_info = (DiagInfo_t *)DIAG_INFO_ADDR;

/* 检测复位原因 */
static uint32_t detect_reset_reason(void) {
    uint32_t reason = RESET_UNKNOWN;
    
    if (__HAL_RCC_GET_FLAG(RCC_FLAG_IWDGRST)) {
        reason = RESET_WATCHDOG;
    } else if (__HAL_RCC_GET_FLAG(RCC_FLAG_SFTRST)) {
        reason = RESET_SOFTWARE;
    } else if (__HAL_RCC_GET_FLAG(RCC_FLAG_PORRST)) {
        reason = RESET_POWER_ON;
    } else if (__HAL_RCC_GET_FLAG(RCC_FLAG_PINRST)) {
        reason = RESET_PIN;
    }
    
    __HAL_RCC_CLEAR_RESET_FLAGS();
    return reason;
}

/* Bootloader 入口 */
int main(void) {
    HAL_Init();
    SystemClock_Config();
    
    // 检测复位原因
    diag_info->reset_reason = detect_reset_reason();
    diag_info->boot_count++;
    
    // 初始化通信接口
    comm_init();
    
    // 初始化看门狗
    IWDG_Init();
    
    // 检查是否需要进入升级模式
    if (comm_has_upgrade_request() || 
        diag_info->reset_reason == RESET_SOFTWARE) {
        // 进入升级模式
        upgrade_mode_loop();
    }
    
    // 正常启动流程
    BootConfig_t config;
    read_boot_config(&config);
    
    uint32_t app_addr = select_boot_slot(&config);
    
    if (app_addr != 0) {
        // 验证固件
        if (verify_app_signature(app_addr) == VERIFY_OK) {
            // 清除看门狗
            HAL_IWDG_Refresh(&hiwdg);
            
            // 标记启动成功
            config.boot_attempts++;
            if (config.boot_attempts > MAX_BOOT_ATTEMPTS) {
                // 启动失败过多，切换到备用槽
                switch_boot_slot(&config);
                config.boot_attempts = 0;
            }
            write_boot_config(&config);
            
            // 跳转到应用
            jump_to_application(app_addr);
        }
    }
    
    // 所有启动尝试失败，进入恢复模式
    diag_info->last_error = ERROR_BOOT_FAILED;
    recovery_mode_loop();
    
    while (1) {
        HAL_IWDG_Refresh(&hiwdg);
    }
}
```

### 升级管理器
```c
/* bootloader/upgrade_manager.c */
#include "upgrade_manager.h"
#include "flash_driver.h"
#include "protocol.h"
#include "crypto_verify.h"

static UpgradeState_t state = STATE_IDLE;
static uint32_t target_addr = 0;
static uint32_t received_bytes = 0;
static uint32_t total_bytes = 0;
static uint32_t packet_count = 0;
static SHA256_CTX sha_ctx;

/* 开始升级 */
int upgrade_start(UpgradeStartCmd_t *cmd) {
    if (state != STATE_IDLE) {
        return ERR_BUSY;
    }
    
    // 验证硬件版本兼容性
    if (!is_hw_version_compatible(cmd->hw_version)) {
        return ERR_HW_INCOMPATIBLE;
    }
    
    // 验证签名 (可选，整包预验证)
    if (cmd->flags & UPGRADE_FLAG_VERIFY_START) {
        if (!verify_package_signature(cmd)) {
            return ERR_SIGNATURE;
        }
    }
    
    // 选择目标槽位
    target_addr = get_next_slot_addr();
    total_bytes = cmd->firmware_size;
    received_bytes = 0;
    packet_count = 0;
    
    // 初始化 SHA256
    sha256_init(&sha_ctx);
    
    // 擦除目标 Flash
    uint32_t sectors = (total_bytes + FLASH_SECTOR_SIZE - 1) 
                       / FLASH_SECTOR_SIZE;
    if (flash_erase_sectors(target_addr, sectors) != 0) {
        return ERR_FLASH_ERASE;
    }
    
    state = STATE_RECEIVING;
    return ERR_NONE;
}

/* 接收数据包 */
int upgrade_data(uint8_t *data, uint32_t len) {
    if (state != STATE_RECEIVING) {
        return ERR_INVALID_STATE;
    }
    
    // 检查长度
    if (received_bytes + len > total_bytes) {
        return ERR_OVERFLOW;
    }
    
    // 写入 Flash
    if (flash_write(target_addr + received_bytes, data, len) != 0) {
        state = STATE_ERROR;
        return ERR_FLASH_WRITE;
    }
    
    // 更新 SHA256
    sha256_update(&sha_ctx, data, len);
    
    received_bytes += len;
    packet_count++;
    
    // 喂狗
    HAL_IWDG_Refresh(&hiwdg);
    
    return ERR_NONE;
}

/* 验证升级包 */
int upgrade_verify(uint8_t *expected_hash) {
    if (state != STATE_RECEIVING) {
        return ERR_INVALID_STATE;
    }
    
    if (received_bytes != total_bytes) {
        return ERR_SIZE_MISMATCH;
    }
    
    state = STATE_VERIFYING;
    
    // 计算最终 SHA256
    uint8_t hash[32];
    sha256_final(&sha_ctx, hash);
    
    // 比较哈希
    if (memcmp(hash, expected_hash, 32) != 0) {
        state = STATE_ERROR;
        return ERR_HASH_MISMATCH;
    }
    
    // 验证应用头 (栈指针、复位向量)
    if (!verify_app_header(target_addr)) {
        state = STATE_ERROR;
        return ERR_INVALID_HEADER;
    }
    
    state = STATE_VERIFIED;
    return ERR_NONE;
}

/* 应用升级 */
int upgrade_apply(void) {
    if (state != STATE_VERIFIED) {
        return ERR_INVALID_STATE;
    }
    
    // 更新启动配置
    BootConfig_t config;
    read_boot_config(&config);
    
    config.active_slot = (config.active_slot == SLOT_A) 
                         ? SLOT_B : SLOT_A;
    config.boot_attempts = 0;
    config.firmware_version++;
    config.upgrade_pending = 0;
    
    write_boot_config(&config);
    
    state = STATE_IDLE;
    
    // 延迟确保写入完成
    HAL_Delay(100);
    
    // 重启
    NVIC_SystemReset();
    
    return ERR_NONE;  // 不会执行到这里
}

/* 进度回调 */
uint32_t upgrade_get_progress(void) {
    if (total_bytes == 0) return 0;
    return (received_bytes * 100) / total_bytes;
}
```

### 协议处理器
```c
/* bootloader/protocol.c */
#include "protocol.h"
#include "upgrade_manager.h"

#define FRAME_SOF   0xAA
#define FRAME_EOF   0x55

/* 帧解析状态机 */
typedef enum {
    PARSE_SOF,
    PARSE_CMD,
    PARSE_LEN_H,
    PARSE_LEN_L,
    PARSE_DATA,
    PARSE_CRC_H,
    PARSE_CRC_L,
    PARSE_EOF,
} ParseState_t;

static ParseState_t parse_state = PARSE_SOF;
static ProtocolFrame_t rx_frame;
static uint16_t data_index = 0;

/* 处理接收到的字节 */
void protocol_process_byte(uint8_t byte) {
    switch (parse_state) {
    case PARSE_SOF:
        if (byte == FRAME_SOF) {
            rx_frame.sof = byte;
            parse_state = PARSE_CMD;
        }
        break;
        
    case PARSE_CMD:
        rx_frame.cmd = byte;
        parse_state = PARSE_LEN_H;
        break;
        
    case PARSE_LEN_H:
        rx_frame.len = byte << 8;
        parse_state = PARSE_LEN_L;
        break;
        
    case PARSE_LEN_L:
        rx_frame.len |= byte;
        data_index = 0;
        parse_state = (rx_frame.len > 0) ? PARSE_DATA : PARSE_CRC_H;
        break;
        
    case PARSE_DATA:
        rx_frame.data[data_index++] = byte;
        if (data_index >= rx_frame.len) {
            parse_state = PARSE_CRC_H;
        }
        break;
        
    case PARSE_CRC_H:
        rx_frame.crc = byte << 8;
        parse_state = PARSE_CRC_L;
        break;
        
    case PARSE_CRC_L:
        rx_frame.crc |= byte;
        parse_state = PARSE_EOF;
        break;
        
    case PARSE_EOF:
        if (byte == FRAME_EOF) {
            rx_frame.eof = byte;
            // 验证 CRC
            uint16_t calc_crc = crc16(rx_frame.data, rx_frame.len);
            if (calc_crc == rx_frame.crc) {
                // 处理命令
                process_command(&rx_frame);
            } else {
                send_response(rx_frame.cmd, ERR_CRC, NULL, 0);
            }
        }
        parse_state = PARSE_SOF;
        break;
    }
}

/* 处理命令 */
static void process_command(ProtocolFrame_t *frame) {
    uint8_t response_data[64];
    uint16_t resp_len = 0;
    int result;
    
    switch (frame->cmd) {
    case CMD_UPGRADE_START: {
        UpgradeStartCmd_t *cmd = (UpgradeStartCmd_t *)frame->data;
        result = upgrade_start(cmd);
        break;
    }
    
    case CMD_UPGRADE_DATA:
        result = upgrade_data(frame->data, frame->len);
        break;
        
    case CMD_UPGRADE_VERIFY:
        result = upgrade_verify(frame->data);
        break;
        
    case CMD_UPGRADE_APPLY:
        result = upgrade_apply();
        break;
        
    case CMD_QUERY_STATUS: {
        StatusResponse_t *resp = (StatusResponse_t *)response_data;
        resp->state = upgrade_get_state();
        resp->progress = upgrade_get_progress();
        resp->error_code = upgrade_get_last_error();
        resp_len = sizeof(StatusResponse_t);
        result = ERR_NONE;
        break;
    }
    
    case CMD_QUERY_VERSION: {
        VersionResponse_t *resp = (VersionResponse_t *)response_data;
        read_current_version(resp);
        resp_len = sizeof(VersionResponse_t);
        result = ERR_NONE;
        break;
    }
    
    case CMD_RESET:
        NVIC_SystemReset();
        break;
        
    default:
        result = ERR_UNKNOWN_CMD;
        break;
    }
    
    send_response(frame->cmd, result, response_data, resp_len);
}

/* 发送响应 */
void send_response(uint8_t cmd, int result, 
                   uint8_t *data, uint16_t len) {
    ProtocolFrame_t tx;
    tx.sof = FRAME_SOF;
    tx.cmd = cmd | 0x80;  // 响应标志
    tx.len = len + 1;     // +1 for result code
    tx.data[0] = result;
    if (len > 0 && data != NULL) {
        memcpy(tx.data + 1, data, len);
    }
    tx.crc = crc16(tx.data, tx.len);
    tx.eof = FRAME_EOF;
    
    comm_send((uint8_t *)&tx, 7 + tx.len);
}
```

## 4. 看门狗保护

### 独立看门狗 (IWDG) 配置
```c
/* 超时计算: T = (4 * 2^prescaler * reload) / LSI_freq
 * LSI = 32kHz
 * prescaler = 256, reload = 4095
 * T = (4 * 256 * 4095) / 32000 ≈ 131 秒 */

/* 在 Bootloader 中 */
void feed_watchdog(void) {
    HAL_IWDG_Refresh(&hiwdg);
}

/* 在升级过程中定期喂狗 */
void upgrade_with_watchdog(void) {
    while (receiving_data) {
        receive_packet();
        write_to_flash();
        feed_watchdog();  // 每个包喂一次
    }
}
```

### 窗口看门狗 (WWDG) 用于应用监控
```c
/* 应用层: 定期喂狗 */
void WWDG_Init(void) {
    __HAL_RCC_WWDG_CLK_ENABLE();
    
    hwwdg.Instance = WWDG;
    hwwdg.Init.Prescaler = WWDG_PRESCALER_8;
    hwwdg.Init.Window = 100;      // 窗口上限
    hwwdg.Init.Counter = 127;     // 计数器初始值
    hwwdg.Init.EWIMode = WWDG_EWI_ENABLE;  // 早期唤醒中断
    HAL_WWDG_Init(&hwwdg);
}

/* 在主循环中喂狗 (必须在窗口内) */
void main_loop(void) {
    while (1) {
        process_tasks();
        
        // 在正确的时间窗口内喂狗
        if (HAL_WWDG_GetCounter(&hwwdg) < 100) {
            HAL_WWDG_Refresh(&hwwdg);
        }
    }
}
```
