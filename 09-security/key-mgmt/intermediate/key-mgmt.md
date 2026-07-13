level: intermediate
---
title: "密钥管理"
aliases:
  - "密钥生命周期"
tags:
  - security
  - key-management
  - hsm
  - efuse
module: "04-security"
status: active
---

# 密钥管理

## 概述

本文介绍 key-mgmt 领域的 intermediate 级别知识。

完成本文学习后，你将能够：

- 掌握密钥层次和生命周期管理
- 能够实现密钥轮换和撤销
- 理解 HSM 和安全芯片

## 背景知识

### 相关概念

### 前置知识

- 完成初级内容的学习
- 熟悉嵌入式开发流程
- 掌握基本的数据结构和算法

### 学习建议

- 理解原理后动手实现
- 对比不同算法的优缺点
- 关注工程实践中的细节

## 核心内容

### 1. 密钥生命周期

### 密钥生命周期管理
```
┌─────────────────────────────────────────────────────────┐
│                    密钥生命周期                           │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  生成 ──→ 存储 ──→ 分发 ──→ 使用 ──→ 轮换 ──→ 销毁     │
│   │       │       │       │       │       │              │
│   │       │       │       │       │       └── 安全擦除   │
│   │       │       │       │       └── 定期更新           │
│   │       │       │       └── 加密/签名/认证             │
│   │       │       └── 安全分发                           │
│   │       └── HSM/TPM/eFuse/安全芯片                     │
│   └── CSPRNG/硬件随机数                                  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 密钥层次结构
```
Root Key (根密钥)
│
├── Key Encryption Key (KEK)
│   └── 用于加密 DEK
│
├── Data Encryption Key (DEK)
│   └── 用于加密固件/数据
│
├── Code Signing Key (代码签名密钥)
│   └── 用于签名固件/代码
│
├── Authentication Key (认证密钥)
│   └── 用于设备认证
│
└── Session Key (会话密钥)
    └── 用于通信加密
```

### 2. 密钥生成

### 安全随机数生成
```c
/* secure_random.c */
#include "crypto.h"
#include "hardware_rng.h"

/* 硬件随机数生成器 (TRNG) */
int hardware_random_generate(uint8_t *buf, size_t len) {
    // STM32 硬件 RNG
    for (size_t i = 0; i < len; i += 4) {
        uint32_t random;
        
        // 等待 RNG 就绪
        while (!(RNG->SR & RNG_SR_DRDY));
        
        random = RNG->DR;
        
        size_t copy_len = (len - i) > 4 ? 4 : (len - i);
        memcpy(buf + i, &random, copy_len);
    }
    
    return 0;
}

/* CSPRNG (密码学安全伪随机数生成器) */
typedef struct {
    uint8_t key[32];
    uint8_t counter[16];
    uint64_t generated;
} CSPRNG_State;

int csprng_init(CSPRNG_State *state) {
    // 使用硬件 RNG 种子
    uint8_t seed[48];
    hardware_random_generate(seed, sizeof(seed));
    
    // 使用 SHA-256 生成初始密钥
    sha256(seed, 32, state->key);
    memcpy(state->counter, seed + 32, 16);
    state->generated = 0;
    
    // 清除种子
    secure_memzero(seed, sizeof(seed));
    
    return 0;
}

int csprng_generate(CSPRNG_State *state, uint8_t *buf, size_t len) {
    uint8_t block[16];
    size_t offset = 0;
    
    while (offset < len) {
        // AES-CTR 生成随机块
        aes_encrypt(state->key, state->counter, block);
        
        // 复制到输出
        size_t copy_len = (len - offset) > 16 ? 16 : (len - offset);
        memcpy(buf + offset, block, copy_len);
        offset += copy_len;
        
        // 递增计数器
        for (int i = 15; i >= 0; i--) {
            if (++state->counter[i] != 0) break;
        }
        
        state->generated += copy_len;
        
        // 定期重新播种 (每 1MB)
        if (state->generated >= 1048576) {
            uint8_t new_seed[48];
            hardware_random_generate(new_seed, sizeof(new_seed));
            
            // 更新密钥
            uint8_t combined[80];
            memcpy(combined, state->key, 32);
            memcpy(combined + 32, new_seed, 48);
            sha256(combined, 80, state->key);
            
            secure_memzero(new_seed, sizeof(new_seed));
            secure_memzero(combined, sizeof(combined));
            
            state->generated = 0;
        }
    }
    
    secure_memzero(block, sizeof(block));
    
    return 0;
}
```

### 密钥对生成
```python
#!/usr/bin/env python3
"""密钥对生成工具"""
import os
from cryptography.hazmat.primitives.asymmetric import rsa, ec
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

def generate_rsa_keypair(key_size=2048):
    """生成 RSA 密钥对"""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
        backend=default_backend()
    )
    
    # 导出私钥 (PEM)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # 导出公钥 (PEM)
    public_pem = private_key.public_key().private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    # 导出公钥 (DER，用于嵌入设备)
    public_der = private_key.public_key().private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    return private_pem, public_pem, public_der

def generate_ec_keypair(curve=ec.SECP256R1()):
    """生成 ECC 密钥对"""
    private_key = ec.generate_private_key(curve, default_backend())
    
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    public_pem = private_key.public_key().private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    public_der = private_key.public_key().private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    return private_pem, public_pem, public_der

def generate_symmetric_key(key_size=256):
    """生成对称密钥"""
    return os.urandom(key_size // 8)

# 使用示例
if __name__ == '__main__':
    # RSA 密钥对
    rsa_private, rsa_public, rsa_public_der = generate_rsa_keypair(2048)
    
    with open('rsa_private.pem', 'wb') as f:
        f.write(rsa_private)
    
    with open('rsa_public.pem', 'wb') as f:
        f.write(rsa_public)
    
    with open('rsa_public.der', 'wb') as f:
        f.write(rsa_public_der)
    
    # ECC 密钥对
    ec_private, ec_public, ec_public_der = generate_ec_keypair()
    
    with open('ec_private.pem', 'wb') as f:
        f.write(ec_private)
    
    with open('ec_public.pem', 'wb') as f:
        f.write(ec_public)
    
    with open('ec_public.der', 'wb') as f:
        f.write(ec_public_der)
    
    # 对称密钥
    aes_key = generate_symmetric_key(256)
    
    with open('aes_key.bin', 'wb') as f:
        f.write(aes_key)
    
    print("密钥生成完成")
```

### 3. 密钥存储

### eFuse/OTP 存储方案
```
eFuse 区域规划:
┌─────────────────────────────────────────┐
│  eFuse 区域                               │
├─────────────────────────────────────────┤
│  0x0000 - 0x001F: 设备信息               │
│    - 芯片型号 (32-bit)                   │
│    - 版本号 (16-bit)                     │
│    - 序列号 (64-bit)                     │
│    - 保留 (128-bit)                      │
│                                           │
│  0x0020 - 0x003F: 安全配置               │
│    - Secure Boot Enable (1-bit)          │
│    - JTAG Disable (1-bit)               │
│    - Debug Disable (1-bit)              │
│    - 回滚计数器 (32-bit)                 │
│    - 保留 (221-bit)                      │
│                                           │
│  0x0040 - 0x005F: Root Key Hash          │
│    - SHA-256 Hash (256-bit)              │
│                                           │
│  0x0060 - 0x007F: 设备唯一密钥           │
│    - Device Key (256-bit, 可选)          │
│                                           │
│  0x0080 - 0x00FF: 保留                   │
└─────────────────────────────────────────┘

写入流程:
1. 准备数据
2. 校验数据完整性
3. 调用 eFuse 写入 API
4. 验证写入结果
5. 记录日志

注意: eFuse 写入后不可逆，务必谨慎!
```

### 安全芯片存储
```c
/* secure_element.c */
#include "atecc608a.h"

/* ATECC608A 配置 */
#define ATECC_SLOT_DEVICE_KEY    0   // 设备密钥槽
#define ATECC_SLOT_SIGN_KEY      1   // 签名密钥槽
#define ATECC_SLOT_AUTH_KEY      2   // 认证密钥槽
#define ATECC_SLOT_DATA_KEY      3   // 数据密钥槽

/* 生成密钥对 (私钥在安全芯片内部) */
int secure_generate_keypair(uint8_t slot, uint8_t *public_key) {
    // 发送生成密钥对命令
    uint8_t cmd[4] = {0x40, 0x04, slot, 0x00};
    
    int ret = atecc_send_command(cmd, sizeof(cmd));
    if (ret != 0) return ret;
    
    // 读取公钥
    ret = atecc_read_public_key(slot, public_key, 64);
    
    return ret;
}

/* 签名数据 */
int secure_sign(uint8_t slot, const uint8_t *data, 
                 size_t data_len, uint8_t *signature) {
    // 计算哈希
    uint8_t hash[32];
    sha256(data, data_len, hash);
    
    // 发送签名命令
    uint8_t cmd[35] = {0x40, 0x05, slot, 0x00};
    memcpy(cmd + 4, hash, 32);
    
    int ret = atecc_send_command(cmd, sizeof(cmd));
    if (ret != 0) return ret;
    
    // 读取签名
    ret = atecc_read_signature(signature, 64);
    
    return ret;
}

/* 验证签名 */
int secure_verify(const uint8_t *public_key, const uint8_t *data,
                   size_t data_len, const uint8_t *signature) {
    // 计算哈希
    uint8_t hash[32];
    sha256(data, data_len, hash);
    
    // 发送验证命令
    uint8_t cmd[135] = {0x40, 0x06, 0x00, 0x00};
    memcpy(cmd + 4, public_key, 64);
    memcpy(cmd + 68, hash, 32);
    memcpy(cmd + 100, signature, 32);
    
    return atecc_send_command(cmd, sizeof(cmd));
}
```

### 4. 密钥轮换

### 密钥轮换策略
```c
/* key_rotation.c */

#define MAX_KEY_VERSION  255
#define KEY_ROTATION_INTERVAL_DAYS  90

typedef struct {
    uint8_t version;
    uint8_t key[32];
    uint32_t created_time;
    uint32_t expires_time;
    bool is_active;
} KeyEntry_t;

/* 密钥轮换 */
int rotate_key(KeyStore_t *store) {
    // 1. 生成新密钥
    uint8_t new_key[32];
    secure_random_generate(new_key, sizeof(new_key));
    
    // 2. 创建新密钥条目
    KeyEntry_t new_entry;
    new_entry.version = store->current_version + 1;
    memcpy(new_entry.key, new_key, 32);
    new_entry.created_time = get_current_time();
    new_entry.expires_time = new_entry.created_time + 
                             KEY_ROTATION_INTERVAL_DAYS * 86400;
    new_entry.is_active = true;
    
    // 3. 标记旧密钥为非活跃
    store->entries[store->current_version].is_active = false;
    
    // 4. 存储新密钥
    store->entries[new_entry.version] = new_entry;
    store->current_version = new_entry.version;
    
    // 5. 安全擦除旧密钥 (可选，保留用于解密旧数据)
    // secure_memzero(store->entries[old_version].key, 32);
    
    // 6. 持久化存储
    save_keystore(store);
    
    return 0;
}

/* 获取当前活跃密钥 */
int get_active_key(KeyStore_t *store, uint8_t *key) {
    KeyEntry_t *entry = &store->entries[store->current_version];
    
    if (!entry->is_active) {
        return -1;
    }
    
    // 检查是否过期
    if (get_current_time() > entry->expires_time) {
        // 自动轮换
        rotate_key(store);
        entry = &store->entries[store->current_version];
    }
    
    memcpy(key, entry->key, 32);
    
    return entry->version;
}

/* 使用指定版本密钥解密 */
int decrypt_with_version(KeyStore_t *store, uint8_t version,
                          const uint8_t *ciphertext, size_t len,
                          uint8_t *plaintext) {
    if (version > store->current_version) {
        return -1;  // 无效版本
    }
    
    KeyEntry_t *entry = &store->entries[version];
    
    return aes_decrypt(entry->key, ciphertext, len, plaintext);
}
```

### 5. 密钥销毁

### 安全擦除
```c
/* secure_erase.c */

/* 安全内存擦除 */
void secure_memzero(void *ptr, size_t len) {
    volatile uint8_t *p = (volatile uint8_t *)ptr;
    
    // 使用 volatile 防止编译器优化
    for (size_t i = 0; i < len; i++) {
        p[i] = 0;
    }
    
    // 内存屏障确保写入完成
    __asm__ volatile("" ::: "memory");
}

/* 多次覆写擦除 */
int secure_erase_flash(uint32_t addr, size_t len) {
    // 第一次: 写 0
    uint8_t *zeros = calloc(len, 1);
    flash_write(addr, zeros, len);
    free(zeros);
    
    // 第二次: 写 1
    uint8_t *ones = malloc(len);
    memset(ones, 0xFF, len);
    flash_write(addr, ones, len);
    free(ones);
    
    // 第三次: 写随机数
    uint8_t *random = malloc(len);
    secure_random_generate(random, len);
    flash_write(addr, random, len);
    free(random);
    
    // 第四次: 写 0
    zeros = calloc(len, 1);
    flash_write(addr, zeros, len);
    free(zeros);
    
    return 0;
}

/* 密钥销毁 */
int destroy_key(KeyStore_t *store, uint8_t version) {
    if (version > store->current_version) {
        return -1;
    }
    
    KeyEntry_t *entry = &store->entries[version];
    
    // 安全擦除密钥
    secure_memzero(entry->key, 32);
    
    // 标记为无效
    entry->is_active = false;
    entry->version = 0;
    entry->created_time = 0;
    entry->expires_time = 0;
    
    // 持久化
    save_keystore(store);
    
    return 0;
}
```

### 6. 密钥管理最佳实践

### 安全检查清单
```
密钥生成:
□ 使用硬件随机数生成器
□ 密钥长度满足安全要求
□ 生成环境安全
□ 生成过程可审计

密钥存储:
□ 私钥永不导出
□ 使用安全存储 (HSM/安全芯片)
□ 访问控制严格
□ 备份密钥安全存储

密钥分发:
□ 使用安全通道
□ 验证接收方身份
□ 记录分发日志
□ 限制分发范围

密钥使用:
□ 最小权限原则
□ 使用后清除内存
□ 防止侧信道攻击
□ 记录使用日志

密钥轮换:
□ 定期轮换
□ 旧密钥保留用于解密
□ 轮换过程自动化
□ 轮换日志完整

密钥销毁:
□ 安全擦除
□ 多次覆写
□ 验证擦除结果
□ 记录销毁日志
```
---

### 相关链接

- [[bootloader-design|Bootloader]]
- [[android-security|Android 安全]]

## 实践示例

### 示例代码

```c
// 示例代码 - 结合正文理解
```

**代码说明**：
- 详见正文

## 深入理解

### 原理分析

请参考核心内容部分的详细讲解。

### 最佳实践

1. 模块化设计，接口清晰
2. 充分的错误处理和边界检查
3. 编写可测试的代码

## 常见问题

### Q1: 如何调试复杂问题？

**A**: 使用逻辑分析仪/示波器抓取信号；添加日志输出关键变量；使用 GDB 在线调试；分模块隔离问题。

### Q2: 性能不够怎么办？

**A**: 使用 DMA 减少 CPU 负担；优化中断处理 (Top/Bottom Half)；使用硬件加速器；降低采样率或简化算法。

## 总结

本文深入讲解了核心技术和实现方法：

- 掌握了关键算法的原理和实现
- 能够独立完成模块级开发
- 理解了工程实践中的优化技巧

下一步建议进入高级内容，学习系统级设计和生产级优化。

## 延伸阅读

- [[MOC|知识地图]] - 返回总索引
- 相关模块文档 - 交叉参考
- 厂商数据手册 - 详细规格

## 参考资料

- 厂商数据手册和技术参考
- 开源项目文档和代码
- 学术论文和行业标准

---

**练习题**：

- 厂商数据手册和技术参考
- 开源项目文档和代码
- 学术论文和行业标准

**下一步**：建议学习 [[key-mgmt/advanced/|高级内容]]
