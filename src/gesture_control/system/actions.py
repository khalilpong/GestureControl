from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol
import subprocess

from gesture_control.config import CommandConfig
from gesture_control.core.rate_limit import RateLimiter
from gesture_control.core.types import GestureAction, GestureActionType


class SystemController(Protocol):
    def scroll(self, delta: float) -> None:
        ...

    def adjust_volume(self, delta: float) -> None:
        ...

    def set_paused(self, paused: bool) -> None:
        ...


@dataclass
class DryRunSystemController:
    events: list[tuple[str, float]] = field(default_factory=list)

    def scroll(self, delta: float) -> None:
        self.events.append(("scroll", delta))

    def adjust_volume(self, delta: float) -> None:
        self.events.append(("volume", delta))

    def set_paused(self, paused: bool) -> None:
        self.events.append(("pause", 1.0 if paused else 0.0))


class MacSystemController:
    def scroll(self, delta: float) -> None:
        try:
            import pyautogui
        except ImportError as exc:
            raise RuntimeError("Scrolling requires pyautogui.") from exc

        amount = int(round(delta))
        if amount != 0:
            pyautogui.scroll(amount)

    def adjust_volume(self, delta: float) -> None:
        change = int(round(delta))
        if change == 0:
            return

        script = f"""
set currentVolume to output volume of (get volume settings)
set targetVolume to currentVolume + ({change})
if targetVolume < 0 then set targetVolume to 0
if targetVolume > 100 then set targetVolume to 100
set volume output volume targetVolume
"""
        subprocess.run(["osascript", "-e", script], check=True)

    def set_paused(self, paused: bool) -> None:
        return None


class CommandDispatcher:
    def __init__(self, controller: SystemController, config: CommandConfig) -> None:
        self.controller = controller
        self.limiter = RateLimiter(
            {
                "scroll": config.scroll_hz,
                "volume": config.volume_hz,
            }
        )

    def handle(self, action: GestureAction, timestamp: float) -> None:
        if action.kind is GestureActionType.SCROLL_DELTA:
            if self.limiter.allow("scroll", timestamp):
                self.controller.scroll(action.value)
            return

        if action.kind is GestureActionType.VOLUME_DELTA:
            if self.limiter.allow("volume", timestamp):
                self.controller.adjust_volume(action.value)
            return

        if action.kind is GestureActionType.TOGGLE_PAUSE:
            self.controller.set_paused(action.value > 0)
            return

        raise ValueError(f"Unsupported gesture action: {action.kind}")
