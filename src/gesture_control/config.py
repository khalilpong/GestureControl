from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CameraConfig:
    index: int = 0
    width: int = 640
    height: int = 480
    fps: int = 60


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
