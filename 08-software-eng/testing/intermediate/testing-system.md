level: intermediate
---
title: "产品测试体系"
aliases:
  - "测试策略"
  - "测试管理"
  - "产品测试"
tags:
  - testing
  - test-planning
  - test-automation
  - quality
module: "10-reliability"
status: active
---

# 产品测试体系

## 概述

本文介绍 testing 领域的 intermediate 级别知识。

完成本文学习后，你将能够：

- 掌握 HIL 硬件在环测试
- 能够实现自动化测试框架
- 理解测试覆盖率和回归测试

## 背景知识

### 相关概念

### 前置知识

- 完成初级内容的学习
- 熟悉嵌入式开发流程
- 掌握基本的数据结构和算法

### 学习建议

- 理解原理后动手实现
- 对比不同算法的优缺点
- 关注工程实践中的细节

## 核心内容

### 1. 测试分层体系

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        产品测试分层体系                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Level 5: 验收测试 (Acceptance)                                        │
│  ├── 用户场景测试 (真实使用环境)                                        │
│  ├── Beta 测试 (外部用户)                                               │
│  └── 判定: 是否可发布                                                   │
│                                                                         │
│  Level 4: 系统测试 (System)                                            │
│  ├── 功能测试 (需求全覆盖)                                              │
│  ├── 性能测试 (响应/功耗/发热)                                          │
│  ├── 可靠性测试 (环境/机械/EMC)                                         │
│  ├── 安全测试 (渗透/漏洞)                                               │
│  └── 兼容性测试 (配件/APP/平台)                                         │
│                                                                         │
│  Level 3: 集成测试 (Integration)                                       │
│  ├── 模块间接口测试                                                     │
│  ├── 硬件在环 (HIL) 测试                                               │
│  ├── 通信协议测试                                                       │
│  └── 驱动 + 应用联调                                                    │
│                                                                         │
│  Level 2: 单元测试 (Unit)                                              │
│  ├── 函数级测试 (Host 端)                                               │
│  ├── 算法验证 (PID/EKF/SLAM)                                           │
│  ├── 协议解析测试                                                       │
│  └── 边界条件/异常测试                                                  │
│                                                                         │
│  Level 1: 代码检查 (Code Review)                                       │
│  ├── 静态分析 (Cppcheck/SonarQube)                                     │
│  ├── 代码规范检查 (MISRA-C)                                            │
│  └── 人工 Code Review                                                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2. 测试用例设计方法

### 测试用例模板
```markdown

### 测试用例: TC-IMU-001

### 基本信息
| 属性 | 值 |
|------|-----|
| 用例ID | TC-IMU-001 |
| 模块 | IMU |
| 优先级 | P0 |
| 类型 | 功能测试 |
| 前置条件 | 设备已校准, 静止状态 |

### 测试步骤
| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 上电初始化 | IMU 初始化成功 |
| 2 | 静止采集 10s | 姿态角变化 < 0.5° |
| 3 | 记录数据 | 数据完整无丢失 |

### 判定标准
- [ ] 初始化成功 (返回 0)
- [ ] 姿态角漂移 < 0.5°/10s
- [ ] 数据采样率 ≥ 100Hz
- [ ] 无丢包 (序列号连续)

### 测试数据
- 采样率: 100Hz
- 测试时长: 10s
- 数据量: 1000 帧
```

### 等价类划分
```
示例: GPS 经度输入验证

有效等价类:
├── EC1: 有效经度 (-180 ~ +180)
│   ├── 代表值: 0, 116.4, -122.3, 180, -180
│   └── 预期: 接受
│
无效等价类:
├── EC2: 超出范围 (>180 或 <-180)
│   ├── 代表值: 181, -181, 999
│   └── 预期: 拒绝
│
├── EC3: 非数值
│   ├── 代表值: "abc", "", NULL
│   └── 预期: 拒绝
│
└── EC4: 精度异常
    ├── 代表值: 116.12345678901234 (超精度)
    └── 预期: 截断或拒绝
```

### 边界值分析
```
示例: 电机油门值 (0-1000)

边界值:
├── 最小值: 0
├── 最小值+1: 1
├── 典型值: 500
├── 最大值-1: 999
├── 最大值: 1000
├── 超出: -1, 1001

测试矩阵:
| 输入 | 预期 | 说明 |
|------|------|------|
| -1 | 拒绝/限幅到 0 | 下界越界 |
| 0 | 接受, 电机停转 | 下界 |
| 1 | 接受, 最小转速 | 下界+1 |
| 500 | 接受, 中等转速 | 典型值 |
| 999 | 接受, 接近最大 | 上界-1 |
| 1000 | 接受, 最大转速 | 上界 |
| 1001 | 拒绝/限幅到 1000 | 上界越界 |
```

### 3. 硬件在环 (HIL) 测试

### HIL 测试架构
```
HIL 测试系统:

┌─────────────────────────────────────────────────────────────┐
│                        HIL 测试台                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │ 测试主机  │    │ 信号注入 │    │ 被测设备  │              │
│  │ (PC)     │───→│ 模拟器   │───→│ (DUT)    │              │
│  │          │    │          │    │          │              │
│  │ Robot    │    │ IMU 模拟 │    │ 飞控板   │              │
│  │ Framework│    │ GPS 模拟 │    │          │              │
│  │          │    │ 电池模拟 │    │          │              │
│  └──────────┘    └──────────┘    └──────────┘              │
│       │                               │                     │
│       │          ┌──────────┐         │                     │
│       └─────────→│ 数据采集 │←────────┘                     │
│                  │ (示波器)  │                               │
│                  └──────────┘                               │
│                                                              │
└─────────────────────────────────────────────────────────────┘

信号注入:
├── IMU: SPI 模拟器 (注入姿态数据)
├── GPS: UART 模拟器 (NMEA 注入)
├── 电池: 可调电源 (模拟电压/电流)
├── 遥控器: PWM 生成器 (模拟遥控信号)
└── 传感器: DAC 输出 (模拟传感器信号)

数据采集:
├── 电机 PWM: 示波器测量
├── 通信数据: 逻辑分析仪
├── 串口日志: 串口监控
└── 功耗: 电流探头
```

### 4. 测试自动化框架

### 嵌入式测试自动化
```python
#!/usr/bin/env python3
"""嵌入式产品自动化测试框架"""
import serial
import time
import json
import pytest

class DeviceTester:
    def __init__(self, port='/dev/ttyUSB0', baudrate=115200):
        self.ser = serial.Serial(port, baudrate, timeout=5)
        self.results = []
    
    def send_command(self, cmd, args=''):
        """发送命令并等待响应"""
        full_cmd = f"{cmd} {args}\n"
        self.ser.write(full_cmd.encode())
        response = self.ser.readline().decode().strip()
        return response
    
    def wait_for(self, keyword, timeout=10):
        """等待特定关键字"""
        start = time.time()
        while time.time() - start < timeout:
            line = self.ser.readline().decode().strip()
            if keyword in line:
                return line
        raise TimeoutError(f"未检测到 '{keyword}'")
    
    def measure_current(self):
        """测量电流 (需要电流表)"""
        # 通过 SCPI 命令控制电流表
        import pyvisa
        rm = pyvisa.ResourceManager()
        meter = rm.open_resource('USB0::0x1234::0x5678::INSTR')
        return float(meter.query('MEAS:CURR?'))

@pytest.fixture
def device():
    dev = DeviceTester()
    dev.send_command('reset')
    time.sleep(2)
    yield dev
    dev.ser.close()

class TestIMU:
    def test_imu_init(self, device):
        """IMU 初始化测试"""
        resp = device.send_command('imu_init')
        assert 'OK' in resp
    
    def test_imu_data_rate(self, device):
        """IMU 采样率测试"""
        device.send_command('imu_start')
        time.sleep(1)
        count = int(device.send_command('imu_count'))
        assert count >= 95  # >=95Hz (100Hz 目标)
    
    def test_imu_drift(self, device):
        """IMU 漂移测试"""
        device.send_command('imu_start')
        device.send_command('attitude_reset')
        time.sleep(10)
        drift = float(device.send_command('attitude_drift'))
        assert drift < 0.5  # <0.5°

class TestMotor:
    def test_motor_start(self, device):
        """电机启动测试"""
        resp = device.send_command('motor_set', '100')
        assert 'OK' in resp
        speed = int(device.send_command('motor_get_speed'))
        assert speed > 0
    
    def test_motor_stop(self, device):
        """电机停止测试"""
        device.send_command('motor_set', '100')
        time.sleep(1)
        device.send_command('motor_set', '0')
        time.sleep(0.5)
        speed = int(device.send_command('motor_get_speed'))
        assert speed == 0
    
    def test_motor_speed_range(self, device):
        """电机速度范围测试"""
        for speed in [0, 100, 500, 1000]:
            device.send_command('motor_set', str(speed))
            time.sleep(0.5)
            actual = int(device.send_command('motor_get_speed'))
            assert abs(actual - speed) < 50

class TestOTA:
    def test_ota_check(self, device):
        """OTA 检查测试"""
        resp = device.send_command('ota_check')
        assert 'update_available' in resp
    
    def test_ota_download(self, device):
        """OTA 下载测试"""
        device.send_command('ota_start')
        progress = 0
        while progress < 100:
            resp = device.send_command('ota_progress')
            progress = int(resp)
            time.sleep(0.1)
        assert progress == 100

class TestPower:
    def test_sleep_current(self, device):
        """休眠功耗测试"""
        device.send_command('power_mode', 'sleep')
        time.sleep(2)
        current = device.measure_current()
        assert current < 0.01  # <10mA
    
    def test_active_current(self, device):
        """工作功耗测试"""
        device.send_command('power_mode', 'active')
        device.send_command('motor_set', '500')
        time.sleep(2)
        current = device.measure_current()
        assert current < 2.0  # <2A
```

### 5. 测试报告自动化

### 测试报告生成
```python
"""测试报告自动生成"""
from jinja2 import Template
import datetime

REPORT_TEMPLATE = """
# 产品测试报告

### 基本信息

| 项目 | 内容 |
|------|------|
| 产品 | {{ product_name }} |
| 版本 | {{ firmware_version }} |
| 测试日期 | {{ test_date }} |
| 测试工程师 | {{ tester }} |

### 测试概况

| 指标 | 值 |
|------|-----|
| 总用例数 | {{ total_cases }} |
| 通过数 | {{ pass_cases }} |
| 失败数 | {{ fail_cases }} |
| 跳过数 | {{ skip_cases }} |
| 通过率 | {{ pass_rate }}% |
| 测试时长 | {{ duration }} |

### 测试结果详情

| 用例ID | 模块 | 描述 | 结果 | 耗时 |
|--------|------|------|------|------|
{% for tc in test_cases %}
| {{ tc.id }} | {{ tc.module }} | {{ tc.desc }} | {{ tc.result }} | {{ tc.duration }} |
{% endfor %}

### 失败用例分析

{% for tc in failed_cases %}
### {{ tc.id }}: {{ tc.desc }}
- 失败原因: {{ tc.error }}
- 日志: {{ tc.log }}
- 建议: {{ tc.suggestion }}
{% endfor %}

### 结论

{{ conclusion }}
"""

def generate_report(test_results, output_path):
    template = Template(REPORT_TEMPLATE)
    
    total = len(test_results)
    passed = sum(1 for r in test_results if r['result'] == 'PASS')
    failed = sum(1 for r in test_results if r['result'] == 'FAIL')
    skipped = sum(1 for r in test_results if r['result'] == 'SKIP')
    
    report = template.render(
        product_name="无人机 V2",
        firmware_version="v2.1.3",
        test_date=datetime.date.today().isoformat(),
        tester="张三",
        total_cases=total,
        pass_cases=passed,
        fail_cases=failed,
        skip_cases=skipped,
        pass_rate=round(passed / total * 100, 1) if total > 0 else 0,
        duration="2h 30min",
        test_cases=test_results,
        failed_cases=[r for r in test_results if r['result'] == 'FAIL'],
        conclusion="测试通过率 98.5%, 满足发布标准 (≥95%)"
    )
    
    with open(output_path, 'w') as f:
        f.write(report)
```

---

### 相关链接

- [[ci-cd-pipeline|CI/CD 流水线]]
- [[env-testing|可靠性测试]]
- [[dev-process|项目管理]]
- [[product-design|产品设计]]

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

1. 模块化设计，接口清晰
2. 充分的错误处理和边界检查
3. 编写可测试的代码

## 常见问题

### Q1: 如何调试复杂问题？

**A**: 使用逻辑分析仪/示波器抓取信号；添加日志输出关键变量；使用 GDB 在线调试；分模块隔离问题。

### Q2: 性能不够怎么办？

**A**: 使用 DMA 减少 CPU 负担；优化中断处理 (Top/Bottom Half)；使用硬件加速器；降低采样率或简化算法。

## 总结

本文深入讲解了核心技术和实现方法：

- 掌握了关键算法的原理和实现
- 能够独立完成模块级开发
- 理解了工程实践中的优化技巧

下一步建议进入高级内容，学习系统级设计和生产级优化。

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

**下一步**：建议学习 [[testing/advanced/|高级内容]]
