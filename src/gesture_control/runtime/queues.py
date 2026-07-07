from __future__ import annotations

from threading import Condition
from time import monotonic
from typing import Generic, TypeVar


T = TypeVar("T")


class LatestValueSlot(Generic[T]):
    def __init__(self) -> None:
        self._condition = Condition()
        self._value: T | None = None
        self._has_value = False

    def put(self, value: T) -> None:
        with self._condition:
            self._value = value
            self._has_value = True
            self._condition.notify()

    def get(self, timeout: float | None = None) -> T | None:
        deadline = None if timeout is None else monotonic() + timeout
        with self._condition:
            while not self._has_value:
                if timeout is None:
                    self._condition.wait()
                    continue

                remaining = deadline - monotonic() if deadline is not None else 0.0
                if remaining <= 0:
                    return None
                self._condition.wait(remaining)

            value = self._value
            self._value = None
            self._has_value = False
            return value
