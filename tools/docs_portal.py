from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Yaşayan mimari doküman portalı")
    parser.add_argument("command", choices=["serve", "build"], nargs="?", default="serve")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--open", action="store_true", dest="open_browser")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if importlib.util.find_spec("mkdocs") is None:
        print("[HATA] MkDocs kurulu değil.")
        print("Aktif sanal ortamda şu komutu çalıştırın:")
        print('  python -m pip install -e ".[docs]"')
        return 20

    validation = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "tools" / "validate_project.py")],
        cwd=PROJECT_ROOT,
        check=False,
    )
    if validation.returncode != 0:
        print("[HATA] Doküman portalı proje doğrulaması başarısız olduğu için açılmadı.")
        return 21

    if args.command == "build":
        command = [sys.executable, "-m", "mkdocs", "build", "--strict"]
    else:
        command = [
            sys.executable,
            "-m",
            "mkdocs",
            "serve",
            "--dev-addr",
            f"{args.host}:{args.port}",
        ]
        if args.open_browser:
            command.append("--open")
    return subprocess.call(command, cwd=PROJECT_ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
