from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def test_default_config_matches_mvp_targets() -> None:
    from gesture_control.config import AppConfig

    config = AppConfig.default()

    assert config.camera.index == 0
    assert config.camera.width == 640
    assert config.camera.height == 480
    assert config.gesture.max_hands == 2
    assert config.gesture.palm_pause_hold_seconds == 0.8
    assert config.command.scroll_hz == 30.0
    assert config.command.volume_hz == 10.0
    assert config.debug.overlay_enabled is True


def test_load_config_merges_yaml_overrides(tmp_path: Path) -> None:
    from gesture_control.config import load_config

    config_file = tmp_path / "custom.yaml"
    config_file.write_text(
        "camera:\n  index: 1\n  fps: 30\n"
        "gesture:\n  scroll_sensitivity: 900.0\n",
        encoding="utf-8",
    )

    config = load_config(config_file)

    assert config.camera.index == 1
    assert config.camera.fps == 30
    assert config.camera.width == 640  # untouched fields keep their defaults
    assert config.gesture.scroll_sensitivity == 900.0


def test_load_config_rejects_unknown_keys(tmp_path: Path) -> None:
    from gesture_control.config import load_config

    config_file = tmp_path / "bad.yaml"
    config_file.write_text("camera:\n  bogus: 1\n", encoding="utf-8")

    try:
        load_config(config_file)
    except ValueError as exc:
        assert "bogus" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown config key.")


def test_load_config_returns_defaults_for_missing_path(tmp_path: Path) -> None:
    from gesture_control.config import AppConfig, load_config

    missing = tmp_path / "does-not-exist.yaml"

    assert load_config(missing) == AppConfig.default()


def test_default_config_path_resolves_to_repo_config_file() -> None:
    from gesture_control.config import default_config_path

    path = default_config_path()

    assert path is not None
    assert path == ROOT / "config" / "default.yaml"
    assert path.exists()


def test_default_config_path_honors_env_override(monkeypatch, tmp_path: Path) -> None:
    from gesture_control.config import default_config_path

    override = tmp_path / "override.yaml"
    monkeypatch.setenv("GESTURE_CONTROL_CONFIG", str(override))

    assert default_config_path() == override


def test_load_default_config_reads_repo_yaml() -> None:
    from gesture_control.config import AppConfig, load_default_config

    config = load_default_config()

    # The checked-in config/default.yaml currently mirrors AppConfig.default(),
    # so loading it should round-trip to the same values.
    assert config == AppConfig.default()


def test_core_types_are_importable_without_optional_dependencies() -> None:
    from gesture_control.core.types import GestureAction, GestureActionType, GestureState, HandLandmarks, Landmark

    hand = HandLandmarks(
        handedness="Left",
        landmarks=[Landmark(0.0, 0.0, 0.0) for _ in range(21)],
        confidence=0.9,
        timestamp=1.25,
    )
    action = GestureAction(GestureActionType.SCROLL_DELTA, value=3.5, timestamp=1.3)

    assert hand.handedness == "Left"
    assert len(hand.landmarks) == 21
    assert action.kind is GestureActionType.SCROLL_DELTA
    assert GestureState.IDLE.value == "idle"
