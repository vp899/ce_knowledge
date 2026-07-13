# 04 - 安全启动

## 模块概述

嵌入式设备安全启动链设计、固件加密、密钥管理与安全生命周期。

## 目录结构

```
04-security/
├── secure-boot/    # 安全启动流程与实现
├── encryption/     # 固件加密与签名
└── key-management/ # 密钥生成、存储、轮换
```

## 核心知识领域

### 1. 安全启动 (Secure Boot)

#### 启动信任链
```
ROM Boot (Root of Trust)
    │
    ├── 验证 Bootloader 签名 (RSA/ECDSA)
    │       │
    │       ├── 验证 TEE OS 签名
    │       │       └── 验证 Trusted App 签名
    │       │
    │       └── 验证 Kernel 签名
    │               │
    │               ├── 验证 DTB 签名
    │               └── 验证 Rootfs 签名
    │                       └── dm-verity 保护
    └── [任一验证失败 → 拒绝启动 / Recovery]
```

#### 安全级别
| 级别 | 描述 | 实现 |
|------|------|------|
| Level 0 | 无安全 | 直接启动 |
| Level 1 | 软件验证 | Bootloader 校验固件 Hash |
| Level 2 | 签名验证 | RSA/ECDSA 签名校验 |
| Level 3 | 硬件信任根 | eFuse/OTP 中的公钥哈希 |
| Level 4 | 完整信任链 | 每级验证 + 防回滚 + 加密 |

### 2. 固件加密与签名

#### 签名算法对比
| 算法 | 密钥长度 | 签名长度 | 速度 | 安全性 |
|------|----------|----------|------|--------|
| RSA-2048 | 2048-bit | 256B | 慢 | 中 |
| RSA-4096 | 4096-bit | 512B | 很慢 | 高 |
| ECDSA-P256 | 256-bit | 64B | 快 | 高 |
| Ed25519 | 256-bit | 64B | 很快 | 高 |

#### 固件打包格式
```
┌─────────────────────────────────┐
│  Header (Magic, Version, Size)  │
├─────────────────────────────────┤
│  Key Table (公钥 / 证书链)      │
├─────────────────────────────────┤
│  Signature (签名)               │
├─────────────────────────────────┤
│  Payload (加密/明文固件)        │
├─────────────────────────────────┤
│  Manifest (元数据、CRC)         │
└─────────────────────────────────┘
```

### 3. 密钥管理

#### 密钥层次
```
Root Key (HSM / eFuse)
    │
    ├── Code Signing Key (签名密钥)
    │       └── 用于签名 Bootloader / Kernel / App
    │
    ├── Key Encryption Key (KEK)
    │       └── 用于加密 DEK
    │
    └── Data Encryption Key (DEK)
            └── 用于加密固件 payload
```

#### 密钥存储方案
| 方案 | 安全性 | 成本 | 适用 |
|------|--------|------|------|
| eFuse / OTP | 最高 | 低 | 量产设备 |
| 安全芯片 (ATECC608) | 高 | 中 | IoT 产品 |
| TEE (TrustZone) | 高 | 低 | Android / Linux |
| 文件系统存储 | 低 | 低 | 仅开发阶段 |
| HSM (服务器端) | 最高 | 高 | 签名服务器 |

### 4. 防回滚机制

- **单调计数器 (Monotonic Counter)**：存储在 OTP/eFuse
- **版本号嵌入**：固件中嵌入最低允许版本
- **安全存储**：防篡改的版本号存储（RPMB、安全分区）

### 5. 安全启动调试

#### 常见问题
- 签名格式不匹配（DER vs PEM、padding）
- 公钥哈希与 eFuse 不一致
- 时钟配置错误导致加密引擎异常
- Flash 偏移地址计算错误
- 固件升级后未更新版本号导致回滚失败

## 参考资源

- [ARM TrustZone 技术](https://developer.arm.com/Architectures/TrustZone)
- [NIST SP 800-193 (平台固件保护)](https://csrc.nist.gov/publications/detail/sp/800-193/final)
- [OWASP Embedded Security](https://owasp.org/www-project-internet-of-things/)
