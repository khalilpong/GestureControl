from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def test_default_model_path_resolves_to_repo_model_file() -> None:
    from gesture_control.vision.mediapipe_hands import default_model_path

    path = default_model_path()

    assert path is not None
    assert path == ROOT / "models" / "hand_landmarker.task"
    assert path.exists()


def test_default_model_path_honors_env_override(monkeypatch, tmp_path: Path) -> None:
    from gesture_control.vision.mediapipe_hands import default_model_path

    override = tmp_path / "custom.task"
    monkeypatch.setenv("GESTURE_CONTROL_HAND_MODEL", str(override))

    assert default_model_path() == override


def test_tracker_raises_clear_error_when_model_missing(tmp_path: Path) -> None:
    from gesture_control.config import GestureConfig
    from gesture_control.vision.mediapipe_hands import MediaPipeHandTracker

    tracker = MediaPipeHandTracker(GestureConfig(), model_path=tmp_path / "missing.task")

    try:
        tracker._ensure_open()
    except RuntimeError as exc:
        assert "model" in str(exc).lower()
    else:
        raise AssertionError("Expected RuntimeError for missing model file.")


def test_detect_returns_no_hands_on_blank_frame() -> None:
    import numpy as np

    from gesture_control.config import GestureConfig
    from gesture_control.vision.mediapipe_hands import MediaPipeHandTracker

    tracker = MediaPipeHandTracker(GestureConfig())
    frame = np.zeros((480, 640, 3), dtype="uint8")

    try:
        hands = tracker.detect(frame, 1.0)
        assert hands == []
    finally:
        tracker.close()
