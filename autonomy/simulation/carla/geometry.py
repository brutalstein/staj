from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite
from typing import Any

from autonomy.configuration.loader import SensorDefinition
from autonomy.simulation.carla.adapter import CarlaConnectionError


class VehicleGeometryError(CarlaConnectionError):
    """CARLA aktör geometrisi güvenilir biçimde çıkarılamadığında üretilir."""


@dataclass(frozen=True, slots=True)
class Vector3:
    x: float
    y: float
    z: float

    def as_dict(self) -> dict[str, float]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class VehicleGeometry:
    """CARLA aktöründen çalışma zamanında çıkarılan araç geometrisi."""

    bounding_box_center_m: Vector3
    half_extents_m: Vector3
    body_length_m: float
    body_width_m: float
    body_height_m: float
    body_bottom_z_m: float
    rear_axle_center_m: Vector3
    front_axle_center_m: Vector3
    wheelbase_m: float
    front_track_width_m: float
    rear_track_width_m: float
    wheel_positions_m: tuple[Vector3, Vector3, Vector3, Vector3]

    def as_dict(self) -> dict[str, object]:
        return {
            "bounding_box_center_m": self.bounding_box_center_m.as_dict(),
            "half_extents_m": self.half_extents_m.as_dict(),
            "body_length_m": self.body_length_m,
            "body_width_m": self.body_width_m,
            "body_height_m": self.body_height_m,
            "body_bottom_z_m": self.body_bottom_z_m,
            "rear_axle_center_m": self.rear_axle_center_m.as_dict(),
            "front_axle_center_m": self.front_axle_center_m.as_dict(),
            "wheelbase_m": self.wheelbase_m,
            "front_track_width_m": self.front_track_width_m,
            "rear_track_width_m": self.rear_track_width_m,
            "wheel_positions_m": [position.as_dict() for position in self.wheel_positions_m],
        }


@dataclass(frozen=True, slots=True)
class ResolvedSensorPose:
    sensor_id: str
    location_m: Vector3
    roll_deg: float
    pitch_deg: float
    yaw_deg: float

    def as_dict(self) -> dict[str, object]:
        return {
            "sensor_id": self.sensor_id,
            "location_m": self.location_m.as_dict(),
            "rotation_deg": {
                "roll": self.roll_deg,
                "pitch": self.pitch_deg,
                "yaw": self.yaw_deg,
            },
        }


class VehicleGeometryAdapter:
    """CARLA bounding box ve teker konumlarını ego-rear-axle geometrisine dönüştürür."""

    _MIN_DIMENSION_M = 0.1
    _MIN_WHEELBASE_M = 0.5

    def extract(self, vehicle: Any) -> VehicleGeometry:
        try:
            bounding_box = vehicle.bounding_box
            extent = bounding_box.extent
            center = bounding_box.location
            wheels = tuple(vehicle.get_physics_control().wheels)
        except Exception as exc:
            raise VehicleGeometryError("Araç geometrisi CARLA aktöründen okunamadı.") from exc

        if len(wheels) < 4:
            raise VehicleGeometryError(
                f"Dört teker geometrisi bekleniyordu; CARLA {len(wheels)} teker döndürdü."
            )

        half_extents = Vector3(float(extent.x), float(extent.y), float(extent.z))
        box_center = Vector3(float(center.x), float(center.y), float(center.z))
        dimensions = (
            2.0 * half_extents.x,
            2.0 * half_extents.y,
            2.0 * half_extents.z,
        )
        if any(not isfinite(value) or value < self._MIN_DIMENSION_M for value in dimensions):
            raise VehicleGeometryError(f"Geçersiz CARLA bounding box boyutları: {dimensions}")

        raw_positions = tuple(
            Vector3(
                float(wheel.position.x),
                float(wheel.position.y),
                float(wheel.position.z),
            )
            for wheel in wheels[:4]
        )
        scale = self._wheel_position_scale(raw_positions, dimensions[0])
        wheel_positions = tuple(
            Vector3(position.x * scale, position.y * scale, position.z * scale)
            for position in raw_positions
        )
        front_axle = self._average(wheel_positions[0], wheel_positions[1])
        rear_axle = self._average(wheel_positions[2], wheel_positions[3])
        wheelbase = front_axle.x - rear_axle.x
        if not isfinite(wheelbase) or wheelbase < self._MIN_WHEELBASE_M:
            raise VehicleGeometryError(
                "CARLA teker sırası/ölçeği beklenen ego x-forward geometrisiyle uyuşmuyor: "
                f"front_x={front_axle.x:.3f}, rear_x={rear_axle.x:.3f}."
            )

        front_track = abs(wheel_positions[0].y - wheel_positions[1].y)
        rear_track = abs(wheel_positions[2].y - wheel_positions[3].y)
        if min(front_track, rear_track) < self._MIN_DIMENSION_M:
            raise VehicleGeometryError(
                f"Geçersiz teker iz genişliği: front={front_track}, rear={rear_track}."
            )

        return VehicleGeometry(
            bounding_box_center_m=box_center,
            half_extents_m=half_extents,
            body_length_m=dimensions[0],
            body_width_m=dimensions[1],
            body_height_m=dimensions[2],
            body_bottom_z_m=box_center.z - half_extents.z,
            rear_axle_center_m=rear_axle,
            front_axle_center_m=front_axle,
            wheelbase_m=wheelbase,
            front_track_width_m=front_track,
            rear_track_width_m=rear_track,
            wheel_positions_m=wheel_positions,  # type: ignore[arg-type]
        )

    def resolve_sensor_pose(
        self,
        geometry: VehicleGeometry,
        sensor: SensorDefinition,
    ) -> ResolvedSensorPose:
        position = sensor.normalized_position
        location = Vector3(
            x=geometry.rear_axle_center_m.x
            + position.wheelbase_ratio_x * geometry.wheelbase_m,
            y=geometry.bounding_box_center_m.y
            + position.vehicle_width_ratio_y * geometry.body_width_m,
            z=geometry.body_bottom_z_m
            + position.vehicle_height_ratio_z * geometry.body_height_m
            + position.additional_height_m,
        )
        values = (*location.as_dict().values(), *sensor.orientation_rpy_deg)
        if any(not isfinite(float(value)) for value in values):
            raise VehicleGeometryError(f"{sensor.sensor_id}: çözümlenen sensör pozu sonlu değil.")

        longitudinal_margin = 2.0
        lateral_margin = 1.0
        vertical_margin = 2.0
        min_x = geometry.bounding_box_center_m.x - geometry.half_extents_m.x
        max_x = geometry.bounding_box_center_m.x + geometry.half_extents_m.x
        if not min_x - longitudinal_margin <= location.x <= max_x + longitudinal_margin:
            raise VehicleGeometryError(f"{sensor.sensor_id}: x konumu araç zarfının dışında.")
        if abs(location.y - geometry.bounding_box_center_m.y) > (
            geometry.half_extents_m.y + lateral_margin
        ):
            raise VehicleGeometryError(f"{sensor.sensor_id}: y konumu araç zarfının dışında.")
        if not geometry.body_bottom_z_m - 0.2 <= location.z <= (
            geometry.body_bottom_z_m + geometry.body_height_m + vertical_margin
        ):
            raise VehicleGeometryError(f"{sensor.sensor_id}: z konumu araç zarfının dışında.")

        roll, pitch, yaw = sensor.orientation_rpy_deg
        return ResolvedSensorPose(sensor.sensor_id, location, roll, pitch, yaw)

    @staticmethod
    def _average(first: Vector3, second: Vector3) -> Vector3:
        return Vector3(
            (first.x + second.x) / 2.0,
            (first.y + second.y) / 2.0,
            (first.z + second.z) / 2.0,
        )

    @staticmethod
    def _wheel_position_scale(
        wheel_positions: tuple[Vector3, Vector3, Vector3, Vector3],
        body_length_m: float,
    ) -> float:
        front_x = (wheel_positions[0].x + wheel_positions[1].x) / 2.0
        rear_x = (wheel_positions[2].x + wheel_positions[3].x) / 2.0
        raw_wheelbase = abs(front_x - rear_x)
        # CARLA/PhysX wheel positions are commonly exposed in centimetres while
        # actor transforms and bounding boxes use metres. The ratio check keeps
        # compatibility with builds that already expose metre values.
        if raw_wheelbase > max(20.0, body_length_m * 4.0):
            return 0.01
        return 1.0
