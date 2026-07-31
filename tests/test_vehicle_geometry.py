from __future__ import annotations

from math import cos, radians, sin
from types import SimpleNamespace

import pytest

from autonomy.configuration.loader import NormalizedSensorPosition, SensorDefinition
from autonomy.simulation.carla.geometry import VehicleGeometryAdapter


def vector(x: float, y: float, z: float) -> SimpleNamespace:
    return SimpleNamespace(x=x, y=y, z=z)


class FakeTransform:
    def __init__(self, x: float, y: float, z: float, yaw_deg: float) -> None:
        self.location = vector(x, y, z)
        self.rotation = SimpleNamespace(roll=0.0, pitch=0.0, yaw=yaw_deg)
        self._yaw = radians(yaw_deg)

    def transform(self, point: SimpleNamespace) -> SimpleNamespace:
        c, s = cos(self._yaw), sin(self._yaw)
        return vector(
            self.location.x + c * point.x - s * point.y,
            self.location.y + s * point.x + c * point.y,
            self.location.z + point.z,
        )

    def inverse_transform(self, point: SimpleNamespace) -> SimpleNamespace:
        dx = point.x - self.location.x
        dy = point.y - self.location.y
        c, s = cos(self._yaw), sin(self._yaw)
        return vector(c * dx + s * dy, -s * dx + c * dy, point.z - self.location.z)


def vehicle_with_wheels(
    wheels: list[SimpleNamespace],
    transform: FakeTransform | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        bounding_box=SimpleNamespace(
            extent=vector(2.35, 0.95, 0.75),
            location=vector(0.05, 0.0, 0.78),
        ),
        get_transform=lambda: transform or FakeTransform(0.0, 0.0, 0.0, 0.0),
        get_physics_control=lambda: SimpleNamespace(wheels=wheels),
    )


def local_wheel_positions() -> tuple[SimpleNamespace, ...]:
    return (
        vector(1.45, -0.80, 0.35),
        vector(1.45, 0.80, 0.35),
        vector(-1.40, -0.80, 0.35),
        vector(-1.40, 0.80, 0.35),
    )


def test_geometry_adapter_converts_world_centimetre_wheels_to_actor_frame() -> None:
    transform = FakeTransform(0.0, 0.0, 0.4, 90.0)
    local_positions = local_wheel_positions()
    world_centimetres = [
        SimpleNamespace(
            position=vector(world.x * 100.0, world.y * 100.0, world.z * 100.0)
        )
        for world in (
            transform.transform(local_positions[2]),
            transform.transform(local_positions[0]),
            transform.transform(local_positions[3]),
            transform.transform(local_positions[1]),
        )
    ]

    geometry = VehicleGeometryAdapter().extract(
        vehicle_with_wheels(world_centimetres, transform)
    )

    assert geometry.wheelbase_m == pytest.approx(2.85)
    assert geometry.front_track_width_m == pytest.approx(1.60)
    assert geometry.rear_axle_center_m.x == pytest.approx(-1.40)
    assert geometry.wheel_position_reference == "world_to_actor"
    assert geometry.wheel_position_scale == pytest.approx(0.01)


def test_geometry_adapter_keeps_actor_local_centimetre_compatibility() -> None:
    local_centimetres = [
        SimpleNamespace(position=vector(point.x * 100, point.y * 100, point.z * 100))
        for point in reversed(local_wheel_positions())
    ]
    geometry = VehicleGeometryAdapter().extract(
        vehicle_with_wheels(
            local_centimetres,
            FakeTransform(120.0, 80.0, 0.4, -35.0),
        )
    )

    assert geometry.wheelbase_m == pytest.approx(2.85)
    assert geometry.rear_track_width_m == pytest.approx(1.60)
    assert geometry.wheel_position_reference == "actor_local"


def test_geometry_adapter_resolves_roof_pose_from_normalized_geometry() -> None:
    wheels = [
        SimpleNamespace(position=vector(point.x * 100, point.y * 100, point.z * 100))
        for point in local_wheel_positions()
    ]
    adapter = VehicleGeometryAdapter()
    geometry = adapter.extract(vehicle_with_wheels(wheels))
    sensor = SensorDefinition(
        sensor_id="lidar_roof",
        sensor_type="lidar_64_channel",
        normalized_position=NormalizedSensorPosition(0.45, 0.0, 1.0, 0.1),
        orientation_rpy_deg=(0.0, 0.0, 0.0),
        attributes={"sensor_tick": "0.04"},
    )

    pose = adapter.resolve_sensor_pose(geometry, sensor)

    assert pose.location_m.x == pytest.approx(-0.1175)
    assert pose.location_m.z == pytest.approx(1.63)
