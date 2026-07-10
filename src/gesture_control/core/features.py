from __future__ import annotations

from math import atan2, hypot

from gesture_control.config import GestureConfig

from .types import HandLandmarks, Landmark


THUMB_TIP = 4
INDEX_TIP = 8
MIDDLE_TIP = 12
RING_TIP = 16
PINKY_TIP = 20

FINGER_TIPS = (INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP)
FINGER_PIPS = (6, 10, 14, 18)
PALM_POINTS = (0, 5, 9, 13, 17)


def palm_center(hand: HandLandmarks) -> tuple[float, float]:
    points = [hand.landmarks[index] for index in PALM_POINTS]
    x = sum(point.x for point in points) / len(points)
    y = sum(point.y for point in points) / len(points)
    return (round(x, 3), round(y, 3))


def pinch_distance(hand: HandLandmarks) -> float:
    thumb = hand.landmarks[THUMB_TIP]
    index = hand.landmarks[INDEX_TIP]
    return _distance(thumb, index)


def pinch_angle(hand: HandLandmarks) -> float:
    thumb = hand.landmarks[THUMB_TIP]
    index = hand.landmarks[INDEX_TIP]
    return atan2(index.y - thumb.y, index.x - thumb.x)


def is_fist(hand: HandLandmarks, config: GestureConfig | None = None) -> bool:
    config = config or GestureConfig()
    center = _point_from_tuple(palm_center(hand))
    scale = _hand_scale(hand)
    if scale == 0:
        return False

    fingers_curled = all(
        _distance(hand.landmarks[index], center) <= config.fist_finger_curl_ratio * scale
        for index in FINGER_TIPS
    )
    thumb = hand.landmarks[THUMB_TIP]
    thumb_curled = _distance(thumb, center) <= config.fist_thumb_curl_ratio * scale
    return fingers_curled and thumb_curled


def is_palm_open(hand: HandLandmarks, config: GestureConfig | None = None) -> bool:
    config = config or GestureConfig()
    center = _point_from_tuple(palm_center(hand))
    scale = _hand_scale(hand)
    if scale == 0:
        return False

    extended = []
    for tip_index, pip_index in zip(FINGER_TIPS, FINGER_PIPS):
        tip = hand.landmarks[tip_index]
        pip = hand.landmarks[pip_index]
        extended.append(
            tip.y < pip.y and _distance(tip, center) >= config.palm_finger_extend_ratio * scale
        )

    thumb = hand.landmarks[THUMB_TIP]
    thumb_extended = _distance(thumb, center) >= config.palm_thumb_extend_ratio * scale
    return all(extended) and thumb_extended


def _hand_scale(hand: HandLandmarks) -> float:
    xs = [point.x for point in hand.landmarks]
    ys = [point.y for point in hand.landmarks]
    return hypot(max(xs) - min(xs), max(ys) - min(ys))


def _distance(a: Landmark, b: Landmark) -> float:
    return hypot(a.x - b.x, a.y - b.y)


def _point_from_tuple(value: tuple[float, float]) -> Landmark:
    return Landmark(value[0], value[1], 0.0)
