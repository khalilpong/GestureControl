# Gesture Control App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a macOS app-like Python gesture control MVP that can launch from a GUI, run a threaded camera/MediaPipe pipeline, map three hand gestures to system actions, and package as `GestureControl.app`.

**Architecture:** The app is split into pure core modules, runtime worker modules, system adapters, and a PySide6 shell. Core gesture and command behavior is tested first without camera or macOS permissions; runtime and GUI modules depend on optional packages and degrade with clear errors when dependencies are missing.

**Tech Stack:** Python 3.12 target, OpenCV, MediaPipe, PySide6, PyAutoGUI, AppleScript via `osascript`, pytest, PyInstaller.

## Global Constraints

- Work in the current repository because the user explicitly approved direct implementation in this new project.
- Keep core modules importable with only the Python standard library.
- Do not require camera, Accessibility, Automation, PySide6, OpenCV, or MediaPipe for unit tests.
- Use TDD for pure behavior: write failing tests before production code.
- Keep optional runtime imports inside runtime modules so missing GUI/vision dependencies do not break core tests.
- Keep system command sending behind interfaces and include dry-run testability.
- The app must expose Start, Pause, Stop, and Quit controls.
- The first packaged target is `dist/GestureControl.app`; notarization and App Store distribution are out of scope.

---

## File Structure

- `pyproject.toml`: project metadata, dependencies, pytest config, console entry.
- `README.md`: setup, permissions, run, test, and package instructions.
- `config/default.yaml`: default camera, gesture, command, and debug settings.
- `src/gesture_control/__init__.py`: package version.
- `src/gesture_control/__main__.py`: `python -m gesture_control` entrypoint.
- `src/gesture_control/app.py`: PySide6 GUI shell and app lifecycle.
- `src/gesture_control/config.py`: default config dataclasses and YAML loading fallback.
- `src/gesture_control/core/types.py`: landmarks, handedness, action, and state data types.
- `src/gesture_control/core/features.py`: gesture geometry and feature extraction.
- `src/gesture_control/core/state_machine.py`: gesture state machine.
- `src/gesture_control/core/rate_limit.py`: command limiter.
- `src/gesture_control/system/actions.py`: system command interfaces and macOS adapters.
- `src/gesture_control/runtime/queues.py`: latest-value queue primitives.
- `src/gesture_control/runtime/pipeline.py`: threaded camera, inference, gesture, and command orchestration.
- `src/gesture_control/vision/camera.py`: OpenCV camera adapter.
- `src/gesture_control/vision/mediapipe_hands.py`: MediaPipe adapter.
- `src/gesture_control/diagnostics/overlay.py`: OpenCV overlay helpers.
- `scripts/package_app.py`: PyInstaller wrapper.
- `tests/`: pytest tests for core behavior.

## Task 1: Project Skeleton And Core Types

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `config/default.yaml`
- Create: `src/gesture_control/__init__.py`
- Create: `src/gesture_control/__main__.py`
- Create: `src/gesture_control/config.py`
- Create: `src/gesture_control/core/types.py`
- Create: `tests/test_config.py`

**Interfaces:**
- Produces: `AppConfig.default() -> AppConfig`
- Produces: `Landmark`, `HandLandmarks`, `GestureAction`, `GestureActionType`, `GestureState`

- [ ] Step 1: Write failing tests for default config values.
- [ ] Step 2: Run `python3 -m pytest tests/test_config.py -v` and confirm config module is missing.
- [ ] Step 3: Implement config dataclasses, package skeleton, and project metadata.
- [ ] Step 4: Run `python3 -m pytest tests/test_config.py -v` and confirm pass.
- [ ] Step 5: Commit skeleton.

## Task 2: Gesture Feature Extraction

**Files:**
- Create: `src/gesture_control/core/features.py`
- Create: `tests/test_features.py`

**Interfaces:**
- Consumes: `HandLandmarks`
- Produces: `is_fist(hand: HandLandmarks) -> bool`
- Produces: `is_palm_open(hand: HandLandmarks) -> bool`
- Produces: `pinch_distance(hand: HandLandmarks) -> float`
- Produces: `pinch_angle(hand: HandLandmarks) -> float`
- Produces: `palm_center(hand: HandLandmarks) -> tuple[float, float]`

- [ ] Step 1: Write failing tests using synthetic 21-point hand landmarks.
- [ ] Step 2: Run `python3 -m pytest tests/test_features.py -v` and confirm functions are missing.
- [ ] Step 3: Implement simple normalized geometry helpers.
- [ ] Step 4: Run `python3 -m pytest tests/test_features.py -v` and confirm pass.
- [ ] Step 5: Commit feature extraction.

## Task 3: Gesture State Machine

**Files:**
- Create: `src/gesture_control/core/state_machine.py`
- Create: `tests/test_state_machine.py`

**Interfaces:**
- Consumes: `list[HandLandmarks]`, timestamp seconds.
- Produces: `GestureStateMachine.update(hands, timestamp) -> list[GestureAction]`
- Emits: `SCROLL_DELTA`, `VOLUME_DELTA`, `TOGGLE_PAUSE`

- [ ] Step 1: Write failing tests for fist scroll, pinch volume, palm pause, cooldown, and paused state.
- [ ] Step 2: Run `python3 -m pytest tests/test_state_machine.py -v` and confirm state machine is missing.
- [ ] Step 3: Implement state machine with hysteresis, deadzone, and cooldown.
- [ ] Step 4: Run `python3 -m pytest tests/test_state_machine.py -v` and confirm pass.
- [ ] Step 5: Commit state machine.

## Task 4: System Command Abstraction

**Files:**
- Create: `src/gesture_control/core/rate_limit.py`
- Create: `src/gesture_control/system/actions.py`
- Create: `tests/test_actions.py`

**Interfaces:**
- Produces: `RateLimiter.allow(key: str, timestamp: float) -> bool`
- Produces: `DryRunSystemController`
- Produces: `MacSystemController`
- Produces: `CommandDispatcher.handle(action: GestureAction, timestamp: float) -> None`

- [ ] Step 1: Write failing tests for scroll limit, volume limit, pause passthrough, and dry-run recording.
- [ ] Step 2: Run `python3 -m pytest tests/test_actions.py -v` and confirm modules are missing.
- [ ] Step 3: Implement rate limiter and system controller adapters.
- [ ] Step 4: Run `python3 -m pytest tests/test_actions.py -v` and confirm pass.
- [ ] Step 5: Commit system command layer.

## Task 5: Threaded Runtime Pipeline

**Files:**
- Create: `src/gesture_control/runtime/queues.py`
- Create: `src/gesture_control/runtime/pipeline.py`
- Create: `src/gesture_control/vision/camera.py`
- Create: `src/gesture_control/vision/mediapipe_hands.py`
- Create: `tests/test_runtime.py`

**Interfaces:**
- Produces: `LatestValueSlot.put(value)`, `LatestValueSlot.get(timeout=None)`
- Produces: `GestureRuntime.start()`, `GestureRuntime.stop()`, `GestureRuntime.snapshot()`
- Produces: `OpenCVCamera`
- Produces: `MediaPipeHandTracker`

- [ ] Step 1: Write failing tests for latest-value replacement and runtime start/stop with fake camera/tracker/controller.
- [ ] Step 2: Run `python3 -m pytest tests/test_runtime.py -v` and confirm modules are missing.
- [ ] Step 3: Implement latest-value slot and runtime orchestration.
- [ ] Step 4: Implement OpenCV and MediaPipe adapters with optional imports and clear ImportError messages.
- [ ] Step 5: Run `python3 -m pytest tests/test_runtime.py -v` and confirm pass.
- [ ] Step 6: Commit runtime pipeline.

## Task 6: App Shell

**Files:**
- Create: `src/gesture_control/app.py`
- Create: `tests/test_app_imports.py`

**Interfaces:**
- Produces: `run_app() -> int`
- Produces: `GestureControlWindow`
- Produces: `FloatingStopWindow`

- [ ] Step 1: Write failing test that app module imports without PySide6 runtime side effects and exposes `run_app`.
- [ ] Step 2: Run `python3 -m pytest tests/test_app_imports.py -v`.
- [ ] Step 3: Implement PySide6 app shell with lazy PySide6 imports, Start, Pause, Stop, Quit, status menu, and floating stop window.
- [ ] Step 4: Run `python3 -m pytest tests/test_app_imports.py -v` and confirm pass.
- [ ] Step 5: Commit app shell.

## Task 7: Diagnostics And Packaging

**Files:**
- Create: `src/gesture_control/diagnostics/overlay.py`
- Create: `scripts/package_app.py`
- Modify: `README.md`
- Create: `tests/test_overlay_imports.py`

**Interfaces:**
- Produces: `draw_overlay(frame, hands, status) -> frame`
- Produces: `scripts/package_app.py` command wrapper

- [ ] Step 1: Write failing import test for overlay helper.
- [ ] Step 2: Run `python3 -m pytest tests/test_overlay_imports.py -v`.
- [ ] Step 3: Implement overlay helper with optional OpenCV drawing.
- [ ] Step 4: Add PyInstaller packaging wrapper and README instructions.
- [ ] Step 5: Run all tests with `python3 -m pytest -v`.
- [ ] Step 6: Commit diagnostics and packaging.

## Task 8: Final Verification

**Files:**
- Verify all files.

- [ ] Step 1: Run `python3 -m pytest -v`.
- [ ] Step 2: Run `python3 -m compileall src tests scripts`.
- [ ] Step 3: Run `git status --short`.
- [ ] Step 4: Report implemented scope, test evidence, and remaining manual steps for camera permissions and `.app` packaging.
