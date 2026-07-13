level: intermediate
---
title: "OTA 后台升级系统"
aliases:
  - "OTA 服务器"
  - "固件升级后台"
  - "设备管理系统"
tags:
  - ota
  - backend
  - cloud
  - device-management
  - upgrade
module: "12-backend"
status: active
---

# OTA 后台升级系统

## 概述

本文介绍 ota-server 领域的 intermediate 级别知识。

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

### 1. 系统架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          OTA 升级系统架构                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │                        管理后台 (Admin Portal)                     │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐             │ │
│  │  │ 固件管理 │ │ 设备管理 │ │ 升级策略 │ │ 数据统计 │             │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘             │ │
│  └───────────────────────────────┬───────────────────────────────────┘ │
│                                  │ HTTPS                                │
│  ┌───────────────────────────────┴───────────────────────────────────┐ │
│  │                          API 网关                                   │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐             │ │
│  │  │ 认证鉴权 │ │ 限流熔断 │ │ 日志审计 │ │ API 路由 │             │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘             │ │
│  └───────────────────────────────┬───────────────────────────────────┘ │
│                                  │                                      │
│  ┌───────────────────────────────┴───────────────────────────────────┐ │
│  │                        微服务层                                     │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐             │ │
│  │  │ 设备服务 │ │ 固件服务 │ │ 升级服务 │ │ 通知服务 │             │ │
│  │  │(Registry)│ │(Package) │ │(Upgrade) │ │(Push)    │             │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘             │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐                          │ │
│  │  │ 统计服务 │ │ 配置服务 │ │ 日志服务 │                          │ │
│  │  └──────────┘ └──────────┘ └──────────┘                          │ │
│  └───────────────────────────────┬───────────────────────────────────┘ │
│                                  │                                      │
│  ┌───────────────────────────────┴───────────────────────────────────┐ │
│  │                        数据层                                       │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐             │ │
│  │  │PostgreSQL│ │  Redis   │ │  MinIO   │ │ Kafka    │             │ │
│  │  │(元数据)  │ │(缓存/在线│ │(固件存储)│ │(消息队列)│             │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘             │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                  │                                      │
│                              MQTT/HTTPS                                 │
│                                  │                                      │
│  ┌───────────────────────────────┴───────────────────────────────────┐ │
│  │                        设备端                                       │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐             │ │
│  │  │ 无人机   │ │ 手持云台 │ │ 扫地机   │ │ 3D 打印机│             │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘             │ │
│  └───────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2. 数据库设计

### 核心数据表
```sql
-- 设备注册表
CREATE TABLE devices (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_sn       VARCHAR(64) UNIQUE NOT NULL,        -- 设备序列号
    product_id      VARCHAR(32) NOT NULL,               -- 产品型号
    hw_version      VARCHAR(16) NOT NULL,               -- 硬件版本
    fw_version      VARCHAR(32),                        -- 当前固件版本
    mcu_type        VARCHAR(32),                        -- MCU 型号
    status          VARCHAR(16) DEFAULT 'offline',      -- online/offline/locked
    last_heartbeat  TIMESTAMP,                          -- 最后心跳
    last_upgrade    TIMESTAMP,                          -- 最后升级时间
    ota_state       VARCHAR(16) DEFAULT 'idle',         -- idle/downloading/installing
    ota_progress    SMALLINT DEFAULT 0,                 -- 升级进度 0-100
    region          VARCHAR(16),                        -- 区域 (cn/us/eu)
    tags            JSONB DEFAULT '{}',                 -- 标签 (测试/量产/内测)
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_devices_product ON devices(product_id);
CREATE INDEX idx_devices_status ON devices(status);
CREATE INDEX idx_devices_version ON devices(fw_version);

-- 固件版本表
CREATE TABLE firmware_packages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id      VARCHAR(32) NOT NULL,               -- 产品型号
    version         VARCHAR(32) NOT NULL,               -- 版本号 (v2.1.3)
    build_number    INTEGER NOT NULL,                   -- 构建号
    hw_version_min  VARCHAR(16),                        -- 最低硬件版本
    hw_version_max  VARCHAR(16),                        -- 最高硬件版本
    file_path       VARCHAR(256) NOT NULL,              -- 文件存储路径
    file_size       BIGINT NOT NULL,                    -- 文件大小 (bytes)
    file_checksum   VARCHAR(128) NOT NULL,              -- SHA256 校验
    signature       TEXT,                                -- 签名
    release_notes   TEXT,                                -- 更新说明
    changelog       JSONB,                               -- 变更列表
    status          VARCHAR(16) DEFAULT 'draft',        -- draft/published/deprecated
    is_mandatory    BOOLEAN DEFAULT FALSE,              -- 是否强制升级
    rollout_ratio   SMALLINT DEFAULT 0,                 -- 灰度比例 0-100
    target_tags     JSONB DEFAULT '[]',                 -- 目标设备标签
    created_at      TIMESTAMP DEFAULT NOW(),
    published_at    TIMESTAMP,
    UNIQUE(product_id, version)
);

-- 升级任务表
CREATE TABLE upgrade_tasks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id       UUID REFERENCES devices(id),
    package_id      UUID REFERENCES firmware_packages(id),
    from_version    VARCHAR(32),                        -- 原版本
    to_version      VARCHAR(32),                        -- 目标版本
    status          VARCHAR(16) DEFAULT 'pending',      -- pending/downloading/installing/success/failed/rollback
    progress        SMALLINT DEFAULT 0,                 -- 进度 0-100
    error_code      INTEGER,                            -- 错误码
    error_message   TEXT,                                -- 错误信息
    retry_count     SMALLINT DEFAULT 0,                 -- 重试次数
    max_retries     SMALLINT DEFAULT 3,                 -- 最大重试
    scheduled_at    TIMESTAMP,                          -- 计划执行时间
    started_at      TIMESTAMP,                          -- 实际开始时间
    completed_at    TIMESTAMP,                          -- 完成时间
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_upgrade_device ON upgrade_tasks(device_id);
CREATE INDEX idx_upgrade_status ON upgrade_tasks(status);

-- 升级日志表
CREATE TABLE upgrade_logs (
    id              BIGSERIAL PRIMARY KEY,
    task_id         UUID REFERENCES upgrade_tasks(id),
    device_id       UUID REFERENCES devices(id),
    event_type      VARCHAR(32) NOT NULL,               -- check/download/install/verify/reboot/complete/error
    event_data      JSONB,                               -- 事件详情
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_logs_task ON upgrade_logs(task_id);
CREATE INDEX idx_logs_device ON upgrade_logs(device_id);
```

### 3. OTA 升级 API

### 设备端 API
```
API 1: 查询可用升级
─────────────────────────────────────────────
POST /api/v1/ota/check
Content-Type: application/json
Authorization: Bearer <device_token>

Request:
{
    "device_sn": "DRN-2025-001234",
    "product_id": "drone_v2",
    "hw_version": "3.2",
    "fw_version": "2.1.0",
    "region": "cn"
}

Response (有升级):
{
    "update_available": true,
    "package": {
        "version": "2.1.3",
        "file_url": "https://cdn.example.com/firmware/v2.1.3.bin",
        "file_size": 524288,
        "file_checksum": "sha256:abc123...",
        "signature": "base64:...",
        "is_mandatory": false,
        "release_notes": "修复了 GPS 定位问题..."
    }
}

Response (无升级):
{
    "update_available": false
}

─────────────────────────────────────────────
API 2: 上报升级进度
─────────────────────────────────────────────
POST /api/v1/ota/progress
Authorization: Bearer <device_token>

Request:
{
    "device_sn": "DRN-2025-001234",
    "task_id": "uuid-xxx",
    "status": "downloading",
    "progress": 45,
    "error_code": 0
}

Response:
{
    "ack": true,
    "action": "continue"  // continue/pause/abort
}

─────────────────────────────────────────────
API 3: 上报升级结果
─────────────────────────────────────────────
POST /api/v1/ota/result
Authorization: Bearer <device_token>

Request:
{
    "device_sn": "DRN-2025-001234",
    "task_id": "uuid-xxx",
    "status": "success",
    "from_version": "2.1.0",
    "to_version": "2.1.3",
    "upgrade_duration": 120,
    "reboot_count": 1
}
```

### 管理端 API
```
API: 创建升级任务
─────────────────────────────────────────────
POST /api/v1/admin/upgrade/create
Authorization: Bearer <admin_token>

Request:
{
    "package_id": "uuid-xxx",
    "target": {
        "type": "device_list",      // device_list/product/version/tag
        "device_sns": ["DRN-001", "DRN-002"]
    },
    "strategy": {
        "scheduled_at": "2025-01-16T02:00:00Z",
        "max_concurrent": 100,
        "retry_count": 3,
        "rollback_on_failure": true,
        "timeout_minutes": 30
    }
}

API: 查询升级统计
─────────────────────────────────────────────
GET /api/v1/admin/upgrade/stats?package_id=xxx

Response:
{
    "total_devices": 10000,
    "pending": 2000,
    "downloading": 500,
    "installing": 100,
    "success": 7000,
    "failed": 300,
    "rollback": 100,
    "success_rate": 95.8
}
```

### 4. 升级策略

### 灰度发布
```
灰度发布流程:

Phase 1: 内部测试 (0.1%)
├── 目标: 内部测试设备 (10-50 台)
├── 时间: 1-3 天
├── 关注: 基本功能, 严重 Bug
└── 决策: 继续/暂停/回滚

Phase 2: 小范围灰度 (1%)
├── 目标: 随机 1% 用户
├── 时间: 3-7 天
├── 关注: 稳定性, 用户反馈, 崩溃率
└── 决策: 继续/暂停/回滚

Phase 3: 中范围灰度 (10%)
├── 目标: 随机 10% 用户
├── 时间: 3-7 天
├── 关注: 性能, 兼容性, 长稳
└── 决策: 继续/暂停/回滚

Phase 4: 全量发布 (100%)
├── 目标: 所有用户
├── 时间: 持续
├── 关注: 持续监控
└── 决策: 正常/回滚

灰度选择策略:
├── 随机: 设备 ID 哈希取模
├── 区域: 先小区域后大区域
├── 机型: 先旗舰后入门
├── 标签: 内测用户 → 公测用户 → 全量
└── 版本: 先旧版本设备
```

### 回滚机制
```
设备端回滚策略:

方案 1: A/B 分区 (推荐)
┌─────────────────────────────────────┐
│  Slot A (当前运行)  │  Slot B (待升级)│
│  v2.1.0            │  v2.1.3        │
└────────────────────┴────────────────┘
升级流程:
1. 写入 Slot B
2. 设置启动标志指向 B
3. 重启
4. 启动成功 → 标记 B 为活动
5. 启动失败 → 计数器++
6. 计数器 > 3 → 回滚到 A

方案 2: Recovery 分区
┌──────────┬──────────┬──────────┐
│ Boot     │ System   │ Recovery │
│ (loader) │ (主系统) │ (恢复)   │
└──────────┴──────────┴──────────┘
升级流程:
1. 下载到 Recovery
2. 校验签名
3. 替换 System
4. 失败 → 从 Recovery 恢复

服务端回滚:
1. 检测到失败率 > 阈值 (5%)
2. 自动暂停灰度
3. 通知研发团队
4. 评估是否回滚
5. 回滚: 废弃当前版本, 推送上一版本
```

### 5. 设备端 OTA 客户端

```c
/* ota_client.c */
#include "ota_client.h"
#include "http_client.h"
#include "crypto.h"
#include "flash.h"

#define OTA_STATE_IDLE        0
#define OTA_STATE_CHECKING    1
#define OTA_STATE_DOWNLOADING 2
#define OTA_STATE_VERIFYING   3
#define OTA_STATE_INSTALLING  4
#define OTA_STATE_REBOOTING   5

typedef struct {
    int state;
    char current_version[32];
    char target_version[32];
    uint32_t total_size;
    uint32_t downloaded;
    uint32_t retry_count;
    char download_url[256];
    uint8_t expected_hash[32];
    ota_callback_t callback;
} OTA_Client;

/* 检查升级 */
int ota_check_update(OTA_Client *ota) {
    ota->state = OTA_STATE_CHECKING;
    
    // 构建请求
    cJSON *req = cJSON_CreateObject();
    cJSON_AddStringToObject(req, "device_sn", get_device_sn());
    cJSON_AddStringToObject(req, "product_id", get_product_id());
    cJSON_AddStringToObject(req, "hw_version", get_hw_version());
    cJSON_AddStringToObject(req, "fw_version", ota->current_version);
    
    // 发送请求
    HTTP_Response resp;
    int ret = http_post(OTA_CHECK_URL, req, &resp);
    cJSON_Delete(req);
    
    if (ret != 0) {
        ota->state = OTA_STATE_IDLE;
        return -1;
    }
    
    // 解析响应
    cJSON *json = cJSON_Parse(resp.body);
    bool available = cJSON_GetObjectItem(json, "update_available")->valueint;
    
    if (!available) {
        cJSON_Delete(json);
        ota->state = OTA_STATE_IDLE;
        return 0;  // 无升级
    }
    
    // 提取升级信息
    cJSON *package = cJSON_GetObjectItem(json, "package");
    strncpy(ota->target_version,
            cJSON_GetObjectItem(package, "version")->valuestring,
            sizeof(ota->target_version));
    strncpy(ota->download_url,
            cJSON_GetObjectItem(package, "file_url")->valuestring,
            sizeof(ota->download_url));
    ota->total_size = cJSON_GetObjectItem(package, "file_size")->valueint;
    
    // 提取校验和
    hex_to_bytes(cJSON_GetObjectItem(package, "file_checksum")->valuestring,
                 ota->expected_hash, 32);
    
    cJSON_Delete(json);
    ota->state = OTA_STATE_IDLE;
    
    return 1;  // 有升级
}

/* 下载固件 */
int ota_download(OTA_Client *ota) {
    ota->state = OTA_STATE_DOWNLOADING;
    ota->downloaded = 0;
    
    // 打开目标 Flash
    uint32_t target_addr = get_next_slot_addr();
    flash_erase_region(target_addr, ota->total_size);
    
    // HTTP 流式下载
    HTTP_DownloadCtx ctx;
    http_download_init(&ctx, ota->download_url);
    
    uint8_t buffer[4096];
    while (ota->downloaded < ota->total_size) {
        int len = http_download_read(&ctx, buffer, sizeof(buffer));
        if (len <= 0) {
            if (ota->retry_count < MAX_RETRIES) {
                ota->retry_count++;
                http_download_resume(&ctx, ota->downloaded);
                continue;
            }
            ota->state = OTA_STATE_IDLE;
            return -1;
        }
        
        flash_write(target_addr + ota->downloaded, buffer, len);
        ota->downloaded += len;
        
        // 上报进度
        int progress = (ota->downloaded * 100) / ota->total_size;
        ota_report_progress(ota, progress);
        
        // 喂狗
        watchdog_feed();
    }
    
    http_download_cleanup(&ctx);
    return 0;
}

/* 验证固件 */
int ota_verify(OTA_Client *ota) {
    ota->state = OTA_STATE_VERIFYING;
    
    uint32_t target_addr = get_next_slot_addr();
    
    // 计算哈希
    uint8_t hash[32];
    sha256_file(target_addr, ota->total_size, hash);
    
    // 比较
    if (memcmp(hash, ota->expected_hash, 32) != 0) {
        return -1;  // 校验失败
    }
    
    // 验证签名
    uint8_t *signature = get_package_signature();
    if (verify_signature(hash, signature) != 0) {
        return -2;  // 签名失败
    }
    
    return 0;
}

/* 安装并重启 */
int ota_install(OTA_Client *ota) {
    ota->state = OTA_STATE_INSTALLING;
    
    // 更新启动标志
    BootConfig config;
    read_boot_config(&config);
    config.active_slot = (config.active_slot == SLOT_A) 
                         ? SLOT_B : SLOT_A;
    config.pending_version = ota->target_version;
    config.boot_attempts = 0;
    write_boot_config(&config);
    
    // 上报结果
    ota_report_result(ota, "installing", 0);
    
    // 延迟重启
    ota->state = OTA_STATE_REBOOTING;
    HAL_Delay(1000);
    NVIC_SystemReset();
    
    return 0;
}
```

---

### 相关链接

- [[ci-cd-pipeline|CI/CD 流水线]]
- [[firmware-upgrade|固件升级方案]]
- [[secure-boot-impl|安全启动]]
- [[dev-process|项目管理]]

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

**下一步**：建议学习 [[ota-server/advanced/|高级内容]]
