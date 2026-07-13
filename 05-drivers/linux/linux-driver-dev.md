---
title: "Linux 驱动开发"
aliases:
  - "Linux 驱动"
tags:
  - drivers
  - linux
  - v4l2
  - i2c
  - platform
module: "05-drivers"
status: active
---

# Linux 驱动开发

## 1. 字符设备驱动

### 完整字符设备驱动示例
```c
/* my_chardev.c - 完整的字符设备驱动 */
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/fs.h>
#include <linux/cdev.h>
#include <linux/device.h>
#include <linux/uaccess.h>
#include <linux/mutex.h>
#include <linux/wait.h>
#include <linux/poll.h>

#define DEVICE_NAME "my_chardev"
#define BUFFER_SIZE 4096

static dev_t dev_num;
static struct cdev my_cdev;
static struct class *my_class;
static struct device *my_device;

static char device_buffer[BUFFER_SIZE];
static size_t data_size = 0;
static DEFINE_MUTEX(buffer_mutex);
static DECLARE_WAIT_QUEUE_HEAD(read_queue);

/* 打开设备 */
static int my_open(struct inode *inode, struct file *filp) {
    pr_info("%s: opened by pid %d\n", DEVICE_NAME, current->pid);
    return 0;
}

/* 释放设备 */
static int my_release(struct inode *inode, struct file *filp) {
    pr_info("%s: closed by pid %d\n", DEVICE_NAME, current->pid);
    return 0;
}

/* 读取数据 */
static ssize_t my_read(struct file *filp, char __user *buf,
                        size_t count, loff_t *f_pos) {
    ssize_t ret;
    
    mutex_lock(&buffer_mutex);
    
    // 非阻塞模式
    if ((filp->f_flags & O_NONBLOCK) && data_size == 0) {
        ret = -EAGAIN;
        goto out;
    }
    
    // 阻塞等待数据
    ret = wait_event_interruptible(read_queue, data_size > 0);
    if (ret) {
        goto out;
    }
    
    // 限制读取大小
    if (count > data_size) {
        count = data_size;
    }
    
    // 复制到用户空间
    if (copy_to_user(buf, device_buffer, count)) {
        ret = -EFAULT;
        goto out;
    }
    
    // 移动剩余数据
    memmove(device_buffer, device_buffer + count, data_size - count);
    data_size -= count;
    *f_pos += count;
    
    ret = count;
    
out:
    mutex_unlock(&buffer_mutex);
    return ret;
}

/* 写入数据 */
static ssize_t my_write(struct file *filp, const char __user *buf,
                         size_t count, loff_t *f_pos) {
    ssize_t ret;
    
    mutex_lock(&buffer_mutex);
    
    if (count > BUFFER_SIZE - data_size) {
        count = BUFFER_SIZE - data_size;
    }
    
    if (count == 0) {
        ret = -ENOSPC;
        goto out;
    }
    
    if (copy_from_user(device_buffer + data_size, buf, count)) {
        ret = -EFAULT;
        goto out;
    }
    
    data_size += count;
    *f_pos += count;
    
    // 唤醒等待读取的进程
    wake_up_interruptible(&read_queue);
    
    ret = count;
    
out:
    mutex_unlock(&buffer_mutex);
    return ret;
}

/* ioctl 控制 */
static long my_ioctl(struct file *filp, unsigned int cmd, 
                      unsigned long arg) {
    switch (cmd) {
    case 0x1000: // 清空缓冲区
        mutex_lock(&buffer_mutex);
        data_size = 0;
        mutex_unlock(&buffer_mutex);
        return 0;
        
    case 0x1001: // 获取数据大小
        return put_user(data_size, (size_t __user *)arg);
        
    default:
        return -ENOTTY;
    }
}

/* poll 支持 (select/epoll) */
static unsigned int my_poll(struct file *filp, 
                             poll_table *wait) {
    unsigned int mask = 0;
    
    poll_wait(filp, &read_queue, wait);
    
    if (data_size > 0) {
        mask |= POLLIN | POLLRDNORM;  // 可读
    }
    
    if (data_size < BUFFER_SIZE) {
        mask |= POLLOUT | POLLWRNORM; // 可写
    }
    
    return mask;
}

/* mmap 支持 */
static int my_mmap(struct file *filp, struct vm_area_struct *vma) {
    unsigned long size = vma->vm_end - vma->vm_start;
    
    if (size > BUFFER_SIZE) {
        return -EINVAL;
    }
    
    return remap_pfn_range(vma, vma->vm_start,
                           virt_to_phys(device_buffer) >> PAGE_SHIFT,
                           size, vma->vm_page_prot);
}

/* 文件操作结构体 */
static const struct file_operations my_fops = {
    .owner          = THIS_MODULE,
    .open           = my_open,
    .release        = my_release,
    .read           = my_read,
    .write          = my_write,
    .unlocked_ioctl = my_ioctl,
    .poll           = my_poll,
    .mmap           = my_mmap,
};

/* 模块初始化 */
static int __init my_init(void) {
    int ret;
    
    // 1. 分配设备号
    ret = alloc_chrdev_region(&dev_num, 0, 1, DEVICE_NAME);
    if (ret < 0) {
        pr_err("Failed to allocate device number\n");
        return ret;
    }
    
    // 2. 初始化 cdev
    cdev_init(&my_cdev, &my_fops);
    my_cdev.owner = THIS_MODULE;
    
    // 3. 添加 cdev
    ret = cdev_add(&my_cdev, dev_num, 1);
    if (ret < 0) {
        goto err_cdev;
    }
    
    // 4. 创建设备类
    my_class = class_create(DEVICE_NAME);
    if (IS_ERR(my_class)) {
        ret = PTR_ERR(my_class);
        goto err_class;
    }
    
    // 5. 创建设备节点
    my_device = device_create(my_class, NULL, dev_num, 
                               NULL, DEVICE_NAME);
    if (IS_ERR(my_device)) {
        ret = PTR_ERR(my_device);
        goto err_device;
    }
    
    pr_info("%s: initialized, major=%d minor=%d\n",
            DEVICE_NAME, MAJOR(dev_num), MINOR(dev_num));
    
    return 0;

err_device:
    class_destroy(my_class);
err_class:
    cdev_del(&my_cdev);
err_cdev:
    unregister_chrdev_region(dev_num, 1);
    return ret;
}

/* 模块退出 */
static void __exit my_exit(void) {
    device_destroy(my_class, dev_num);
    class_destroy(my_class);
    cdev_del(&my_cdev);
    unregister_chrdev_region(dev_num, 1);
    pr_info("%s: removed\n", DEVICE_NAME);
}

module_init(my_init);
module_exit(my_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("My Company");
MODULE_DESCRIPTION("Character device driver example");
MODULE_VERSION("1.0");
```

## 2. Platform 驱动

### 设备树 + Platform 驱动
```c
/* my_platform.c */
#include <linux/module.h>
#include <linux/platform_device.h>
#include <linux/of.h>
#include <linux/of_device.h>
#include <linux/interrupt.h>
#include <linux/io.h>
#include <linux/clk.h>
#include <linux/reset.h>

struct my_device_data {
    void __iomem *regs;
    struct clk *clk;
    struct reset_control *rst;
    int irq;
    struct device *dev;
};

/* 设备树匹配表 */
static const struct of_device_id my_of_match[] = {
    { .compatible = "vendor,my-device-v1", },
    { .compatible = "vendor,my-device-v2", },
    { /* sentinel */ },
};
MODULE_DEVICE_TABLE(of, my_of_match);

/* 中断处理 */
static irqreturn_t my_irq_handler(int irq, void *dev_id) {
    struct my_device_data *data = dev_id;
    u32 status;
    
    // 读取中断状态
    status = readl(data->regs + 0x10);
    
    if (!(status & 0x1)) {
        return IRQ_NONE;  // 不是我们的中断
    }
    
    // 清除中断
    writel(status, data->regs + 0x10);
    
    // 处理中断事件
    // ...
    
    return IRQ_HANDLED;
}

/* 探测函数 */
static int my_probe(struct platform_device *pdev) {
    struct my_device_data *data;
    struct resource *res;
    int ret;
    
    // 1. 分配驱动数据
    data = devm_kzalloc(&pdev->dev, sizeof(*data), GFP_KERNEL);
    if (!data) {
        return -ENOMEM;
    }
    data->dev = &pdev->dev;
    platform_set_drvdata(pdev, data);
    
    // 2. 获取时钟
    data->clk = devm_clk_get(&pdev->dev, NULL);
    if (IS_ERR(data->clk)) {
        return PTR_ERR(data->clk);
    }
    
    // 3. 使能时钟
    ret = clk_prepare_enable(data->clk);
    if (ret) {
        return ret;
    }
    
    // 4. 获取复位控制
    data->rst = devm_reset_control_get(&pdev->dev, NULL);
    if (!IS_ERR(data->rst)) {
        reset_control_deassert(data->rst);
    }
    
    // 5. 获取内存资源 (从设备树)
    res = platform_get_resource(pdev, IORESOURCE_MEM, 0);
    data->regs = devm_ioremap_resource(&pdev->dev, res);
    if (IS_ERR(data->regs)) {
        ret = PTR_ERR(data->regs);
        goto err_clk;
    }
    
    // 6. 获取中断
    data->irq = platform_get_irq(pdev, 0);
    if (data->irq < 0) {
        ret = data->irq;
        goto err_clk;
    }
    
    ret = devm_request_irq(&pdev->dev, data->irq, my_irq_handler,
                            IRQF_SHARED, "my-device", data);
    if (ret) {
        dev_err(&pdev->dev, "Failed to request IRQ\n");
        goto err_clk;
    }
    
    // 7. 读取设备树属性
    u32 reg_value;
    if (of_property_read_u32(pdev->dev.of_node, "vendor,config-reg",
                              &reg_value) == 0) {
        writel(reg_value, data->regs + 0x04);
    }
    
    // 8. 初始化硬件
    writel(0x01, data->regs + 0x00);  // 使能模块
    
    dev_info(&pdev->dev, "my-device probed successfully\n");
    
    return 0;

err_clk:
    clk_disable_unprepare(data->clk);
    return ret;
}

/* 移除函数 */
static int my_remove(struct platform_device *pdev) {
    struct my_device_data *data = platform_get_drvdata(pdev);
    
    // 关闭硬件
    writel(0x00, data->regs + 0x00);
    
    // 释放资源
    if (!IS_ERR(data->rst)) {
        reset_control_assert(data->rst);
    }
    clk_disable_unprepare(data->clk);
    
    dev_info(&pdev->dev, "my-device removed\n");
    
    return 0;
}

/* 电源管理 - 挂起 */
static int my_suspend(struct device *dev) {
    struct my_device_data *data = dev_get_drvdata(dev);
    
    // 保存寄存器状态
    // ...
    
    // 关闭时钟
    clk_disable_unprepare(data->clk);
    
    return 0;
}

/* 电源管理 - 恢复 */
static int my_resume(struct device *dev) {
    struct my_device_data *data = dev_get_drvdata(dev);
    
    // 恢复时钟
    clk_prepare_enable(data->clk);
    
    // 恢复寄存器状态
    // ...
    
    return 0;
}

static const struct dev_pm_ops my_pm_ops = {
    .suspend = my_suspend,
    .resume = my_resume,
};

/* Platform 驱动结构体 */
static struct platform_driver my_driver = {
    .probe = my_probe,
    .remove = my_remove,
    .driver = {
        .name = "my-device",
        .of_match_table = my_of_match,
        .pm = &my_pm_ops,
    },
};

module_platform_driver(my_driver);

MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Platform driver with device tree support");
```

## 3. I2C 驱动

### I2C 设备驱动
```c
/* my_i2c_driver.c */
#include <linux/module.h>
#include <linux/i2c.h>
#include <linux/regmap.h>

#define MY_REG_CHIP_ID      0x00
#define MY_REG_CONFIG       0x01
#define MY_REG_DATA_H       0x02
#define MY_REG_DATA_L       0x03
#define MY_CHIP_ID          0xAB

struct my_sensor_data {
    struct i2c_client *client;
    struct regmap *regmap;
    struct mutex lock;
};

/* regmap 配置 */
static const struct regmap_config my_regmap_config = {
    .reg_bits = 8,
    .val_bits = 8,
    .max_register = 0x0F,
};

/* 读取传感器数据 */
static int my_sensor_read(struct my_sensor_data *data, s16 *value) {
    unsigned int high, low;
    int ret;
    
    mutex_lock(&data->lock);
    
    ret = regmap_read(data->regmap, MY_REG_DATA_H, &high);
    if (ret) goto out;
    
    ret = regmap_read(data->regmap, MY_REG_DATA_L, &low);
    if (ret) goto out;
    
    *value = (s16)((high << 8) | low);
    
out:
    mutex_unlock(&data->lock);
    return ret;
}

/* I2C 探测 */
static int my_i2c_probe(struct i2c_client *client,
                          const struct i2c_device_id *id) {
    struct my_sensor_data *data;
    unsigned int chip_id;
    int ret;
    
    // 检查 I2C 功能
    if (!i2c_check_functionality(client->adapter, 
                                  I2C_FUNC_SMBUS_BYTE_DATA)) {
        dev_err(&client->dev, "I2C functionality not supported\n");
        return -ENODEV;
    }
    
    // 分配驱动数据
    data = devm_kzalloc(&client->dev, sizeof(*data), GFP_KERNEL);
    if (!data) {
        return -ENOMEM;
    }
    
    data->client = client;
    mutex_init(&data->lock);
    
    // 初始化 regmap
    data->regmap = devm_regmap_init_i2c(client, &my_regmap_config);
    if (IS_ERR(data->regmap)) {
        return PTR_ERR(data->regmap);
    }
    
    // 验证芯片 ID
    ret = regmap_read(data->regmap, MY_REG_CHIP_ID, &chip_id);
    if (ret) {
        return ret;
    }
    
    if (chip_id != MY_CHIP_ID) {
        dev_err(&client->dev, "Unknown chip ID: 0x%02x\n", chip_id);
        return -ENODEV;
    }
    
    // 配置芯片
    ret = regmap_write(data->regmap, MY_REG_CONFIG, 0x01);
    if (ret) {
        return ret;
    }
    
    i2c_set_clientdata(client, data);
    
    dev_info(&client->dev, "my-sensor probed, chip_id=0x%02x\n",
             chip_id);
    
    return 0;
}

static int my_i2c_remove(struct i2c_client *client) {
    dev_info(&client->dev, "my-sensor removed\n");
    return 0;
}

static const struct i2c_device_id my_i2c_id[] = {
    { "my-sensor", 0 },
    { /* sentinel */ },
};
MODULE_DEVICE_TABLE(i2c, my_i2c_id);

static const struct of_device_id my_i2c_of_match[] = {
    { .compatible = "vendor,my-sensor" },
    { /* sentinel */ },
};
MODULE_DEVICE_TABLE(of, my_i2c_of_match);

static struct i2c_driver my_i2c_driver = {
    .driver = {
        .name = "my-sensor",
        .of_match_table = my_i2c_of_match,
    },
    .probe = my_i2c_probe,
    .remove = my_i2c_remove,
    .id_table = my_i2c_id,
};

module_i2c_driver(my_i2c_driver);

MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("I2C sensor driver");
```

## 4. 中断处理

### 中断处理最佳实践
```c
/* 中断处理分层 */

/* 1. 硬中断 (Top Half) - 快速处理 */
static irqreturn_t my_hardirq(int irq, void *dev_id) {
    struct my_device *dev = dev_id;
    u32 status;
    
    // 读取中断状态
    status = readl(dev->regs + IRQ_STATUS_REG);
    
    if (!status) {
        return IRQ_NONE;
    }
    
    // 清除中断
    writel(status, dev->regs + IRQ_STATUS_REG);
    
    // 保存状态到 tasklet
    dev->irq_status = status;
    
    // 调度 tasklet
    tasklet_schedule(&dev->tasklet);
    
    return IRQ_HANDLED;
}

/* 2. Tasklet (Bottom Half) - 延迟处理 */
static void my_tasklet_func(unsigned long data) {
    struct my_device *dev = (struct my_device *)data;
    u32 status = dev->irq_status;
    
    if (status & IRQ_DATA_READY) {
        // 处理数据就绪
        wake_up_interruptible(&dev->read_queue);
    }
    
    if (status & IRQ_ERROR) {
        // 处理错误
        dev_err(dev->dev, "Hardware error\n");
    }
}

/* 3. 工作队列 - 可睡眠的延迟处理 */
static void my_work_func(struct work_struct *work) {
    struct my_device *dev = container_of(work, struct my_device, work);
    
    // 可以在这里做可睡眠的操作
    // 例如: I2C 通信、内存分配、文件操作
    
    mutex_lock(&dev->lock);
    // 处理工作
    mutex_unlock(&dev->lock);
}

/* 初始化 */
static int my_init(struct my_device *dev) {
    // 初始化 tasklet
    tasklet_init(&dev->tasklet, my_tasklet_func, (unsigned long)dev);
    
    // 初始化工作队列
    INIT_WORK(&dev->work, my_work_func);
    
    // 申请中断
    return request_irq(dev->irq, my_hardirq, IRQF_SHARED,
                        "my-device", dev);
}
```

## 5. 内核调试

### 调试工具与技巧
```bash
# 动态调试
echo "module my_driver +p" > /sys/kernel/debug/dynamic_debug/control
echo "file my_driver.c +p" > /sys/kernel/debug/dynamic_debug/control

# 查看内核日志
dmesg | tail -50
dmesg -w  # 实时查看

# 查看模块信息
lsmod | grep my
modinfo my_driver

# 查看设备树
ls /sys/firmware/devicetree/base/
cat /sys/firmware/devicetree/base/compatible

# 查看中断
cat /proc/interrupts | grep my

# 查看 I2C 设备
i2cdetect -y 0
i2cget -y 0 0x48 0x00

# 查看 GPIO
cat /sys/kernel/debug/gpio

# 性能分析
perf top
perf record -g -p <pid>
perf report

# 内存调试
echo 1 > /proc/sys/kernel/panic_on_oops
echo KMEMLEAK > /sys/kernel/debug/kmemleak
cat /sys/kernel/debug/kmemleak
```

### Kprobe 动态插桩
```c
/* kprobe_example.c */
#include <linux/kprobes.h>

static struct kprobe kp = {
    .symbol_name = "my_target_function",
};

static int handler_pre(struct kprobe *p, struct pt_regs *regs) {
    printk("my_target_function called, ip=%lx\n", regs->ip);
    return 0;
}

static int __init kprobe_init(void) {
    kp.pre_handler = handler_pre;
    return register_kprobe(&kp);
}

static void __exit kprobe_exit(void) {
    unregister_kprobe(&kp);
}
```
---

## 相关链接

- [[framework-customization|Android Framework]]
- [[protocol-details|通信协议]]
