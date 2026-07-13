level: advanced
---
title: "安全启动实现"
aliases:
  - "Secure Boot"
tags:
  - security
  - secure-boot
  - rsa
  - trust-chain
module: "04-security"
status: active
---

# 安全启动实现

## 概述

本文介绍 secure-boot 领域的 advanced 级别知识。

完成本文学习后，你将能够：

- 理解核心概念和基本原理
- 掌握关键技术和实现方法
- 应用到实际产品开发中

## 背景知识

### 相关概念

> 占位 - 待补充前置概念

## 核心内容

### 1. 安全启动信任链

### 完整信任链架构
```
┌─────────────────────────────────────────────────────────────────┐
│                        硬件信任根 (Hardware Root of Trust)        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  ROM Boot Code (不可修改)                                  │   │
│  │  ├── 存储 Root Public Key Hash (eFuse/OTP)                │   │
│  │  ├── 初始化安全引擎 (AES, SHA, RSA)                       │   │
│  │  └── 验证 Bootloader 签名                                 │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Stage 1: Bootloader (First Stage)                        │   │
│  │  ├── 被 ROM 验证签名                                      │   │
│  │  ├── 初始化 DDR, 时钟, 电源                                │   │
│  │  └── 验证 Stage 2 签名                                    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Stage 2: Bootloader (Second Stage)                       │   │
│  │  ├── 被 Stage 1 验证签名                                  │   │
│  │  ├── 加载 Kernel + DTB                                    │   │
│  │  ├── 验证 Kernel 签名                                     │   │
│  │  └── 设置 dm-verity (可选)                                │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Linux Kernel                                             │   │
│  │  ├── 被 Bootloader 验证签名                               │   │
│  │  ├── dm-verity 验证 Rootfs                                │   │
│  │  └── 验证关键模块签名                                     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Userspace                                                 │   │
│  │  ├── Verified Boot 完成                                   │   │
│  │  ├── 应用层签名验证 (APK)                                 │   │
│  │  └── 安全存储 (KeyStore)                                  │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 2. RSA 签名实现

### 固件签名流程
```
构建服务器 (CI/CD)
    │
    ├── 编译固件
    ├── 计算 SHA256 哈希
    ├── 使用私钥签名哈希
    │       │
    │       ├── RSA-2048: 签名 256 字节
    │       └── RSA-4096: 签名 512 字节
    │
    └── 打包: [固件] + [签名] + [证书]

设备端验证:
    │
    ├── 提取固件和签名
    ├── 计算固件 SHA256
    ├── 使用公钥验证签名
    │       │
    │       ├── 公钥 Hash 存储在 eFuse
    │       └── 先验证公钥完整性
    │
    └── 验证通过 → 允许启动
```

### 嵌入式 RSA 验证代码
```c
/* crypto_verify.c */
#include "mbedtls/rsa.h"
#include "mbedtls/sha256.h"
#include "mbedtls/pk.h"

#define FIRMWARE_HASH_SIZE   32
#define RSA_SIGNATURE_SIZE   256  // RSA-2048

/* 从 eFuse 读取公钥哈希 */
static int read_root_key_hash(uint8_t *hash) {
    // 读取 OTP/eFuse 中存储的公钥哈希
    // 具体实现取决于芯片平台
    return otp_read(ROOT_KEY_HASH_OFFSET, hash, 32);
}

/* 验证公钥完整性 */
static int verify_public_key(const uint8_t *pub_key, 
                              uint32_t pub_key_len) {
    uint8_t stored_hash[32];
    uint8_t calc_hash[32];
    
    // 读取存储的哈希
    if (read_root_key_hash(stored_hash) != 0) {
        return -1;
    }
    
    // 计算公钥哈希
    mbedtls_sha256(pub_key, pub_key_len, calc_hash, 0);
    
    // 比较
    if (memcmp(stored_hash, calc_hash, 32) != 0) {
        return -2;  // 公钥被篡改
    }
    
    return 0;
}

/* 验证固件签名 */
int verify_firmware_signature(const uint8_t *firmware, 
                               uint32_t firmware_len,
                               const uint8_t *signature,
                               const uint8_t *public_key,
                               uint32_t public_key_len) {
    int ret;
    uint8_t hash[32];
    mbedtls_pk_context pk;
    
    // 1. 验证公钥完整性
    if (verify_public_key(public_key, public_key_len) != 0) {
        return VERIFY_ERR_KEY_INVALID;
    }
    
    // 2. 计算固件哈希
    mbedtls_sha256(firmware, firmware_len, hash, 0);
    
    // 3. 初始化 RSA 上下文
    mbedtls_pk_init(&pk);
    ret = mbedtls_pk_parse_public_key(&pk, public_key, public_key_len);
    if (ret != 0) {
        mbedtls_pk_free(&pk);
        return VERIFY_ERR_KEY_PARSE;
    }
    
    // 4. 验证签名
    ret = mbedtls_pk_verify(&pk, MBEDTLS_MD_SHA256,
                             hash, FIRMWARE_HASH_SIZE,
                             signature, RSA_SIGNATURE_SIZE);
    
    mbedtls_pk_free(&pk);
    
    if (ret != 0) {
        return VERIFY_ERR_SIGNATURE;
    }
    
    return VERIFY_OK;
}

/* 验证应用头 (启动前检查) */
int verify_app_header(uint32_t app_addr) {
    // 检查栈指针 (应在 RAM 范围内)
    uint32_t sp = *(volatile uint32_t *)app_addr;
    if (sp < RAM_START || sp > RAM_END) {
        return VERIFY_ERR_HEADER;
    }
    
    // 检查复位向量 (应在 Flash 范围内)
    uint32_t reset_vec = *(volatile uint32_t *)(app_addr + 4);
    if (reset_vec < FLASH_START || reset_vec > FLASH_END) {
        return VERIFY_ERR_HEADER;
    }
    
    // 检查中断向量表 (可选)
    uint32_t nmi_vec = *(volatile uint32_t *)(app_addr + 8);
    if (reset_vec < FLASH_START || reset_vec > FLASH_END) {
        return VERIFY_ERR_HEADER;
    }
    
    return VERIFY_OK;
}
```

### 3. [[key-mgmt|密钥管理]]

### 密钥生成脚本
```bash
#!/bin/bash
# generate_keys.sh - 生成安全启动密钥

KEY_DIR="./keys"
mkdir -p $KEY_DIR

# 生成 Root CA 密钥对 (RSA-4096)
openssl genrsa -out $KEY_DIR/root_ca.key 4096
openssl req -new -x509 -key $KEY_DIR/root_ca.key \
    -out $KEY_DIR/root_ca.crt -days 3650 \
    -subj "/CN=Root CA/O=MyCompany"

# 生成代码签名密钥对 (RSA-2048)
openssl genrsa -out $KEY_DIR/code_sign.key 2048
openssl req -new -key $KEY_DIR/code_sign.key \
    -out $KEY_DIR/code_sign.csr \
    -subj "/CN=Code Sign/O=MyCompany"
openssl x509 -req -in $KEY_DIR/code_sign.csr \
    -CA $KEY_DIR/root_ca.crt -CAkey $KEY_DIR/root_ca.key \
    -CAcreateserial -out $KEY_DIR/code_sign.crt -days 365

# 导出公钥 (DER 格式，用于嵌入设备)
openssl rsa -in $KEY_DIR/code_sign.key -pubout \
    -out $KEY_DIR/code_sign_pub.der -outform DER

# 计算公钥哈希 (用于写入 eFuse)
sha256sum $KEY_DIR/code_sign_pub.der | cut -d' ' -f1 > \
    $KEY_DIR/pub_key_hash.txt

echo "密钥生成完成"
echo "公钥哈希 (写入 eFuse): $(cat $KEY_DIR/pub_key_hash.txt)"
```

### 安全存储方案
```
方案 1: eFuse/OTP (最安全)
┌─────────────────────────────────────────┐
│  eFuse 区域                               │
│  ├── Root Key Hash (256-bit)             │
│  ├── Secure Boot Enable (1-bit)          │
│  ├── JTAG Disable (1-bit)               │
│  ├── 固件版本计数器 (32-bit)             │
│  └── 设备唯一密钥 (256-bit, 可选)       │
│                                           │
│  写入后不可修改                           │
│  需要物理访问才能读取                     │
└─────────────────────────────────────────┘

方案 2: 安全芯片 (ATECC608A)
┌─────────────────────────────────────────┐
│  ATECC608A 安全芯片                       │
│  ├── 存储私钥 (不可导出)                 │
│  ├── 硬件加密加速                        │
│  ├── 安全世界 (Secure Element)           │
│  ├── 防物理攻击                          │
│  └── I2C 接口                            │
└─────────────────────────────────────────┘

方案 3: TrustZone (ARM)
┌─────────────────────────────────────────┐
│  Secure World (安全世界)                  │
│  ├── 存储密钥                            │
│  ├── 加密操作                            │
│  └── 安全服务                            │
│                                           │
│  Normal World (普通世界)                  │
│  ├── 应用代码                            │
│  └── 不能访问安全世界数据                │
└─────────────────────────────────────────┘
```

### 4. 防回滚机制

### 单调计数器实现
```c
/* anti_rollback.c */

#define ROLLBACK_COUNTER_ADDR   0x080A0000
#define MAX_COUNTER_VALUE       255

/* 读取当前版本计数器 */
uint32_t read_rollback_counter(void) {
    return *(volatile uint32_t *)ROLLBACK_COUNTER_ADDR;
}

/* 递增计数器 (写入 OTP) */
int increment_rollback_counter(void) {
    uint32_t current = read_rollback_counter();
    
    if (current >= MAX_COUNTER_VALUE) {
        return -1;  // 计数器溢出
    }
    
    // 写入新值 (OTP 只能 0→1，不能 1→0)
    // 具体实现取决于 OTP 硬件
    otp_write(ROLLBACK_COUNTER_ADDR, current + 1);
    
    return 0;
}

/* 验证固件版本 */
int verify_firmware_version(uint32_t firmware_version) {
    uint32_t counter = read_rollback_counter();
    
    // 固件版本必须大于等于计数器值
    if (firmware_version < counter) {
        return -1;  // 回滚攻击检测
    }
    
    return 0;
}

/* 固件升级时更新计数器 */
int update_after_upgrade(uint32_t new_version) {
    uint32_t counter = read_rollback_counter();
    
    if (new_version > counter) {
        // 递增计数器到新版本
        while (read_rollback_counter() < new_version) {
            if (increment_rollback_counter() != 0) {
                return -1;
            }
        }
    }
    
    return 0;
}
```

### 5. 安全启动调试

### 调试流程
```
安全启动失败调试:

1. 检查 eFuse 配置
   ├── Root Key Hash 是否正确
   ├── Secure Boot 是否使能
   └── JTAG 是否禁用

2. 检查签名
   ├── 签名格式 (DER/PEM, PKCS#1/PKCS#8)
   ├── 哈希算法 (SHA256)
   ├── 签名填充 (PKCS#1 v1.5 / PSS)
   └── 公钥匹配

3. 检查固件
   ├── 固件地址偏移
   ├── 固件大小
   ├── 固件完整性
   └── 版本号

4. 常见错误
   ├── eFuse 写入错误 → 重新烧录
   ├── 签名格式错误 → 检查 OpenSSL 版本
   ├── 地址偏移错误 → 检查链接脚本
   └── 版本回滚 → 更新版本号
```

### 测试用例
```c
/* test_secure_boot.c */

void test_signature_verification(void) {
    // 测试 1: 正常签名验证
    assert(verify_firmware_signature(
        valid_firmware, valid_firmware_len,
        valid_signature, public_key, pub_key_len) == VERIFY_OK);
    
    // 测试 2: 篡改固件
    uint8_t tampered_firmware[100];
    memcpy(tampered_firmware, valid_firmware, 100);
    tampered_firmware[50] ^= 0x01;  // 翻转一位
    assert(verify_firmware_signature(
        tampered_firmware, 100,
        valid_signature, public_key, pub_key_len) != VERIFY_OK);
    
    // 测试 3: 错误签名
    assert(verify_firmware_signature(
        valid_firmware, valid_firmware_len,
        wrong_signature, public_key, pub_key_len) != VERIFY_OK);
    
    // 测试 4: 错误公钥
    assert(verify_firmware_signature(
        valid_firmware, valid_firmware_len,
        valid_signature, wrong_pub_key, wrong_key_len) != VERIFY_OK);
}

void test_anti_rollback(void) {
    // 测试版本回滚检测
    set_rollback_counter(10);
    
    assert(verify_firmware_version(11) == 0);   // 允许升级
    assert(verify_firmware_version(10) == 0);   // 允许当前版本
    assert(verify_firmware_version(9) != 0);    // 拒绝回滚
    assert(verify_firmware_version(5) != 0);    // 拒绝回滚
}
```
---

### 相关链接

- [[bootloader-design|Bootloader]]
- [[android-security|Android 安全]]

## 实践示例

### 示例代码

```c
// 占位 - 待补充示例代码
```

**代码说明**：
- 待补充

## 深入理解

### 原理分析

> 占位 - 待补充原理分析

### 最佳实践

1. 待补充

## 常见问题

### Q1: 待补充常见问题？

**A**: 待补充答案。

## 总结

本文核心要点：

- 待补充

## 延伸阅读

- 待补充相关文章链接

## 参考资料

1. 待补充

---

**练习题**：

1. 待补充

**下一步**：建议学习 [[MOC|返回知识地图]]
