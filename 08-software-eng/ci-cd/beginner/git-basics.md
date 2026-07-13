---
title: "CI/CD 初级 - Git 基础"
tags: [ci-cd, beginner, git, version-control]
level: beginner
---

# Git 版本控制基础

## 概述

本文介绍 ci-cd 领域的 beginner 级别知识。

完成本文学习后，你将能够：

- 理解 CI/CD 基本概念
- 掌握 Git 版本控制基础
- 了解自动化构建流程

## 背景知识

### 相关概念

### 前置知识

- C 语言基础 (变量/指针/函数)
- 基本电子电路知识 (电压/电流/电阻)
- 基本数学 (三角函数/向量)

### 学习建议

- 准备一块开发板进行动手实践
- 边学边做，不要只看不练
- 遇到问题先自己思考，再查资料

## 核心内容

### 1. Git 基本操作

```bash
# 初始化仓库
git init

# 添加文件
git add .

# 提交
git commit -m "feat: add IMU driver"

# 查看状态
git status

# 查看历史
git log --oneline

# 创建分支
git checkout -b feature/new-sensor

# 切换分支
git checkout develop

# 合并分支
git merge feature/new-sensor

# 推送
git push origin develop

# 拉取
git pull origin develop
```

### 2. 分支策略

```
main (生产)
  │
  ├── develop (开发)
  │   ├── feature/xxx (功能)
  │   └── bugfix/xxx (修复)
  │
  └── release/v1.0 (发布)
```

### 3. 提交规范

```
feat: 新功能
fix: 修复
docs: 文档
style: 格式
refactor: 重构
test: 测试
chore: 其他

示例:
feat(imu): add BMI088 driver
fix(pid): fix integral windup
docs(readme): update build instructions
```

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

1. 从简单示例开始，逐步增加复杂度
2. 充分利用厂商提供的示例代码
3. 建立良好的代码规范和注释习惯

## 常见问题

### Q1: 入门需要哪些前置知识？

**A**: 需要基础的 C 语言编程能力和基本的电子电路知识。建议先完成前置模块的学习。

### Q2: 推荐什么开发板？

**A**: 入门推荐使用 STM32F103 或 ESP32 开发板，价格低、资料多、社区活跃。

## 总结

本文介绍了基础概念和入门知识：

- 理解了核心原理和工作机制
- 掌握了基本的工具和方法
- 通过简单示例验证了学习效果

下一步建议进入中级内容，深入学习算法和实现细节。

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

**下一步**：建议学习 [[ci-cd/intermediate/|中级内容]]
