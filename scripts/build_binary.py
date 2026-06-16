#!/usr/bin/env python3
"""
Build script for cross-platform standalone binaries.

Usage:
    python scripts/build_binary.py

Requires: pip install pyinstaller
"""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def get_platform():
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    return system


def build_for_current():
    """Build a standalone binary for the current platform."""
    plat = get_platform()
    print(f"Building for {plat} ({platform.machine()})...")

    src_dir = Path(__file__).parent.parent
    dist_dir = src_dir / "dist"
    build_dir = src_dir / "build"

    # Clean previous builds
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    if build_dir.exists():
        shutil.rmtree(build_dir)

    entry = str(src_dir / "src" / "ternary_emulator" / "cli.py")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", "ternary-emulator",
        "--distpath", str(dist_dir),
        "--workpath", str(build_dir),
        "--specpath", str(build_dir),
        "--console",
        entry,
    ]

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(src_dir), capture_output=False)

    if result.returncode != 0:
        print("ERROR: Build failed!")
        sys.exit(1)

    binary_name = "ternary-emulator.exe" if plat == "windows" else "ternary-emulator"
    binary_path = dist_dir / binary_name
    if binary_path.exists():
        size_mb = binary_path.stat().st_size / (1024 * 1024)
        print(f"\n✓ Build successful: {binary_path} ({size_mb:.1f} MB)")
    else:
        print(f"\n✗ Binary not found at {binary_path}")
        sys.exit(1)


if __name__ == "__main__":
    build_for_current()
