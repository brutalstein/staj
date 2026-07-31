from __future__ import annotations

import argparse
import logging
from pathlib import Path

from autonomy.application.app import AutonomyApplication
from autonomy.configuration.loader import ConfigurationError, load_configuration
from autonomy.simulation.carla.adapter import CarlaConnectionError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="L4 otonomi uygulaması")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/runtime/default.yaml"),
        help="Çalışma zamanı konfigürasyonu",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        configuration = load_configuration(args.config)
    except ConfigurationError as exc:
        print(f"[HATA] {exc}")
        return 2

    logging.basicConfig(
        level=getattr(logging, configuration.runtime.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    try:
        return AutonomyApplication(configuration).run()
    except CarlaConnectionError as exc:
        print(f"[HATA] {exc}")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
