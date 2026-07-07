from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def test_app_module_imports_without_gui_side_effects() -> None:
    import gesture_control.app as app

    assert callable(app.run_app)
    assert app.GestureControlWindow.__name__ == "GestureControlWindow"
    assert app.FloatingStopWindow.__name__ == "FloatingStopWindow"
