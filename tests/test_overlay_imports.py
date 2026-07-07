from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def test_overlay_helper_imports_and_returns_non_image_frame_unchanged() -> None:
    from gesture_control.diagnostics.overlay import draw_overlay

    frame = object()

    assert draw_overlay(frame, [], {"state": "idle"}) is frame
