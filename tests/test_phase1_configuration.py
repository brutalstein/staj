from pathlib import Path

import pytest
import yaml

from autonomy.configuration.loader import ConfigurationError, load_configuration


DEFAULT_CONFIG = Path("config/runtime/default.yaml")


def test_phase1_default_configuration_is_complete_and_deterministic() -> None:
    configuration = load_configuration(DEFAULT_CONFIG)

    assert configuration.phase1.vehicle.carla_blueprint == "vehicle.tesla.model3"
    assert configuration.phase1.vehicle.manual_dimensions_allowed is False
    assert len(configuration.phase1.sensor_layout.sensors) == 16
    assert {sensor.sensor_type for sensor in configuration.phase1.sensor_layout.sensors} == {
        "rgb_camera",
        "lidar_64_channel",
        "4d_radar_proxy",
        "gnss",
        "imu",
    }
    sensors = configuration.phase1.sensor_layout.sensors
    assert sum(sensor.sensor_type == "rgb_camera" for sensor in sensors) == 6
    assert sum(sensor.sensor_type == "4d_radar_proxy" for sensor in sensors) == 6
    assert all(sensor.required_for_synchronization for sensor in sensors)
    assert len(configuration.configuration_hash) == 64


def test_configuration_hash_includes_referenced_sensor_layout(tmp_path: Path) -> None:
    runtime_path = tmp_path / "runtime.yaml"
    vehicle_path = tmp_path / "vehicle.yaml"
    layout_path = tmp_path / "layout.yaml"

    source = yaml.safe_load(DEFAULT_CONFIG.read_text(encoding="utf-8"))
    vehicle_path.write_text(
        Path("config/vehicles/tesla_model3.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    layout_path.write_text(
        Path("config/sensors/layouts/tesla_model3_omnihd_v1.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    source["phase1"]["vehicle_config"] = vehicle_path.name
    source["phase1"]["sensor_layout_config"] = layout_path.name
    source["phase1"]["recording"]["output_directory"] = "recordings"
    runtime_path.write_text(yaml.safe_dump(source, sort_keys=False), encoding="utf-8")

    first_hash = load_configuration(runtime_path).configuration_hash
    layout_document = yaml.safe_load(layout_path.read_text(encoding="utf-8"))
    layout_document["sensors"][0]["attributes"]["range"] = "119.0"
    layout_path.write_text(yaml.safe_dump(layout_document, sort_keys=False), encoding="utf-8")

    assert load_configuration(runtime_path).configuration_hash != first_hash


def test_sensor_tick_must_be_multiple_of_world_delta(tmp_path: Path) -> None:
    runtime_path = tmp_path / "runtime.yaml"
    vehicle_path = tmp_path / "vehicle.yaml"
    layout_path = tmp_path / "layout.yaml"
    vehicle_path.write_text(
        Path("config/vehicles/tesla_model3.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    layout_document = yaml.safe_load(
        Path("config/sensors/layouts/tesla_model3_omnihd_v1.yaml").read_text(encoding="utf-8")
    )
    layout_document["sensors"][0]["attributes"]["sensor_tick"] = "0.03"
    layout_path.write_text(yaml.safe_dump(layout_document, sort_keys=False), encoding="utf-8")
    runtime_document = yaml.safe_load(DEFAULT_CONFIG.read_text(encoding="utf-8"))
    runtime_document["phase1"]["vehicle_config"] = vehicle_path.name
    runtime_document["phase1"]["sensor_layout_config"] = layout_path.name
    runtime_document["phase1"]["recording"]["output_directory"] = "recordings"
    runtime_path.write_text(yaml.safe_dump(runtime_document, sort_keys=False), encoding="utf-8")

    with pytest.raises(ConfigurationError, match="tam katı"):
        load_configuration(runtime_path)
