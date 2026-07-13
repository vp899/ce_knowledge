# Android 系统层开发

## 1. Init 系统

### init.rc 语法
```rc
# 触发器
on boot
    # 设置系统属性
    setprop sys.boot_completed 0
    
    # 创建目录
    mkdir /data/my_service 0770 system system
    
    # 挂载文件系统
    mount ext4 /dev/block/by-name/vendor /vendor wait

# 服务定义
service my_daemon /vendor/bin/my_daemon
    class main
    user system
    group system audio
    capabilities SYS_NICE
    oneshot                    # 只运行一次
    disabled                   # 默认不启动
    seclabel u:r:my_daemon:s0  # SELinux 标签
    socket my_socket stream 0660 system system  # 创建 socket
    writepid /dev/cpuset/foreground/tasks       # 写入 cpuset

# 触发器链
on property:sys.boot_completed=1
    start my_daemon

on property:debug.my.enable=1
    restart my_daemon
```

### 自定义 Init 服务完整流程

#### 1. 编写 Native 守护进程
```cpp
// system/core/my_daemon/main.cpp
#include <utils/Log.h>
#include <binder/IPCThreadState.h>
#include <binder/ProcessState.h>
#include <binder/IServiceManager.h>

#define LOG_TAG "my_daemon"

int main(int argc, char** argv) {
    ALOGI("my_daemon starting");
    
    // 初始化 Binder
    sp<ProcessState> proc(ProcessState::self());
    
    // 注册服务
    sp<IServiceManager> sm = defaultServiceManager();
    sm->addService(String16("my_daemon"), new MyDaemonService());
    
    // 进入主循环
    IPCThreadState::self()->startThreadPool();
    
    // 主循环处理
    while (true) {
        // 处理业务逻辑
        sleep(1);
    }
    
    return 0;
}
```

#### 2. Android.bp 编译
```json
cc_binary {
    name: "my_daemon",
    vendor: true,
    srcs: [
        "main.cpp",
        "MyDaemonService.cpp",
    ],
    shared_libs: [
        "libbase",
        "libbinder",
        "libcutils",
        "liblog",
        "libutils",
    ],
    cflags: [
        "-Wall",
        "-Werror",
        "-Wno-unused-parameter",
    ],
}
```

#### 3. SELinux 策略
```te
# 定义域
type my_daemon, domain;
type my_daemon_exec, exec_type, vendor_file_type, file_type;

# 允许从 init 启动
init_daemon_domain(my_daemon)

# 允许访问设备节点
allow my_daemon my_device:chr_file { open read write ioctl };

# 允许使用 Binder
binder_use(my_daemon)
binder_call(my_daemon, servicemanager)

# 允许写日志
allow my_daemon kmsg_device:file { open write };
```

#### 4. 文件系统权限 (file_contexts)
```
/vendor/bin/my_daemon    u:object_r:my_daemon_exec:s0
/dev/my_device           u:object_r:my_device:s0
/data/my_service(/.*)?   u:object_r:my_service_data_file:s0
```

## 2. Native 服务开发

### Binder 服务框架
```cpp
// IMyService.h
#pragma once
#include <binder/IInterface.h>
#include <binder/Parcel.h>

namespace android {

class IMyService : public IInterface {
public:
    DECLARE_META_INTERFACE(MyService);
    
    enum {
        GET_DATA = IBinder::FIRST_CALL_TRANSACTION,
        SET_DATA,
        REGISTER_LISTENER,
    };
    
    virtual status_t getData(const String16& key, String16* outValue) = 0;
    virtual status_t setData(const String16& key, const String16& value) = 0;
};

// BnMyService.h (服务端)
class BnMyService : public BnInterface<IMyService> {
public:
    virtual status_t onTransact(uint32_t code, const Parcel& data,
                                Parcel* reply, uint32_t flags);
};

// BpMyService.h (客户端代理)
class BpMyService : public BpInterface<IMyService> {
public:
    BpMyService(const sp<IBinder>& impl) : BpInterface<IMyService>(impl) {}
    
    virtual status_t getData(const String16& key, String16* outValue) {
        Parcel data, reply;
        data.writeInterfaceToken(IMyService::getInterfaceDescriptor());
        data.writeString16(key);
        remote()->transact(GET_DATA, data, &reply);
        *outValue = reply.readString16();
        return reply.readInt32();
    }
};

} // namespace android
```

### HIDL 服务注册
```cpp
// 注册 HIDL 服务
#include <android/hardware/mydevice/1.0/IMyDevice.h>

int main() {
    sp<IMyDevice> device = new MyDevice();
    
    // 注册为 HAL 服务
    device->registerAsService();
    
    // 进入 HIDL 线程池
    joinRpcThreadpool();
    
    return 0;
}
```

## 3. 系统属性 (System Properties)

### 属性分类
| 前缀 | 权限 | 用途 |
|------|------|------|
| `ro.` | 只读 | 系统常量 (ro.build.version) |
| `persist.` | 持久化 | 重启后保留 (persist.sys.timezone) |
| `sys.` | 运行时 | 系统状态 (sys.boot_completed) |
| `ctl.` | 控制 | 服务控制 (ctl.start/stop) |
| `debug.` | 调试 | 调试开关 (debug.my.verbose) |
| `vendor.` | vendor | 厂商属性 |

### 属性配置
```xml
<!-- vendor/etc/my_property_contexts -->
my.device.mode     u:object_r:my_prop:s0
my.device.config   u:object_r:my_prop:s0
```

```te
# SELinux: 定义属性类型
vendor_internal_prop(my_prop)
set_prop(my_daemon, my_prop)
get_prop(default_prop, my_prop)
```

## 4. 存储与分区

### Android 分区布局 (A/B)
```
Slot A                    Slot B
├── boot_a                ├── boot_b
├── dtbo_a                ├── dtbo_b
├── vendor_boot_a         ├── vendor_boot_b
├── system_a              ├── system_b
├── vendor_a              ├── vendor_b
├── product_a             ├── product_b
├── vbmeta_a              ├── vbmeta_b
└── init_boot_a           └── init_boot_b

公共分区:
├── super                 (动态分区容器)
├── userdata              (用户数据)
├── metadata              (元数据/加密)
├── misc                  (bootloader 控制)
├── frp                   (恢复出厂保护)
└── persist               (持久化数据)
```

### 动态分区 (Dynamic Partitions)
```cpp
// device.mk 中定义
PRODUCT_USE_DYNAMIC_PARTITIONS := true
PRODUCT_SUPER_PARTITION_SIZE := 6442450944  # 6GB

# 定义逻辑分区组
PRODUCT_SUPER_PARTITION_GROUPS := my_group
PRODUCT_PARTITION_SIZE := 2147483648  # 2GB
my_group_partition_list := system vendor product

# 各分区默认大小
BOARD_SYSTEMIMAGE_PARTITION_SIZE := 2147483648
BOARD_VENDORIMAGE_PARTITION_SIZE := 536870912
BOARD_PRODUCTIMAGE_PARTITION_SIZE := 536870912
```

## 5. SELinux 策略开发

### 策略文件结构
```
system/sepolicy/
├── private/            # 系统私有策略
├── public/             # 公共接口策略
├── vendor/             # vendor 策略
├── reqd_mask/          # 必需策略
└── prebuilts/          # 预编译策略

device/<vendor>/<product>/sepolicy/
├── private/            # 设备私有策略
├── public/             # 设备公共策略
└── vendor/             # 设备 vendor 策略
```

### 常用策略规则
```te
# 允许 my_daemon 访问 /dev/my_device
allow my_daemon my_device:chr_file { open read write ioctl getattr };

# 允许 my_daemon 调用 my_service
allow my_daemon my_service:service_manager { find add };

# 允许 my_daemon 使用 Binder
binder_use(my_daemon)
binder_call(my_daemon, platform_app)

# 属性上下文
set_prop(my_daemon, my_prop)

# neverallow 检查 (防止过度授权)
neverallow my_daemon block_device:blk_file { read write };
neverallow my_daemon { file_type -my_data_file }:file { write append };
```

### 调试 SELinux
```bash
# 查看审计日志
adb logcat | grep avc

# 典型拒绝日志
# avc: denied { read } for name="my_device" dev="tmpfs"
#   scontext=u:r:my_daemon:s0 tcontext=u:object_r:device:s0
#   tclass=chr_file permissive=0

# 生成策略规则
adb shell audit2allow -i /dev/stdin < avc_log.txt

# 临时切换到宽容模式 (调试)
adb shell setenforce 0
adb shell getenforce  # 显示 Permissive

# 查看文件标签
adb shell ls -Z /dev/
adb shell ls -Z /vendor/bin/
```

## 6. 日志系统

### Android 日志层次
```cpp
// 内核日志 → /dev/kmsg → dmesg
// Native 日志 → __android_log_print → logd
// Java 日志 → android.util.Log → logd

// Native 日志使用
#include <log/log.h>

ALOGV("Verbose message: %d", value);  // Verbose
ALOGD("Debug message");                // Debug
ALOGI("Info message");                 // Info
ALOGW("Warning message");              // Warning
ALOGE("Error message: %s", err);       // Error
ALOGF("Fatal message");                // Fatal (abort)

// 条件日志
ALOGI_IF(debug_enabled, "Debug info: %s", data);
```

### 自定义 Log Tag 控制
```cpp
// 使用 property 控制日志级别
static bool isVerboseEnabled() {
    char value[PROPERTY_VALUE_MAX];
    property_get("debug.my.verbose", value, "0");
    return atoi(value) == 1;
}

#define MY_LOGV(fmt, ...) \
    do { if (isVerboseEnabled()) ALOGV(fmt, ##__VA_ARGS__); } while(0)
```
