from __future__ import annotations


class RateLimiter:
    def __init__(self, rates_hz: dict[str, float]) -> None:
        self._rates_hz = rates_hz
        self._last_allowed: dict[str, float] = {}

    def allow(self, key: str, timestamp: float) -> bool:
        rate = self._rates_hz.get(key)
        if rate is None or rate <= 0:
            return True

        previous = self._last_allowed.get(key)
        interval = 1.0 / rate
        if previous is not None and timestamp - previous < interval:
            return False

        self._last_allowed[key] = timestamp
        return True
