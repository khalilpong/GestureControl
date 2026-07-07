# Gesture Control

A macOS app-style air gesture control MVP. It uses the built-in FaceTime camera,
MediaPipe hand landmarks, and a small PySide6 shell to map stable hand gestures
to system actions such as scrolling and volume changes.

## Current Scope

- Double-clickable app target through PyInstaller.
- PySide6 control panel with Start, Pause, Stop, and Quit.
- Threaded camera, inference, gesture, and command pipeline.
- MVP gestures:
  - Left fist vertical movement scrolls.
  - Right pinch rotation changes system volume.
  - Open palm hold toggles pause.

## Local Setup

Use Python 3.12. MediaPipe may not support Python 3.13 in this project target.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Run Tests

```bash
python -m pytest -v
```

## Run App

```bash
python -m gesture_control
```

macOS will require Camera, Accessibility, and Automation permissions for the
full control path.
