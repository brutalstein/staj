from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping

import yaml


class ConfigurationError(RuntimeError):
    """Konfigürasyon eksik veya geçersiz olduğunda üretilir."""


@dataclass(frozen=True, slots=True)
class CarlaConfiguration:
    host: str
    rpc_port: int
    timeout_seconds: float
    supported_versions: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RuntimeConfiguration:
    simulation_frequency_hz: int
    fixed_delta_seconds: float
    control_frequency_hz: int
    log_level: str


@dataclass(frozen=True, slots=True)
class ProjectConfiguration:
    schema_version: str
    configuration_hash: str
    carla: CarlaConfiguration
    runtime: RuntimeConfiguration
    source_path: Path


def _required(mapping: Mapping[str, Any], key: str, context: str) -> Any:
    if key not in mapping:
        raise ConfigurationError(f"{context} içinde zorunlu '{key}' alanı eksik.")
    return mapping[key]


def load_configuration(path: Path) -> ProjectConfiguration:
    """YAML konfigürasyonunu yükler, temel tip ve aralık kontrollerini yapar."""

    if not path.is_file():
        raise ConfigurationError(f"Konfigürasyon dosyası bulunamadı: {path}")

    raw_bytes = path.read_bytes()
    try:
        document = yaml.safe_load(raw_bytes) or {}
    except yaml.YAMLError as exc:
        raise ConfigurationError(f"YAML okunamadı: {path}: {exc}") from exc

    if not isinstance(document, dict):
        raise ConfigurationError("Konfigürasyonun kök değeri mapping olmalıdır.")

    schema_version = str(_required(document, "schema_version", "kök"))
    carla_raw = _required(document, "carla", "kök")
    runtime_raw = _required(document, "runtime", "kök")
    if not isinstance(carla_raw, dict) or not isinstance(runtime_raw, dict):
        raise ConfigurationError("carla ve runtime alanları mapping olmalıdır.")

    carla = CarlaConfiguration(
        host=str(_required(carla_raw, "host", "carla")),
        rpc_port=int(_required(carla_raw, "rpc_port", "carla")),
        timeout_seconds=float(_required(carla_raw, "timeout_seconds", "carla")),
        supported_versions=tuple(str(v) for v in _required(carla_raw, "supported_versions", "carla")),
    )
    runtime = RuntimeConfiguration(
        simulation_frequency_hz=int(_required(runtime_raw, "simulation_frequency_hz", "runtime")),
        fixed_delta_seconds=float(_required(runtime_raw, "fixed_delta_seconds", "runtime")),
        control_frequency_hz=int(_required(runtime_raw, "control_frequency_hz", "runtime")),
        log_level=str(_required(runtime_raw, "log_level", "runtime")),
    )

    if not 1 <= carla.rpc_port <= 65535:
        raise ConfigurationError("CARLA rpc_port 1 ile 65535 arasında olmalıdır.")
    if carla.timeout_seconds <= 0:
        raise ConfigurationError("CARLA timeout_seconds pozitif olmalıdır.")
    if runtime.simulation_frequency_hz <= 0 or runtime.control_frequency_hz <= 0:
        raise ConfigurationError("Çalışma frekansları pozitif olmalıdır.")
    expected_delta = 1.0 / runtime.simulation_frequency_hz
    if abs(runtime.fixed_delta_seconds - expected_delta) > 1e-9:
        raise ConfigurationError(
            "fixed_delta_seconds, simulation_frequency_hz değerinin tersi olmalıdır."
        )

    return ProjectConfiguration(
        schema_version=schema_version,
        configuration_hash=sha256(raw_bytes).hexdigest(),
        carla=carla,
        runtime=runtime,
        source_path=path.resolve(),
    )
