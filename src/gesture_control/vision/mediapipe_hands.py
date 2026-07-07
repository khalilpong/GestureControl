from __future__ import annotations

from typing import Any

from gesture_control.config import GestureConfig
from gesture_control.core.types import HandLandmarks, Landmark


class MediaPipeHandTracker:
    def __init__(self, config: GestureConfig) -> None:
        self.config = config
        self._cv2 = None
        self._hands = None

    def _ensure_open(self) -> None:
        if self._hands is not None:
            return

        try:
            import cv2
            import mediapipe as mp
        except ImportError as exc:
            raise RuntimeError("MediaPipeHandTracker requires mediapipe and opencv-python.") from exc

        self._cv2 = cv2
        self._hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=self.config.max_hands,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

    def detect(self, frame: Any, timestamp: float) -> list[HandLandmarks]:
        self._ensure_open()
        rgb = self._cv2.cvtColor(frame, self._cv2.COLOR_BGR2RGB)
        results = self._hands.process(rgb)
        if not results.multi_hand_landmarks:
            return []

        handedness = results.multi_handedness or []
        output: list[HandLandmarks] = []
        for index, hand_landmarks in enumerate(results.multi_hand_landmarks):
            classification = handedness[index].classification[0] if index < len(handedness) else None
            label = classification.label if classification is not None else "Unknown"
            score = float(classification.score) if classification is not None else 0.0
            output.append(
                HandLandmarks(
                    handedness=label,
                    landmarks=[
                        Landmark(float(point.x), float(point.y), float(point.z))
                        for point in hand_landmarks.landmark
                    ],
                    confidence=score,
                    timestamp=timestamp,
                )
            )
        return output

    def close(self) -> None:
        if self._hands is not None:
            self._hands.close()
            self._hands = None
