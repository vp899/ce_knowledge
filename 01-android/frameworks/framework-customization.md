# Android Framework 定制开发

## 1. AOSP 源码结构

### 核心目录
```
aosp/
├── art/                # Android Runtime (ART)
├── bionic/             # C 库 (libc, libm, libdl)
├── bootable/           # Recovery、Bootloader
├── build/              # 构建系统核心
│   ├── core/           # Makefile 规则
│   ├── make/           # 主构建脚本
│   └── soong/          # Blueprint 构建
├── cts/                # 兼容性测试套件
├── device/             # 设备配置 (每个产品一个目录)
├── external/           # 第三方开源库
├── frameworks/         # ★ Framework 核心
│   ├── base/           # Android Framework (SystemServer, AMS, WMS...)
│   ├── av/             # 多媒体框架 (AudioFlinger, Camera, MediaCodec)
│   ├── native/         # Native 服务 (SurfaceFlinger, InputFlinger)
│   └── opt/            # 可选组件 (Telephony, Calendar)
├── hardware/           # HAL 层定义与默认实现
│   ├── interfaces/     # HIDL 接口定义
│   └── libhardware/    # 传统 HAL
├── kernel/             # 内核源码
├── packages/           # 系统应用
│   ├── apps/           # 可替换应用 (Settings, Camera, Launcher)
│   ├── providers/      # ContentProvider (ContactsProvider, MediaProvider)
│   └── services/       # 系统服务
├── platform_testing/   # 平台测试
├── system/             # 底层系统组件
│   ├── core/           # init, adb, logd, property
│   ├── sepolicy/       # SELinux 策略
│   └── vold/           # 存储管理
├── tools/              # 开发工具
└── vendor/             # 厂商私有代码
```

### 关键文件
| 文件 | 用途 |
|------|------|
| `build/envsetup.sh` | 初始化编译环境 |
| `device/<vendor>/<product>/AndroidProducts.mk` | 产品定义入口 |
| `device/<vendor>/<product>/BoardConfig.mk` | 硬件配置 |
| `device/<vendor>/<product>/device.mk` | 产品配置 |
| `frameworks/base/core/res/res/values/config.xml` | 系统配置常量 |

## 2. SystemServer 服务

### 启动流程
```
init 进程 (PID 1)
    │
    ├── 解析 init.rc
    │
    ├── 启动 zygote 进程
    │       │
    │       ├── 加载 ART 虚拟机
    │       ├── 预加载公共类与资源
    │       └── 等待 Socket 连接
    │
    └── Zygote fork 出 system_server
            │
            ├── startBootstrapServices()
            │       ├── ActivityManagerService
            │       ├── PowerManagerService
            │       ├── PackageManagerService
            │       └── ...
            │
            ├── startCoreServices()
            │       ├── BatteryService
            │       ├── UsageStatsService
            │       └── ...
            │
            └── startOtherServices()
                    ├── WindowManagerService
                    ├── InputManagerService
                    ├── ConnectivityService
                    ├── AudioService
                    └── ...
```

### 添加自定义系统服务

#### 步骤 1: 定义 AIDL 接口
```java
// frameworks/base/core/java/android/app/IMyService.aidl
package android.app;

interface IMyService {
    void setData(String key, String value);
    String getData(String key);
    void registerCallback(IMyCallback callback);
}
```

#### 步骤 2: 实现服务
```java
// frameworks/base/services/core/java/com/android/server/MyService.java
package com.android.server;

import android.app.IMyService;

public class MyService extends IMyService.Stub {
    private static final String TAG = "MyService";
    private final Context mContext;
    private final ArrayMap<String, String> mData = new ArrayMap<>();

    MyService(Context context) {
        mContext = context;
    }

    @Override
    public void setData(String key, String value) {
        mContext.enforceCallingOrSelfPermission(
            "com.android.permission.MY_SERVICE", "Need MY_SERVICE permission");
        synchronized (mData) {
            mData.put(key, value);
        }
    }

    @Override
    public String getData(String key) {
        synchronized (mData) {
            return mData.get(key);
        }
    }
}
```

#### 步骤 3: 注册到 SystemServer
```java
// frameworks/base/services/java/com/android/server/SystemServer.java
private void startOtherServices() {
    // ... 已有代码 ...
    
    // 注册自定义服务
    ServiceManager.addService("my_service", new MyService(mSystemContext));
    
    // 或者通过 publishBinderService 方式
    traceBeginAndSlog("MyService");
    mSystemServiceManager.startService(MyService.class);
    traceEnd();
}
```

#### 步骤 4: 创建 Manager 类供应用调用
```java
// frameworks/base/core/java/android/app/MyManager.java
package android.app;

public class MyManager {
    private final IMyService mService;

    public MyManager(IMyService service) {
        mService = service;
    }

    public void setData(String key, String value) {
        try {
            mService.setData(key, value);
        } catch (RemoteException e) {
            throw e.rethrowFromSystemServer();
        }
    }

    public String getData(String key) {
        try {
            return mService.getData(key);
        } catch (RemoteException e) {
            throw e.rethrowFromSystemServer();
        }
    }
}
```

#### 步骤 5: 注册到 Context
```java
// frameworks/base/core/java/android/app/SystemServiceRegistry.java
static {
    // ... 已有注册 ...
    
    registerService(Context.MY_SERVICE, MyManager.class,
        new CachedServiceFetcher<MyManager>() {
            @Override
            public MyManager createService(ContextImpl ctx) {
                IBinder binder = ServiceManager.getService(Context.MY_SERVICE);
                IMyService service = IMyService.Stub.asInterface(binder);
                return new MyManager(service);
            }
        });
}
```

## 3. HAL 层开发

### HIDL 接口定义
```hal
// hardware/interfaces/mydevice/1.0/IMyDevice.hal
package android.hardware.mydevice@1.0;

interface IMyDevice {
    init() generates (int32_t status);
    
    readSensor() generates (int32_t status, SensorData data);
    
    setConfig(Config config) generates (int32_t status);

    struct SensorData {
        int32_t temperature;
        int32_t humidity;
        int64_t timestamp;
    };

    struct Config {
        int32_t sampleRate;
        bool enableLog;
    };
};
```

### HAL 实现
```cpp
// hardware/interfaces/mydevice/1.0/default/MyDevice.cpp
#include "MyDevice.h"

namespace android::hardware::mydevice::V1_0::implementation {

Return<int32_t> MyDevice::init() {
    // 打开设备节点
    mFd = open("/dev/my_sensor", O_RDWR);
    if (mFd < 0) {
        ALOGE("Failed to open device: %s", strerror(errno));
        return -1;
    }
    return 0;
}

Return<void> MyDevice::readSensor(readSensor_cb _hidl_cb) {
    SensorData data = {};
    struct raw_sensor raw;
    
    if (ioctl(mFd, IOCTL_READ_SENSOR, &raw) < 0) {
        _hidl_cb(-1, data);
        return Void();
    }
    
    data.temperature = raw.temp;
    data.humidity = raw.humi;
    data.timestamp = systemTime(SYSTEM_TIME_MONOTONIC);
    
    _hidl_cb(0, data);
    return Void();
}

} // namespace
```

### SELinux 策略配置
```te
# system/sepolicy/private/my_service.te
type my_service, system_api_service, system_server_service, service_manager_type;

# system/sepolicy/private/service_contexts
my_service                  u:object_r:my_service:s0

# system/sepolicy/private/my_device.te
type my_device, dev_type;
allow hal_mydevice_default my_device:chr_file rw_file_perms;

# device/<vendor>/<product>/sepolicy/my_device.te
allow hal_mydevice_default my_device:chr_file { open read write ioctl };
```

## 4. Input 系统定制

### InputManagerService 架构
```
硬件事件
    │
    ├── EventHub (/dev/input/*)
    │       │
    │       └── 读取 input_event
    │
    ├── InputReader
    │       ├── EventHub 接口
    │       ├── 设备配置 (InputDeviceConfig)
    │       ├── 映射器 (TouchInputMapper, KeyboardInputMapper)
    │       └── 生成 RawEvent
    │
    ├── InputDispatcher
    │       ├── 查找目标窗口 (findFocusedWindow)
    │       ├── ANR 检测
    │       └── 分发事件
    │
    └── 应用层 (ViewRootImpl → InputEventReceiver)
```

### 自定义按键映射
```ini
# device/<vendor>/<product>/keylayout/Generic.kl
# 格式: key <scan_code> <key_code> [flags...]

key 115   VOLUME_UP
key 116   VOLUME_DOWN
key 114   VOLUME_DOWN
key 158   BACK
key 139   MENU
key 102   HOME
key 217   FOCUS

# 自定义按键
key 200   MY_FUNCTION_1
key 201   MY_FUNCTION_2
```

### 自定义按键处理
```java
// 在 PhoneWindowManager.java 中拦截
@Override
public int interceptKeyBeforeDispatching(KeyEvent event, int policyFlags) {
    final int keyCode = event.getKeyCode();
    
    if (keyCode == KeyEvent.KEYCODE_MY_FUNCTION_1) {
        if (event.getAction() == KeyEvent.ACTION_DOWN) {
            // 启动自定义功能
            launchMyApp();
            return -1; // 消费事件
        }
    }
    
    return super.interceptKeyBeforeDispatching(event, policyFlags);
}
```

## 5. 电源管理定制

### PowerManagerService 工作流
```
用户操作 / Sensor 事件
    │
    ├── 更新 WakeLock 状态
    ├── 更新 Display 状态
    │       │
    │       ├── Brightness (亮度策略)
    │       ├── Screen Off Timeout
    │       └── Doze Mode
    │
    └── 系统电源状态切换
            │
            ├── Awake → Dim → Doze → Sleep
            ├── WakeLock 阻止休眠
            └── Suspend Blocker 控制
```

### 低功耗模式实现
```cpp
// 内核层: 定义休眠状态
static int my_suspend_enter(suspend_state_t state) {
    switch (state) {
    case PM_SUSPEND_STANDBY:
        // 浅睡眠: 关闭 CPU 时钟，保留 RAM
        clk_disable(cpu_clk);
        break;
    case PM_SUSPEND_MEM:
        // 深睡眠: 保存上下文到 RAM，关闭大部分电源
        save_context();
        power_off_non_essential();
        break;
    }
    return 0;
}
```

## 6. WindowManager 定制

### 窗口层级
```
TYPE_STATUS_BAR              (系统状态栏)
TYPE_NAVIGATION_BAR          (导航栏)
TYPE_INPUT_METHOD            (输入法)
TYPE_SYSTEM_ALERT            (系统弹窗)
TYPE_APPLICATION_OVERLAY     (悬浮窗)
TYPE_APPLICATION             (普通应用)
TYPE_WALLPAPER               (壁纸)
```

### 自定义窗口动画
```xml
<!-- frameworks/base/core/res/res/anim/my_window_enter.xml -->
<set xmlns:android="http://schemas.android.com/apk/res/android"
    android:interpolator="@android:interpolator/decelerate_cubic">
    
    <alpha
        android:fromAlpha="0.0"
        android:toAlpha="1.0"
        android:duration="300" />
    
    <scale
        android:fromXScale="0.9"
        android:toXScale="1.0"
        android:fromYScale="0.9"
        android:toYScale="1.0"
        android:pivotX="50%"
        android:pivotY="50%"
        android:duration="300" />
</set>
```

## 7. 调试技巧

### 常用调试命令
```bash
# 查看系统服务
adb shell service list
adb shell dumpsys activity
adb shell dumpsys window
adb shell dumpsys power

# 日志过滤
adb logcat -s ActivityManager:I WindowManager:I
adb logcat | grep -E "^(E|W)/"

# Trace 分析
adb shell atrace -t 10 -o /data/local/tmp/trace.html am wm view
adb pull /data/local/tmp/trace.html

# 性能分析
adb shell dumpsys gfxinfo <package>
adb shell dumpsys meminfo <package>
adb shell top -m 10

# 系统属性
adb shell getprop | grep my.property
adb shell setprop debug.my.module 1
```

### Systrace / Perfetto 分析
```bash
# Perfetto trace 配置
cat > /tmp/config.pbtx << EOF
buffers {
  size_kb: 65536
  fill_policy: RING_BUFFER
}
data_sources {
  config {
    name: "linux.ftrace"
    ftrace_config {
      ftrace_events: "sched/sched_switch"
      ftrace_events: "power/suspend_resume"
      ftrace_events: "power/cpu_frequency"
      atrace_categories: "am"
      atrace_categories: "wm"
      atrace_categories: "view"
    }
  }
}
duration_ms: 10000
EOF

adb push /tmp/config.pbtx /data/local/tmp/
adb shell perfetto -c /data/local/tmp/config.pbtx -o /data/local/tmp/trace.perfetto
```
