from __future__ import annotations

from typing import Any

from gesture_control.core.types import HandLandmarks


HAND_CONNECTIONS = (
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 4),
    (0, 5),
    (5, 6),
    (6, 7),
    (7, 8),
    (5, 9),
    (9, 10),
    (10, 11),
    (11, 12),
    (9, 13),
    (13, 14),
    (14, 15),
    (15, 16),
    (13, 17),
    (17, 18),
    (18, 19),
    (19, 20),
    (0, 17),
)


def draw_overlay(frame: Any, hands: list[HandLandmarks], status: dict[str, object]) -> Any:
    if not hasattr(frame, "shape"):
        return frame

    try:
        import cv2
    except ImportError:
        return frame

    height, width = frame.shape[:2]
    for hand in hands:
        points = [
            (int(landmark.x * width), int(landmark.y * height))
            for landmark in hand.landmarks
        ]
        for start, end in HAND_CONNECTIONS:
            cv2.line(frame, points[start], points[end], (40, 220, 120), 2)
        for point in points:
            cv2.circle(frame, point, 3, (0, 255, 255), -1)

    y = 24
    for key, value in status.items():
        cv2.putText(
            frame,
            f"{key}: {value}",
            (12, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )
        y += 22
    return frame


def to_rgb_bytes(frame: Any) -> tuple[bytes, int, int, int] | None:
    """Convert a BGR frame into (rgb_bytes, width, height, bytes_per_line) for GUI rendering.

    Returns None when the frame isn't an image-like array or OpenCV is unavailable,
    so callers can skip rendering without importing Qt or OpenCV themselves.
    """

    if not hasattr(frame, "shape"):
        return None

    try:
        import cv2
    except ImportError:
        return None

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    height, width = rgb.shape[:2]
    channels = rgb.shape[2] if rgb.ndim == 3 else 1
    return rgb.tobytes(), width, height, channels * width
