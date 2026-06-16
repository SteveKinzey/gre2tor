#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import platform
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
BUILD = ROOT / "build"
SPEC = ROOT / "GRE2Tor.spec"


def _run(command: list[str]) -> None:
    print("$", " ".join(command))
    subprocess.run(command, cwd=ROOT, check=True)


def _artifact_path() -> Path:
    system = platform.system().lower()
    exe_name = "GRE2Tor.exe" if system == "windows" else "GRE2Tor"
    return DIST / exe_name


def _zip_artifact(executable: Path) -> Path:
    system = platform.system().lower()
    machine = platform.machine().lower() or "unknown"
    archive = DIST / f"GRE2Tor-{system}-{machine}.zip"
    if archive.exists():
        archive.unlink()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        arcname = "GRE2Tor.exe" if executable.suffix.lower() == ".exe" else "GRE2Tor"
        zf.write(executable, arcname)
        zf.write(ROOT / "README.md", "README.md")
    return archive


def main() -> None:
    if not SPEC.exists():
        raise SystemExit(f"Missing spec file: {SPEC}")

    shutil.rmtree(BUILD, ignore_errors=True)
    DIST.mkdir(exist_ok=True)

    _run([sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm", str(SPEC)])

    executable = _artifact_path()
    if not executable.exists():
        raise SystemExit(f"Expected packaged executable was not created: {executable}")

    archive = _zip_artifact(executable)
    print(f"Created package: {archive}")


if __name__ == "__main__":
    main()
