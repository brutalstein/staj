from __future__ import annotations

from dataclasses import dataclass
import logging
from math import hypot, lcm
from typing import Any

from autonomy.configuration.loader import ProjectConfiguration
from autonomy.contracts.runtime import ComponentState
from autonomy.recording import RunRecorder
from autonomy.runtime.lifecycle import BaseService
from autonomy.sensing.gateway import SensorGateway
from autonomy.sensing.synchronization import FrameSynchronizer, SynchronizedMeasurements
from autonomy.simulation.carla.adapter import CarlaAdapter, CarlaConnectionError
from autonomy.simulation.carla.geometry import VehicleGeometry, VehicleGeometryAdapter
from autonomy.simulation.carla.sensor_factory import CarlaSensorFactory, SpawnedSensor

LOGGER = logging.getLogger(__name__)


class CarlaPhase1Error(CarlaConnectionError):
    """Faz 1 synchronous runtime başlatma, tick veya cleanup hatası."""


@dataclass(frozen=True, slots=True)
class Phase1TickResult:
    simulation_frame: int
    timestamp_seconds: float
    synchronized: SynchronizedMeasurements | None
    vehicle_feedback: dict[str, Any]


class CarlaPhase1Runtime(BaseService):
    """Tek CARLA tick sahibi; ego, sensör, sync ve recorder yaşam döngüsünü yönetir."""

    def __init__(self, adapter: CarlaAdapter, configuration: ProjectConfiguration) -> None:
        super().__init__(component_id="carla_phase1_runtime")
        self._adapter = adapter
        self._configuration = configuration
        self._world: Any = None
        self._carla: Any = None
        self._original_world_settings: Any = None
        self._vehicle: Any = None
        self._geometry: VehicleGeometry | None = None
        self._spawned_sensors: tuple[SpawnedSensor, ...] = ()
        self._gateway: SensorGateway | None = None
        self._synchronizer: FrameSynchronizer | None = None
        self._recorder = RunRecorder(configuration.phase1.recording)
        self._sensor_factory: CarlaSensorFactory | None = None
        self._synchronization_stride = 1
        self._next_synchronization_frame: int | None = None
        self._consecutive_sync_misses = 0
        self._shutdown_status = "COMPLETED"

    @property
    def vehicle(self) -> Any:
        if self._vehicle is None:
            raise CarlaPhase1Error("Ego araç henüz oluşturulmadı.")
        return self._vehicle

    @property
    def geometry(self) -> VehicleGeometry:
        if self._geometry is None:
            raise CarlaPhase1Error("Araç geometrisi henüz çıkarılmadı.")
        return self._geometry

    @property
    def sensor_count(self) -> int:
        return len(self._spawned_sensors)

    @property
    def recorder_run_directory(self):
        return self._recorder.run_directory

    def on_initialize(self) -> None:
        self._shutdown_status = "COMPLETED"
        self._world = self._adapter.world
        self._carla = self._adapter.carla_module
        required = tuple(
            sensor.sensor_id
            for sensor in self._configuration.phase1.sensor_layout.sensors
            if sensor.required_for_synchronization
        )
        if not required:
            raise CarlaPhase1Error("Senkronizasyon için zorunlu sensör tanımlı değil.")

        strides = []
        fixed_delta = self._configuration.runtime.fixed_delta_seconds
        for sensor in self._configuration.phase1.sensor_layout.sensors:
            if sensor.required_for_synchronization:
                strides.append(round(sensor.sensor_tick_seconds() / fixed_delta))
        self._synchronization_stride = lcm(*strides)
        self._gateway = SensorGateway(self._configuration.phase1.sensor_buffer_capacity)
        self._synchronizer = FrameSynchronizer(
            gateway=self._gateway,
            required_sensor_ids=required,
            coordinate_frame=self._configuration.phase1.sensor_layout.reference_frame,
            configuration_hash=self._configuration.configuration_hash,
        )

    def on_start(self) -> None:
        if self._world is None or self._carla is None or self._gateway is None:
            raise CarlaPhase1Error("Faz 1 runtime initialize edilmeden başlatılamaz.")
        try:
            self._enable_synchronous_mode()
            self._vehicle = self._spawn_ego_vehicle()
            geometry_adapter = VehicleGeometryAdapter()
            self._geometry = geometry_adapter.extract(self._vehicle)
            self._sensor_factory = CarlaSensorFactory(
                self._carla,
                self._world,
                geometry_adapter,
                self._gateway,
            )
            self._spawned_sensors = self._sensor_factory.spawn_all(
                self._vehicle,
                self._geometry,
                self._configuration.phase1.sensor_layout,
            )
            self._start_recorder()
            LOGGER.info(
                "Faz 1 hazır: ego_actor=%s sensors=%s sync_stride=%s recorder=%s",
                self._vehicle.id,
                len(self._spawned_sensors),
                self._synchronization_stride,
                self._recorder.run_directory,
            )
        except Exception as exc:
            self._shutdown_status = "FAILED"
            self._cleanup(status="FAILED", raise_on_error=False)
            if isinstance(exc, CarlaConnectionError):
                raise
            raise CarlaPhase1Error("Faz 1 kaynakları başlatılamadı.") from exc

    def tick(self) -> Phase1TickResult:
        try:
            return self._tick_once()
        except Exception as exc:
            self._shutdown_status = "FAILED"
            if isinstance(exc, CarlaPhase1Error):
                raise
            raise CarlaPhase1Error("Faz 1 tick işlemi başarısız.") from exc

    def _tick_once(self) -> Phase1TickResult:
        if self.state is not ComponentState.RUNNING:
            raise CarlaPhase1Error(f"Runtime RUNNING değil: {self.state}.")
        if self._world is None or self._synchronizer is None:
            raise CarlaPhase1Error("Runtime kaynakları hazır değil.")

        try:
            reported_frame = int(self._world.tick(self._configuration.carla.timeout_seconds))
            snapshot = self._world.get_snapshot()
            frame = int(getattr(snapshot, "frame", reported_frame))
            timestamp = float(snapshot.timestamp.elapsed_seconds)
        except Exception as exc:
            raise CarlaPhase1Error("CARLA synchronous world tick başarısız.") from exc

        feedback = self._read_vehicle_feedback(frame, timestamp)
        synchronized = None
        synchronization_due = (
            self._next_synchronization_frame is None
            or frame >= self._next_synchronization_frame
        )
        if synchronization_due:
            try:
                synchronized = self._synchronizer.collect(
                    maximum_frame=frame,
                    timeout_seconds=self._configuration.phase1.synchronization_timeout_seconds,
                )
            except Exception as exc:
                raise CarlaPhase1Error(f"Sensör frame senkronizasyonu başarısız: {exc}") from exc
            if synchronized is None:
                self._consecutive_sync_misses += 1
                if (
                    self._consecutive_sync_misses
                    >= self._configuration.phase1.maximum_consecutive_sync_misses
                ):
                    raise CarlaPhase1Error(
                        "Zorunlu sensörler ortak frame üretemedi; "
                        f"ardışık kaçırma={self._consecutive_sync_misses}."
                    )
            else:
                self._consecutive_sync_misses = 0
                self._next_synchronization_frame = (
                    synchronized.contract.metadata.simulation_frame
                    + self._synchronization_stride
                )
                self._recorder.record(synchronized, feedback)

        return Phase1TickResult(frame, timestamp, synchronized, feedback)

    def on_stop(self) -> None:
        self._cleanup(status=self._shutdown_status, raise_on_error=True)

    def _enable_synchronous_mode(self) -> None:
        if self._world is None:
            raise CarlaPhase1Error("CARLA world hazır değil.")
        try:
            self._original_world_settings = self._world.get_settings()
            settings = self._world.get_settings()
            settings.synchronous_mode = True
            settings.fixed_delta_seconds = self._configuration.runtime.fixed_delta_seconds
            self._world.apply_settings(settings)
        except Exception as exc:
            raise CarlaPhase1Error("CARLA synchronous mode etkinleştirilemedi.") from exc

    def _spawn_ego_vehicle(self) -> Any:
        if self._world is None:
            raise CarlaPhase1Error("CARLA world hazır değil.")
        vehicle_config = self._configuration.phase1.vehicle
        try:
            blueprint = self._world.get_blueprint_library().find(
                vehicle_config.carla_blueprint
            )
            if hasattr(blueprint, "has_attribute") and blueprint.has_attribute("role_name"):
                blueprint.set_attribute("role_name", vehicle_config.role_name)
            spawn_points = tuple(self._world.get_map().get_spawn_points())
        except Exception as exc:
            raise CarlaPhase1Error("Ego blueprint veya spawn noktaları okunamadı.") from exc
        if not spawn_points:
            raise CarlaPhase1Error("Haritada ego araç için spawn noktası bulunmuyor.")

        start = self._configuration.phase1.spawn_point_index % len(spawn_points)
        vehicle = None
        for offset in range(len(spawn_points)):
            transform = spawn_points[(start + offset) % len(spawn_points)]
            try:
                vehicle = self._world.try_spawn_actor(blueprint, transform)
            except Exception as exc:
                raise CarlaPhase1Error("Ego araç spawn RPC çağrısı başarısız.") from exc
            if vehicle is not None:
                break
        if vehicle is None:
            raise CarlaPhase1Error("Hiçbir CARLA spawn noktası ego araç için boş değil.")

        try:
            if hasattr(vehicle, "set_autopilot"):
                vehicle.set_autopilot(False)
            if vehicle_config.hold_brake_on_start:
                vehicle.apply_control(
                    self._carla.VehicleControl(
                        throttle=0.0,
                        steer=0.0,
                        brake=1.0,
                        hand_brake=True,
                    )
                )
        except Exception as exc:
            try:
                vehicle.destroy()
            finally:
                raise CarlaPhase1Error("Ego başlangıç güvenlik kontrolü uygulanamadı.") from exc
        return vehicle

    def _start_recorder(self) -> None:
        if self._vehicle is None or self._geometry is None:
            raise CarlaPhase1Error("Recorder için ego araç/geometri hazır değil.")
        info = self._adapter.server_info
        sensor_descriptions = tuple(
            {
                "sensor_id": sensor.definition.sensor_id,
                "sensor_type": sensor.definition.sensor_type,
                "carla_blueprint": CarlaSensorFactory.BLUEPRINT_BY_TYPE[
                    sensor.definition.sensor_type
                ],
                "required_for_synchronization": sensor.definition.required_for_synchronization,
                "attributes": dict(sensor.definition.attributes),
                "pose": sensor.pose.as_dict(),
                "actor_id": sensor.actor.id,
            }
            for sensor in self._spawned_sensors
        )
        self._recorder.start(
            configuration_hash=self._configuration.configuration_hash,
            configuration_sources={
                "runtime": str(self._configuration.source_path),
                "vehicle": str(self._configuration.phase1.vehicle.source_path),
                "sensor_layout": str(
                    self._configuration.phase1.sensor_layout.source_path
                ),
            },
            map_name=info.map_name,
            client_version=info.client_version,
            server_version=info.server_version,
            compatibility_version=info.compatibility_version,
            vehicle_id=self._configuration.phase1.vehicle.vehicle_id,
            vehicle_blueprint=self._configuration.phase1.vehicle.carla_blueprint,
            vehicle_role_name=self._configuration.phase1.vehicle.role_name,
            vehicle_actor_id=int(self._vehicle.id),
            sensor_layout_id=self._configuration.phase1.sensor_layout.layout_id,
            reference_frame=self._configuration.phase1.sensor_layout.reference_frame,
            geometry=self._geometry,
            sensor_descriptions=sensor_descriptions,
            fixed_delta_seconds=self._configuration.runtime.fixed_delta_seconds,
        )

    def _read_vehicle_feedback(self, frame: int, timestamp: float) -> dict[str, Any]:
        vehicle = self.vehicle
        try:
            transform = vehicle.get_transform()
            velocity = vehicle.get_velocity()
            acceleration = vehicle.get_acceleration()
            angular_velocity = vehicle.get_angular_velocity()
            control = vehicle.get_control()
        except Exception as exc:
            raise CarlaPhase1Error("Ego araç geri bildirimi okunamadı.") from exc

        steering_angle_deg = None
        try:
            wheel_location = self._carla.VehicleWheelLocation
            left = float(vehicle.get_wheel_steer_angle(wheel_location.FL_Wheel))
            right = float(vehicle.get_wheel_steer_angle(wheel_location.FR_Wheel))
            steering_angle_deg = (left + right) / 2.0
        except (AttributeError, RuntimeError, TypeError, ValueError):
            # 0.9.15 uyumluluğunda gerçek wheel angle API bulunmayabilir;
            # normalize control.steer yine kaydedilir.
            steering_angle_deg = None

        speed = hypot(float(velocity.x), float(velocity.y), float(velocity.z))
        dropped_counts = self._gateway.dropped_counts() if self._gateway is not None else {}
        return {
            "simulation_frame": frame,
            "timestamp_seconds": timestamp,
            "transform": {
                "location_m": self._vector_dict(transform.location),
                "rotation_deg": {
                    "roll": float(transform.rotation.roll),
                    "pitch": float(transform.rotation.pitch),
                    "yaw": float(transform.rotation.yaw),
                },
            },
            "linear_velocity_mps": self._vector_dict(velocity),
            "speed_mps": speed,
            "acceleration_mps2": self._vector_dict(acceleration),
            "angular_velocity_degps": self._vector_dict(angular_velocity),
            "sensor_buffer_dropped_counts": dropped_counts,
            "actuation": {
                "throttle": float(control.throttle),
                "steer_normalized": float(control.steer),
                "brake": float(control.brake),
                "hand_brake": bool(control.hand_brake),
                "reverse": bool(control.reverse),
                "gear": int(control.gear),
                "steering_angle_deg": steering_angle_deg,
            },
        }

    def _cleanup(self, status: str, raise_on_error: bool) -> None:
        errors: list[str] = []
        if self._sensor_factory is not None and self._spawned_sensors:
            errors.extend(self._sensor_factory.destroy_all(self._spawned_sensors))
        self._spawned_sensors = ()
        if self._gateway is not None:
            self._gateway.clear()

        if self._vehicle is not None:
            try:
                if getattr(self._vehicle, "is_alive", True):
                    self._vehicle.destroy()
            except Exception as exc:
                errors.append(f"ego destroy: {exc}")
            finally:
                self._vehicle = None

        try:
            self._recorder.stop(status=status)
        except Exception as exc:
            errors.append(f"recorder stop: {exc}")

        if self._world is not None and self._original_world_settings is not None:
            try:
                self._world.apply_settings(self._original_world_settings)
            except Exception as exc:
                errors.append(f"world settings restore: {exc}")
        self._original_world_settings = None
        self._geometry = None
        self._sensor_factory = None
        self._next_synchronization_frame = None
        self._consecutive_sync_misses = 0
        if errors:
            message = "; ".join(errors)
            LOGGER.error("Faz 1 cleanup hataları: %s", message)
            if raise_on_error:
                raise CarlaPhase1Error(f"Faz 1 kaynakları tam temizlenemedi: {message}")

    @staticmethod
    def _vector_dict(vector: Any) -> dict[str, float]:
        return {"x": float(vector.x), "y": float(vector.y), "z": float(vector.z)}
