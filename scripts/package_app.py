from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    config_dir = root / "build" / "pyinstaller-config"
    matplotlib_dir = root / "build" / "matplotlib"
    config_dir.mkdir(parents=True, exist_ok=True)
    matplotlib_dir.mkdir(parents=True, exist_ok=True)

    spec_path = root / "GestureControl.spec"

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        str(spec_path),
    ]
    env = os.environ.copy()
    env["PYINSTALLER_CONFIG_DIR"] = str(config_dir)
    env["MPLCONFIGDIR"] = str(matplotlib_dir)
    env.setdefault("LC_ALL", "en_US.UTF-8")
    env.setdefault("LANG", "en_US.UTF-8")
    return subprocess.run(cmd, cwd=root, env=env, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
