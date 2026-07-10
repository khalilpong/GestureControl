from __future__ import annotations

from math import pi

from gesture_control.config import GestureConfig

from .features import is_fist, is_palm_open, palm_center, pinch_angle, pinch_distance
from .types import GestureAction, GestureActionType, GestureState, HandLandmarks


class GestureStateMachine:
    def __init__(self, config: GestureConfig | None = None) -> None:
        self.config = config or GestureConfig()
        self.state = GestureState.IDLE
        self.paused = False

        self._candidate: str | None = None
        self._candidate_since: float | None = None
        self._last_scroll_y: float | None = None
        self._last_pinch_angle: float | None = None

        self._palm_since: float | None = None
        self._palm_consumed = False
        self._last_pause_toggle = float("-inf")

    def update(self, hands: list[HandLandmarks], timestamp: float) -> list[GestureAction]:
        actions = self._handle_palm_pause(hands, timestamp)
        if actions:
            return actions

        if self.paused:
            self.state = GestureState.PAUSED
            self._clear_candidate()
            return []

        left = _find_hand(hands, "Left")
        right = _find_hand(hands, "Right")

        if self.state is GestureState.FIST_SCROLL:
            return self._update_fist_scroll(left, timestamp)
        if self.state is GestureState.PINCH_ROTATE:
            return self._update_pinch_rotate(right, timestamp)

        if left is not None and is_fist(left, self.config):
            return self._hold_then_enter_fist(left, timestamp)
        if right is not None and _is_pinched(right, self.config):
            return self._hold_then_enter_pinch(right, timestamp)

        self.state = GestureState.TRACKING if hands else GestureState.IDLE
        self._clear_candidate()
        return []

    def _handle_palm_pause(
        self, hands: list[HandLandmarks], timestamp: float
    ) -> list[GestureAction]:
        palm = next((hand for hand in hands if is_palm_open(hand, self.config)), None)
        if palm is None:
            self._palm_since = None
            self._palm_consumed = False
            return []

        if self._palm_since is None:
            self._palm_since = timestamp
            return []

        held_long_enough = (
            timestamp - self._palm_since >= self.config.palm_pause_hold_seconds
        )
        cooled_down = (
            timestamp - self._last_pause_toggle >= self.config.pause_cooldown_seconds
        )
        if not held_long_enough or not cooled_down or self._palm_consumed:
            return []

        self.paused = not self.paused
        self.state = GestureState.PAUSED if self.paused else GestureState.TRACKING
        self._last_pause_toggle = timestamp
        self._palm_consumed = True
        self._clear_candidate()
        return [
            GestureAction(
                GestureActionType.TOGGLE_PAUSE,
                value=1.0 if self.paused else 0.0,
                timestamp=timestamp,
            )
        ]

    def _hold_then_enter_fist(
        self, hand: HandLandmarks, timestamp: float
    ) -> list[GestureAction]:
        if not self._candidate_active("fist", timestamp):
            self.state = GestureState.TRACKING
            return []

        self.state = GestureState.FIST_SCROLL
        self._last_scroll_y = palm_center(hand)[1]
        return []

    def _hold_then_enter_pinch(
        self, hand: HandLandmarks, timestamp: float
    ) -> list[GestureAction]:
        if not self._candidate_active("pinch", timestamp):
            self.state = GestureState.TRACKING
            return []

        self.state = GestureState.PINCH_ROTATE
        self._last_pinch_angle = pinch_angle(hand)
        return []

    def _update_fist_scroll(
        self, hand: HandLandmarks | None, timestamp: float
    ) -> list[GestureAction]:
        if hand is None or not is_fist(hand, self.config):
            self.state = GestureState.TRACKING
            self._last_scroll_y = None
            self._clear_candidate()
            return []

        current_y = palm_center(hand)[1]
        if self._last_scroll_y is None:
            self._last_scroll_y = current_y
            return []

        delta_y = current_y - self._last_scroll_y
        if abs(delta_y) < self.config.deadzone:
            return []

        self._last_scroll_y = current_y
        return [
            GestureAction(
                GestureActionType.SCROLL_DELTA,
                value=delta_y * self.config.scroll_sensitivity,
                timestamp=timestamp,
            )
        ]

    def _update_pinch_rotate(
        self, hand: HandLandmarks | None, timestamp: float
    ) -> list[GestureAction]:
        if hand is None or not _is_pinched(hand, self.config):
            self.state = GestureState.TRACKING
            self._last_pinch_angle = None
            self._clear_candidate()
            return []

        current_angle = pinch_angle(hand)
        if self._last_pinch_angle is None:
            self._last_pinch_angle = current_angle
            return []

        delta_angle = _normalize_angle(current_angle - self._last_pinch_angle)
        if abs(delta_angle) < self.config.deadzone:
            return []

        self._last_pinch_angle = current_angle
        return [
            GestureAction(
                GestureActionType.VOLUME_DELTA,
                value=delta_angle / self.config.volume_sensitivity,
                timestamp=timestamp,
            )
        ]

    def _candidate_active(self, name: str, timestamp: float) -> bool:
        if self._candidate != name:
            self._candidate = name
            self._candidate_since = timestamp
            return False

        if self._candidate_since is None:
            self._candidate_since = timestamp
            return False

        hold = (
            self.config.fist_hold_seconds
            if name == "fist"
            else self.config.pinch_hold_seconds
        )
        return timestamp - self._candidate_since >= hold

    def _clear_candidate(self) -> None:
        self._candidate = None
        self._candidate_since = None


def _find_hand(hands: list[HandLandmarks], handedness: str) -> HandLandmarks | None:
    return next(
        (hand for hand in hands if hand.handedness == handedness and hand.confidence > 0.2),
        None,
    )


def _is_pinched(hand: HandLandmarks, config: GestureConfig) -> bool:
    return pinch_distance(hand) <= config.pinch_distance_threshold


def _normalize_angle(value: float) -> float:
    while value > pi:
        value -= 2 * pi
    while value < -pi:
        value += 2 * pi
    return value
