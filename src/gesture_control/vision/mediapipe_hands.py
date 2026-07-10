from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from gesture_control.config import GestureConfig
from gesture_control.core.types import HandLandmarks, Landmark


MODEL_FILENAME = "hand_landmarker.task"


def default_model_path() -> Path | None:
    """Resolve models/hand_landmarker.task across dev, editable-install, and PyInstaller runs."""

    env_override = os.environ.get("GESTURE_CONTROL_HAND_MODEL")
    if env_override:
        return Path(env_override)

    if getattr(sys, "frozen", False):
        bundled = Path(getattr(sys, "_MEIPASS", "")) / "models" / MODEL_FILENAME
        if bundled.exists():
            return bundled

    repo_model = Path(__file__).resolve().parents[3] / "models" / MODEL_FILENAME
    if repo_model.exists():
        return repo_model

    return None


class MediaPipeHandTracker:
    """Hand landmark detector built on MediaPipe's Tasks API.

    Older mediapipe releases exposed a `mediapipe.solutions.hands` API that
    worked directly on frames with no external model file. That API has been
    removed from current mediapipe packages (mp.solutions no longer exists),
    so this uses the replacement Tasks API (`HandLandmarker`), which loads a
    `.task` model bundle from disk instead.
    """

    def __init__(self, config: GestureConfig, *, model_path: str | Path | None = None) -> None:
        self.config = config
        self._model_path = Path(model_path) if model_path is not None else None
        self._cv2 = None
        self._mp = None
        self._detector = None
        self._last_timestamp_ms = -1

    def _ensure_open(self) -> None:
        if self._detector is not None:
            return

        try:
            import cv2
            import mediapipe as mp
            from mediapipe.tasks.python import vision
            from mediapipe.tasks.python.core.base_options import BaseOptions
        except ImportError as exc:
            raise RuntimeError("MediaPipeHandTracker requires mediapipe and opencv-python.") from exc

        model_path = self._model_path or default_model_path()
        if model_path is None or not Path(model_path).exists():
            raise RuntimeError(
                "Hand landmark model not found. Expected models/hand_landmarker.task "
                "next to the project, or set GESTURE_CONTROL_HAND_MODEL to a valid "
                "path to a MediaPipe HandLandmarker .task file."
            )

        self._cv2 = cv2
        self._mp = mp
        options = vision.HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(model_path)),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=self.config.max_hands,
            min_hand_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self._detector = vision.HandLandmarker.create_from_options(options)

    def detect(self, frame: Any, timestamp: float) -> list[HandLandmarks]:
        self._ensure_open()
        rgb = self._cv2.cvtColor(frame, self._cv2.COLOR_BGR2RGB)
        mp_image = self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=rgb)

        # detect_for_video requires strictly increasing millisecond timestamps.
        timestamp_ms = max(int(timestamp * 1000), self._last_timestamp_ms + 1)
        self._last_timestamp_ms = timestamp_ms

        result = self._detector.detect_for_video(mp_image, timestamp_ms)
        if not result.hand_landmarks:
            return []

        output: list[HandLandmarks] = []
        for index, landmarks in enumerate(result.hand_landmarks):
            categories = result.handedness[index] if index < len(result.handedness) else []
            label = categories[0].category_name if categories else "Unknown"
            score = float(categories[0].score) if categories else 0.0
            output.append(
                HandLandmarks(
                    handedness=label,
                    landmarks=[
                        Landmark(float(point.x), float(point.y), float(point.z))
                        for point in landmarks
                    ],
                    confidence=score,
                    timestamp=timestamp,
                )
            )
        return output

    def close(self) -> None:
        if self._detector is not None:
            self._detector.close()
            self._detector = None
