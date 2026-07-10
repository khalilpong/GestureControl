# Gesture Control

A macOS app for touch-free control of your Mac using just the built-in
FaceTime camera. It tracks your hand with [MediaPipe](https://ai.google.dev/edge/mediapipe)
and maps a few stable, deliberate gestures to everyday system actions —
scrolling, adjusting the volume, and pausing/resuming control — through a
small native-feeling PySide6 app shell (menu bar icon, floating stop button,
and all).

No extra hardware, no cloud services: video is processed entirely on-device
and is never recorded or transmitted anywhere.

## Gestures

| Gesture | Action |
| --- | --- |
| ✊ Left hand fist, move up/down | Scroll the page |
| 🤏 Right hand pinch (thumb + index), rotate wrist | Adjust system volume |
| 🖐️ Either hand, open palm held ~0.8s | Pause / resume gesture control |

All thresholds, hold times, and sensitivities are tunable in
[`config/default.yaml`](config/default.yaml) — no code changes or rebuilding
required.

## Features

- **Runs as a real macOS app** — double-click `GestureControl.app`, click
  Start, and go. A floating "Stop" window and a menu bar icon are always
  available while it's running.
- **Threaded pipeline** — camera capture, MediaPipe inference, gesture state
  machine, and system command dispatch each run on their own thread, so a
  slow inference frame never blocks the UI or drops the newest camera frame.
- **Debug View** — a live camera + hand-skeleton overlay window for tuning
  gesture thresholds against your actual lighting, camera angle, and hand
  size, instead of guessing.
- **Self-reporting failures** — if a background thread dies (e.g. a missing
  Accessibility permission), the app surfaces the error in the status bar
  within half a second instead of silently doing nothing.

## Requirements

- macOS (Apple Silicon or Intel)
- Python 3.12 (MediaPipe does not yet support 3.13 on this project's pinned
  version range)
- A working camera, plus these permissions the first time you run it:
  - **Camera** — to see your hand
  - **Accessibility** — to send scroll events
  - System volume control uses AppleScript and needs no extra permission

## Quick Start (prebuilt app)

Grab `GestureControl.app` from a release / the `dist/` build output, then:

```bash
xattr -cr /path/to/GestureControl.app   # clears the download quarantine flag
```

Double-click to launch (the app isn't notarized, so the first launch may
require right-click → Open, or the `xattr` step above). Click **Start**, grant
the Camera and Accessibility prompts, and try the gestures above.

## Development Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Run the test suite:

```bash
python -m pytest -v
```

Run from source:

```bash
python -m gesture_control
```

## Configuration

Runtime behavior is controlled by [`config/default.yaml`](config/default.yaml),
loaded automatically on startup (override the path with the
`GESTURE_CONTROL_CONFIG` environment variable). Notable knobs:

| Key | What it tunes |
| --- | --- |
| `camera.fps` / `camera.width` / `camera.height` | Capture resolution and target frame rate |
| `gesture.fist_finger_curl_ratio` / `fist_thumb_curl_ratio` | How tightly fingers/thumb must curl to count as a fist |
| `gesture.pinch_distance_threshold` | How close thumb and index must be to count as a pinch |
| `gesture.*_hold_seconds` | How long a gesture must be held before it triggers |
| `gesture.scroll_sensitivity` / `volume_sensitivity` | How much movement maps to how much scroll/volume change |
| `command.scroll_hz` / `volume_hz` | Max rate system commands are sent, to avoid overwhelming macOS |
| `debug.overlay_enabled` | Enables the Debug View button in the app |

## Troubleshooting

If gestures don't seem to register, or the Debug View stays on "Waiting for
camera frames...", run these directly in a terminal (not through an
automation tool) to isolate the problem layer by layer:

```bash
python scripts/camera_diag.py    # raw OpenCV camera capture only
python scripts/pipeline_diag.py  # camera + MediaPipe + full threaded runtime
```

Any background thread failure (e.g. a missing permission) is also surfaced
directly in the app's status bar as `Status: Error - ...`.

## Packaging a Standalone App

```bash
python scripts/package_app.py
```

Builds `dist/GestureControl.app` via the checked-in [`GestureControl.spec`](GestureControl.spec).
The spec pins down a few things PyInstaller's default CLI can't express:

- `NSCameraUsageDescription` in `Info.plist` — without it, macOS hard-kills
  the process the instant it touches the camera instead of prompting.
- `collect_all("mediapipe")` — MediaPipe's Tasks API loads a native library
  dynamically in a way PyInstaller's static analysis misses, so it has to be
  force-included.

The build isn't code-signed or notarized. To share it with another Mac,
`ditto -c -k --sequesterRsrc --keepParent GestureControl.app GestureControl.zip`
preserves the bundle correctly for distribution; recipients will need to
right-click → Open (or run `xattr -cr`) on first launch.

## Architecture

```text
src/gesture_control/
├── app.py              # PySide6 app shell: main window, floating stop, Debug View
├── config.py           # AppConfig dataclasses + YAML loading/merging
├── core/
│   ├── features.py      # Pure geometry: fist/palm/pinch detection from landmarks
│   ├── state_machine.py # Gesture state machine (hold timers, debouncing, pause)
│   ├── rate_limit.py    # Rate limiter for outgoing system commands
│   └── types.py         # Shared dataclasses (HandLandmarks, GestureAction, ...)
├── vision/
│   ├── camera.py         # OpenCV camera adapter
│   └── mediapipe_hands.py# MediaPipe Tasks API hand landmark detector
├── runtime/
│   ├── pipeline.py       # 4-thread runtime: camera, inference, gesture, command
│   └── queues.py         # LatestValueSlot — always processes the newest frame
├── system/
│   └── actions.py        # System control (pyautogui scroll, AppleScript volume)
└── diagnostics/
    └── overlay.py         # Hand-skeleton + status drawing for the Debug View
```

## License

MIT — see [LICENSE](LICENSE).
