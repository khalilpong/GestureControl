from __future__ import annotations

from pathlib import Path
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


from gesture_control.config import AppConfig
from gesture_control.system.actions import DryRunSystemController


def test_latest_value_slot_replaces_old_value_and_consumes_latest() -> None:
    from gesture_control.runtime.queues import LatestValueSlot

    slot = LatestValueSlot[str]()

    slot.put("first")
    slot.put("second")

    assert slot.get(timeout=0.01) == "second"
    assert slot.get(timeout=0.01) is None


def test_runtime_start_stop_opens_and_closes_fake_camera_and_tracker() -> None:
    from gesture_control.runtime.pipeline import GestureRuntime

    camera = FakeCamera()
    tracker = FakeTracker()
    controller = DryRunSystemController()
    runtime = GestureRuntime(
        config=AppConfig.default(),
        camera=camera,
        tracker=tracker,
        controller=controller,
    )

    runtime.start()
    time.sleep(0.03)
    running_snapshot = runtime.snapshot()
    runtime.stop()
    stopped_snapshot = runtime.snapshot()

    assert camera.opened is True
    assert camera.closed is True
    assert tracker.closed is True
    assert running_snapshot.running is True
    assert stopped_snapshot.running is False
    assert stopped_snapshot.thread_count == 0


def test_latest_debug_frame_is_none_when_overlay_disabled() -> None:
    from dataclasses import replace

    from gesture_control.runtime.pipeline import GestureRuntime

    config = AppConfig.default()
    config = replace(config, debug=replace(config.debug, overlay_enabled=False))

    camera = FrameCamera()
    tracker = FakeTracker()
    controller = DryRunSystemController()
    runtime = GestureRuntime(
        config=config,
        camera=camera,
        tracker=tracker,
        controller=controller,
    )

    runtime.start()
    try:
        time.sleep(0.03)
        assert runtime.latest_debug_frame() is None
    finally:
        runtime.stop()


def test_latest_debug_frame_returns_frame_and_hands_when_overlay_enabled() -> None:
    from gesture_control.runtime.pipeline import GestureRuntime

    config = AppConfig.default()
    assert config.debug.overlay_enabled is True

    camera = FrameCamera()
    tracker = FakeTracker()
    controller = DryRunSystemController()
    runtime = GestureRuntime(
        config=config,
        camera=camera,
        tracker=tracker,
        controller=controller,
    )

    runtime.start()
    try:
        deadline = time.monotonic() + 1.0
        item = None
        while item is None and time.monotonic() < deadline:
            item = runtime.latest_debug_frame()
            if item is None:
                time.sleep(0.01)
    finally:
        runtime.stop()

    assert item is not None
    frame, hands = item
    assert frame == "frame-data"
    assert hands == []


class FakeCamera:
    def __init__(self) -> None:
        self.opened = False
        self.closed = False

    def open(self) -> None:
        self.opened = True

    def read(self) -> object | None:
        time.sleep(0.002)
        return None

    def close(self) -> None:
        self.closed = True


class FrameCamera:
    """Fake camera that continuously yields a sentinel frame for debug-view tests."""

    def __init__(self) -> None:
        self.opened = False
        self.closed = False

    def open(self) -> None:
        self.opened = True

    def read(self) -> object | None:
        time.sleep(0.002)
        return "frame-data"

    def close(self) -> None:
        self.closed = True


class FakeTracker:
    def __init__(self) -> None:
        self.closed = False

    def detect(self, frame: object, timestamp: float) -> list[object]:
        return []

    def close(self) -> None:
        self.closed = True
