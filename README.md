# 消费电子软件开发知识库

> Consumer Electronics Software Development Knowledge Base

## 知识库结构

| # | 模块 | 目录 | 说明 |
|---|------|------|------|
| 01 | Android 开发 | `01-android/` | 系统定制、应用开发、构建系统 |
| 02 | STM32 升级 | `02-stm32/` | 固件升级、Bootloader、外设驱动 |
| 03 | 硬件设计 | `03-hardware/` | 原理图、PCB、打板、BOM |
| 04 | 安全启动 | `04-security/` | Secure Boot、加密、密钥管理 |
| 05 | 驱动开发 | `05-drivers/` | Linux/RTOS 驱动、BSP |
| 06 | 通信协议 | `06-communication/` | 有线/无线协议、协议栈 |
| 07 | 可靠性测试 | `07-reliability/` | 环境、机械、EMC、寿命 |
| 08 | 产品提案 | `08-proposal/` | 模板、市场分析、商业论证 |
| 09 | 架构设计 | `09-architecture/` | 系统架构、软硬件架构、接口 |
| 10 | 风险管理 | `10-risk/` | 风险评估、缓解、跟踪 |
| 11 | 项目管理 | `11-project-management/` | 计划、敏捷、工具、质量 |
| 12 | 市场宣传 | `12-marketing/` | 品牌、内容、渠道、活动 |
| 13 | 产品网站 | `13-website/` | 设计、开发、SEO、分析 |

## 使用方式

1. **查阅**：按模块浏览，每个目录下有 `README.md` 作为入口
2. **贡献**：在对应目录下添加文档，遵循各模块的模板规范
3. **搜索**：使用 `grep -r "关键词" consumer-electronics-kb/` 全文检索

## 命名规范

- 文档名：小写英文 + 连字符，如 `secure-boot-flow.md`
- 图片：放入各模块的 `assets/` 子目录
- 代码示例：放入各模块的 `examples/` 子目录
