from __future__ import annotations

import os
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CameraConfig:
    index: int = 0
    width: int = 640
    height: int = 480
    # Most built-in FaceTime cameras only cleanly negotiate 30fps at this
    # resolution over AVFoundation; requesting 60fps can cause inconsistent
    # frame pacing (stutter) instead of an outright failure, since the
    # capture backend often accepts the request without honoring it.
    fps: int = 30


@dataclass(frozen=True)
class GestureConfig:
    max_hands: int = 2
    fist_hold_seconds: float = 0.15
    pinch_hold_seconds: float = 0.15
    palm_pause_hold_seconds: float = 0.8
    pause_cooldown_seconds: float = 0.8
    deadzone: float = 0.015
    scroll_sensitivity: float = 1800.0
    volume_sensitivity: float = 0.08
    # Fingertip-to-palm-center distance (as a ratio of hand size) below which a
    # finger counts as "curled in" for fist detection. The thumb gets its own,
    # looser ratio because it naturally rests further from the palm center than
    # the other four fingers even in a fully closed fist.
    fist_finger_curl_ratio: float = 0.30
    fist_thumb_curl_ratio: float = 0.45
    # Fingertip-to-palm-center distance ratio above which a finger counts as
    # "extended" for open-palm detection.
    palm_finger_extend_ratio: float = 0.35
    palm_thumb_extend_ratio: float = 0.25
    # Thumb-to-index-tip distance ratio below which the hand counts as pinched.
    pinch_distance_threshold: float = 0.08


@dataclass(frozen=True)
class CommandConfig:
    scroll_hz: float = 30.0
    volume_hz: float = 10.0


@dataclass(frozen=True)
class DebugConfig:
    overlay_enabled: bool = True
    log_file: str = "gesture-control.log"


@dataclass(frozen=True)
class AppConfig:
    camera: CameraConfig
    gesture: GestureConfig
    command: CommandConfig
    debug: DebugConfig

    @classmethod
    def default(cls) -> "AppConfig":
        return cls(
            camera=CameraConfig(),
            gesture=GestureConfig(),
            command=CommandConfig(),
            debug=DebugConfig(),
        )


def default_config_path() -> Path | None:
    """Resolve config/default.yaml across dev, editable-install, and PyInstaller runs."""

    env_override = os.environ.get("GESTURE_CONTROL_CONFIG")
    if env_override:
        return Path(env_override)

    if getattr(sys, "frozen", False):
        bundled = Path(getattr(sys, "_MEIPASS", "")) / "config" / "default.yaml"
        if bundled.exists():
            return bundled

    repo_config = Path(__file__).resolve().parents[2] / "config" / "default.yaml"
    if repo_config.exists():
        return repo_config

    return None


def load_default_config() -> AppConfig:
    """Load AppConfig from the resolved default config file, falling back to defaults."""

    return load_config(default_config_path())


def load_config(path: str | Path | None = None) -> AppConfig:
    config = AppConfig.default()
    if path is None:
        return config

    config_path = Path(path)
    if not config_path.exists():
        return config

    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("Loading YAML config requires PyYAML.") from exc

    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError("Config file must contain a mapping at the top level.")
    return merge_config(config, raw)


def merge_config(config: AppConfig, raw: dict[str, Any]) -> AppConfig:
    return replace(
        config,
        camera=_merge_dataclass(config.camera, raw.get("camera")),
        gesture=_merge_dataclass(config.gesture, raw.get("gesture")),
        command=_merge_dataclass(config.command, raw.get("command")),
        debug=_merge_dataclass(config.debug, raw.get("debug")),
    )


def _merge_dataclass(instance: Any, raw: Any) -> Any:
    if raw is None:
        return instance
    if not isinstance(raw, dict):
        raise ValueError("Config section must be a mapping.")

    allowed = set(instance.__dataclass_fields__)
    unknown = set(raw) - allowed
    if unknown:
        names = ", ".join(sorted(unknown))
        raise ValueError(f"Unknown config keys: {names}")
    return replace(instance, **raw)
