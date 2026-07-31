from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from math import isfinite
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

import yaml


class ConfigurationError(RuntimeError):
    """Konfigürasyon eksik veya geçersiz olduğunda üretilir."""


def _empty_aliases() -> Mapping[str, str]:
    return MappingProxyType({})


def _empty_attributes() -> Mapping[str, str]:
    return MappingProxyType({})


@dataclass(frozen=True, slots=True)
class CarlaConfiguration:
    host: str
    rpc_port: int
    timeout_seconds: float
    supported_versions: tuple[str, ...]
    server_version_aliases: Mapping[str, str] = field(default_factory=_empty_aliases)

    def resolve_version(self, reported_version: str) -> str:
        """CARLA'nın raporladığı build kimliğini uyumluluk sürümüne çevirir."""

        return self.server_version_aliases.get(reported_version, reported_version)


@dataclass(frozen=True, slots=True)
class RuntimeConfiguration:
    simulation_frequency_hz: int
    fixed_delta_seconds: float
    control_frequency_hz: int
    log_level: str


@dataclass(frozen=True, slots=True)
class VehicleConfiguration:
    vehicle_id: str
    carla_blueprint: str
    role_name: str
    geometry_source: str
    reference_frame: str
    manual_dimensions_allowed: bool
    hold_brake_on_start: bool
    source_path: Path


@dataclass(frozen=True, slots=True)
class NormalizedSensorPosition:
    wheelbase_ratio_x: float
    vehicle_width_ratio_y: float
    vehicle_height_ratio_z: float
    additional_height_m: float = 0.0


@dataclass(frozen=True, slots=True)
class SensorDefinition:
    sensor_id: str
    sensor_type: str
    normalized_position: NormalizedSensorPosition
    orientation_rpy_deg: tuple[float, float, float]
    attributes: Mapping[str, str] = field(default_factory=_empty_attributes)
    required_for_synchronization: bool = True

    def sensor_tick_seconds(self) -> float:
        try:
            value = float(self.attributes["sensor_tick"])
        except (KeyError, ValueError) as exc:
            raise ConfigurationError(
                f"{self.sensor_id}: sensor_tick geçerli bir sayı olmalıdır."
            ) from exc
        if not isfinite(value) or value <= 0:
            raise ConfigurationError(f"{self.sensor_id}: sensor_tick pozitif ve sonlu olmalıdır.")
        return value


@dataclass(frozen=True, slots=True)
class SensorLayoutConfiguration:
    layout_id: str
    reference_frame: str
    vehicle_blueprint: str
    sensors: tuple[SensorDefinition, ...]
    source_path: Path


@dataclass(frozen=True, slots=True)
class RecordingConfiguration:
    enabled: bool
    output_directory: Path
    record_raw_data: bool
    flush_every_frames: int


@dataclass(frozen=True, slots=True)
class Phase1Configuration:
    vehicle: VehicleConfiguration
    sensor_layout: SensorLayoutConfiguration
    spawn_point_index: int
    sensor_buffer_capacity: int
    synchronization_timeout_seconds: float
    maximum_consecutive_sync_misses: int
    recording: RecordingConfiguration


@dataclass(frozen=True, slots=True)
class ProjectConfiguration:
    schema_version: str
    configuration_hash: str
    carla: CarlaConfiguration
    runtime: RuntimeConfiguration
    phase1: Phase1Configuration
    source_path: Path


def _required(mapping: Mapping[str, Any], key: str, context: str) -> Any:
    if key not in mapping:
        raise ConfigurationError(f"{context} içinde zorunlu '{key}' alanı eksik.")
    return mapping[key]


def _mapping(value: Any, context: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise ConfigurationError(f"{context} mapping olmalıdır.")
    return value


def _string_mapping(value: Any, context: str) -> Mapping[str, str]:
    source = _mapping(value, context)
    result: dict[str, str] = {}
    for raw_key, raw_value in source.items():
        if isinstance(raw_value, (dict, list, tuple, set)):
            raise ConfigurationError(f"{context}.{raw_key} scalar olmalıdır.")
        key = str(raw_key).strip()
        mapped = str(raw_value).strip()
        if not key or not mapped:
            raise ConfigurationError(f"{context} boş anahtar veya değer içeremez.")
        result[key] = mapped
    return MappingProxyType(result)


def _read_yaml(path: Path, context: str) -> tuple[Mapping[str, Any], bytes]:
    if not path.is_file():
        raise ConfigurationError(f"{context} dosyası bulunamadı: {path}")
    raw_bytes = path.read_bytes()
    try:
        document = yaml.safe_load(raw_bytes) or {}
    except yaml.YAMLError as exc:
        raise ConfigurationError(f"YAML okunamadı: {path}: {exc}") from exc
    return _mapping(document, context), raw_bytes


def _resolve_path(base_path: Path, raw_value: Any, context: str) -> Path:
    value = str(raw_value).strip()
    if not value:
        raise ConfigurationError(f"{context} boş olamaz.")
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = base_path / candidate
    return candidate.resolve()


def _load_vehicle(path: Path) -> tuple[VehicleConfiguration, bytes]:
    document, raw_bytes = _read_yaml(path, "vehicle_config")
    vehicle = VehicleConfiguration(
        vehicle_id=str(_required(document, "vehicle_id", "vehicle_config")).strip(),
        carla_blueprint=str(_required(document, "carla_blueprint", "vehicle_config")).strip(),
        role_name=str(document.get("role_name", "hero")).strip(),
        geometry_source=str(_required(document, "geometry_source", "vehicle_config")).strip(),
        reference_frame=str(_required(document, "reference_frame", "vehicle_config")).strip(),
        manual_dimensions_allowed=bool(
            _required(document, "manual_dimensions_allowed", "vehicle_config")
        ),
        hold_brake_on_start=bool(document.get("hold_brake_on_start", True)),
        source_path=path,
    )
    if not all(
        (
            vehicle.vehicle_id,
            vehicle.carla_blueprint,
            vehicle.role_name,
            vehicle.geometry_source,
            vehicle.reference_frame,
        )
    ):
        raise ConfigurationError("vehicle_config zorunlu metin alanları boş olamaz.")
    if vehicle.manual_dimensions_allowed:
        raise ConfigurationError(
            "Faz 1'de elle araç boyutu girilemez; VehicleGeometryAdapter kullanılmalıdır."
        )
    if vehicle.geometry_source != "runtime_vehicle_geometry_adapter":
        raise ConfigurationError(
            "vehicle_config.geometry_source runtime_vehicle_geometry_adapter olmalıdır."
        )
    return vehicle, raw_bytes


def _normalized_position(value: Any, sensor_id: str) -> NormalizedSensorPosition:
    source = _mapping(value, f"sensor[{sensor_id}].normalized_position")
    position = NormalizedSensorPosition(
        wheelbase_ratio_x=float(_required(source, "wheelbase_ratio_x", sensor_id)),
        vehicle_width_ratio_y=float(_required(source, "vehicle_width_ratio_y", sensor_id)),
        vehicle_height_ratio_z=float(_required(source, "vehicle_height_ratio_z", sensor_id)),
        additional_height_m=float(source.get("additional_height_m", 0.0)),
    )
    if not -0.5 <= position.wheelbase_ratio_x <= 1.5:
        raise ConfigurationError(f"{sensor_id}: wheelbase_ratio_x [-0.5, 1.5] dışında.")
    if not -0.6 <= position.vehicle_width_ratio_y <= 0.6:
        raise ConfigurationError(f"{sensor_id}: vehicle_width_ratio_y [-0.6, 0.6] dışında.")
    if not 0.0 <= position.vehicle_height_ratio_z <= 1.5:
        raise ConfigurationError(f"{sensor_id}: vehicle_height_ratio_z [0, 1.5] dışında.")
    if not -1.0 <= position.additional_height_m <= 2.0:
        raise ConfigurationError(f"{sensor_id}: additional_height_m makul aralık dışında.")
    return position


def _orientation(value: Any, sensor_id: str) -> tuple[float, float, float]:
    source = _mapping(value, f"sensor[{sensor_id}].orientation_deg")
    orientation = (
        float(source.get("roll", 0.0)),
        float(source.get("pitch", 0.0)),
        float(source.get("yaw", 0.0)),
    )
    if any(not isfinite(angle) for angle in orientation):
        raise ConfigurationError(f"{sensor_id}: orientation değerleri sonlu olmalıdır.")
    return orientation


def _load_sensor_layout(path: Path) -> tuple[SensorLayoutConfiguration, bytes]:
    document, raw_bytes = _read_yaml(path, "sensor_layout_config")
    raw_sensors = _required(document, "sensors", "sensor_layout_config")
    if not isinstance(raw_sensors, list):
        raise ConfigurationError("sensor_layout_config.sensors liste olmalıdır.")

    sensors: list[SensorDefinition] = []
    for index, raw_sensor in enumerate(raw_sensors):
        source = _mapping(raw_sensor, f"sensors[{index}]")
        sensor_id = str(_required(source, "sensor_id", f"sensors[{index}]")).strip()
        sensor_type = str(_required(source, "type", f"sensors[{index}]")).strip()
        attributes = _string_mapping(
            source.get("attributes", {}),
            f"sensor[{sensor_id}].attributes",
        )
        definition = SensorDefinition(
            sensor_id=sensor_id,
            sensor_type=sensor_type,
            normalized_position=_normalized_position(
                _required(source, "normalized_position", f"sensor[{sensor_id}]"), sensor_id
            ),
            orientation_rpy_deg=_orientation(
                _required(source, "orientation_deg", f"sensor[{sensor_id}]"), sensor_id
            ),
            attributes=attributes,
            required_for_synchronization=bool(source.get("required_for_synchronization", True)),
        )
        if not sensor_id or not sensor_type:
            raise ConfigurationError("Sensör kimliği ve tipi boş olamaz.")
        definition.sensor_tick_seconds()
        sensors.append(definition)

    sensor_ids = [sensor.sensor_id for sensor in sensors]
    duplicate_ids = sorted(
        {sensor_id for sensor_id in sensor_ids if sensor_ids.count(sensor_id) > 1}
    )
    if duplicate_ids:
        raise ConfigurationError(f"Tekrarlanan sensor_id: {', '.join(duplicate_ids)}")

    expected_counts = {
        "rgb_camera": 6,
        "lidar_64_channel": 1,
        "4d_radar_proxy": 6,
        "gnss": 2,
        "imu": 1,
    }
    actual_counts = {
        sensor_type: sum(sensor.sensor_type == sensor_type for sensor in sensors)
        for sensor_type in expected_counts
    }
    if actual_counts != expected_counts:
        raise ConfigurationError(
            "Faz 1 sensör topolojisi geçersiz. "
            f"Beklenen={expected_counts}, gerçek={actual_counts}."
        )
    unsupported = sorted(
        {sensor.sensor_type for sensor in sensors if sensor.sensor_type not in expected_counts}
    )
    if unsupported:
        raise ConfigurationError(f"Desteklenmeyen sensör tipleri: {', '.join(unsupported)}")

    layout = SensorLayoutConfiguration(
        layout_id=str(_required(document, "layout_id", "sensor_layout_config")).strip(),
        reference_frame=str(_required(document, "reference_frame", "sensor_layout_config")).strip(),
        vehicle_blueprint=str(
            _required(document, "vehicle_blueprint", "sensor_layout_config")
        ).strip(),
        sensors=tuple(sensors),
        source_path=path,
    )
    if not layout.layout_id or not layout.reference_frame or not layout.vehicle_blueprint:
        raise ConfigurationError("sensor_layout_config zorunlu metin alanları boş olamaz.")
    return layout, raw_bytes


def _configuration_hash(*documents: tuple[str, bytes]) -> str:
    digest = sha256()
    for label, raw_bytes in documents:
        digest.update(label.encode("utf-8"))
        digest.update(b"\0")
        digest.update(raw_bytes)
        digest.update(b"\0")
    return digest.hexdigest()


def load_configuration(path: Path) -> ProjectConfiguration:
    """Ana ve referans verilen Faz 1 YAML dosyalarını yükleyip doğrular."""

    path = path.resolve()
    document, runtime_bytes = _read_yaml(path, "runtime_config")
    schema_version = str(_required(document, "schema_version", "kök"))
    carla_raw = _mapping(_required(document, "carla", "kök"), "carla")
    runtime_raw = _mapping(_required(document, "runtime", "kök"), "runtime")

    raw_supported_versions = _required(carla_raw, "supported_versions", "carla")
    if not isinstance(raw_supported_versions, list):
        raise ConfigurationError("carla.supported_versions liste olmalıdır.")
    supported_versions = tuple(str(value).strip() for value in raw_supported_versions)
    if len(set(supported_versions)) != len(supported_versions):
        raise ConfigurationError("carla.supported_versions tekrarlı değer içeremez.")
    carla = CarlaConfiguration(
        host=str(_required(carla_raw, "host", "carla")),
        rpc_port=int(_required(carla_raw, "rpc_port", "carla")),
        timeout_seconds=float(_required(carla_raw, "timeout_seconds", "carla")),
        supported_versions=supported_versions,
        server_version_aliases=_string_mapping(
            carla_raw.get("server_version_aliases", {}), "carla.server_version_aliases"
        ),
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
    if not carla.supported_versions or any(not version for version in carla.supported_versions):
        raise ConfigurationError("CARLA supported_versions boş değer içeremez.")
    invalid_alias_targets = sorted(
        target
        for target in set(carla.server_version_aliases.values())
        if target not in carla.supported_versions
    )
    if invalid_alias_targets:
        raise ConfigurationError(
            "CARLA server_version_aliases yalnızca desteklenen sürümlere yönlenmelidir. "
            f"Geçersiz hedefler: {', '.join(invalid_alias_targets)}"
        )
    if runtime.simulation_frequency_hz <= 0 or runtime.control_frequency_hz <= 0:
        raise ConfigurationError("Çalışma frekansları pozitif olmalıdır.")
    expected_delta = 1.0 / runtime.simulation_frequency_hz
    if abs(runtime.fixed_delta_seconds - expected_delta) > 1e-9:
        raise ConfigurationError(
            "fixed_delta_seconds, simulation_frequency_hz değerinin tersi olmalıdır."
        )

    phase1_raw = _mapping(_required(document, "phase1", "kök"), "phase1")
    vehicle_path = _resolve_path(
        path.parent, _required(phase1_raw, "vehicle_config", "phase1"), "phase1.vehicle_config"
    )
    layout_path = _resolve_path(
        path.parent,
        _required(phase1_raw, "sensor_layout_config", "phase1"),
        "phase1.sensor_layout_config",
    )
    vehicle, vehicle_bytes = _load_vehicle(vehicle_path)
    sensor_layout, layout_bytes = _load_sensor_layout(layout_path)

    recording_raw = _mapping(_required(phase1_raw, "recording", "phase1"), "phase1.recording")
    recording = RecordingConfiguration(
        enabled=bool(_required(recording_raw, "enabled", "phase1.recording")),
        output_directory=_resolve_path(
            path.parent,
            _required(recording_raw, "output_directory", "phase1.recording"),
            "phase1.recording.output_directory",
        ),
        record_raw_data=bool(recording_raw.get("record_raw_data", False)),
        flush_every_frames=int(recording_raw.get("flush_every_frames", 25)),
    )
    phase1 = Phase1Configuration(
        vehicle=vehicle,
        sensor_layout=sensor_layout,
        spawn_point_index=int(phase1_raw.get("spawn_point_index", 0)),
        sensor_buffer_capacity=int(phase1_raw.get("sensor_buffer_capacity", 8)),
        synchronization_timeout_seconds=float(
            phase1_raw.get("synchronization_timeout_seconds", 1.0)
        ),
        maximum_consecutive_sync_misses=int(
            phase1_raw.get("maximum_consecutive_sync_misses", 5)
        ),
        recording=recording,
    )

    if phase1.spawn_point_index < 0:
        raise ConfigurationError("phase1.spawn_point_index negatif olamaz.")
    if phase1.sensor_buffer_capacity < 2:
        raise ConfigurationError("phase1.sensor_buffer_capacity en az 2 olmalıdır.")
    if phase1.synchronization_timeout_seconds <= 0:
        raise ConfigurationError("Senkronizasyon timeout pozitif olmalıdır.")
    if phase1.maximum_consecutive_sync_misses < 1:
        raise ConfigurationError("maximum_consecutive_sync_misses en az 1 olmalıdır.")
    if recording.flush_every_frames < 1:
        raise ConfigurationError("recording.flush_every_frames en az 1 olmalıdır.")
    if sensor_layout.vehicle_blueprint != vehicle.carla_blueprint:
        raise ConfigurationError(
            "Araç ve sensör layout blueprint değerleri eşleşmiyor: "
            f"{vehicle.carla_blueprint} != {sensor_layout.vehicle_blueprint}."
        )
    if sensor_layout.reference_frame != vehicle.reference_frame:
        raise ConfigurationError(
            "Araç ve sensör layout reference_frame değerleri eşleşmelidir."
        )

    for sensor in sensor_layout.sensors:
        ratio = sensor.sensor_tick_seconds() / runtime.fixed_delta_seconds
        rounded = round(ratio)
        if rounded < 1 or abs(ratio - rounded) > 1e-9:
            raise ConfigurationError(
                f"{sensor.sensor_id}: sensor_tick ({sensor.sensor_tick_seconds()}) "
                "fixed_delta_seconds değerinin tam katı olmalıdır."
            )

    return ProjectConfiguration(
        schema_version=schema_version,
        configuration_hash=_configuration_hash(
            ("runtime", runtime_bytes),
            ("vehicle", vehicle_bytes),
            ("sensor_layout", layout_bytes),
        ),
        carla=carla,
        runtime=runtime,
        phase1=phase1,
        source_path=path,
    )
