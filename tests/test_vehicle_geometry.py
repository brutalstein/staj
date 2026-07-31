from types import SimpleNamespace

import pytest

from autonomy.configuration.loader import NormalizedSensorPosition, SensorDefinition
from autonomy.simulation.carla.geometry import VehicleGeometryAdapter, VehicleGeometryError


def vector(x: float, y: float, z: float) -> SimpleNamespace:
    return SimpleNamespace(x=x, y=y, z=z)


def vehicle_with_wheels(wheels: list[SimpleNamespace]) -> SimpleNamespace:
    return SimpleNamespace(
        bounding_box=SimpleNamespace(
            extent=vector(2.35, 0.95, 0.75),
            location=vector(0.05, 0.0, 0.78),
        ),
        get_physics_control=lambda: SimpleNamespace(wheels=wheels),
    )


def test_geometry_adapter_converts_centimetre_wheels_and_resolves_pose() -> None:
    vehicle = vehicle_with_wheels(
        [
            SimpleNamespace(position=vector(145.0, -80.0, -35.0)),
            SimpleNamespace(position=vector(145.0, 80.0, -35.0)),
            SimpleNamespace(position=vector(-140.0, -80.0, -35.0)),
            SimpleNamespace(position=vector(-140.0, 80.0, -35.0)),
        ]
    )
    adapter = VehicleGeometryAdapter()

    geometry = adapter.extract(vehicle)

    assert geometry.wheelbase_m == pytest.approx(2.85)
    assert geometry.front_track_width_m == pytest.approx(1.60)
    assert geometry.rear_axle_center_m.x == pytest.approx(-1.40)
    sensor = SensorDefinition(
        sensor_id="roof",
        sensor_type="imu",
        normalized_position=NormalizedSensorPosition(0.5, 0.0, 1.0, 0.1),
        orientation_rpy_deg=(0.0, 0.0, 0.0),
        attributes={"sensor_tick": "0.02"},
    )
    pose = adapter.resolve_sensor_pose(geometry, sensor)
    assert pose.location_m.x == pytest.approx(0.025)
    assert pose.location_m.z == pytest.approx(1.63)


def test_geometry_adapter_rejects_wrong_wheel_order() -> None:
    vehicle = vehicle_with_wheels(
        [
            SimpleNamespace(position=vector(-140.0, -80.0, -35.0)),
            SimpleNamespace(position=vector(-140.0, 80.0, -35.0)),
            SimpleNamespace(position=vector(145.0, -80.0, -35.0)),
            SimpleNamespace(position=vector(145.0, 80.0, -35.0)),
        ]
    )

    with pytest.raises(VehicleGeometryError, match="teker sırası"):
        VehicleGeometryAdapter().extract(vehicle)
