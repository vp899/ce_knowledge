---
title: "Android 安全机制"
aliases:
  - "Android 安全"
tags:
  - android
  - security
  - selinux
  - keymaster
module: "01-android"
status: active
---

# Android 安全机制

## 1. 签名体系

### 签名密钥类型
| 密钥 | 用途 | 签名的应用 |
|------|------|------------|
| platform | 系统核心 | Settings, SystemUI, Framework |
| shared | 共享进程 | ContactsProvider, Launcher |
| media | 媒体/下载 | DownloadProvider, MediaProvider |
| testkey | 默认测试 | 开发阶段使用 |
| verity | dm-verity | 系统分区验证 |

### APK 签名方案
```
v1: JAR 签名 (META-INF/)
    ├── CERT.SF    (签名文件)
    ├── CERT.RSA   (签名证书)
    └── MANIFEST.MF (摘要清单)

v2: APK 签名方案 v2 (Android 7.0+)
    └── APK Signing Block (APK 中央目录前)

v3: APK 签名方案 v3 (Android 9.0+)
    └── 支持密钥轮换 (Proof of Rotation)

v4: APK 签名方案 v4 (Android 11+)
    └── 基于 Merkle 增量验证
```

### 签名实践
```bash
# 生成密钥对
keytool -genkeypair -v \
    -keystore platform.keystore \
    -alias platform \
    -keyalg RSA -keysize 2048 \
    -validity 10000

# 签名 APK
apksigner sign \
    --ks platform.keystore \
    --ks-key-alias platform \
    --ks-pass pass:android \
    --out signed.apk unsigned.apk

# 验证签名
apksigner verify --verbose signed.apk

# OTA 包签名
java -jar signapk.jar -w \
    platform.x509.pem platform.pk8 \
    unsigned_ota.zip signed_ota.zip
```

## 2. SELinux / SEAndroid

### 策略架构
```
system/sepolicy/
├── public/             # 所有分区共享的类型和属性
│   ├── domain.te       # 域通用规则
│   ├── file.te         # 文件类型定义
│   └── property.te     # 属性类型定义
├── private/            # system 分区私有策略
│   ├── app.te          # 应用域规则
│   ├── system_server.te # SystemServer 规则
│   └── shell.te        # Shell 域规则
├── vendor/             # vendor 分区策略
│   ├── domain.te       # vendor 域规则
│   └── file.te         # vendor 文件类型
└── prebuilts/api/      # 策略版本管理
```

### 策略编写规则
```te
# ============ 域定义 ============
# 定义新的域类型
type my_app, domain;

# ============ 文件类型 ============
# 定义新的文件类型
type my_data_file, file_type, data_file_type;

# ============ 基本规则 ============
# 允许 my_app 读取 my_data_file
allow my_app my_data_file:file { read open getattr };

# 允许 my_app 创建/写入 my_data_file
allow my_app my_data_file:file { create write append unlink };

# 允许 my_app 创建目录
allow my_app my_data_file:dir { create add_name remove_name search };

# ============ 属性规则 ============
# 允许 my_app 设置 my_prop 属性
set_prop(my_app, my_prop)

# 允许 my_app 查看 default_prop
get_prop(my_app, default_prop)

# ============ Binder 规则 ============
binder_use(my_app)
binder_call(my_app, system_server)

# ============ 服务规则 ============
allow my_app my_service:service_manager { find add };

# ============ neverallow (禁止规则) ============
# 禁止普通应用直接访问设备节点
neverallow appdomain device:chr_file { read write };
```

### 调试 SELinux
```bash
# 查看当前模式
adb shell getenforce          # Enforcing / Permissive

# 临时切换模式 (调试用)
adb shell setenforce 0        # Permissive
adb shell setenforce 1        # Enforcing

# 查看拒绝日志
adb logcat | grep "avc: denied"
# 示例输出:
# avc: denied { read } for name="my_device" dev="tmpfs"
#   ino=12345 scontext=u:r:my_app:s0
#   tcontext=u:object_r:device:s0 tclass=chr_file permissive=0

# 从日志生成策略规则
adb logcat -d | audit2allow -p out/target/product/<device>/root/sepolicy

# 查看文件/设备标签
adb shell ls -Z /dev/
adb shell ls -Z /data/
adb shell restorecon -Rv /data/my_app/   # 恢复默认标签
```

## 3. Keymaster / Keymint

### 密钥层次
```
                    Boot ROM
                       │
                  (硬件密钥)
                       │
                ┌──────┴──────┐
                │  Keymaster  │
                │  (硬件支持)  │
                └──────┬──────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   设备密钥        应用密钥       凭据密钥
   (device key)   (app key)    (credential key)
```

### Keymaster 功能
```java
// 生成密钥
KeyGenerator keyGen = KeyGenerator.getInstance(
    KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore");
keyGen.init(new KeyGenParameterSpec.Builder(
    "my_key",
    KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
    .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
    .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
    .setUserAuthenticationRequired(true)
    .setUserAuthenticationValidityDurationSeconds(300)
    .build());
SecretKey key = keyGen.generateKey();

// 加密
Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
cipher.init(Cipher.ENCRYPT_MODE, key);
byte[] iv = cipher.getIV();
byte[] ciphertext = cipher.doFinal(plaintext);

// 解密
cipher.init(Cipher.DECRYPT_MODE, key, new GCMParameterSpec(128, iv));
byte[] plaintext = cipher.doFinal(ciphertext);
```

## 4. Verified Boot (dm-verity)

### 验证流程
```
Bootloader
    │
    ├── 验证 boot 分区签名
    │       └── RSA 公钥存储在 bootloader 中
    │
    ├── 加载 kernel + ramdisk
    │
    └── 设置 dm-verity
            │
            ├── 从 vbmeta 读取 hashtree
            ├── 配置 device-mapper
            └── 挂载 system/vendor/product 分区
                    │
                    └── 每次读取数据块时验证 hash
                            │
                            ├── 验证通过 → 返回数据
                            └── 验证失败 → I/O 错误 / Recovery
```

### dm-verity 配置
```bash
# 生成 verity image
system/build/make/tools/verity/build_verity_metadata.py \
    --size $SYSTEM_SIZE \
    --block-device /dev/block/system \
    --algorithm sha256 \
    --salt $SALT \
    --root-hash $ROOT_HASH \
    --key verity.pk8 \
    --signer_path build/make/tools/verity \
    system.img verity.img

# 合并到 system image
system/build/make/tools/verity/append2simg \
    system.img verity.img
```

## 5. 权限管理

### 运行时权限
```java
// 检查权限
if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA)
        != PackageManager.PERMISSION_GRANTED) {
    // 请求权限
    ActivityCompat.requestPermissions(this,
        new String[]{Manifest.permission.CAMERA}, REQUEST_CAMERA);
}

// 处理权限结果
@Override
public void onRequestPermissionsResult(int requestCode,
        String[] permissions, int[] grantResults) {
    if (requestCode == REQUEST_CAMERA) {
        if (grantResults[0] == PackageManager.PERMISSION_GRANTED) {
            openCamera();
        } else {
            showPermissionDeniedDialog();
        }
    }
}
```

### 特权权限
```xml
<!-- 在 privapp-permissions-platform.xml 中声明 -->
<privapp-permissions package="com.android.settings">
    <permission name="android.permission.MANAGE_USERS"/>
    <permission name="android.permission.INTERACT_ACROSS_USERS"/>
    <permission name="android.permission.MOUNT_UNMOUNT_FILESYSTEMS"/>
</privapp-permissions>
```

## 6. 安全最佳实践

### 安全编码清单
- [ ] 所有外部输入进行验证 (Intent、URI、文件路径)
- [ ] 使用 ContentProvider 而非文件共享
- [ ] 组件导出检查 (`android:exported="false"`)
- [ ] WebView 安全配置 (禁用 JS 接口或限制)
- [ ] 数据加密存储 (KeyStore + 加密数据库)
- [ ] 网络通信使用 TLS 1.2+
- [ ] 代码混淆 (ProGuard / R8)
- [ ] 禁止日志输出敏感信息
- [ ] 使用 FLAG_SECURE 防止截屏
- [ ] Root 检测与完整性校验
---

## 相关链接

- [[linux-driver-dev|Linux 驱动]]
- [[secure-boot-impl|安全启动]]
- [[firmware-upgrade|固件升级]]
