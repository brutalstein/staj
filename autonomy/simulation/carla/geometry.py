from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite, sqrt
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
    wheel_position_reference: str
    wheel_position_scale: float

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
            "wheel_position_reference": self.wheel_position_reference,
            "wheel_position_scale": self.wheel_position_scale,
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


@dataclass(frozen=True, slots=True)
class _WheelCandidate:
    reference: str
    ordered_positions: tuple[Vector3, Vector3, Vector3, Vector3]
    score: float


class VehicleGeometryAdapter:
    """CARLA bounding box ve teker konumlarını ego-rear-axle geometrisine dönüştürür."""

    _MIN_DIMENSION_M = 0.1
    _MIN_WHEELBASE_M = 0.5
    _MAX_CANDIDATE_SCORE = 25.0

    def extract(
        self,
        vehicle: Any,
        pre_tick_fn: Any = None,
    ) -> VehicleGeometry:
        """Ego-aracından geometri çıkarır.

        Args:
            vehicle: CARLA araç aktörü.
            pre_tick_fn: Opsiyonel.  Actor transform okunmadan önce çağrılacak
                callable (örn. ``world.tick``).  CARLA synchronous modda araç
                spawn edilir edilmez ``get_transform()`` henüz dünya konumunu
                yansıtmaz; bir tick ile güncellenir.  Test mock'larında bu
                parametreyi geçmeyerek eski davranış korunur.
        """
        try:
            bounding_box = vehicle.bounding_box
            extent = bounding_box.extent
            center = bounding_box.location
            if pre_tick_fn is not None:
                pre_tick_fn()
            actor_transform = vehicle.get_transform()
            wheels = tuple(vehicle.get_physics_control().wheels)
        except VehicleGeometryError:
            raise
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
        wheel_candidate = self._select_wheel_candidate(
            actor_transform,
            raw_positions,
            scale,
            box_center,
            half_extents,
        )
        wheel_positions = wheel_candidate.ordered_positions
        front_axle = self._average(wheel_positions[0], wheel_positions[1])
        rear_axle = self._average(wheel_positions[2], wheel_positions[3])
        wheelbase = front_axle.x - rear_axle.x
        if not isfinite(wheelbase) or wheelbase < self._MIN_WHEELBASE_M:
            raise VehicleGeometryError(
                "CARLA teker geometrisi beklenen ego x-forward düzeniyle uyuşmuyor: "
                f"front_x={front_axle.x:.3f}, rear_x={rear_axle.x:.3f}, "
                f"reference={wheel_candidate.reference}."
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
            wheel_positions_m=wheel_positions,
            wheel_position_reference=wheel_candidate.reference,
            wheel_position_scale=scale,
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
            raise VehicleGeometryError(
                f"{sensor.sensor_id}: x={location.x:.3f} m araç zarfının dışında; "
                f"izin verilen=[{min_x - longitudinal_margin:.3f}, "
                f"{max_x + longitudinal_margin:.3f}], "
                f"rear_axle={geometry.rear_axle_center_m.x:.3f}, "
                f"wheelbase={geometry.wheelbase_m:.3f}, "
                f"wheel_reference={geometry.wheel_position_reference}."
            )
        if abs(location.y - geometry.bounding_box_center_m.y) > (
            geometry.half_extents_m.y + lateral_margin
        ):
            raise VehicleGeometryError(
                f"{sensor.sensor_id}: y={location.y:.3f} m araç zarfının dışında."
            )
        if not geometry.body_bottom_z_m - 0.2 <= location.z <= (
            geometry.body_bottom_z_m + geometry.body_height_m + vertical_margin
        ):
            raise VehicleGeometryError(
                f"{sensor.sensor_id}: z={location.z:.3f} m araç zarfının dışında."
            )

        roll, pitch, yaw = sensor.orientation_rpy_deg
        return ResolvedSensorPose(sensor.sensor_id, location, roll, pitch, yaw)

    def _select_wheel_candidate(
        self,
        actor_transform: Any,
        raw_positions: tuple[Vector3, Vector3, Vector3, Vector3],
        scale: float,
        box_center: Vector3,
        half_extents: Vector3,
    ) -> _WheelCandidate:
        # Raw positions need to be in metres for the geometry scoring to be
        # comparable against box_center (which is already in actor-local metres).
        metres_positions = tuple(
            Vector3(p.x * scale, p.y * scale, p.z * scale) for p in raw_positions
        )

        # Candidate A — actor_local
        # Hypothesis: WheelPhysicsControl.position values are actor-local centimetres.
        # After scaling to metres they are actor-local metres, directly comparable
        # with box_center and half_extents.
        candidates = [
            self._build_candidate(
                "actor_local",
                metres_positions,  # type: ignore[arg-type]
                box_center,
                half_extents,
            )
        ]

        # Candidate B — world_to_actor
        # Hypothesis: WheelPhysicsControl.position values are world-space centimetres
        # (observed in this custom CARLA build).  Steps:
        #   1. Scale raw cm → world-space metres  (already done → metres_positions)
        #   2. Apply inverse_transform to convert world metres → actor-local metres.
        # CARLA's inverse_transform operates in metres, so metres_positions must be
        # passed — NOT the raw centimetre values.
        world_transform_error = None
        try:
            local_from_world = tuple(
                self._inverse_transform(actor_transform, p) for p in metres_positions
            )
        except Exception as exc:
            world_transform_error = exc
        else:
            candidates.append(
                self._build_candidate(
                    "world_to_actor",
                    local_from_world,  # type: ignore[arg-type]
                    box_center,
                    half_extents,
                )
            )

        best = min(candidates, key=lambda candidate: candidate.score)
        if best.score > self._MAX_CANDIDATE_SCORE:
            details = ", ".join(
                f"{candidate.reference}={candidate.score:.2f}" for candidate in candidates
            )
            if world_transform_error is not None:
                details += f", inverse_transform_error={world_transform_error}"
            raise VehicleGeometryError(
                "CARLA teker koordinat referansı güvenilir biçimde çözülemedi: " + details
            )
        return best

    def _build_candidate(
        self,
        reference: str,
        positions: tuple[Vector3, Vector3, Vector3, Vector3],
        box_center: Vector3,
        half_extents: Vector3,
    ) -> _WheelCandidate:
        sorted_by_x = sorted(positions, key=lambda position: position.x, reverse=True)
        front_pair = sorted(sorted_by_x[:2], key=lambda position: position.y)
        rear_pair = sorted(sorted_by_x[2:], key=lambda position: position.y)
        ordered = (front_pair[0], front_pair[1], rear_pair[0], rear_pair[1])
        front_axle = self._average(ordered[0], ordered[1])
        rear_axle = self._average(ordered[2], ordered[3])
        wheelbase = front_axle.x - rear_axle.x
        front_track = abs(ordered[0].y - ordered[1].y)
        rear_track = abs(ordered[2].y - ordered[3].y)

        score = 0.0
        score += abs(ordered[0].x - ordered[1].x) * 10.0
        score += abs(ordered[2].x - ordered[3].x) * 10.0
        score += abs(front_axle.y - box_center.y) * 2.0
        score += abs(rear_axle.y - box_center.y) * 2.0
        score += self._outside_penalty(front_axle.x, box_center.x, half_extents.x, 0.8)
        score += self._outside_penalty(rear_axle.x, box_center.x, half_extents.x, 0.8)
        score += self._outside_penalty(front_axle.y, box_center.y, half_extents.y, 0.5)
        score += self._outside_penalty(rear_axle.y, box_center.y, half_extents.y, 0.5)
        body_length = 2.0 * half_extents.x
        body_width = 2.0 * half_extents.y
        wheelbase_ratio = wheelbase / body_length
        front_track_ratio = front_track / body_width
        rear_track_ratio = rear_track / body_width
        if not 0.40 <= wheelbase_ratio <= 0.90:
            score += 100.0
        if not 0.50 <= front_track_ratio <= 1.20:
            score += 100.0
        if not 0.50 <= rear_track_ratio <= 1.20:
            score += 100.0
        return _WheelCandidate(reference, ordered, score)

    @staticmethod
    def _outside_penalty(value: float, center: float, half_extent: float, margin: float) -> float:
        distance = abs(value - center) - (half_extent + margin)
        return max(0.0, distance) * 20.0

    @staticmethod
    def _inverse_transform(actor_transform: Any, position: Vector3) -> Vector3:
        """World-space pozisyonu actor-local frame'e çevirir.

        position değerleri raw (ölçeksiz) olmalıdır; scale bu çağrıdan sonra uygulanır.
        """
        location_type = type(actor_transform.location)
        point = location_type(x=position.x, y=position.y, z=position.z)
        local = actor_transform.inverse_transform(point)
        return Vector3(float(local.x), float(local.y), float(local.z))

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
        maximum_separation = max(
            sqrt(
                (first.x - second.x) ** 2
                + (first.y - second.y) ** 2
                + (first.z - second.z) ** 2
            )
            for index, first in enumerate(wheel_positions)
            for second in wheel_positions[index + 1 :]
        )
        # WheelPhysicsControl.position has historically been exposed in centimetres
        # in CARLA/PhysX builds, while actor transforms and bounding boxes use metres.
        # Pairwise separation is translation/rotation invariant and therefore works
        # for both world-space and actor-local wheel coordinates.
        if maximum_separation > max(20.0, body_length_m * 4.0):
            return 0.01
        return 1.0
