from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal


Handedness = Literal["Left", "Right", "Unknown"]


@dataclass(frozen=True)
class Landmark:
    x: float
    y: float
    z: float = 0.0


@dataclass(frozen=True)
class HandLandmarks:
    handedness: Handedness
    landmarks: list[Landmark]
    confidence: float
    timestamp: float

    def __post_init__(self) -> None:
        if len(self.landmarks) != 21:
            raise ValueError("HandLandmarks requires exactly 21 landmarks.")


class GestureActionType(Enum):
    SCROLL_DELTA = "scroll_delta"
    VOLUME_DELTA = "volume_delta"
    TOGGLE_PAUSE = "toggle_pause"


@dataclass(frozen=True)
class GestureAction:
    kind: GestureActionType
    value: float = 0.0
    timestamp: float = 0.0
    metadata: dict[str, object] = field(default_factory=dict)


class GestureState(Enum):
    IDLE = "idle"
    STARTING = "starting"
    TRACKING = "tracking"
    FIST_SCROLL = "fist_scroll"
    PINCH_ROTATE = "pinch_rotate"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"
