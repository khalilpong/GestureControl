from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


from gesture_control.config import CommandConfig
from gesture_control.core.types import GestureAction, GestureActionType


def test_rate_limiter_allows_first_event_and_blocks_until_interval() -> None:
    from gesture_control.core.rate_limit import RateLimiter

    limiter = RateLimiter({"scroll": 2.0})

    assert limiter.allow("scroll", 0.0) is True
    assert limiter.allow("scroll", 0.20) is False
    assert limiter.allow("scroll", 0.50) is True


def test_dispatcher_limits_scroll_but_records_allowed_events() -> None:
    from gesture_control.system.actions import CommandDispatcher, DryRunSystemController

    controller = DryRunSystemController()
    dispatcher = CommandDispatcher(
        controller=controller,
        config=CommandConfig(scroll_hz=2.0, volume_hz=1.0),
    )

    dispatcher.handle(GestureAction(GestureActionType.SCROLL_DELTA, 10.0, 0.0), 0.0)
    dispatcher.handle(GestureAction(GestureActionType.SCROLL_DELTA, 20.0, 0.2), 0.2)
    dispatcher.handle(GestureAction(GestureActionType.SCROLL_DELTA, 30.0, 0.5), 0.5)

    assert controller.events == [("scroll", 10.0), ("scroll", 30.0)]


def test_dispatcher_limits_volume_independently_from_scroll() -> None:
    from gesture_control.system.actions import CommandDispatcher, DryRunSystemController

    controller = DryRunSystemController()
    dispatcher = CommandDispatcher(
        controller=controller,
        config=CommandConfig(scroll_hz=30.0, volume_hz=1.0),
    )

    dispatcher.handle(GestureAction(GestureActionType.VOLUME_DELTA, -2.0, 1.0), 1.0)
    dispatcher.handle(GestureAction(GestureActionType.VOLUME_DELTA, -3.0, 1.5), 1.5)
    dispatcher.handle(GestureAction(GestureActionType.SCROLL_DELTA, 4.0, 1.5), 1.5)

    assert controller.events == [("volume", -2.0), ("scroll", 4.0)]


def test_pause_toggle_is_passed_through_without_rate_limit() -> None:
    from gesture_control.system.actions import CommandDispatcher, DryRunSystemController

    controller = DryRunSystemController()
    dispatcher = CommandDispatcher(controller=controller, config=CommandConfig())

    dispatcher.handle(GestureAction(GestureActionType.TOGGLE_PAUSE, 1.0, 2.0), 2.0)
    dispatcher.handle(GestureAction(GestureActionType.TOGGLE_PAUSE, 0.0, 2.1), 2.1)

    assert controller.events == [("pause", 1.0), ("pause", 0.0)]
