from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable
import sys

from gesture_control.config import AppConfig, load_default_config


@dataclass(frozen=True)
class QtModules:
    widgets: Any
    gui: Any
    core: Any


class FloatingStopWindow:
    def __init__(
        self,
        *,
        qt: QtModules | None = None,
        on_stop: Callable[[], None] | None = None,
    ) -> None:
        self.qt = qt or _load_qt()
        self._on_stop = on_stop or (lambda: None)
        self.widget = self.qt.widgets.QWidget()
        self.widget.setWindowTitle("Gesture Control")
        self.widget.setWindowFlags(
            self.qt.core.Qt.WindowType.Tool
            | self.qt.core.Qt.WindowType.WindowStaysOnTopHint
        )

        layout = self.qt.widgets.QHBoxLayout(self.widget)
        self.status = self.qt.widgets.QLabel("Gesture: Off")
        self.stop_button = self.qt.widgets.QPushButton("Stop")
        self.stop_button.clicked.connect(self._on_stop)
        layout.addWidget(self.status)
        layout.addWidget(self.stop_button)
        self.widget.setFixedSize(220, 54)

    def set_status(self, text: str) -> None:
        self.status.setText(text)

    def show(self) -> None:
        screen = self.qt.widgets.QApplication.primaryScreen()
        if screen is not None:
            geometry = screen.availableGeometry()
            self.widget.move(geometry.right() - self.widget.width() - 24, geometry.top() + 24)
        self.widget.show()

    def hide(self) -> None:
        self.widget.hide()


class DebugPreviewWindow:
    """Live camera + hand-skeleton overlay window for real-world gesture tuning."""

    def __init__(
        self,
        *,
        qt: QtModules | None = None,
        runtime_provider: Callable[[], Any | None],
        interval_ms: int = 66,
    ) -> None:
        self.qt = qt or _load_qt()
        self._runtime_provider = runtime_provider

        self.widget = self.qt.widgets.QWidget()
        self.widget.setWindowTitle("Gesture Control - Debug View")
        self.widget.resize(480, 360)

        self.label = self.qt.widgets.QLabel("Waiting for camera frames...")
        self.label.setAlignment(self.qt.core.Qt.AlignmentFlag.AlignCenter)
        self.label.setMinimumSize(320, 240)

        layout = self.qt.widgets.QVBoxLayout(self.widget)
        layout.addWidget(self.label)

        self.timer = self.qt.core.QTimer(self.widget)
        self.timer.setInterval(interval_ms)
        self.timer.timeout.connect(self._refresh)

    def show(self) -> None:
        self._place_next_to_primary_screen()
        self.widget.show()
        self.widget.raise_()
        self.widget.activateWindow()
        self.timer.start()

    def hide(self) -> None:
        self.timer.stop()
        self.widget.hide()

    def _place_next_to_primary_screen(self) -> None:
        screen = self.qt.widgets.QApplication.primaryScreen()
        if screen is None:
            return
        geometry = screen.availableGeometry()
        self.widget.move(geometry.left() + 24, geometry.top() + 24)

    def _refresh(self) -> None:
        runtime = self._runtime_provider()
        if runtime is None:
            return

        item = runtime.latest_debug_frame()
        if item is None:
            return

        frame, hands = item
        status = {"state": runtime.state_machine.state.value, "hands": len(hands)}
        pixmap = _frame_to_pixmap(self.qt, frame, hands, status)
        if pixmap is None:
            return

        self.label.setPixmap(
            pixmap.scaled(
                self.label.size(),
                self.qt.core.Qt.AspectRatioMode.KeepAspectRatio,
                self.qt.core.Qt.TransformationMode.SmoothTransformation,
            )
        )


class GestureControlWindow:
    def __init__(
        self,
        *,
        config: AppConfig | None = None,
        qt: QtModules | None = None,
    ) -> None:
        self.qt = qt or _load_qt()
        self.config = config or load_default_config()
        self.runtime = None

        self.window = self.qt.widgets.QMainWindow()
        self.window.setWindowTitle("Gesture Control")
        self.window.resize(420, 260)
        self.status_label = self.qt.widgets.QLabel("Status: Idle")
        self.detail_label = self.qt.widgets.QLabel(_config_summary(self.config))
        self.detail_label.setWordWrap(True)

        self.start_button = self.qt.widgets.QPushButton("Start")
        self.pause_button = self.qt.widgets.QPushButton("Pause")
        self.stop_button = self.qt.widgets.QPushButton("Stop")
        self.quit_button = self.qt.widgets.QPushButton("Quit")
        self.debug_button = self.qt.widgets.QPushButton("Debug View")
        self.debug_button.setCheckable(True)
        self.debug_button.setEnabled(self.config.debug.overlay_enabled)

        self.start_button.clicked.connect(self.start)
        self.pause_button.clicked.connect(self.pause)
        self.stop_button.clicked.connect(self.stop)
        self.quit_button.clicked.connect(self.quit)
        self.debug_button.toggled.connect(self._toggle_debug_view)

        root = self.qt.widgets.QWidget()
        layout = self.qt.widgets.QVBoxLayout(root)
        layout.addWidget(self.status_label)
        layout.addWidget(self.detail_label)

        button_row = self.qt.widgets.QHBoxLayout()
        for button in (
            self.start_button,
            self.pause_button,
            self.stop_button,
            self.quit_button,
            self.debug_button,
        ):
            button_row.addWidget(button)
        layout.addLayout(button_row)
        self.window.setCentralWidget(root)

        self.floating = FloatingStopWindow(qt=self.qt, on_stop=self.stop)
        self.debug_window = DebugPreviewWindow(qt=self.qt, runtime_provider=lambda: self.runtime)
        self.tray = self._create_tray()
        self._set_running_ui(False)

        self.status_timer = self.qt.core.QTimer(self.window)
        self.status_timer.setInterval(400)
        self.status_timer.timeout.connect(self._poll_runtime_status)

    def show(self) -> None:
        self._center_on_primary_screen()
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()
        if self.tray is not None:
            self.tray.show()

    def _center_on_primary_screen(self) -> None:
        screen = self.qt.widgets.QApplication.primaryScreen()
        if screen is None:
            return
        geometry = screen.availableGeometry()
        frame = self.window.frameGeometry()
        frame.moveCenter(geometry.center())
        self.window.move(frame.topLeft())

    def start(self) -> None:
        if self.runtime is None:
            self.runtime = _build_runtime(self.config)
        try:
            self.runtime.start()
        except Exception as exc:
            self._set_status(f"Status: Error - {exc}")
            return

        self._set_status("Status: Running")
        self._set_running_ui(True)
        self.floating.set_status("Gesture: On")
        self.floating.show()
        self.status_timer.start()

    def pause(self) -> None:
        if self.runtime is None:
            self._set_status("Status: Idle")
            return

        self.runtime.state_machine.paused = not self.runtime.state_machine.paused
        paused = self.runtime.state_machine.paused
        self._set_status("Status: Paused" if paused else "Status: Running")
        self.floating.set_status("Gesture: Paused" if paused else "Gesture: On")

    def stop(self) -> None:
        self.status_timer.stop()
        if self.runtime is not None:
            self.runtime.stop()
        self._set_status("Status: Stopped")
        self._set_running_ui(False)
        self.floating.hide()
        self.debug_button.setChecked(False)

    def _poll_runtime_status(self) -> None:
        if self.runtime is None:
            return

        snapshot = self.runtime.snapshot()
        if snapshot.latest_error:
            self._set_status(f"Status: Error - {snapshot.latest_error}")
            self.floating.set_status("Gesture: Error")
            self._set_running_ui(False)
            self.floating.hide()
            self.debug_button.setChecked(False)
            self.status_timer.stop()
            return

        if not snapshot.running:
            self._set_status("Status: Stopped (background thread ended unexpectedly)")
            self.floating.set_status("Gesture: Off")
            self._set_running_ui(False)
            self.floating.hide()
            self.debug_button.setChecked(False)
            self.status_timer.stop()
            return

        if self.runtime.state_machine.paused:
            self._set_status("Status: Paused")
            self.floating.set_status("Gesture: Paused")
        else:
            self._set_status(f"Status: Running ({snapshot.state})")
            self.floating.set_status("Gesture: On")

    def quit(self) -> None:
        self.stop()
        self.qt.widgets.QApplication.quit()

    def _create_tray(self):
        if not self.qt.widgets.QSystemTrayIcon.isSystemTrayAvailable():
            return None

        icon = self.window.style().standardIcon(
            self.qt.widgets.QStyle.StandardPixmap.SP_ComputerIcon
        )
        tray = self.qt.widgets.QSystemTrayIcon(icon, self.window)
        tray.setToolTip("Gesture Control")
        menu = self.qt.widgets.QMenu()
        menu.addAction("Start", self.start)
        menu.addAction("Pause", self.pause)
        menu.addAction("Stop", self.stop)
        menu.addSeparator()
        menu.addAction("Quit", self.quit)
        tray.setContextMenu(menu)
        return tray

    def _toggle_debug_view(self, checked: bool) -> None:
        if checked:
            self.debug_window.show()
        else:
            self.debug_window.hide()

    def _set_status(self, text: str) -> None:
        self.status_label.setText(text)

    def _set_running_ui(self, running: bool) -> None:
        self.start_button.setEnabled(not running)
        self.pause_button.setEnabled(running)
        self.stop_button.setEnabled(running)


def run_app() -> int:
    try:
        qt = _load_qt()
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 1

    app = qt.widgets.QApplication.instance() or qt.widgets.QApplication(sys.argv)
    window = GestureControlWindow(qt=qt)
    window.show()
    print(
        "Gesture Control window opened. If you don't see it, check Mission "
        "Control / other desktop Spaces, or press Cmd+Tab to find \"Python\".",
        flush=True,
    )
    return int(app.exec())


def _load_qt() -> QtModules:
    try:
        from PySide6 import QtCore, QtGui, QtWidgets
    except ImportError as exc:
        raise RuntimeError("Gesture Control app requires PySide6.") from exc
    return QtModules(widgets=QtWidgets, gui=QtGui, core=QtCore)


def _build_runtime(config: AppConfig):
    from gesture_control.runtime.pipeline import GestureRuntime
    from gesture_control.system.actions import MacSystemController
    from gesture_control.vision.camera import OpenCVCamera
    from gesture_control.vision.mediapipe_hands import MediaPipeHandTracker

    return GestureRuntime(
        config=config,
        camera=OpenCVCamera(config.camera),
        tracker=MediaPipeHandTracker(config.gesture),
        controller=MacSystemController(),
    )


def _frame_to_pixmap(qt: QtModules, frame: Any, hands: list[Any], status: dict[str, object]) -> Any | None:
    from gesture_control.diagnostics.overlay import draw_overlay, to_rgb_bytes

    annotated = draw_overlay(frame.copy() if hasattr(frame, "copy") else frame, hands, status)
    converted = to_rgb_bytes(annotated)
    if converted is None:
        return None

    data, width, height, bytes_per_line = converted
    image = qt.gui.QImage(data, width, height, bytes_per_line, qt.gui.QImage.Format.Format_RGB888)
    return qt.gui.QPixmap.fromImage(image.copy())


def _config_summary(config: AppConfig) -> str:
    return (
        f"Camera {config.camera.index} at {config.camera.width}x{config.camera.height}; "
        f"scroll {config.command.scroll_hz:.0f}Hz; "
        f"volume {config.command.volume_hz:.0f}Hz; "
        f"overlay {'on' if config.debug.overlay_enabled else 'off'}."
    )
