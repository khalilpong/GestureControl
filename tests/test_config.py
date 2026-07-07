from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def test_default_config_matches_mvp_targets() -> None:
    from gesture_control.config import AppConfig

    config = AppConfig.default()

    assert config.camera.index == 0
    assert config.camera.width == 640
    assert config.camera.height == 480
    assert config.gesture.max_hands == 2
    assert config.gesture.palm_pause_hold_seconds == 0.8
    assert config.command.scroll_hz == 30.0
    assert config.command.volume_hz == 10.0
    assert config.debug.overlay_enabled is True


def test_core_types_are_importable_without_optional_dependencies() -> None:
    from gesture_control.core.types import GestureAction, GestureActionType, GestureState, HandLandmarks, Landmark

    hand = HandLandmarks(
        handedness="Left",
        landmarks=[Landmark(0.0, 0.0, 0.0) for _ in range(21)],
        confidence=0.9,
        timestamp=1.25,
    )
    action = GestureAction(GestureActionType.SCROLL_DELTA, value=3.5, timestamp=1.3)

    assert hand.handedness == "Left"
    assert len(hand.landmarks) == 21
    assert action.kind is GestureActionType.SCROLL_DELTA
    assert GestureState.IDLE.value == "idle"
