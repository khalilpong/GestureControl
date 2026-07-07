from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


from gesture_control.core.types import GestureActionType, GestureState, HandLandmarks, Landmark


def make_fist(*, handedness: str = "Left", dy: float = 0.0) -> HandLandmarks:
    base = [
        (0.5, 0.9),
        (0.38, 0.68),
        (0.44, 0.66),
        (0.48, 0.65),
        (0.51, 0.65),
        (0.35, 0.62),
        (0.4, 0.64),
        (0.46, 0.66),
        (0.5, 0.66),
        (0.5, 0.62),
        (0.52, 0.64),
        (0.53, 0.66),
        (0.52, 0.67),
        (0.65, 0.62),
        (0.62, 0.64),
        (0.58, 0.66),
        (0.54, 0.67),
        (0.8, 0.62),
        (0.72, 0.64),
        (0.64, 0.66),
        (0.56, 0.67),
    ]
    return _hand(base, handedness=handedness, dy=dy)


def make_open_palm(*, handedness: str = "Left") -> HandLandmarks:
    base = [
        (0.5, 0.9),
        (0.25, 0.65),
        (0.2, 0.52),
        (0.16, 0.43),
        (0.12, 0.35),
        (0.35, 0.62),
        (0.34, 0.43),
        (0.33, 0.28),
        (0.32, 0.14),
        (0.5, 0.62),
        (0.5, 0.38),
        (0.5, 0.22),
        (0.5, 0.08),
        (0.65, 0.62),
        (0.66, 0.43),
        (0.67, 0.28),
        (0.68, 0.14),
        (0.8, 0.62),
        (0.82, 0.45),
        (0.84, 0.31),
        (0.86, 0.18),
    ]
    return _hand(base, handedness=handedness)


def make_pinched(*, angle_variant: str = "flat") -> HandLandmarks:
    hand = make_open_palm(handedness="Right")
    points = list(hand.landmarks)
    points[4] = Landmark(0.42, 0.28)
    if angle_variant == "flat":
        points[8] = Landmark(0.44, 0.28)
    elif angle_variant == "up":
        points[8] = Landmark(0.42, 0.22)
    else:
        raise ValueError(angle_variant)
    return replace(hand, landmarks=points)


def test_left_fist_scroll_emits_delta_after_hold() -> None:
    from gesture_control.core.state_machine import GestureStateMachine

    machine = GestureStateMachine()

    assert machine.update([make_fist()], timestamp=0.0) == []
    assert machine.update([make_fist()], timestamp=0.16) == []
    actions = machine.update([make_fist(dy=0.04)], timestamp=0.20)

    assert machine.state is GestureState.FIST_SCROLL
    assert [action.kind for action in actions] == [GestureActionType.SCROLL_DELTA]
    assert actions[0].value > 0


def test_right_pinch_rotation_emits_volume_delta_after_hold() -> None:
    from gesture_control.core.state_machine import GestureStateMachine

    machine = GestureStateMachine()

    assert machine.update([make_pinched(angle_variant="flat")], timestamp=0.0) == []
    assert machine.update([make_pinched(angle_variant="flat")], timestamp=0.16) == []
    actions = machine.update([make_pinched(angle_variant="up")], timestamp=0.20)

    assert machine.state is GestureState.PINCH_ROTATE
    assert [action.kind for action in actions] == [GestureActionType.VOLUME_DELTA]
    assert actions[0].value < 0


def test_open_palm_toggles_pause_after_hold_and_blocks_scroll() -> None:
    from gesture_control.core.state_machine import GestureStateMachine

    machine = GestureStateMachine()

    assert machine.update([make_open_palm()], timestamp=0.0) == []
    actions = machine.update([make_open_palm()], timestamp=0.81)

    assert [action.kind for action in actions] == [GestureActionType.TOGGLE_PAUSE]
    assert machine.state is GestureState.PAUSED

    assert machine.update([make_fist()], timestamp=1.2) == []
    assert machine.state is GestureState.PAUSED


def test_pause_toggle_requires_release_and_cooldown() -> None:
    from gesture_control.core.state_machine import GestureStateMachine

    machine = GestureStateMachine()

    machine.update([make_open_palm()], timestamp=0.0)
    first = machine.update([make_open_palm()], timestamp=0.81)
    repeated = machine.update([make_open_palm()], timestamp=1.7)
    machine.update([], timestamp=1.8)
    machine.update([make_open_palm()], timestamp=1.9)
    second = machine.update([make_open_palm()], timestamp=2.71)

    assert [action.kind for action in first] == [GestureActionType.TOGGLE_PAUSE]
    assert repeated == []
    assert [action.kind for action in second] == [GestureActionType.TOGGLE_PAUSE]
    assert machine.state is GestureState.TRACKING


def _hand(points: list[tuple[float, float]], *, handedness: str, dy: float = 0.0) -> HandLandmarks:
    return HandLandmarks(
        handedness=handedness,
        landmarks=[Landmark(x, y + dy) for x, y in points],
        confidence=0.95,
        timestamp=0.0,
    )
