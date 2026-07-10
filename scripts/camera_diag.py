from __future__ import annotations

import time

import cv2


def main() -> None:
    print(f"OpenCV version: {cv2.__version__}")
    backend = getattr(cv2, "CAP_AVFOUNDATION", 0)
    print(f"Opening camera index 0 with backend={backend} (AVFoundation)...")

    capture = cv2.VideoCapture(0, backend)
    if not capture.isOpened():
        print("AVFoundation backend failed to open, retrying with default backend...")
        capture = cv2.VideoCapture(0)

    print(f"isOpened() = {capture.isOpened()}")
    if not capture.isOpened():
        print("FAILED: camera did not open at all. This is almost certainly a macOS")
        print("Camera permission issue for whatever app/process is running Python")
        print("(Terminal, iTerm, VS Code, etc.) — check System Settings > Privacy &")
        print("Security > Camera.")
        return

    print("Reading 30 frames over ~3 seconds...")
    ok_count = 0
    fail_count = 0
    first_shape = None
    start = time.monotonic()
    for i in range(30):
        ok, frame = capture.read()
        if ok and frame is not None:
            ok_count += 1
            if first_shape is None:
                first_shape = frame.shape
        else:
            fail_count += 1
        time.sleep(0.1)
    elapsed = time.monotonic() - start

    capture.release()

    print(f"Done in {elapsed:.1f}s: ok={ok_count} fail={fail_count} frame_shape={first_shape}")
    if ok_count == 0:
        print("FAILED: camera opened but never returned a real frame.")
        print("Possible causes: another app is holding the camera (FaceTime, Photo")
        print("Booth, Zoom, another Python process), or a driver/index mismatch if")
        print("you have multiple cameras (Continuity Camera, USB webcam, etc).")
    else:
        print("SUCCESS: raw OpenCV camera capture works fine on this machine.")


if __name__ == "__main__":
    main()
