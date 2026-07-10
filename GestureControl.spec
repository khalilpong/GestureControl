# -*- mode: python ; coding: utf-8 -*-
#
# Maintained PyInstaller spec (checked into git, not auto-generated).
#
# Custom Info.plist entries -- especially NSCameraUsageDescription -- can only
# be set through a spec file's BUNDLE(info_plist=...) call; PyInstaller's CLI
# has no flag for it. Without NSCameraUsageDescription, macOS hard-crashes the
# process (TCC) the moment it touches the camera instead of prompting for
# permission, so this key is required for the packaged app to work at all.

from pathlib import Path

from PyInstaller.utils.hooks import collect_all

root = Path(SPECPATH)

# MediaPipe's Tasks API loads a native library (mediapipe/tasks/c/libmediapipe.dylib)
# and several other submodules dynamically, in ways PyInstaller's static import
# analysis doesn't detect. collect_all() force-includes the entire package tree
# (modules, binaries, and data files) instead of relying on that analysis.
mediapipe_datas, mediapipe_binaries, mediapipe_hiddenimports = collect_all("mediapipe")

a = Analysis(
    [str(root / "scripts" / "gesture_control_launcher.py")],
    pathex=[str(root / "src")],
    binaries=mediapipe_binaries,
    datas=[
        (str(root / "config" / "default.yaml"), "config"),
        (str(root / "models" / "hand_landmarker.task"), "models"),
    ] + mediapipe_datas,
    hiddenimports=mediapipe_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="GestureControl",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="GestureControl",
)
app = BUNDLE(
    coll,
    name="GestureControl.app",
    icon=None,
    bundle_identifier="com.khalilpong.gesturecontrol",
    version="0.1.0",
    info_plist={
        "NSCameraUsageDescription": (
            "Gesture Control uses the camera to detect hand gestures for "
            "scrolling and adjusting system volume. Video is processed "
            "locally and is never recorded or transmitted."
        ),
        "CFBundleShortVersionString": "0.1.0",
        "CFBundleVersion": "0.1.0",
        "NSHighResolutionCapable": True,
        "LSMinimumSystemVersion": "11.0",
    },
)
