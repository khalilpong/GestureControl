from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def test_draw_overlay_draws_skeleton_and_status_on_real_frame() -> None:
    import numpy as np

    from gesture_control.core.types import HandLandmarks, Landmark
    from gesture_control.diagnostics.overlay import draw_overlay

    frame = np.zeros((100, 100, 3), dtype="uint8")
    hand = HandLandmarks(
        handedness="Left",
        landmarks=[Landmark(0.5, 0.5, 0.0) for _ in range(21)],
        confidence=0.9,
        timestamp=1.0,
    )

    annotated = draw_overlay(frame, [hand], {"state": "tracking"})

    assert annotated is frame
    assert annotated.any()  # something was drawn onto the previously-blank frame


def test_to_rgb_bytes_converts_bgr_frame_to_rgb_buffer() -> None:
    import numpy as np

    from gesture_control.diagnostics.overlay import to_rgb_bytes

    frame = np.zeros((4, 6, 3), dtype="uint8")
    frame[:, :, 2] = 255  # OpenCV stores this as BGR, so channel 2 is red.

    result = to_rgb_bytes(frame)

    assert result is not None
    data, width, height, bytes_per_line = result
    assert (width, height) == (6, 4)
    assert bytes_per_line == width * 3
    assert len(data) == width * height * 3
    # BGR (0, 0, 255) must become RGB (255, 0, 0) in the output buffer.
    assert data[0] == 255
    assert data[1] == 0
    assert data[2] == 0


def test_to_rgb_bytes_returns_none_for_non_image_input() -> None:
    from gesture_control.diagnostics.overlay import to_rgb_bytes

    assert to_rgb_bytes(object()) is None
