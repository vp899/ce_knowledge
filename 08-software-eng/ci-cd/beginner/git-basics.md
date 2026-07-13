---
title: "CI/CD 初级 - Git 基础"
tags: [ci-cd, beginner, git, version-control]
level: beginner
---

# Git 版本控制基础

## 概述

本文介绍 ci-cd 领域的 beginner 级别知识。

完成本文学习后，你将能够：

- 理解核心概念和基本原理
- 掌握关键技术和实现方法
- 应用到实际产品开发中

## 背景知识

### 相关概念

> 占位 - 待补充前置概念

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
// 占位 - 待补充示例代码
```

**代码说明**：
- 待补充

## 深入理解

### 原理分析

> 占位 - 待补充原理分析

### 最佳实践

1. 待补充

## 常见问题

### Q1: 待补充常见问题？

**A**: 待补充答案。

## 总结

本文核心要点：

- 待补充

## 延伸阅读

- 待补充相关文章链接

## 参考资料

1. 待补充

---

**练习题**：

1. 待补充

**下一步**：建议学习 [[ci-cd/intermediate/|中级内容]]
