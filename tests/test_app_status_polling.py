from __future__ import annotations

from pathlib import Path
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def test_poll_runtime_status_surfaces_background_thread_error() -> None:
    from PySide6.QtWidgets import QApplication

    from gesture_control.app import GestureControlWindow
    from gesture_control.config import AppConfig
    from gesture_control.runtime.pipeline import GestureRuntime
    from gesture_control.system.actions import DryRunSystemController

    QApplication.instance() or QApplication(sys.argv)

    window = GestureControlWindow(config=AppConfig.default())
    window.runtime = GestureRuntime(
        config=AppConfig.default(),
        camera=_FailingCamera(),
        tracker=_NoopTracker(),
        controller=DryRunSystemController(),
    )
    window._set_running_ui(True)
    window.runtime.start()

    try:
        deadline = time.monotonic() + 1.0
        while window.runtime.snapshot().latest_error is None and time.monotonic() < deadline:
            time.sleep(0.01)

        window._poll_runtime_status()

        assert "Error" in window.status_label.text()
        assert window.start_button.isEnabled() is True
        assert window.stop_button.isEnabled() is False
    finally:
        window.runtime.stop()


class _FailingCamera:
    def open(self) -> None:
        return None

    def read(self) -> object:
        raise RuntimeError("camera exploded")

    def close(self) -> None:
        return None


class _NoopTracker:
    def detect(self, frame: object, timestamp: float) -> list[object]:
        return []

    def close(self) -> None:
        return None
