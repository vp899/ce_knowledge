---
title: "Android 构建系统"
aliases:
  - "Soong 构建"
tags:
  - android
  - soong
  - ota
  - treble
module: "01-android"
status: active
---

# Android 构建系统

## 1. Soong (Blueprint) 构建系统

### Android.bp 基础语法

#### 模块类型
```json
// C/C++ 可执行文件
cc_binary {
    name: "my_binary",
    srcs: ["main.cpp"],
    shared_libs: ["liblog"],
    vendor: true,
}

// C/C++ 静态库
cc_library_static {
    name: "libmy_static",
    srcs: ["lib.cpp"],
    export_include_dirs: ["include"],
}

// C/C++ 共享库
cc_library_shared {
    name: "libmy_shared",
    srcs: ["lib.cpp"],
    shared_libs: ["liblog"],
    export_include_dirs: ["include"],
    version_script: "libmy.map",
}

// C/C++ 同时生成静态库和共享库
cc_library {
    name: "libmy",
    srcs: ["lib.cpp"],
    shared_libs: ["liblog"],
    export_include_dirs: ["include"],
}

// Java 库
java_library {
    name: "my_java_lib",
    srcs: ["src/**/*.java"],
    static_libs: ["lib_utils"],
    sdk_version: "current",
}

// Android 应用
android_app {
    name: "MyApp",
    srcs: ["src/**/*.java"],
    static_libs: ["my_java_lib"],
    certificate: "platform",    // 使用平台签名
    privileged: true,           // 特权应用
    required: ["my_daemon"],    // 依赖
}

// AIDL 接口
aidl_interface {
    name: "vendor.mydevice",
    vendor_available: true,
    srcs: ["aidl/**/*.aidl"],
    stability: "vintf",
}
```

#### 条件编译
```json
cc_binary {
    name: "my_binary",
    srcs: ["main.cpp"],
    
    target: {
        android: {
            cflags: ["-DANDROID_BUILD"],
            shared_libs: ["liblog"],
        },
        linux: {
            cflags: ["-DLINUX_BUILD"],
        },
    },
    
    product_variables: {
        debuggable: {
            true: {
                cflags: ["-DDEBUG_BUILD"],
                srcs: ["debug.cpp"],
            },
        },
    },
}
```

### Makefile 迁移到 Soong

| Makefile 语法 | Soong (Blueprint) |
|----------------|-------------------|
| `LOCAL_MODULE` | `name` |
| `LOCAL_SRC_FILES` | `srcs` |
| `LOCAL_C_INCLUDES` | `include_dirs` |
| `LOCAL_SHARED_LIBRARIES` | `shared_libs` |
| `LOCAL_STATIC_LIBRARIES` | `static_libs` |
| `LOCAL_CFLAGS` | `cflags` |
| `LOCAL_MODULE_PATH` | `relative_install_path` |
| `LOCAL_INIT_RC` | `init_rc` |
| `LOCAL_VINTF_FRAGMENTS` | `vintf_fragments` |

## 2. 产品配置

### 产品配置文件结构
```
device/<vendor>/<product>/
├── AndroidProducts.mk          # 产品列表入口
├── aosp_product.mk             # 产品继承
├── BoardConfig.mk              # 硬件/Board 配置
├── device.mk                   # 产品配置
├── vendorsetup.sh              # 环境设置脚本
├── overlay/                    # 资源覆盖
│   └── frameworks/base/core/res/res/values/config.xml
├── sepolicy/                   # SELinux 策略
├── fstab.<product>             # 挂载表
├── init.<product>.rc           # Init 脚本
└── bluetooth/                  # 蓝牙配置
```

### AndroidProducts.mk
```makefile
PRODUCT_MAKEFILES := \
    $(LOCAL_DIR)/aosp_product.mk

COMMON_LUNCH_CHOICES := \
    aosp_product-userdebug \
    aosp_product-user \
    aosp_product-eng
```

### BoardConfig.mk
```makefile
# 架构
TARGET_ARCH := arm64
TARGET_ARCH_VARIANT := armv8-a
TARGET_CPU_ABI := arm64-v8a
TARGET_CPU_VARIANT := cortex-a53

TARGET_2ND_ARCH := arm
TARGET_2ND_ARCH_VARIANT := armv7-a-neon
TARGET_2ND_CPU_ABI := armeabi-v7a
TARGET_2ND_CPU_ABI2 := armeabi

# 内核
BOARD_KERNEL_BASE := 0x80000000
BOARD_KERNEL_PAGESIZE := 2048
BOARD_KERNEL_CMDLINE := console=ttyMSM0,115200,n8
TARGET_PREBUILT_KERNEL := device/<vendor>/<product>/kernel

# 分区
BOARD_BOOTIMAGE_PARTITION_SIZE := 67108864
BOARD_SYSTEMIMAGE_PARTITION_SIZE := 2147483648
BOARD_VENDORIMAGE_PARTITION_SIZE := 536870912
BOARD_USERDATAIMAGE_PARTITION_SIZE := 576716800

# 文件系统
BOARD_SYSTEMIMAGE_FILE_SYSTEM_TYPE := ext4
BOARD_VENDORIMAGE_FILE_SYSTEM_TYPE := ext4

# 显示
TARGET_SCREEN_DENSITY := 320

# 蓝牙
BOARD_BLUETOOTH_BDROID_BUILDCFG_INCLUDE_DIR := device/<vendor>/<product>/bluetooth

# WiFi
WPA_SUPPLICANT_VERSION := VER_0_8_X
BOARD_WPA_SUPPLICANT_DRIVER := NL80211
```

### device.mk
```makefile
# 继承通用配置
$(call inherit-product, $(SRC_TARGET_DIR)/product/core_64_bit.mk)
$(call inherit-product, $(SRC_TARGET_DIR)/product/full_base.mk)

# 产品属性
PRODUCT_NAME := my_product
PRODUCT_DEVICE := my_device
PRODUCT_BRAND := MyBrand
PRODUCT_MODEL := MyDevice
PRODUCT_MANUFACTURER := MyManufacturer

# 包含产品文件
PRODUCT_COPY_FILES += \
    device/<vendor>/<product>/fstab.my_device:$(TARGET_COPY_OUT_VENDOR)/etc/fstab.my_device \
    device/<vendor>/<product>/init.my_device.rc:$(TARGET_COPY_OUT_VENDOR)/etc/init/hw/init.my_device.rc

# 产品包
PRODUCT_PACKAGES += \
    MySystemApp \
    my_daemon \
    libmy_shared

# 属性
PRODUCT_PROPERTY_OVERRIDES += \
    ro.my.device=1 \
    persist.my.config=default

# SELinux
BOARD_SEPOLICY_DIRS += device/<vendor>/<product>/sepolicy
```

## 3. [[firmware-upgrade|OTA]] 升级

### OTA 包生成
```bash
# 完整包
make otapackage -j$(nproc)

# 增量包
./build/tools/releasetools/ota_from_target_files \
    -i old_target_files.zip \
    new_target_files.zip \
    incremental_ota.zip

# 签名
java -jar signapk.jar -w \
    testkey.x509.pem testkey.pk8 \
    ota_unsigned.zip ota_signed.zip
```

### A/B 升级流程
```
1. 下载 OTA 包到 /data/ota_package/
2. UpdateEngine 解析 payload
3. 写入非活动分区 (slot B)
4. 更新 slot B 的 metadata
5. 设置 slot B 为 bootable
6. 重启 → bootloader 切换到 slot B
7. 启动成功 → 标记 slot B 为 successful
8. 启动失败 → bootloader 回滚到 slot A
```

### 自定义 OTA Server
```python
# 简单的 OTA 服务器接口
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/v1/ota/check', methods=['POST'])
def check_update():
    device_info = request.json
    
    current_version = device_info.get('build_number')
    device_model = device_info.get('model')
    
    # 查询是否有新版本
    update = db.find_update(device_model, current_version)
    
    if update:
        return jsonify({
            'update_available': True,
            'version': update.version,
            'download_url': update.download_url,
            'size': update.file_size,
            'checksum': update.sha256,
            'changelog': update.changelog,
        })
    
    return jsonify({'update_available': False})
```

## 4. 调试构建

### 常用构建命令
```bash
# 初始化环境
source build/envsetup.sh
lunch aosp_product-userdebug

# 构建整个系统
make -j$(nproc)

# 构建单个模块
m MyModule
mm                     # 构建当前目录模块
mmm path/to/module     # 构建指定路径模块

# 构建并刷机
make -j$(nproc) && \
m fastboot && \
fastboot flashall -w

# 清理
make clean
make clobber
```

### 构建加速
```bash
# 使用 ccache
export USE_CCACHE=1
export CCACHE_DIR=~/.ccache
ccache -M 50G

# 使用 distcc (分布式编译)
export DISTCC_HOSTS="localhost/8 host2/8 host3/8"

# 减少构建日志
make -j$(nproc) 2>&1 | tee build.log

# 只构建 vendor 部分
make vendorimage -j$(nproc)
```

## 5. Treble 架构

### 分区边界
```
┌─────────────────────────────────┐
│          System 分区             │
│  (Android Framework, 应用)       │
│  不含厂商代码                     │
└──────────────┬──────────────────┘
               │ HIDL / AIDL 接口
┌──────────────┴──────────────────┐
│          Vendor 分区             │
│  (HAL 实现, 厂商库, 固件)        │
│  与 Android 版本解耦             │
└─────────────────────────────────┘
```

### VINTF (Vendor Interface)
```xml
<!-- vendor manifest -->
<manifest version="1.0" type="device">
    <hal format="hidl">
        <name>android.hardware.camera.provider</name>
        <version>2.6</version>
        <interface>
            <name>ICameraProvider</name>
            <instance>internal/0</instance>
        </interface>
    </hal>
    
    <hal format="aidl">
        <name>android.hardware.health</name>
        <version>2</version>
        <interface>
            <name>IHealth</name>
            <instance>default</instance>
        </interface>
    </hal>
</manifest>
```
---

## 相关链接

- [[linux-driver-dev|Linux 驱动]]
- [[secure-boot-impl|安全启动]]
- [[firmware-upgrade|固件升级]]
