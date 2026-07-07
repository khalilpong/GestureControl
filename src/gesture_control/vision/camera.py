from __future__ import annotations

from gesture_control.config import CameraConfig


class OpenCVCamera:
    def __init__(self, config: CameraConfig) -> None:
        self.config = config
        self._cv2 = None
        self._capture = None

    def open(self) -> None:
        try:
            import cv2
        except ImportError as exc:
            raise RuntimeError("OpenCVCamera requires opencv-python.") from exc

        self._cv2 = cv2
        backend = getattr(cv2, "CAP_AVFOUNDATION", 0)
        capture = cv2.VideoCapture(self.config.index, backend)
        if not capture.isOpened():
            capture = cv2.VideoCapture(self.config.index)
        if not capture.isOpened():
            raise RuntimeError(f"Could not open camera index {self.config.index}.")

        capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.width)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.height)
        capture.set(cv2.CAP_PROP_FPS, self.config.fps)
        self._capture = capture

    def read(self):
        if self._capture is None:
            raise RuntimeError("Camera is not open.")
        ok, frame = self._capture.read()
        if not ok:
            return None
        return frame

    def close(self) -> None:
        if self._capture is not None:
            self._capture.release()
            self._capture = None
