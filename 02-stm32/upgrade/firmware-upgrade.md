# STM32 固件升级方案

## 1. 升级架构设计

### 整体架构
```
┌──────────────────────────────────────────────────────────┐
│                      云端/APP                             │
│   ┌─────────┐    ┌──────────┐    ┌──────────────┐       │
│   │ OTA 服务器│    │ 手机 APP │    │ PC 工具 (USB)│       │
│   └────┬─────┘    └────┬─────┘    └──────┬───────┘       │
└────────┼───────────────┼────────────────┼────────────────┘
         │  HTTPS/MQTT   │  BLE/WiFi      │  USB CDC/DFU
         │               │                │
┌────────┴───────────────┴────────────────┴────────────────┐
│                    设备 (STM32)                            │
│  ┌──────────────────────────────────────────────────┐    │
│  │                  Bootloader                        │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────────┐  │    │
│  │  │ 通信模块  │ │ 升级引擎  │ │ 安全验证 (RSA)   │  │    │
│  │  └──────────┘ └──────────┘ └──────────────────┘  │    │
│  └──────────────────────────┬───────────────────────┘    │
│                              │                            │
│  ┌───────────────────────────┴────────────────────────┐  │
│  │                  Flash 布局                         │  │
│  │  ┌────────┬────────┬────────┬────────┬──────────┐  │  │
│  │  │ Boot   │ App A  │ App B  │ Backup │ Config   │  │  │
│  │  │ (32KB) │ (256KB)│ (256KB)│ (64KB) │ (16KB)   │  │  │
│  │  └────────┴────────┴────────┴────────┴──────────┘  │  │
│  └─────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### A/B 升级流程
```
┌─────────────┐     ┌─────────────┐
│   Slot A    │     │   Slot B    │
│  (当前运行)  │     │  (待升级)    │
│  App v1.0   │     │  空/v旧     │
└──────┬──────┘     └──────┬──────┘
       │                   │
       │    1. 接收升级包    │
       │    2. 写入 Slot B  │
       │    3. 校验签名     │
       │    4. 设置标志     │
       │    5. 重启         │
       │                   │
       │    ┌───────────────┘
       │    │
       ▼    ▼
  Bootloader 检查标志
       │
       ├── 标志有效 → 跳转 Slot B (App v2.0)
       │                    │
       │                    ├── 运行成功 → 标记成功
       │                    └── 运行失败 → 计数器++
       │                         │
       │                         └── 超过阈值 → 回滚 Slot A
       │
       └── 标志无效 → 跳转 Slot A
```

## 2. Bootloader 开发

### Bootloader 核心代码
```c
/* bootloader/main.c */
#include "stm32f4xx_hal.h"
#include "flash.h"
#include "crypto.h"
#include "uart_protocol.h"

#define APP_A_ADDR    0x08010000   // Slot A 起始地址
#define APP_B_ADDR    0x08050000   // Slot B 起始地址
#define BACKUP_ADDR   0x08090000   // 备份区
#define CONFIG_ADDR   0x080A0000   // 配置区
#define APP_SIZE      (256 * 1024) // 256KB

#define UPGRADE_FLAG_MAGIC   0x55AA55AA
#define MAX_BOOT_ATTEMPTS    3

/* 升级标志结构体 */
typedef struct {
    uint32_t magic;           // 魔数
    uint32_t version;         // 固件版本
    uint32_t target_slot;     // 目标槽位 (0=A, 1=B)
    uint32_t boot_attempts;   // 启动尝试次数
    uint32_t is_valid;        // 固件有效标志
    uint32_t checksum;        // 结构体校验
} UpgradeFlag_t;

/* 读取升级标志 */
static int read_upgrade_flag(UpgradeFlag_t *flag) {
    flash_read(CONFIG_ADDR, (uint8_t *)flag, sizeof(UpgradeFlag_t));
    
    if (flag->magic != UPGRADE_FLAG_MAGIC) {
        return -1;  // 无效标志
    }
    
    // 验证校验和
    uint32_t calc_crc = calc_crc32((uint8_t *)flag, 
                                    sizeof(UpgradeFlag_t) - 4);
    if (calc_crc != flag->checksum) {
        return -2;  // 校验失败
    }
    
    return 0;
}

/* 写入升级标志 */
static int write_upgrade_flag(UpgradeFlag_t *flag) {
    flag->magic = UPGRADE_FLAG_MAGIC;
    flag->checksum = calc_crc32((uint8_t *)flag, 
                                 sizeof(UpgradeFlag_t) - 4);
    
    flash_erase(CONFIG_ADDR, 1);
    flash_write(CONFIG_ADDR, (uint8_t *)flag, sizeof(UpgradeFlag_t));
    
    return 0;
}

/* 验证固件完整性 */
static int verify_firmware(uint32_t addr, uint32_t size, 
                           const uint8_t *expected_hash) {
    uint8_t hash[32];
    
    // 计算 SHA256
    sha256_calc((uint8_t *)addr, size, hash);
    
    // 比较哈希
    if (memcmp(hash, expected_hash, 32) != 0) {
        return -1;
    }
    
    // 验证栈指针 (必须在 RAM 范围内)
    uint32_t sp = *(volatile uint32_t *)addr;
    if (sp < 0x20000000 || sp > 0x20020000) {
        return -2;
    }
    
    // 验证复位向量 (必须在 Flash 范围内)
    uint32_t reset_vec = *(volatile uint32_t *)(addr + 4);
    if (reset_vec < 0x08000000 || reset_vec > 0x08100000) {
        return -3;
    }
    
    return 0;
}

/* 跳转到应用程序 */
static void jump_to_app(uint32_t app_addr) {
    // 禁用所有中断
    __disable_irq();
    
    // 设置 MSP
    __set_MSP(*(volatile uint32_t *)app_addr);
    
    // 获取复位向量
    uint32_t jump_addr = *(volatile uint32_t *)(app_addr + 4);
    
    // 重新映射中断向量表
    SCB->VTOR = app_addr;
    
    // 重新启用中断
    __enable_irq();
    
    // 跳转
    void (*reset_handler)(void) = (void (*)(void))jump_addr;
    reset_handler();
}

/* Bootloader 主函数 */
int main(void) {
    HAL_Init();
    SystemClock_Config();
    
    // 初始化通信接口 (UART/USB/BLE)
    comm_init();
    
    UpgradeFlag_t flag;
    int ret = read_upgrade_flag(&flag);
    
    // 检查是否有升级请求
    if (comm_check_upgrade_request()) {
        // 进入升级模式
        perform_upgrade();
    }
    
    // 正常启动流程
    if (ret == 0 && flag.is_valid) {
        uint32_t app_addr;
        
        if (flag.target_slot == 0) {
            app_addr = APP_A_ADDR;
        } else {
            app_addr = APP_B_ADDR;
        }
        
        // 验证固件
        if (verify_firmware(app_addr, APP_SIZE, NULL) == 0) {
            // 检查启动尝试次数
            if (flag.boot_attempts < MAX_BOOT_ATTEMPTS) {
                flag.boot_attempts++;
                write_upgrade_flag(&flag);
                
                // 跳转到应用
                jump_to_app(app_addr);
            } else {
                // 启动失败过多，回滚
                rollback_firmware();
            }
        }
    }
    
    // 如果所有启动尝试都失败，进入恢复模式
    enter_recovery_mode();
    
    while (1) {
        // 处理恢复模式命令
        recovery_process();
    }
}

/* 执行升级 */
int perform_upgrade(void) {
    uint32_t target_addr;
    UpgradeFlag_t flag;
    
    read_upgrade_flag(&flag);
    
    // 确定目标槽位
    if (flag.target_slot == 0) {
        target_addr = APP_A_ADDR;
    } else {
        target_addr = APP_B_ADDR;
    }
    
    // 1. 擦除目标区域
    flash_erase(target_addr, APP_SIZE / FLASH_SECTOR_SIZE);
    
    // 2. 接收并写入固件
    uint32_t offset = 0;
    uint8_t buffer[256];
    
    while (offset < APP_SIZE) {
        int len = comm_receive_data(buffer, sizeof(buffer));
        if (len <= 0) break;
        
        flash_write(target_addr + offset, buffer, len);
        offset += len;
        
        // 上报进度
        comm_send_progress(offset, APP_SIZE);
    }
    
    // 3. 验证固件
    uint8_t hash[32];
    comm_receive_hash(hash);
    
    if (verify_firmware(target_addr, offset, hash) != 0) {
        comm_send_error(ERROR_VERIFY_FAILED);
        return -1;
    }
    
    // 4. 更新升级标志
    flag.is_valid = 1;
    flag.version++;
    flag.boot_attempts = 0;
    write_upgrade_flag(&flag);
    
    // 5. 重启
    comm_send_success();
    HAL_Delay(100);
    NVIC_SystemReset();
    
    return 0;
}
```

## 3. 通信协议设计

### 升级协议帧格式
```
┌──────┬──────┬──────┬──────────┬──────┬──────┐
│ SOF  │ CMD  │ LEN  │  DATA    │ CRC  │ EOF  │
│ 1B   │ 1B   │ 2B   │  nB      │ 2B   │ 1B   │
│ 0xAA │      │      │          │      │ 0x55 │
└──────┴──────┴──────┴──────────┴──────┴──────┘
```

### 命令定义
```c
/* protocol.h */
#define CMD_UPGRADE_START    0x01  // 开始升级
#define CMD_UPGRADE_DATA     0x02  // 数据传输
#define CMD_UPGRADE_END      0x03  // 传输完成
#define CMD_UPGRADE_VERIFY   0x04  // 验证固件
#define CMD_UPGRADE_APPLY    0x05  // 应用升级
#define CMD_QUERY_STATUS     0x10  // 查询状态
#define CMD_QUERY_VERSION    0x11  // 查询版本
#define CMD_RESET            0x20  // 重启设备

#define ACK_SUCCESS          0x00
#define ACK_ERROR_CRC        0x01
#define ACK_ERROR_VERIFY     0x02
#define ACK_ERROR_FLASH      0x03
#define ACK_ERROR_SIZE       0x04

typedef struct {
    uint8_t  sof;           // 0xAA
    uint8_t  cmd;           // 命令码
    uint16_t len;           // 数据长度
    uint8_t  data[256];     // 数据
    uint16_t crc;           // CRC16
    uint8_t  eof;           // 0x55
} __attribute__((packed)) ProtocolFrame_t;
```

### 协议处理状态机
```c
typedef enum {
    STATE_IDLE,
    STATE_UPGRADING,
    STATE_VERIFYING,
    STATE_APPLYING,
} UpgradeState_t;

static UpgradeState_t state = STATE_IDLE;
static uint32_t received_size = 0;
static uint32_t expected_size = 0;

void process_frame(ProtocolFrame_t *frame) {
    switch (frame->cmd) {
    case CMD_UPGRADE_START: {
        if (state != STATE_IDLE) {
            send_nak(ACK_ERROR_CRC);
            return;
        }
        
        // 解析升级信息
        UpgradeStart_t *info = (UpgradeStart_t *)frame->data;
        expected_size = info->firmware_size;
        received_size = 0;
        
        // 擦除目标 Flash
        uint32_t target = get_target_slot_addr();
        flash_erase(target, expected_size / FLASH_SECTOR_SIZE + 1);
        
        state = STATE_UPGRADING;
        send_ack(ACK_SUCCESS);
        break;
    }
    
    case CMD_UPGRADE_DATA: {
        if (state != STATE_UPGRADING) {
            send_nak(ACK_ERROR_CRC);
            return;
        }
        
        uint32_t target = get_target_slot_addr();
        flash_write(target + received_size, frame->data, frame->len);
        received_size += frame->len;
        
        send_ack(ACK_SUCCESS);
        break;
    }
    
    case CMD_UPGRADE_END: {
        if (state != STATE_UPGRADING) {
            send_nak(ACK_ERROR_CRC);
            return;
        }
        
        if (received_size != expected_size) {
            send_nak(ACK_ERROR_SIZE);
            state = STATE_IDLE;
            return;
        }
        
        state = STATE_VERIFYING;
        send_ack(ACK_SUCCESS);
        break;
    }
    
    case CMD_UPGRADE_VERIFY: {
        uint8_t *expected_hash = frame->data;
        uint32_t target = get_target_slot_addr();
        
        if (verify_firmware(target, received_size, expected_hash) == 0) {
            send_ack(ACK_SUCCESS);
        } else {
            send_nak(ACK_ERROR_VERIFY);
            state = STATE_IDLE;
        }
        break;
    }
    
    case CMD_UPGRADE_APPLY: {
        // 更新标志并重启
        UpgradeFlag_t flag;
        read_upgrade_flag(&flag);
        flag.target_slot = (flag.target_slot == 0) ? 1 : 0;
        flag.is_valid = 1;
        flag.version++;
        flag.boot_attempts = 0;
        write_upgrade_flag(&flag);
        
        send_ack(ACK_SUCCESS);
        HAL_Delay(100);
        NVIC_SystemReset();
        break;
    }
    
    default:
        send_nak(ACK_ERROR_CRC);
        break;
    }
}
```

## 4. 无线 OTA (BLE)

### BLE OTA 流程
```
手机 APP                              设备
   │                                    │
   │─── BLE 连接 ──────────────────────→│
   │                                    │
   │─── OTA Start (版本, 大小, CRC) ──→│
   │←── ACK ───────────────────────────│
   │                                    │
   │─── OTA Data (每包 244B) ─────────→│
   │←── ACK (含进度) ─────────────────│
   │    ... (重复 N 次) ...             │
   │                                    │
   │─── OTA End (总包数, 校验) ────────→│
   │←── ACK ───────────────────────────│
   │                                    │
   │─── OTA Verify (SHA256) ──────────→│
   │←── Verify Result ────────────────│
   │                                    │
   │─── OTA Apply ────────────────────→│
   │                                    │ 设备重启
```

### BLE GATT 服务定义
```c
/* BLE OTA Service UUID */
#define OTA_SERVICE_UUID        0xFF00
#define OTA_CMD_CHAR_UUID       0xFF01  // 写: 命令通道
#define OTA_DATA_CHAR_UUID      0xFF02  // 写: 数据通道 (MTU 最大)
#define OTA_STATUS_CHAR_UUID    0xFF03  // 读/通知: 状态通道

/* GATT 服务表 */
static const gatt_attribute_t ota_service[] = {
    // 服务声明
    { PRIMARY_SERVICE, { OTA_SERVICE_UUID } },
    
    // 命令特征
    { CHARACTERISTIC, { GATT_NOTIFY | GATT_WRITE } },
    { OTA_CMD_CHAR_UUID, { 0 } },
    
    // 数据特征 (使用 Write Without Response 提高速度)
    { CHARACTERISTIC, { GATT_WRITE_WO_RSP } },
    { OTA_DATA_CHAR_UUID, { 0 } },
    
    // 状态特征 (通知)
    { CHARACTERISTIC, { GATT_NOTIFY } },
    { OTA_STATUS_CHAR_UUID, { 0 } },
};
```

## 5. Flash 驱动

### STM32 Flash 操作
```c
/* flash_driver.c */
#include "stm32f4xx_hal.h"

#define FLASH_SECTOR_SIZE    (128 * 1024)  // F4 系列扇区大小

/* 擦除 Flash 扇区 */
int flash_erase(uint32_t addr, uint32_t num_sectors) {
    HAL_FLASH_Unlock();
    
    FLASH_EraseInitTypeDef erase;
    uint32_t sector_error;
    
    erase.TypeErase = FLASH_TYPEERASE_SECTORS;
    erase.Sector = addr_to_sector(addr);
    erase.NbSectors = num_sectors;
    erase.VoltageRange = FLASH_VOLTAGE_RANGE_3;  // 2.7-3.6V
    
    HAL_StatusTypeDef status = HAL_FLASHEx_Erase(&erase, &sector_error);
    
    HAL_FLASH_Lock();
    
    return (status == HAL_OK) ? 0 : -1;
}

/* 写入 Flash (字节对齐) */
int flash_write(uint32_t addr, const uint8_t *data, uint32_t len) {
    HAL_FLASH_Unlock();
    
    // 按字 (32-bit) 写入
    for (uint32_t i = 0; i < len; i += 4) {
        uint32_t word = 0xFFFFFFFF;
        uint32_t remaining = len - i;
        
        if (remaining >= 4) {
            memcpy(&word, data + i, 4);
        } else {
            memcpy(&word, data + i, remaining);
        }
        
        if (HAL_FLASH_Program(FLASH_TYPEPROGRAM_WORD, 
                               addr + i, word) != HAL_OK) {
            HAL_FLASH_Lock();
            return -1;
        }
    }
    
    HAL_FLASH_Lock();
    return 0;
}

/* 读取 Flash */
int flash_read(uint32_t addr, uint8_t *buf, uint32_t len) {
    memcpy(buf, (void *)addr, len);
    return 0;
}

/* 获取扇区编号 */
static uint32_t addr_to_sector(uint32_t addr) {
    if (addr < 0x08010000) return FLASH_SECTOR_0;
    if (addr < 0x08020000) return FLASH_SECTOR_1;
    if (addr < 0x08040000) return FLASH_SECTOR_2;
    if (addr < 0x08060000) return FLASH_SECTOR_3;
    if (addr < 0x08080000) return FLASH_SECTOR_4;
    if (addr < 0x080A0000) return FLASH_SECTOR_5;
    if (addr < 0x080C0000) return FLASH_SECTOR_6;
    return FLASH_SECTOR_7;
}
```

## 6. 固件打包工具

### 固件包结构
```c
typedef struct {
    uint8_t  magic[4];        // "FWPK"
    uint16_t version;         // 包格式版本
    uint16_t header_size;     // 头部大小
    uint32_t firmware_size;   // 固件大小
    uint32_t firmware_crc;    // 固件 CRC32
    uint8_t  firmware_hash[32]; // 固件 SHA256
    uint8_t  signature[256];  // RSA 签名
    uint8_t  hw_version[16];  // 硬件版本
    uint8_t  sw_version[16];  // 软件版本
    uint32_t timestamp;       // 构建时间戳
    uint8_t  reserved[32];    // 保留
} __attribute__((packed)) FirmwareHeader_t;
```

### 打包脚本 (Python)
```python
#!/usr/bin/env python3
"""固件打包工具"""
import struct
import hashlib
import zlib
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

FIRMWARE_MAGIC = b'FWPK'

def pack_firmware(bin_path, key_path, output_path, 
                  hw_version, sw_version):
    # 读取固件
    with open(bin_path, 'rb') as f:
        firmware = f.read()
    
    # 计算校验
    crc32 = zlib.crc32(firmware) & 0xFFFFFFFF
    sha256 = hashlib.sha256(firmware).digest()
    
    # 签名
    with open(key_path, 'rb') as f:
        private_key = rsa.load_der_private_key(f.read(), password=None)
    
    signature = private_key.sign(
        sha256,
        padding.PKCS1v15(),
        hashes.SHA256()
    )
    
    # 构建头部
    header = struct.pack(
        '<4sHHII32s256s16s16sI32s',
        FIRMWARE_MAGIC,      # magic
        1,                   # version
        384,                 # header_size
        len(firmware),       # firmware_size
        crc32,               # firmware_crc
        sha256,              # firmware_hash
        signature,           # signature
        hw_version.encode().ljust(16, b'\0'),
        sw_version.encode().ljust(16, b'\0'),
        int(time.time()),    # timestamp
        b'\0' * 32,          # reserved
    )
    
    # 写入文件
    with open(output_path, 'wb') as f:
        f.write(header)
        f.write(firmware)
    
    print(f"固件包已生成: {output_path}")
    print(f"  版本: {sw_version}")
    print(f"  大小: {len(firmware)} bytes")
    print(f"  CRC32: 0x{crc32:08X}")
    print(f"  SHA256: {sha256.hex()}")
```
