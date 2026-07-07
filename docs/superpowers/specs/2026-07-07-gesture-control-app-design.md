# macOS Gesture Control App Design

## 1. Summary

本项目构建一个面向普通用户的 macOS 隔空手势主控台。用户双击 `GestureControl.app` 后进入手势控制模式，应用使用 Mac FaceTime 前置摄像头采集画面，通过 MediaPipe 识别手部关键点，再把稳定的手势状态映射为 macOS 系统操作。

第一版目标不是命令行 demo，而是一个可以像普通 app 一样启动、暂停、退出的本地 macOS 应用。核心能力包括三类手势控制、状态可视化、菜单栏控制、悬浮退出按钮、权限引导和多线程实时管线。

## 2. Goals

- 用户可以双击 `.app` 图标启动，不需要理解命令行。
- 用户可以在控制面板点击 `Start` 进入手势控制模式。
- 用户可以点击悬浮 `Stop` 按钮或菜单栏 `Quit` 退出进程。
- 应用可以识别三种 MVP 手势：
  - 左手握拳上下移动，控制页面滚动。
  - 右手拇指和食指捏合旋转，控制系统音量。
  - 张开手掌保持约 0.8 秒，暂停或恢复手势控制。
- 应用使用多线程隔离摄像头采集、AI 推理、手势状态机、系统命令发送和 GUI。
- 应用提供调试 overlay，显示手部骨架、FPS、当前状态、延迟和最近系统动作。
- 应用使用 Python 3.12 虚拟环境开发，避免 Python 3.13 和 MediaPipe 兼容性风险。
- 最终使用 PyInstaller 打包为 macOS `.app`。

## 3. Non-Goals

- 第一版不做完整商业级签名、公证和 App Store 分发。
- 第一版不保证 AI 推理稳定达到 60fps。目标是摄像头和 UI 低延迟，推理线程尽力使用最新帧。
- 第一版不接入 Final Cut、Logic、Photoshop 等专业软件的专用 API。
- 第一版不做复杂多用户配置同步。
- 第一版不把虚拟多轨控制器做成主要交付，只保留架构扩展点和简单参数面板。

## 4. User Experience

### 4.1 First Launch

首次启动显示欢迎控制面板：

1. 检查摄像头权限。
2. 检查辅助功能权限。
3. 检查 Automation / AppleScript 权限。
4. 检查 Python 运行组件是否可用。
5. 显示 `Start Gesture Control` 按钮。

如果权限缺失，控制面板显示具体权限名称和打开系统设置的指引。第一版可以提供文字说明和 `Open Settings` 按钮，实际权限仍由用户在 macOS 系统设置中授予。

### 4.2 Normal Launch

用户后续双击 app：

1. 应用打开小型控制面板。
2. 菜单栏显示手势图标和当前状态。
3. 用户点击 `Start` 后启动摄像头和手势管线。
4. 屏幕右上角出现一个小型悬浮控制条，显示 `Gesture: On` 和 `Stop`。

### 4.3 Exit Flow

用户可以通过三种方式停止：

- 点击悬浮控制条里的 `Stop`。
- 点击菜单栏图标里的 `Stop` 或 `Quit`。
- 在控制面板点击 `Stop`。

停止时必须按顺序关闭系统控制、AI 推理、摄像头采集和 GUI 资源，避免摄像头灯或后台线程残留。

## 5. Recommended Approach

采用方案 A：MediaPipe Hand Landmarker + 自研手势状态机 + PySide6 app 外壳。

选择理由：

- MediaPipe Hand Landmarker 能提供 21 个关键点，适合连续控制，例如捏合角度、拳头位移和虚拟旋钮。
- 自研状态机可以处理进入阈值、退出阈值、防抖、冷却和误触保护。
- PySide6 更适合做 macOS 风格控制面板、菜单栏、悬浮按钮和权限提示。
- PyInstaller 可以把 Python 项目打包为 `.app`，满足双击启动目标。

不采用 Gesture Recognizer 作为核心，因为内置离散手势不适合后续的连续旋转和多轨参数控制。

## 6. Architecture

应用分为五个主要子系统：

1. App Shell
   - PySide6 GUI。
   - 控制面板。
   - 菜单栏状态菜单。
   - 悬浮 `Stop` 控件。
   - 生命周期管理。

2. Vision Pipeline
   - OpenCV 摄像头采集。
   - MediaPipe 手部关键点推理。
   - 最近帧缓存和低延迟丢帧策略。

3. Gesture Engine
   - Landmark 归一化。
   - 平滑滤波。
   - 手势特征计算。
   - 状态机和防误触逻辑。

4. System Control
   - 滚动命令发送。
   - 音量命令发送。
   - 命令限频和冷却。
   - AppleScript / PyAutoGUI 调用封装。

5. Diagnostics
   - FPS 统计。
   - 队列延迟统计。
   - 手势状态记录。
   - OpenCV debug overlay。
   - 简单日志文件。

## 7. Thread Model

第一版使用线程和 bounded queue，而不是单线程同步循环。

### 7.1 GUI Thread

职责：

- 运行 PySide6 event loop。
- 响应 Start、Stop、Pause、Quit。
- 更新状态文本和菜单栏状态。

约束：

- 不执行 AI 推理。
- 不阻塞等待摄像头帧。
- 只通过线程安全的控制接口启动和停止 worker。

### 7.2 Camera Thread

职责：

- 通过 OpenCV `VideoCapture` 读取 FaceTime 摄像头。
- 把最新帧写入长度为 1 或 2 的队列。
- 当队列满时丢弃旧帧。

目标：

- 优先低延迟，而不是保留每一帧。
- 捕获分辨率默认从 640x480 开始，后续可调。

### 7.3 Inference Thread

职责：

- 从最新帧队列读取图像。
- 调用 MediaPipe Hand Landmarker。
- 输出手部关键点、左右手信息、置信度和时间戳。

目标：

- 处理最新可用帧。
- 如果推理速度慢，不阻塞 camera thread。

### 7.4 Gesture Thread

职责：

- 接收最新 landmarks。
- 计算手势特征。
- 更新状态机。
- 生成语义动作，例如 `SCROLL_DELTA`、`VOLUME_DELTA`、`TOGGLE_PAUSE`。

### 7.5 Command Thread

职责：

- 接收语义动作。
- 按限频策略发送系统命令。
- 对危险动作或高频动作做冷却。

默认限频：

- 滚动命令最高约 30Hz。
- 音量命令最高约 10Hz。
- 暂停切换至少 800ms 冷却。

## 8. Gesture Design

### 8.1 Fist Scroll

触发条件：

- 检测到左手。
- 食指、中指、无名指、小指指尖都靠近各自掌指区域。
- 拇指不伸展或贴近掌心。
- 状态持续超过短时间阈值，例如 150ms。

控制方式：

- 进入 `FIST_SCROLL` 后记录拳头中心点。
- 后续根据拳头中心点垂直位移计算滚动 delta。
- 小幅抖动进入死区，不发送命令。
- 松开拳头或置信度下降后退出。

### 8.2 Pinch Rotate Volume

触发条件：

- 检测到右手。
- 拇指指尖和食指指尖距离小于手掌尺度的一定比例。
- 捏合状态持续超过短时间阈值，例如 150ms。

控制方式：

- 进入 `PINCH_ROTATE` 后记录拇指到食指的初始角度。
- 后续角度变化映射为音量增减。
- 单次变化过小进入死区。
- 音量命令限频到约 10Hz。

### 8.3 Palm Pause

触发条件：

- 检测到张开手掌。
- 五指伸展。
- 手掌保持相对稳定约 0.8 秒。

控制方式：

- 如果当前控制开启，切换到暂停。
- 如果当前暂停，恢复控制。
- 切换后进入冷却，避免连续触发。

## 9. State Machine

主状态：

- `IDLE`: 应用已打开，但未启动控制。
- `STARTING`: 正在启动摄像头和 worker。
- `TRACKING`: 已看到手，等待稳定手势。
- `FIST_SCROLL`: 左手握拳滚动中。
- `PINCH_ROTATE`: 右手捏合旋转调音量中。
- `PAUSED`: 暂停手势控制，但应用仍运行。
- `STOPPING`: 正在释放资源。
- `ERROR`: 摄像头、权限或依赖异常。

状态切换规则：

- 所有系统动作只允许从 `FIST_SCROLL` 或 `PINCH_ROTATE` 发出。
- `PAUSED` 状态不发送滚动和音量命令。
- `STOPPING` 必须停止 command thread 后再停止 camera thread。
- 任何权限错误进入 `ERROR`，GUI 显示可操作说明。

## 10. Permission Model

macOS 第一版需要处理三类权限：

- Camera: 允许读取 FaceTime 摄像头。
- Accessibility: 允许 PyAutoGUI 或事件模拟控制屏幕滚动。
- Automation: 允许 AppleScript 控制系统音量或系统事件。

权限策略：

- 启动时检测可检测的权限状态。
- 对不可直接检测的权限，执行安全的 smoke test。
- 如果失败，GUI 显示具体失败原因。
- 不在无权限状态下静默运行。

## 11. Packaging

开发环境：

- Python 3.12 virtual environment。
- `opencv-python`。
- `mediapipe`。
- `PySide6`。
- `pyautogui`。
- `pytest`。
- `pyinstaller`。

打包目标：

- 生成 `dist/GestureControl.app`。
- app 启动后运行 PySide6 主程序。
- app 内包含必要资源，例如图标、默认配置和模型资源。

第一版不做正式 Developer ID 签名和 notarization。用户可能需要在 macOS 安全设置里允许本地 app 运行。

## 12. Configuration

配置文件建议使用 `config/default.yaml`。

默认配置项：

- camera index。
- capture width and height。
- max hands。
- detection confidence。
- tracking confidence。
- scroll sensitivity。
- volume sensitivity。
- gesture deadzone。
- command rate limits。
- debug overlay enabled。

运行时可以先不做复杂设置页面，但控制面板应显示当前配置摘要。

## 13. Error Handling

必须覆盖以下错误：

- 摄像头无法打开。
- MediaPipe 初始化失败。
- 无法发送滚动事件。
- AppleScript 音量命令失败。
- 权限不足。
- worker 线程异常退出。

处理方式：

- GUI 状态切换为 `ERROR`。
- 停止所有 worker。
- 显示短错误信息和日志路径。
- 允许用户重新点击 `Start`。

## 14. Testing Strategy

### 14.1 Unit Tests

优先测试不依赖摄像头和 macOS 权限的模块：

- 手势特征计算。
- 状态机切换。
- 命令限频。
- 配置加载。

### 14.2 Integration Tests

使用录制或合成 landmark 序列测试：

- 左手握拳上下移动产生滚动动作。
- 右手捏合旋转产生音量动作。
- 张开手掌保持触发暂停。

### 14.3 Manual Verification

在真实 Mac 上验证：

- 双击 `.app` 可启动。
- `Start` 后摄像头灯亮起。
- overlay 显示手部骨架和 FPS。
- 三个 MVP 手势可触发。
- 点击悬浮 `Stop` 后摄像头灯熄灭。
- 菜单栏 `Quit` 能完全退出进程。

## 15. Performance Targets

第一版性能目标：

- GUI 操作无明显卡顿。
- 摄像头采集线程使用低延迟最新帧策略。
- debug overlay 显示总延迟。
- 在普通室内光照下，手势触发延迟体感不超过约 150-250ms。
- 摄像头和显示循环尽量接近 60fps。
- AI 推理按机器能力运行，不把 60fps 作为硬性验收条件。

## 16. Extensibility

第二阶段可以增加：

- 虚拟多轨控制器。
- 用户自定义手势映射。
- 设置页面。
- 自动启动。
- 更好的 macOS 权限检测。
- Swift 原生外壳或菜单栏 app 重写。
- 对专业软件的快捷键配置。

架构必须保留 `GestureAction` 到 `SystemCommand` 的映射层，避免后续每加一个手势都直接调用系统 API。

## 17. Acceptance Criteria

第一版完成标准：

- 可以通过一个入口脚本启动 PySide6 控制面板。
- 可以打包出 `GestureControl.app`。
- app 有控制面板、菜单栏状态和悬浮停止按钮。
- app 可以启动和停止摄像头管线。
- app 可以显示手部骨架 overlay 和 FPS。
- 左手握拳上下移动可以滚动页面。
- 右手捏合旋转可以调系统音量。
- 张开手掌保持可以暂停或恢复控制。
- 点击悬浮 `Stop` 后摄像头释放，worker 线程停止。
- 单元测试覆盖状态机、手势特征和命令限频。

## 18. References

- MediaPipe Hand Landmarker Python: https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker/python
- MediaPipe PyPI: https://pypi.org/project/mediapipe/
- OpenCV VideoCapture: https://docs.opencv.org/4.x/d8/dfe/classcv_1_1VideoCapture.html
- PyAutoGUI documentation: https://pyautogui.readthedocs.io/en/latest/quickstart.html
