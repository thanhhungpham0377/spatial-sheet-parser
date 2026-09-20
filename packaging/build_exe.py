"""Automated build script for Windows Portable Single-File EXE."""

import os
import shutil
import subprocess
import sys


def main() -> int:
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    spec_path = os.path.join(project_root, "packaging", "spatial_sheet_parser.spec")
    output_dir = os.path.join(project_root, "dist")

    os.chdir(project_root)

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        "--distpath",
        output_dir,
        spec_path,
    ]

    print(f"Executing PyInstaller build: {' '.join(cmd)}")
    res = subprocess.run(cmd)

    if res.returncode != 0:
        print("PyInstaller build failed!", file=sys.stderr)
        return res.returncode

    exe_path = os.path.join(output_dir, "spatial-sheet-parser.exe")
    if os.path.isfile(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print(f"Build succeeded! Portable EXE generated at: {exe_path} ({size_mb:.2f} MB)")
        return 0
    else:
        print(f"Error: Expected EXE output not found at {exe_path}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
