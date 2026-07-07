from __future__ import annotations

from pathlib import Path
import subprocess
import sys


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    launcher_dir = root / "build" / "pyinstaller"
    launcher_dir.mkdir(parents=True, exist_ok=True)
    launcher = launcher_dir / "gesture_control_launcher.py"
    launcher.write_text(
        "from gesture_control.app import run_app\n"
        "raise SystemExit(run_app())\n",
        encoding="utf-8",
    )

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name",
        "GestureControl",
        "--windowed",
        "--noconfirm",
        "--clean",
        "--paths",
        str(root / "src"),
        "--add-data",
        f"{root / 'config' / 'default.yaml'}:config",
        str(launcher),
    ]
    return subprocess.run(cmd, cwd=root, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
