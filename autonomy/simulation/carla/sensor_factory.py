from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

from autonomy.configuration.loader import SensorDefinition, SensorLayoutConfiguration
from autonomy.sensing.gateway import SensorGateway
from autonomy.simulation.carla.adapter import CarlaConnectionError
from autonomy.simulation.carla.geometry import (
    ResolvedSensorPose,
    VehicleGeometry,
    VehicleGeometryAdapter,
)

LOGGER = logging.getLogger(__name__)


class SensorFactoryError(CarlaConnectionError):
    """Sensör blueprint, attribute veya actor oluşturma hatası."""


@dataclass(frozen=True, slots=True)
class SpawnedSensor:
    definition: SensorDefinition
    pose: ResolvedSensorPose
    actor: Any


class CarlaSensorFactory:
    """Doğrulanmış layout tanımlarını CARLA sensör aktörlerine dönüştürür."""

    BLUEPRINT_BY_TYPE = {
        "rgb_camera": "sensor.camera.rgb",
        "lidar_64_channel": "sensor.lidar.ray_cast",
        "4d_radar_proxy": "sensor.other.radar",
        "gnss": "sensor.other.gnss",
        "imu": "sensor.other.imu",
    }

    def __init__(
        self,
        carla_module: Any,
        world: Any,
        geometry_adapter: VehicleGeometryAdapter,
        gateway: SensorGateway,
    ) -> None:
        self._carla = carla_module
        self._world = world
        self._geometry_adapter = geometry_adapter
        self._gateway = gateway

    def spawn_all(
        self,
        vehicle: Any,
        geometry: VehicleGeometry,
        layout: SensorLayoutConfiguration,
    ) -> tuple[SpawnedSensor, ...]:
        spawned: list[SpawnedSensor] = []
        try:
            for definition in layout.sensors:
                spawned.append(self._spawn_one(vehicle, geometry, definition))
        except Exception:
            self.destroy_all(tuple(spawned))
            self._gateway.clear()
            raise
        return tuple(spawned)

    def _spawn_one(
        self,
        vehicle: Any,
        geometry: VehicleGeometry,
        definition: SensorDefinition,
    ) -> SpawnedSensor:
        blueprint_id = self.BLUEPRINT_BY_TYPE[definition.sensor_type]
        try:
            blueprint = self._world.get_blueprint_library().find(blueprint_id)
        except Exception as exc:
            raise SensorFactoryError(
                f"{definition.sensor_id}: CARLA blueprint bulunamadı: {blueprint_id}."
            ) from exc

        for name, value in definition.attributes.items():
            try:
                if hasattr(blueprint, "has_attribute") and not blueprint.has_attribute(name):
                    raise SensorFactoryError(
                        f"{definition.sensor_id}: {blueprint_id} '{name}' "
                        "attribute'unu desteklemiyor."
                    )
                blueprint.set_attribute(name, value)
            except SensorFactoryError:
                raise
            except Exception as exc:
                raise SensorFactoryError(
                    f"{definition.sensor_id}: blueprint attribute ayarlanamadı: {name}={value}."
                ) from exc

        pose = self._geometry_adapter.resolve_sensor_pose(geometry, definition)
        transform = self._carla.Transform(
            self._carla.Location(
                x=pose.location_m.x,
                y=pose.location_m.y,
                z=pose.location_m.z,
            ),
            self._carla.Rotation(
                roll=pose.roll_deg,
                pitch=pose.pitch_deg,
                yaw=pose.yaw_deg,
            ),
        )
        self._gateway.register_sensor(definition.sensor_id, definition.sensor_type)
        actor = None
        try:
            actor = self._world.spawn_actor(
                blueprint,
                transform,
                attach_to=vehicle,
                attachment_type=self._carla.AttachmentType.Rigid,
            )
            actor.listen(self._gateway.callback_for(definition.sensor_id))
        except Exception as exc:
            if actor is not None:
                try:
                    if getattr(actor, "is_alive", True):
                        actor.destroy()
                except Exception:
                    LOGGER.exception(
                        "Başarısız sensör spawn cleanup hatası: %s",
                        definition.sensor_id,
                    )
            raise SensorFactoryError(
                f"{definition.sensor_id}: sensör aktörü oluşturulamadı."
            ) from exc
        return SpawnedSensor(definition, pose, actor)

    @staticmethod
    def destroy_all(spawned: tuple[SpawnedSensor, ...]) -> tuple[str, ...]:
        errors: list[str] = []
        for sensor in reversed(spawned):
            actor = sensor.actor
            try:
                listening = getattr(actor, "is_listening", False)
                listening = listening() if callable(listening) else bool(listening)
                if listening and hasattr(actor, "stop"):
                    actor.stop()
            except Exception as exc:  # cleanup diğer aktörler için devam etmelidir
                errors.append(f"{sensor.definition.sensor_id}: stop: {exc}")
            try:
                if getattr(actor, "is_alive", True):
                    actor.destroy()
            except Exception as exc:
                errors.append(f"{sensor.definition.sensor_id}: destroy: {exc}")
        if errors:
            LOGGER.error("Sensör cleanup hataları: %s", "; ".join(errors))
        return tuple(errors)
