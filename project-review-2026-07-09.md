# macOS 隔空手势主控台项目方案与进度报告

**项目名称：** Gesture Control  
**报告日期：** 2026-07-09  
**项目类型：** 基于计算机视觉的人机交互应用  
**目标平台：** macOS  
**当前版本：** MVP / Prototype v0.1.0

## 1. 项目概述

本项目计划实现一个基于计算机视觉的 macOS 隔空手势主控台。用户不需要额外购买外设，只使用 Mac 自带的 FaceTime 前置摄像头，即可通过手势控制系统级操作，例如滚动页面、调节系统音量、暂停或恢复手势控制。

项目最终形态不是命令行脚本，而是接近普通 macOS app 的使用方式：用户双击 `GestureControl.app` 启动，在控制面板中点击 `Start` 进入手势控制模式，并可通过悬浮 `Stop` 按钮或菜单栏退出。

## 2. 核心目标

- 使用 Mac 自带摄像头进行实时手部识别。
- 使用 MediaPipe 获取 21 个手部骨骼关键点。
- 将稳定手势映射为 macOS 系统操作。
- 使用多线程结构隔离摄像头采集、AI 推理、手势判断、系统命令发送和 GUI。
- 提供普通用户可操作的 app 外壳，而不是只提供开发者命令行 demo。
- 支持后续扩展为虚拟多轨控制器、自定义手势映射和更多软件控制场景。

## 3. 技术方案

### 3.1 技术栈

| 模块 | 技术 |
| --- | --- |
| 编程语言 | Python 3.12 |
| 视觉采集 | OpenCV |
| 手部关键点识别 | MediaPipe |
| GUI app 外壳 | PySide6 Essentials |
| 系统控制 | PyAutoGUI / AppleScript `osascript` |
| 多线程运行 | Python `threading` + 最新帧队列 |
| 测试 | pytest |
| macOS 打包 | PyInstaller |

### 3.2 总体架构

项目采用分层架构：

1. **App Shell**
   - PySide6 控制面板。
   - Start / Pause / Stop / Quit 控制。
   - 菜单栏状态菜单。
   - 悬浮 Stop 窗口。

2. **Vision Pipeline**
   - OpenCV 读取 FaceTime 摄像头画面。
   - MediaPipe 识别手部关键点。
   - 使用“最新帧”策略降低延迟，旧帧可丢弃。

3. **Gesture Engine**
   - 对 landmarks 做手势特征计算。
   - 判断握拳、张掌、捏合和旋转。
   - 使用状态机做防抖、冷却和误触保护。

4. **System Control**
   - 将语义动作转换为系统命令。
   - 支持滚动、音量调节、暂停状态切换。
   - 对滚动和音量命令做限频，避免系统事件过载。

5. **Diagnostics**
   - 提供 OpenCV overlay 绘制能力。
   - 用于显示骨架、状态和调试信息。

## 4. 当前支持的 MVP 手势

| 手势 | 触发条件 | 映射动作 | 当前状态 |
| --- | --- | --- | --- |
| 左手握拳上下移动 | 左手五指收拢并稳定超过阈值 | 页面滚动 | 已实现状态机与命令映射 |
| 右手拇指食指捏合旋转 | 右手拇指和食指靠近并产生角度变化 | 系统音量增减 | 已实现状态机与命令映射 |
| 张开手掌保持约 0.8 秒 | 五指伸展并稳定保持 | 暂停 / 恢复控制 | 已实现状态机与冷却逻辑 |

## 5. 多线程设计

当前设计包含 4 个后台 worker：

| 线程 | 职责 |
| --- | --- |
| Camera Thread | 读取摄像头最新帧 |
| Inference Thread | 调用 MediaPipe 输出手部 landmarks |
| Gesture Thread | 根据 landmarks 更新状态机并生成动作 |
| Command Thread | 执行系统滚动、音量等命令 |

GUI 运行在主线程，不直接执行摄像头读取或 AI 推理，避免界面卡顿。

## 6. 当前项目结构

```text
Gesture/
├── config/default.yaml
├── dist/GestureControl.app
├── docs/
│   ├── project-review-2026-07-09.md
│   └── superpowers/
│       ├── plans/2026-07-07-gesture-control-app.md
│       └── specs/2026-07-07-gesture-control-app-design.md
├── scripts/package_app.py
├── src/gesture_control/
│   ├── app.py
│   ├── config.py
│   ├── core/
│   ├── diagnostics/
│   ├── runtime/
│   ├── system/
│   └── vision/
└── tests/
```

## 7. 已完成进度

| 阶段 | 内容 | 状态 |
| --- | --- | --- |
| 需求分析 | 明确 app 化、手势控制、多线程、macOS 权限和打包目标 | 已完成 |
| 设计文档 | 完成系统设计 spec | 已完成 |
| 实施计划 | 完成实现计划文档 | 已完成 |
| 项目骨架 | 创建 Python package、配置、README、入口 | 已完成 |
| 手势特征 | 实现握拳、张掌、捏合距离、捏合角度、掌心中心计算 | 已完成 |
| 手势状态机 | 实现滚动、音量、暂停/恢复状态切换 | 已完成 |
| 系统命令层 | 实现 dry-run controller、macOS controller、命令限频 | 已完成 |
| 多线程运行时 | 实现摄像头、推理、手势、命令四线程管线 | 已完成 |
| GUI 外壳 | 实现 PySide6 控制面板、菜单栏、悬浮 Stop 窗口 | 已完成 |
| 视觉适配器 | 实现 OpenCV 摄像头适配器和 MediaPipe 手部识别适配器 | 已完成 |
| 调试 overlay | 实现手部骨架与状态信息绘制 helper | 已完成 |
| 打包脚本 | 使用 PyInstaller 生成 macOS app bundle | 已完成 |
| 自动化测试 | 编写并通过 17 个 pytest 单元测试 | 已完成 |

## 8. 当前验证结果

### 8.1 单元测试

最新测试命令：

```bash
/opt/anaconda3/bin/python3.12 -m pytest -v
```

测试结果：

```text
17 passed in 0.09s
```

测试覆盖内容：

- 默认配置加载。
- 核心数据类型导入。
- 手势特征计算。
- 手势状态机。
- 命令限频。
- dry-run 系统命令记录。
- 多线程运行时 start / stop。
- GUI 模块无副作用导入。
- overlay helper 导入。

### 8.2 打包产物

当前已生成 macOS app：

```text
dist/GestureControl.app
```

该 app 为本地 PyInstaller 打包结果，尚未做 Apple Developer ID 签名、公证或 App Store 分发。

## 9. 当前限制与风险

1. **macOS 权限仍需人工验证**
   - 摄像头权限。
   - Accessibility 辅助功能权限。
   - Automation / AppleScript 权限。

2. **真实摄像头场景尚需调参**
   - 不同光照、背景、手部距离会影响 MediaPipe 识别稳定性。
   - 需要真实使用后调整阈值、灵敏度和死区。

3. **PyInstaller app 尚未正式签名**
   - 当前 app 可用于本机测试。
   - 首次打开可能需要在 macOS Privacy & Security 中允许运行。

4. **60fps 不是当前硬性保证**
   - 当前策略是摄像头和 UI 尽量低延迟。
   - AI 推理线程按机器能力处理最新帧。
   - 后续可继续优化延迟统计和帧率表现。

5. **虚拟多轨控制器尚未作为第一版主要功能**
   - 当前架构已保留扩展空间。
   - MVP 优先保证三个基础手势可用。

## 10. 下一步计划

1. 在真实 macOS 桌面环境中双击 `GestureControl.app` 启动。
2. 按系统提示授予 Camera、Accessibility、Automation 权限。
3. 实测三个核心手势：
   - 左手握拳上下移动滚动页面。
   - 右手捏合旋转调节音量。
   - 张开手掌保持暂停 / 恢复控制。
4. 根据实测结果调整：
   - `config/default.yaml` 中的灵敏度。
   - 手势 deadzone。
   - 命令发送频率。
5. 增加真实摄像头调试 overlay 窗口。
6. 扩展虚拟多轨控制器和用户自定义手势配置。
7. 如需提交代码仓库，可将项目发布到 GitHub 账号：

```text
https://github.com/khalilpong
```

## 11. 当前结论

本项目目前已经完成可运行 MVP 的主要工程结构和核心代码实现，具备 app 化启动、手势状态机、多线程运行时、系统命令映射、测试验证和 macOS app 打包能力。

当前阶段适合进入真实设备演示和参数调优阶段。项目尚未宣称完成商业级发布，主要待办集中在 macOS 权限实测、真实摄像头场景调参和后续交互体验优化。
