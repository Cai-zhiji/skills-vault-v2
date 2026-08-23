from __future__ import annotations

import argparse
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def target_triple() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    architecture = "aarch64" if machine in {"arm64", "aarch64"} else "x86_64"
    if system == "darwin":
        return f"{architecture}-apple-darwin"
    if system == "windows":
        return f"{architecture}-pc-windows-msvc"
    if system == "linux":
        return f"{architecture}-unknown-linux-gnu"
    raise RuntimeError(f"Unsupported packaging platform: {system}/{machine}")


def build() -> Path:
    triple = target_triple()
    executable_suffix = ".exe" if platform.system().lower() == "windows" else ""
    destination = PROJECT_ROOT / "src-tauri" / "binaries" / f"skills-vault-sidecar-{triple}{executable_suffix}"
    with tempfile.TemporaryDirectory(prefix="skills-vault-sidecar-") as temporary:
        temporary_root = Path(temporary)
        dist = temporary_root / "dist"
        command = [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            "--onefile",
            "--name",
            "skills-vault-sidecar",
            "--paths",
            str(PROJECT_ROOT / "server"),
            "--distpath",
            str(dist),
            "--workpath",
            str(temporary_root / "work"),
            "--specpath",
            str(temporary_root / "spec"),
            str(PROJECT_ROOT / "server" / "http_server.py"),
        ]
        subprocess.run(command, cwd=PROJECT_ROOT, check=True)
        built = dist / f"skills-vault-sidecar{executable_suffix}"
        if not built.is_file():
            raise RuntimeError(f"PyInstaller did not create {built}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(built, destination)
    subprocess.run([str(destination), "--version"], check=True)
    print(destination)
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build the current-platform Tauri sidecar")
    parser.parse_args()
    build()
