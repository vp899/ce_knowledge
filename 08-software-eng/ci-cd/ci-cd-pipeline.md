level: beginner
---
title: "CI/CD 持续集成与交付"
aliases:
  - "持续集成"
  - "持续交付"
  - "CI CD"
  - "自动化构建"
tags:
  - ci-cd
  - devops
  - jenkins
  - gitlab-ci
  - testing
module: "08-software-eng"
status: active
---

# CI/CD 持续集成与交付体系

## 概述

本文介绍  领域的 beginner 级别知识。

完成本文学习后，你将能够：

- 理解核心概念和基本原理
- 掌握关键技术和实现方法
- 应用到实际产品开发中

## 背景知识

### 相关概念

> 占位 - 待补充前置概念

## 核心内容

### 1. 整体 DevOps 架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        消费电子研发 DevOps 全景                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌──────┐ │
│  │  需求    │───→│  编码    │───→│  构建    │───→│  测试    │───→│ 发布 │ │
│  │ (Jira)  │    │ (Git)   │    │ (CI)    │    │ (CD)    │    │ (OTA)│ │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘    └──────┘ │
│       │              │              │              │              │     │
│       ▼              ▼              ▼              ▼              ▼     │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌──────┐ │
│  │ 需求追踪 │    │ 代码评审 │    │ 自动编译 │    │ 自动测试 │    │ 灰度 │ │
│  │ Confluence│   │ GitLab  │    │ Jenkins │    │ Robot   │    │ 发布 │ │
│  │         │    │ MR/PR   │    │ GitLab  │    │ Framework│   │      │ │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘    └──────┘ │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                        基础设施层                                    │ │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐           │ │
│  │  │GitLab│ │Jenkins│ │Nexus │ │Sonar │ │Docker│ │K8s   │           │ │
│  │  │代码库│ │构建  │ │制品库│ │质量  │ │容器  │ │编排  │           │ │
│  │  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘           │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2. 代码管理 (Git)

### 分支策略 (Git Flow for Embedded)
```
main (生产分支)
│
├── develop (开发主分支)
│   │
│   ├── feature/xxx (功能分支)
│   │   └── 开发完成 → MR 到 develop
│   │
│   ├── bugfix/xxx (缺陷修复)
│   │   └── 修复完成 → MR 到 develop
│   │
│   └── release/v1.2.0 (发布分支)
│       └── 测试通过 → 合并到 main + tag
│
├── hotfix/xxx (紧急修复)
│   └── 从 main 拉出 → 修复 → 合并回 main + develop
│
└── tags: v1.0.0, v1.1.0, v1.2.0 ...
```

### 提交规范 (Conventional Commits)
```
格式: <type>(<scope>): <description>

类型:
├── feat:     新功能
├── fix:      修复
├── docs:     文档
├── style:    格式 (不影响逻辑)
├── refactor: 重构
├── perf:     性能优化
├── test:     测试
├── build:    构建系统
├── ci:       CI 配置
├── chore:    其他
└── revert:   回滚

示例:
feat(imu): add BMI088 driver support
fix(pid): fix integral windup issue
docs(readme): update build instructions
refactor(motor): extract FOC module

scope 范围 (嵌入式项目):
├── mcu: MCU 驱动
├── sensor: 传感器
├── motor: 电机控制
├── comm: 通信
├── power: 电源
├── gui: 界面
├── app: 应用层
├── test: 测试
└── ci: 持续集成
```

### 代码评审 (Code Review)
```
Code Review 检查清单:

功能正确性:
□ 代码实现了需求描述的功能
□ 边界条件处理正确
□ 错误处理完整
□ 资源释放 (内存/文件/锁)

代码质量:
□ 命名清晰 (变量/函数/文件)
□ 函数长度 ≤ 50 行
□ 圈复杂度 ≤ 10
□ 注释充分 (关键逻辑/算法)
□ 无魔法数字 (使用常量)

嵌入式特定:
□ 中断安全 (volatile/原子操作)
□ 栈使用合理 (无溢出风险)
□ 内存对齐正确
□ 外设寄存器操作正确
□ 时序满足要求
□ 功耗考虑

安全:
□ 无缓冲区溢出
□ 输入验证
□ 无硬编码密钥
□ 无 printf 泄露敏感信息

测试:
□ 单元测试覆盖
□ 边界测试
□ 异常测试
```

### 3. CI 流水线设计

### GitLab CI 配置 (嵌入式项目)
```yaml
# .gitlab-ci.yml - 嵌入式固件 CI 流水线

stages:
  - lint
  - build
  - test
  - analysis
  - package
  - deploy

variables:
  MCU: "STM32H743"
  TOOLCHAIN: "arm-none-eabi-gcc"
  BUILD_DIR: "build"

# ── 代码检查 ──
lint-cppcheck:
  stage: lint
  image: python:3.11
  script:
    - pip install cppcheck
    - cppcheck --enable=all --error-exitcode=1
        --suppress=missingIncludeSystem
        --inline-suppr
        src/ include/
  rules:
    - if: '$CI_MERGE_REQUEST_IID'
    - if: '$CI_COMMIT_BRANCH == "develop"'

lint-format:
  stage: lint
  image: python:3.11
  script:
    - pip install clang-format
    - find src/ include/ -name "*.c" -o -name "*.h" |
        xargs clang-format --dry-run --Werror
  rules:
    - if: '$CI_MERGE_REQUEST_IID'

# ── 构建 ──
build-debug:
  stage: build
  image: ghcr.io/arm-none-eabi/gcc:12.2
  script:
    - mkdir -p $BUILD_DIR
    - cmake -B $BUILD_DIR
        -DCMAKE_TOOLCHAIN_FILE=cmake/arm-none-eabi.cmake
        -DCMAKE_BUILD_TYPE=Debug
        -DMCU=$MCU
    - cmake --build $BUILD_DIR --parallel $(nproc)
    - arm-none-eabi-size $BUILD_DIR/firmware.elf
  artifacts:
    paths:
      - $BUILD_DIR/firmware.elf
      - $BUILD_DIR/firmware.bin
      - $BUILD_DIR/firmware.hex
    reports:
      metrics: $BUILD_DIR/build_metrics.txt
  rules:
    - if: '$CI_COMMIT_BRANCH == "develop"'
    - if: '$CI_MERGE_REQUEST_IID'

build-release:
  stage: build
  image: ghcr.io/arm-none-eabi/gcc:12.2
  script:
    - cmake -B $BUILD_DIR
        -DCMAKE_TOOLCHAIN_FILE=cmake/arm-none-eabi.cmake
        -DCMAKE_BUILD_TYPE=Release
        -DMCU=$MCU
    - cmake --build $BUILD_DIR --parallel $(nproc)
    - arm-none-eabi-size $BUILD_DIR/firmware.elf
  artifacts:
    paths:
      - $BUILD_DIR/firmware.bin
  rules:
    - if: '$CI_COMMIT_TAG =~ /^v\d+\.\d+\.\d+$/'

# ── 测试 ──
unit-test:
  stage: test
  image: gcc:12
  script:
    - cmake -B build_test -DBUILD_TESTS=ON
    - cmake --build build_test
    - cd build_test && ctest --output-on-failure
  artifacts:
    reports:
      junit: build_test/test_results.xml
      coverage_report:
        coverage_format: cobertura
        path: build_test/coverage.xml
  coverage: '/Lines\s*:\s*(\d+\.\d+)%/'
  rules:
    - if: '$CI_MERGE_REQUEST_IID'
    - if: '$CI_COMMIT_BRANCH == "develop"'

# ── 静态分析 ──
sonarqube:
  stage: analysis
  image: sonarsource/sonar-scanner-cli:latest
  script:
    - sonar-scanner
        -Dsonar.projectKey=$CI_PROJECT_NAME
        -Dsonar.sources=src/,include/
        -Dsonar.tests=test/
        -Dsonar.cfamily.build-wrapper-output=bw-output
        -Dsonar.host.url=$SONAR_URL
        -Dsonar.login=$SONAR_TOKEN
  rules:
    - if: '$CI_COMMIT_BRANCH == "develop"'

# ── 固件打包 ──
package-firmware:
  stage: package
  image: python:3.11
  script:
    - pip install cryptography
    - python tools/sign_firmware.py
        --input $BUILD_DIR/firmware.bin
        --key $SIGNING_KEY
        --output $BUILD_DIR/firmware_signed.bin
    - python tools/create_ota_package.py
        --firmware $BUILD_DIR/firmware_signed.bin
        --version $CI_COMMIT_TAG
        --output $BUILD_DIR/ota_package.bin
  artifacts:
    paths:
      - $BUILD_DIR/firmware_signed.bin
      - $BUILD_DIR/ota_package.bin
      - $BUILD_DIR/firmware.sha256
  rules:
    - if: '$CI_COMMIT_TAG =~ /^v\d+\.\d+\.\d+$/'

# ── 部署到测试设备 ──
deploy-test:
  stage: deploy
  image: python:3.11
  script:
    - python tools/ota_deploy.py
        --package $BUILD_DIR/ota_package.bin
        --target test_devices
        --env staging
  environment:
    name: staging
  rules:
    - if: '$CI_COMMIT_TAG =~ /^v\d+\.\d+\.\d+$/'
    - when: manual

deploy-production:
  stage: deploy
  image: python:3.11
  script:
    - python tools/ota_deploy.py
        --package $BUILD_DIR/ota_package.bin
        --target production
        --rollout 10%
  environment:
    name: production
  rules:
    - if: '$CI_COMMIT_TAG =~ /^v\d+\.\d+\.\d+$/'
    - when: manual
```

### Jenkins Pipeline (Android/Linux)
```groovy
// Jenkinsfile - Android 系统构建
pipeline {
    agent { label 'android-build' }

    environment {
        ANDROID_HOME = '/opt/android-sdk'
        BUILD_NUMBER = "${env.BUILD_NUMBER}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                sh 'git submodule update --init --recursive'
            }
        }

        stage('Lint') {
            steps {
                sh './gradlew lintDebug'
                androidLint pattern: '**/lint-results-*.xml'
            }
        }

        stage('Build') {
            parallel {
                stage('ARM64') {
                    steps {
                        sh 'source build/envsetup.sh'
                        sh 'lunch my_product-userdebug'
                        sh 'make -j$(nproc)'
                    }
                }
                stage('ARM32') {
                    steps {
                        sh 'source build/envsetup.sh'
                        sh 'lunch my_product_arm-userdebug'
                        sh 'make -j$(nproc)'
                    }
                }
            }
        }

        stage('Unit Test') {
            steps {
                sh './gradlew testDebugUnitTest'
                junit '**/test-results/**/*.xml'
            }
        }

        stage('Static Analysis') {
            steps {
                sh 'sonar-scanner'
            }
        }

        stage('Sign') {
            steps {
                sh 'sign_target_files_apks -o my_product-ota.zip'
            }
        }

        stage('OTA Package') {
            steps {
                sh 'ota_from_target_files my_product-ota.zip update.zip'
                archiveArtifacts artifacts: 'update.zip'
            }
        }

        stage('Deploy') {
            when { branch 'release/*' }
            steps {
                input message: 'Deploy to test devices?'
                sh 'python tools/ota_push.py --env staging'
            }
        }
    }

    post {
        always {
            cleanWs()
        }
        success {
            slackSend channel: '#builds',
                      message: "Build ${BUILD_NUMBER} succeeded"
        }
        failure {
            slackSend channel: '#builds',
                      message: "Build ${BUILD_NUMBER} FAILED"
        }
    }
}
```

### 4. 测试自动化

### 测试金字塔
```
                    ┌─────────┐
                    │  E2E    │  ← 少量, 慢, 贵
                    │ (系统测试)│
                    ├─────────┤
                    │ 集成测试 │  ← 中量, 中速
                    │ (模块间) │
                    ├─────────┤
                    │ 单元测试 │  ← 大量, 快, 便宜
                    │ (函数级) │
                    └─────────┘

嵌入式测试策略:
├── 单元测试 (Host 端, 80% 覆盖率)
│   ├── 算法: PID/Kalman/SLAM
│   ├── 协议: 解析/打包/校验
│   └── 工具: 状态机/队列/缓冲区
│
├── 集成测试 (Host 或 HIL)
│   ├── 传感器驱动 + 数据处理
│   ├── 通信协议 + 应用逻辑
│   └── 控制算法 + 电机模型
│
├── 硬件在环 (HIL) 测试
│   ├── 真实硬件 + 仿真环境
│   ├── 传感器注入 + 执行器监测
│   └── 异常注入 (通信中断/传感器故障)
│
└── 系统测试 (真机)
    ├── 功能验证
    ├── 性能测试
    ├── 可靠性测试
    └── 用户场景测试
```

### 单元测试框架 (Unity + CMock)
```c
/* test/test_pid.c */
#include "unity.h"
#include "pid.h"

static PID_Controller pid;

void setUp(void) {
    pid_init(&pid, 1.0f, 0.1f, 0.05f);
    pid.output_limit = 100.0f;
    pid.integral_limit = 50.0f;
}

void tearDown(void) {}

/* 测试: 阶跃响应 */
void test_pid_step_response(void) {
    float output;
    
    // 施加阶跃误差
    for (int i = 0; i < 100; i++) {
        output = pid_update(&pid, 10.0f);  // 设定值=10
    }
    
    // 输出应该趋向稳定
    TEST_ASSERT_FLOAT_WITHIN(5.0f, 10.0f, output);
}

/* 测试: 积分限幅 */
void test_pid_integral_windup(void) {
    // 持续大误差
    for (int i = 0; i < 1000; i++) {
        pid_update(&pid, 100.0f);
    }
    
    // 积分项应该被限幅
    TEST_ASSERT_FLOAT_WITHIN(0.1f, 50.0f, pid.integral);
}

/* 测试: 输出限幅 */
void test_pid_output_limit(void) {
    float output = pid_update(&pid, 1000.0f);
    
    TEST_ASSERT_TRUE(output <= 100.0f);
    TEST_ASSERT_TRUE(output >= -100.0f);
}

/* 测试: 微分项滤波 */
void test_pid_derivative_filter(void) {
    // 噪声输入
    float outputs[10];
    for (int i = 0; i < 10; i++) {
        float noise = (i % 2 == 0) ? 0.1f : -0.1f;
        outputs[i] = pid_update(&pid, 5.0f + noise);
    }
    
    // 输出应该平滑 (变化不大)
    for (int i = 1; i < 10; i++) {
        float delta = fabsf(outputs[i] - outputs[i-1]);
        TEST_ASSERT_TRUE(delta < 10.0f);
    }
}

int main(void) {
    UNITY_BEGIN();
    RUN_TEST(test_pid_step_response);
    RUN_TEST(test_pid_integral_windup);
    RUN_TEST(test_pid_output_limit);
    RUN_TEST(test_pid_derivative_filter);
    return UNITY_END();
}
```

### Robot Framework 自动化测试
```robot
*** Settings ***
Library    SerialLibrary
Library    Collections
Suite Setup    Open Serial Port    /dev/ttyUSB0    115200
Suite Teardown    Close Port

*** Variables ***
${TIMEOUT}    5s
${BAUDRATE}    115200

*** Test Cases ***
Test IMU Data Read
    [Documentation]    验证 IMU 数据读取功能
    Send Command    imu_read
    ${response}=    Read Until    \n    timeout=${TIMEOUT}
    Should Contain    ${response}    accel:
    Should Contain    ${response}    gyro:

Test Motor Control
    [Documentation]    验证电机控制功能
    Send Command    motor_set    50
    ${response}=    Read Until    \n    timeout=${TIMEOUT}
    Should Contain    ${response}    OK
    Send Command    motor_get_speed
    ${speed}=    Read Until    \n    timeout=${TIMEOUT}
    Should Be True    ${speed} > 0

Test OTA Update
    [Documentation]    验证 OTA 升级功能
    Send Command    ota_start
    ${response}=    Read Until    \n    timeout=${TIMEOUT}
    Should Contain    ${response}    READY
    Send Firmware File    firmware.bin
    ${response}=    Read Until    \n    timeout=60s
    Should Contain    ${response}    UPDATE_OK
    Send Command    reboot
    Sleep    3s
    ${response}=    Read Until    \n    timeout=${TIMEOUT}
    Should Contain    ${response}    BOOT_OK

Test Power Consumption
    [Documentation]    验证功耗指标
    Send Command    power_mode    sleep
    Sleep    1s
    ${current}=    Measure Current
    Should Be True    ${current} < 0.01    # <10mA
    Send Command    power_mode    active
    Sleep    1s
    ${current}=    Measure Current
    Should Be True    ${current} < 0.5     # <500mA

*** Keywords ***
Send Command
    [Arguments]    ${cmd}    ${args}=${EMPTY}
    Write    ${cmd} ${args}\n    encoding=ascii
```

### 5. 制品管理

### 固件版本号规范
```
语义化版本: vMAJOR.MINOR.PATCH

├── MAJOR: 不兼容的 API 修改
├── MINOR: 向下兼容的功能新增
├── PATCH: 向下兼容的问题修复
└── 示例: v2.1.3

构建版本: vMAJOR.MINOR.PATCH+BUILD
├── 示例: v2.1.3+1234
└── BUILD = CI 构建号

固件元数据:
{
    "version": "2.1.3",
    "build": 1234,
    "commit": "abc1234",
    "branch": "release/v2.1.3",
    "date": "2025-01-15T10:30:00Z",
    "mcu": "STM32H743",
    "board": "v3.2",
    "checksum": "sha256:..."
}
```

### 制品库 (Nexus/Artifactory)
```
制品库结构:

releases/
├── firmware/
│   ├── drone/
│   │   ├── v2.1.0/
│   │   │   ├── firmware.bin
│   │   │   ├── firmware_signed.bin
│   │   │   ├── ota_package.bin
│   │   │   ├── changelog.md
│   │   │   └── metadata.json
│   │   └── v2.1.3/
│   └── gimbal/
│       └── v1.0.0/
├── android/
│   └── v5.0.0/
│       ├── system.img
│       ├── vendor.img
│       ├── ota_update.zip
│       └── release_notes.md
└── tools/
    ├── flash_tool/
    ├── test_tool/
    └── calibration_tool/
```

---

### 相关链接

- [[devops-practice|DevOps 实践]]
- [[testing-strategy|测试策略]]
- [[ota-server|OTA 升级服务]]
- [[code-management|代码管理]]
- [[dev-process|项目管理流程]]

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

**下一步**：建议学习 [[/intermediate/|中级内容]]
