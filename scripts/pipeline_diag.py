from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gesture_control.config import AppConfig
from gesture_control.runtime.pipeline import GestureRuntime
from gesture_control.system.actions import DryRunSystemController
from gesture_control.vision.camera import OpenCVCamera
from gesture_control.vision.mediapipe_hands import MediaPipeHandTracker


def main() -> None:
    config = AppConfig.default()
    print(f"Camera config: index={config.camera.index} {config.camera.width}x{config.camera.height} @ {config.camera.fps}fps")

    camera = OpenCVCamera(config.camera)
    print("Opening camera via the app's OpenCVCamera wrapper (with 640x480 @ 60fps applied)...")
    camera.open()
    print("Opened. Reading 20 raw frames directly (no threads)...")

    ok = 0
    for i in range(20):
        t0 = time.monotonic()
        frame = camera.read()
        dt = time.monotonic() - t0
        if frame is not None:
            ok += 1
            if i == 0:
                print(f"  frame 0: shape={frame.shape} read_time={dt:.3f}s")
        else:
            print(f"  frame {i}: None (read_time={dt:.3f}s)")
        time.sleep(0.05)
    print(f"Raw read result: {ok}/20 frames ok")

    if ok == 0:
        print("FAILED at the camera wrapper level (with app's 640x480@60fps settings).")
        print("Try lowering fps/resolution in config/default.yaml.")
        camera.close()
        return

    print("\nTesting MediaPipe hand detection on one frame (this loads the model, may take a few seconds)...")
    tracker = MediaPipeHandTracker(config.gesture)
    frame = camera.read()
    t0 = time.monotonic()
    try:
        hands = tracker.detect(frame, time.monotonic())
        dt = time.monotonic() - t0
        print(f"  detect() took {dt:.2f}s, hands found={len(hands)}")
    except Exception as exc:
        print(f"  detect() RAISED: {type(exc).__name__}: {exc}")
        camera.close()
        return

    camera.close()
    tracker.close()

    print("\nNow running the FULL threaded GestureRuntime for 6 seconds (dry-run system control, no real scroll/volume changes)...")
    runtime = GestureRuntime(
        config=config,
        camera=OpenCVCamera(config.camera),
        tracker=MediaPipeHandTracker(config.gesture),
        controller=DryRunSystemController(),
    )
    runtime.start()

    deadline = time.monotonic() + 6.0
    got_frame = False
    while time.monotonic() < deadline:
        snap = runtime.snapshot()
        item = runtime.latest_debug_frame()
        if item is not None:
            got_frame = True
            frame, hands = item
            print(f"  [{time.monotonic():.1f}] debug frame arrived, hands={len(hands)}, state={snap.state}")
        if snap.latest_error:
            print(f"  ERROR: {snap.latest_error}")
            break
        time.sleep(0.2)

    if not got_frame:
        print("\nFAILED: full threaded runtime never produced a debug frame in 6 seconds,")
        print("even though raw camera + single-shot MediaPipe detection worked above.")
        print("This points to a bug in the threading pipeline itself.")
    else:
        print("\nSUCCESS: full pipeline produced debug frames correctly.")

    final = runtime.snapshot()
    print(f"Final snapshot: running={final.running} state={final.state} error={final.latest_error}")
    runtime.stop()


if __name__ == "__main__":
    main()
