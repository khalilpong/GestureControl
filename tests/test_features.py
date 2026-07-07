from __future__ import annotations

from math import isclose
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


from gesture_control.core.types import HandLandmarks, Landmark


def make_hand(*, handedness: str = "Left", open_palm: bool = True, pinched: bool = False) -> HandLandmarks:
    points = [Landmark(0.5, 0.8, 0.0) for _ in range(21)]

    points[0] = Landmark(0.5, 0.9)
    for index, x in ((5, 0.35), (9, 0.5), (13, 0.65), (17, 0.8)):
        points[index] = Landmark(x, 0.62)

    if open_palm:
        chains = {
            1: [(0.25, 0.65), (0.2, 0.52), (0.16, 0.43), (0.12, 0.35)],
            5: [(0.35, 0.62), (0.34, 0.43), (0.33, 0.28), (0.32, 0.14)],
            9: [(0.5, 0.62), (0.5, 0.38), (0.5, 0.22), (0.5, 0.08)],
            13: [(0.65, 0.62), (0.66, 0.43), (0.67, 0.28), (0.68, 0.14)],
            17: [(0.8, 0.62), (0.82, 0.45), (0.84, 0.31), (0.86, 0.18)],
        }
    else:
        chains = {
            1: [(0.38, 0.68), (0.44, 0.66), (0.48, 0.65), (0.51, 0.65)],
            5: [(0.35, 0.62), (0.4, 0.64), (0.46, 0.66), (0.5, 0.66)],
            9: [(0.5, 0.62), (0.52, 0.64), (0.53, 0.66), (0.52, 0.67)],
            13: [(0.65, 0.62), (0.62, 0.64), (0.58, 0.66), (0.54, 0.67)],
            17: [(0.8, 0.62), (0.72, 0.64), (0.64, 0.66), (0.56, 0.67)],
        }

    for start, chain in chains.items():
        for offset, (x, y) in enumerate(chain):
            points[start + offset] = Landmark(x, y)

    if pinched:
        points[4] = Landmark(0.42, 0.28)
        points[8] = Landmark(0.44, 0.28)

    return HandLandmarks(
        handedness=handedness, landmarks=points, confidence=0.95, timestamp=2.0
    )


def test_fist_and_open_palm_are_distinguished() -> None:
    from gesture_control.core.features import is_fist, is_palm_open

    fist = make_hand(open_palm=False)
    open_hand = make_hand(open_palm=True)

    assert is_fist(fist) is True
    assert is_palm_open(fist) is False
    assert is_fist(open_hand) is False
    assert is_palm_open(open_hand) is True


def test_pinch_features_use_thumb_and_index_tip() -> None:
    from gesture_control.core.features import pinch_angle, pinch_distance

    open_hand = make_hand(open_palm=True, pinched=False)
    pinched_hand = make_hand(open_palm=True, pinched=True)

    assert pinch_distance(pinched_hand) < pinch_distance(open_hand)
    assert isclose(pinch_angle(pinched_hand), 0.0, abs_tol=0.001)


def test_palm_center_uses_stable_palm_points() -> None:
    from gesture_control.core.features import palm_center

    hand = make_hand(open_palm=True)

    assert palm_center(hand) == (0.56, 0.676)
