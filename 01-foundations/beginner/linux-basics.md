---
title: "Linux 基础"
tags: [linux, beginner, kernel, command, shell]
level: beginner
module: "01-foundations"
---

# Linux 基础

## 概述

Linux 是嵌入式产品的主流操作系统，广泛应用于路由器、摄像头、机器人等设备。本文介绍 Linux 基本命令、文件系统、进程管理和嵌入式 Linux 的特点。

完成本文学习后，你将能够：

- 熟练使用 Linux 命令行
- 理解 Linux 文件系统结构
- 掌握基本的 Shell 脚本编写
- 了解嵌入式 Linux 与桌面 Linux 的区别

## 背景知识

### 前置知识

- 基本的计算机操作
- 了解操作系统概念

### 学习建议

- 安装 Ubuntu 虚拟机或使用 WSL
- 多用命令行，少用图形界面
- 遇到问题先看 man 手册

## 核心内容

### 1. 常用命令

```bash
# 文件操作
ls -la          # 列出文件 (详细, 含隐藏)
cd /path        # 切换目录
pwd             # 显示当前目录
cp src dst      # 复制
mv src dst      # 移动/重命名
rm file         # 删除
mkdir -p dir    # 创建目录 (含父目录)
find . -name "*.c"  # 查找文件

# 文件内容
cat file        # 显示全部内容
less file       # 分页显示
head -20 file   # 显示前 20 行
tail -f file    # 实时跟踪末尾
grep "pattern" file  # 搜索文本
grep -r "pattern" .  # 递归搜索目录

# 权限
chmod 755 file  # 设置权限 (rwxr-xr-x)
chmod +x file   # 添加执行权限
chown user:group file  # 修改所有者

# 进程
ps aux          # 查看所有进程
top             # 实时进程监控
kill PID        # 终止进程
kill -9 PID     # 强制终止

# 网络
ifconfig        # 网络接口信息
ping host       # 测试连通性
netstat -tlnp   # 查看监听端口
ssh user@host   # 远程登录

# 磁盘
df -h           # 磁盘使用情况
du -sh dir      # 目录大小
mount /dev/sdb1 /mnt  # 挂载
```

### 2. 文件系统结构

```
/                   # 根目录
├── bin/            # 基本命令 (ls, cp, mv)
├── sbin/           # 系统命令 (ifconfig, reboot)
├── etc/            # 配置文件
│   ├── passwd      # 用户信息
│   ├── fstab       # 挂载表
│   └── network/    # 网络配置
├── dev/            # 设备文件
│   ├── ttyS0       # 串口
│   ├── gpio*       # GPIO
│   └── i2c-*       # I2C 设备
├── proc/           # 进程信息 (虚拟)
│   ├── cpuinfo     # CPU 信息
│   └── meminfo     # 内存信息
├── sys/            # 系统信息 (虚拟)
│   ├── class/      # 设备类
│   └── bus/        # 总线
├── tmp/            # 临时文件
├── var/            # 可变数据 (日志)
├── home/           # 用户目录
├── root/           # root 用户目录
├── lib/            # 共享库
├── usr/            # 用户程序
│   ├── bin/        # 用户命令
│   ├── lib/        # 库文件
│   └── share/      # 共享数据
└── mnt/            # 挂载点
```

### 3. Shell 脚本

```bash
#!/bin/bash
# 第一个 Shell 脚本

# 变量
NAME="World"
echo "Hello, $NAME!"

# 条件判断
if [ -f "/etc/passwd" ]; then
    echo "File exists"
else
    echo "File not found"
fi

# 循环
for i in 1 2 3 4 5; do
    echo "Number: $i"
done

# 函数
greet() {
    echo "Hello, $1!"
}
greet "Alice"

# 命令替换
DATE=$(date +%Y-%m-%d)
echo "Today is $DATE"

# 参数
echo "脚本名: $0"
echo "参数个数: $#"
echo "第一个参数: $1"
```

### 4. 嵌入式 Linux 特点

```
与桌面 Linux 的区别:

文件系统:
├── 桌面: ext4 on HDD/SSD
├── 嵌入式: SquashFS/JFFS2/UBIFS on Flash
└── 根文件系统可能只读

启动:
├── 桌面: GRUB → Kernel → systemd
├── 嵌入式: U-Boot → Kernel → init
└── 启动时间要求严格 (<3s)

资源:
├── 桌面: 8GB+ RAM, 256GB+ 存储
├── 嵌入式: 64-512MB RAM, 16-256MB Flash
└── 需要精简系统

实时性:
├── 桌面: 无实时要求
├── 嵌入式: 可能需要 RT-Preempt
└── 关键任务用 RTOS

交叉编译:
├── 桌面: 本机编译
├── 嵌入式: PC 上编译 ARM 代码
└── 交叉编译工具链: arm-linux-gnueabihf-gcc
```

## 实践示例

### 示例1：交叉编译

```bash
# 安装交叉编译工具链
sudo apt install gcc-arm-linux-gnueabihf

# 编译
arm-linux-gnueabihf-gcc -o hello hello.c

# 查看文件类型
file hello
# 输出: hello: ELF 32-bit LSB executable, ARM, EABI5 ...

# 复制到目标板运行
scp hello root@192.168.1.100:/tmp/
ssh root@192.168.1.100 /tmp/hello
```

**代码说明**：
- `arm-linux-gnueabihf-gcc` 是 ARM Linux 交叉编译器
- 编译出的程序只能在 ARM 设备上运行
- `file` 命令可以查看文件格式

### 示例2：系统信息查看

```bash
#!/bin/bash
# 系统信息脚本

echo "=== 系统信息 ==="
echo "内核版本: $(uname -r)"
echo "CPU 信息: $(cat /proc/cpuinfo | grep 'model name' | head -1)"
echo "内存大小: $(free -h | grep Mem | awk '{print $2}')"
echo "磁盘使用: $(df -h / | tail -1 | awk '{print $5}')"
echo "运行时间: $(uptime -p)"
echo "IP 地址: $(hostname -I | awk '{print $1}')"
```

**代码说明**：
- `/proc/cpuinfo` 包含 CPU 信息
- `free -h` 显示内存使用
- `df -h` 显示磁盘使用

## 深入理解

### 原理分析

Linux 启动流程：
```
1. Bootloader (U-Boot)
   ├── 初始化硬件
   ├── 加载内核到内存
   └── 跳转到内核

2. Kernel
   ├── 初始化驱动
   ├── 挂载根文件系统
   └── 启动 init 进程

3. init (PID 1)
   ├── 执行初始化脚本
   ├── 启动系统服务
   └── 启动登录终端
```

### 最佳实践

1. 嵌入式系统用 Buildroot/Yocto 构建，不要手动搭建
2. 根文件系统用只读挂载，数据存放在可写分区
3. 用 syslog 记录日志，不要用 printf
4. 用 watchdog 防止系统死机
5. 用 tmpfs 挂载 /tmp，减少 Flash 写入

## 常见问题

### Q1: 权限不够怎么办？

**A**: 用 `sudo` 执行需要 root 权限的命令。嵌入式设备通常直接用 root 登录。注意：不要在生产环境随意使用 root。

### Q2: 如何查看系统日志？

**A**: 
```bash
dmesg            # 内核日志
journalctl       # systemd 日志
cat /var/log/syslog  # 系统日志
logcat           # Android 日志
```

## 总结

本文涵盖了 Linux 基础知识：

- 常用命令和文件系统结构
- Shell 脚本编写
- 嵌入式 Linux 的特点和交叉编译
- 系统信息查看和调试方法

建议继续学习中级内容，掌握 Linux 驱动开发。

## 延伸阅读

- [[linux-driver-dev|Linux 驱动开发]] - 中级内容
- [[linux-advanced|Linux 内核深入]] - 高级内容
- [[stm32-basics|STM32 基础]] - MCU 入门

## 参考资料

1. 《鸟哥的 Linux 私房菜》- 鸟哥
2. 《Linux 命令行大全》- William Shotts
3. Linux 内核文档 (kernel.org/doc)

---

**练习题**：

1. 编写 Shell 脚本，自动备份 /etc 目录到 /tmp/backup
2. 用命令查看当前系统的 CPU、内存、磁盘使用情况
3. 编写一个简单的 C 程序，用交叉编译器编译并在开发板上运行

**下一步**：建议学习 [[stm32-basics|STM32 基础]]
