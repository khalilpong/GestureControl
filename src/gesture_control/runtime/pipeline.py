from __future__ import annotations

from dataclasses import dataclass
from queue import Empty, Queue
from threading import Event, Thread
from time import monotonic, sleep
from typing import Any, Protocol

from gesture_control.config import AppConfig
from gesture_control.core.state_machine import GestureStateMachine
from gesture_control.core.types import GestureAction, HandLandmarks
from gesture_control.runtime.queues import LatestValueSlot
from gesture_control.system.actions import CommandDispatcher, SystemController


class Camera(Protocol):
    def open(self) -> None:
        ...

    def read(self) -> Any | None:
        ...

    def close(self) -> None:
        ...


class HandTracker(Protocol):
    def detect(self, frame: Any, timestamp: float) -> list[HandLandmarks]:
        ...

    def close(self) -> None:
        ...


@dataclass(frozen=True)
class RuntimeSnapshot:
    running: bool
    thread_count: int
    latest_error: str | None
    state: str


class GestureRuntime:
    def __init__(
        self,
        *,
        config: AppConfig,
        camera: Camera,
        tracker: HandTracker,
        controller: SystemController,
    ) -> None:
        self.config = config
        self.camera = camera
        self.tracker = tracker
        self.dispatcher = CommandDispatcher(controller, config.command)
        self.state_machine = GestureStateMachine(config.gesture)

        self._frames: LatestValueSlot[tuple[float, Any]] = LatestValueSlot()
        self._hands: LatestValueSlot[tuple[float, list[HandLandmarks]]] = LatestValueSlot()
        self._actions: Queue[GestureAction] = Queue()
        self._stop = Event()
        self._threads: list[Thread] = []
        self._running = False
        self._latest_error: str | None = None

    def start(self) -> None:
        if self._running:
            return

        self._latest_error = None
        self._stop.clear()
        self.camera.open()
        self._threads = [
            Thread(target=self._camera_loop, name="gesture-camera", daemon=True),
            Thread(target=self._inference_loop, name="gesture-inference", daemon=True),
            Thread(target=self._gesture_loop, name="gesture-state", daemon=True),
            Thread(target=self._command_loop, name="gesture-command", daemon=True),
        ]
        self._running = True
        for thread in self._threads:
            thread.start()

    def stop(self) -> None:
        if not self._running and not self._threads:
            return

        self._stop.set()
        for thread in self._threads:
            thread.join(timeout=1.0)
        self._threads = [thread for thread in self._threads if thread.is_alive()]
        if not self._threads:
            self._running = False

        self._safe_close(self.tracker)
        self._safe_close(self.camera)

    def snapshot(self) -> RuntimeSnapshot:
        live_threads = [thread for thread in self._threads if thread.is_alive()]
        return RuntimeSnapshot(
            running=self._running and bool(live_threads),
            thread_count=len(live_threads),
            latest_error=self._latest_error,
            state=self.state_machine.state.value,
        )

    def _camera_loop(self) -> None:
        while not self._stop.is_set():
            try:
                frame = self.camera.read()
                if frame is None:
                    sleep(0.005)
                    continue
                self._frames.put((monotonic(), frame))
            except Exception as exc:  # pragma: no cover - defensive worker boundary
                self._fail(exc)

    def _inference_loop(self) -> None:
        while not self._stop.is_set():
            frame_item = self._frames.get(timeout=0.05)
            if frame_item is None:
                continue

            timestamp, frame = frame_item
            try:
                self._hands.put((timestamp, self.tracker.detect(frame, timestamp)))
            except Exception as exc:  # pragma: no cover - defensive worker boundary
                self._fail(exc)

    def _gesture_loop(self) -> None:
        while not self._stop.is_set():
            hands_item = self._hands.get(timeout=0.05)
            if hands_item is None:
                continue

            timestamp, hands = hands_item
            try:
                for action in self.state_machine.update(hands, timestamp):
                    self._actions.put(action)
            except Exception as exc:  # pragma: no cover - defensive worker boundary
                self._fail(exc)

    def _command_loop(self) -> None:
        while not self._stop.is_set():
            try:
                action = self._actions.get(timeout=0.05)
            except Empty:
                continue

            try:
                self.dispatcher.handle(action, action.timestamp)
            except Exception as exc:  # pragma: no cover - defensive worker boundary
                self._fail(exc)

    def _fail(self, exc: Exception) -> None:
        self._latest_error = f"{type(exc).__name__}: {exc}"
        self._stop.set()

    def _safe_close(self, target: object) -> None:
        close = getattr(target, "close", None)
        if close is None:
            return
        try:
            close()
        except Exception as exc:  # pragma: no cover - defensive cleanup boundary
            self._latest_error = f"{type(exc).__name__}: {exc}"
