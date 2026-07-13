level: beginner
---
title: "加密算法详解"
tags: [security, aes, rsa, sha, hmac, ecdsa, algorithm]
module: "09-security"
---

# 加密算法详解

## 概述

本文介绍  领域的 beginner 级别知识。

完成本文学习后，你将能够：

- 掌握本模块的核心概念和原理
- 理解关键技术的实现方法
- 能够应用到实际项目中

## 背景知识

### 相关概念

### 前置知识

- C 语言基础
- 嵌入式开发基础
- 相关模块的初级知识

### 学习建议

- 准备开发板进行动手实践
- 边学边做，不要只看不练
- 遇到问题先自己思考再查资料

## 核心内容

### 1. AES 加密

### AES-128 算法流程
```
明文 (128-bit) → 初始轮密钥加
    │
    ├── 轮 1-9 (重复):
    │   ├── SubBytes (S 盒替换)
    │   ├── ShiftRows (行移位)
    │   ├── MixColumns (列混合)
    │   └── AddRoundKey (轮密钥加)
    │
    └── 轮 10 (最后一轮):
        ├── SubBytes
        ├── ShiftRows
        └── AddRoundKey (无 MixColumns)
    │
    ▼
密文 (128-bit)

S 盒: 8-bit → 8-bit 非线性替换 (防差分攻击)
ShiftRows: 第 i 行左移 i 字节
MixColumns: 列上做 GF(2^8) 乘法
密钥扩展: 128-bit 密钥 → 11 个 128-bit 轮密钥
```

### AES-GCM (认证加密)
```
AES-GCM = AES-CTR (加密) + GHASH (认证)

加密:
  C_i = P_i ⊕ AES_K(CTR + i)

认证:
  T = GHASH_H(C) ⊕ AES_K(CTR_0)

  H = AES_K(0^128)  (哈希子密钥)
  GHASH: GF(2^128) 上的乘法累加

优势:
├── 同时加密 + 认证
├── 可并行 (CTR 模式)
├── 硬件加速支持 (ARM CE, x86 AES-NI)
└── 广泛用于 TLS/VPN
```

### 2. RSA 签名

### RSA 原理
```
密钥生成:
  1. 选两个大素数 p, q
  2. n = p · q
  3. φ(n) = (p-1)·(q-1)
  4. 选 e (通常 65537)
  5. d = e^(-1) mod φ(n)
  
  公钥: (n, e)
  私钥: (n, d)

加密: C = M^e mod n
解密: M = C^d mod n

签名: S = H(M)^d mod n
验证: H(M) == S^e mod n
```

### RSA-PSS 签名 (嵌入式)
```c
/* RSA-PSS 签名验证 */

int rsa_pss_verify(const uint8_t *message, size_t msg_len,
                    const uint8_t *signature, size_t sig_len,
                    const RSA_PublicKey *pub_key) {
    // 1. 计算消息哈希
    uint8_t hash[32];
    sha256(message, msg_len, hash);
    
    // 2. 签名解密: S^e mod n
    uint8_t decrypted[256];
    rsa_public_op(signature, sig_len, pub_key, decrypted);
    
    // 3. PSS 解码
    // EM = 0x00 || maskedDB || H || 0xbc
    // DB = maskedDB ⊕ MGF(H)
    // DB = PS || 0x01 || salt
    
    uint8_t *em = decrypted;
    if (em[sig_len - 1] != 0xbc) return -1;  // 错误
    
    uint8_t h[32];
    memcpy(h, em + sig_len - 33, 32);
    
    uint8_t db[256 - 33];
    mgf1(h, 32, db, sig_len - 33);  // MGF
    for (int i = 0; i < sig_len - 33; i++) {
        db[i] ^= em[i + 1];
    }
    
    // 4. 验证
    // H' = Hash(M' || salt)
    uint8_t salt[32];
    // 从 db 中提取 salt...
    
    uint8_t h_prime[32];
    // 计算 H'...
    
    return memcmp(h, h_prime, 32) == 0 ? 0 : -1;
}
```

### 3. SHA-256 哈希

### SHA-256 算法
```
SHA-256 处理流程:
  1. 消息填充 (使长度 ≡ 448 mod 512)
  2. 添加原始长度 (64-bit)
  3. 每 512-bit 一个块处理

单块处理 (64 轮):
  初始哈希值 H0-H7 (前 8 个素数的平方根小数部分)
  
  扩展消息调度:
    W_t = σ1(W_{t-2}) + W_{t-7} + σ0(W_{t-15}) + W_{t-16}
  
  64 轮迭代:
    T1 = h + Σ1(e) + Ch(e,f,g) + K_t + W_t
    T2 = Σ0(a) + Maj(a,b,c)
    h=g, g=f, f=e, e=d+T1
    d=c, c=b, b=a, a=T1+T2

  最终: H = H + [a,b,c,d,e,f,g,h]
```

### 4. ECDH 密钥交换

### 椭圆曲线 Diffie-Hellman
```
ECDH 协议:
  Alice:
    私钥: a (随机数)
    公钥: A = a · G (椭圆曲线点乘)
  
  Bob:
    私钥: b (随机数)
    公钥: B = b · G
  
  共享密钥:
    S = a · B = b · G · a = a · b · G
  
  安全性: 即使知道 A, B, G, 也无法求出 a 或 b
  (椭圆曲线离散对数问题)

常用曲线:
  P-256 (secp256r1): 128-bit 安全性
  Curve25519: 高性能, 128-bit 安全性
```

---

### 相关链接

- [[secure-boot-impl|安全启动]] — 信任链
- [[key-mgmt|密钥管理]] — 密钥生命周期

## 实践示例

### 示例代码

```c
// 示例代码 - 结合正文理解
```

**代码说明**：
- 详见正文

## 深入理解

### 原理分析

深入理解底层原理有助于写出更高质量的代码。建议结合数据手册和源码进行学习。

### 最佳实践

1. 遵循代码规范，保持良好的注释习惯
2. 充分测试，覆盖边界条件
3. 持续重构，保持代码简洁

## 常见问题

### Q1: 学习本模块需要什么基础？

**A**: 需要 C 语言基础和基本的嵌入式开发知识。建议先完成前置模块的学习。

### Q2: 如何验证学习效果？

**A**: 通过动手实践验证：完成练习题、在开发板上运行示例代码、独立完成一个小项目。

## 总结

本文涵盖了本级别的核心知识：

- 理解了基本概念和工作原理
- 掌握了关键技术和实现方法
- 通过实践加深了理解

建议继续学习更高级别的内容。

## 延伸阅读

- [[MOC|知识地图]] - 返回总索引
- 相关模块文档 - 交叉参考
- 厂商数据手册 - 详细规格

## 参考资料

1. 厂商数据手册和技术参考
2. 开源项目文档和代码
3. 学术论文和行业标准

---

**练习题**：

1. 厂商数据手册和技术参考
2. 开源项目文档和代码
3. 学术论文和行业标准

**下一步**：建议学习 [[/intermediate/|中级内容]]
