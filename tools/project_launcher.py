from __future__ import annotations

import argparse
import importlib.util
import os
from pathlib import Path
import platform
import subprocess
import sys
from typing import Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from autonomy.configuration.loader import ConfigurationError, load_configuration
from autonomy.simulation.carla.adapter import CarlaAdapter, CarlaConnectionError


EXIT_OK = 0
EXIT_ENVIRONMENT = 10
EXIT_CONFIGURATION = 11
EXIT_CARLA = 12
EXIT_VALIDATION = 13


def _is_virtual_environment() -> bool:
    return bool(os.environ.get("CONDA_PREFIX")) or sys.prefix != getattr(sys, "base_prefix", sys.prefix)


def _missing_modules(module_names: Iterable[str]) -> list[str]:
    return [name for name in module_names if importlib.util.find_spec(name) is None]


def _check_python() -> list[str]:
    errors: list[str] = []
    if sys.version_info[:2] != (3, 11):
        errors.append(
            f"Desteklenmeyen Python sürümü: {platform.python_version()}. Python 3.11 kullanın."
        )
    if not _is_virtual_environment():
        errors.append(
            "Aktif conda/venv ortamı bulunamadı. Sistem Python'una paket kurulmayacaktır."
        )
    return errors


def _print_errors(title: str, errors: list[str]) -> None:
    print(f"[HATA] {title}")
    for error in errors:
        print(f"  - {error}")


def run_check(config_path: Path, require_carla: bool) -> int:
    errors = _check_python()
    missing = _missing_modules(["yaml"])
    if missing:
        errors.append(f"Eksik Python modülleri: {', '.join(missing)}")

    try:
        configuration = load_configuration(config_path)
    except ConfigurationError as exc:
        _print_errors("Konfigürasyon doğrulanamadı.", [str(exc)])
        return EXIT_CONFIGURATION

    if errors:
        _print_errors("Ortam kontrolleri başarısız.", errors)
        return EXIT_ENVIRONMENT

    print(f"[OK] Python: {platform.python_version()}")
    print(f"[OK] Sanal ortam: {sys.prefix}")
    print(f"[OK] Konfigürasyon: {configuration.configuration_hash[:12]}")

    if require_carla:
        adapter = CarlaAdapter(configuration.carla)
        try:
            info = adapter.connect()
        except CarlaConnectionError as exc:
            _print_errors("CARLA hazır değil.", [str(exc)])
            return EXIT_CARLA
        finally:
            adapter.disconnect()
        print(f"[OK] CARLA client/server: {info.server_version}")
        print(f"[OK] CARLA haritası: {info.map_name}")
    else:
        carla_status = "kurulu" if importlib.util.find_spec("carla") else "kurulu değil"
        print(f"[BİLGİ] CARLA Python API: {carla_status}")

    validation = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "tools" / "validate_project.py")],
        cwd=PROJECT_ROOT,
        check=False,
    )
    if validation.returncode != 0:
        return EXIT_VALIDATION
    return EXIT_OK


def run_install(include_docs: bool) -> int:
    if not _is_virtual_environment():
        _print_errors(
            "Kurulum durduruldu.",
            ["Önce conda veya venv ortamını etkinleştirin."],
        )
        return EXIT_ENVIRONMENT
    extras = ".[dev,docs]" if include_docs else ".[dev]"
    return subprocess.call([sys.executable, "-m", "pip", "install", "-e", extras], cwd=PROJECT_ROOT)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="L4 Autonomy kontrollü proje başlatıcısı")
    parser.add_argument("command", choices=["start", "check", "doctor", "install"], nargs="?", default="start")
    parser.add_argument("--config", type=Path, default=PROJECT_ROOT / "config/runtime/default.yaml")
    parser.add_argument("--with-docs", action="store_true", help="install komutunda docs bağımlılıklarını da kur")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "install":
        return run_install(args.with_docs)
    if args.command in {"check", "doctor"}:
        return run_check(args.config, require_carla=args.command == "doctor")

    check_code = run_check(args.config, require_carla=True)
    if check_code != EXIT_OK:
        return check_code
    return subprocess.call(
        [sys.executable, "-m", "autonomy.application.cli", "--config", str(args.config)],
        cwd=PROJECT_ROOT,
    )


if __name__ == "__main__":
    raise SystemExit(main())
