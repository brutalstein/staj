from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

import pytest

from autonomy.configuration.loader import load_configuration
from autonomy.contracts.runtime import ComponentState
from autonomy.simulation.carla.phase1_runtime import CarlaPhase1Runtime


def vector(x: float = 0.0, y: float = 0.0, z: float = 0.0) -> SimpleNamespace:
    return SimpleNamespace(x=x, y=y, z=z)


class FakeBlueprint:
    def __init__(self, blueprint_id: str) -> None:
        self.id = blueprint_id
        self.attributes: dict[str, str] = {}

    def has_attribute(self, _name: str) -> bool:
        return True

    def set_attribute(self, name: str, value: str) -> None:
        self.attributes[name] = value


class FakeBlueprintLibrary:
    def __init__(self) -> None:
        self.blueprints: list[FakeBlueprint] = []

    def find(self, blueprint_id: str) -> FakeBlueprint:
        blueprint = FakeBlueprint(blueprint_id)
        self.blueprints.append(blueprint)
        return blueprint


class FakeVehicle:
    def __init__(self, actor_id: int = 100) -> None:
        self.id = actor_id
        self.is_alive = True
        self.autopilot = None
        self.destroy_calls = 0
        self.control = SimpleNamespace(
            throttle=0.0,
            steer=0.0,
            brake=0.0,
            hand_brake=False,
            reverse=False,
            gear=0,
        )
        self.bounding_box = SimpleNamespace(
            extent=vector(2.35, 0.95, 0.75),
            location=vector(0.05, 0.0, 0.78),
        )

    def get_physics_control(self) -> SimpleNamespace:
        return SimpleNamespace(
            wheels=[
                SimpleNamespace(position=vector(145.0, -80.0, -35.0)),
                SimpleNamespace(position=vector(145.0, 80.0, -35.0)),
                SimpleNamespace(position=vector(-140.0, -80.0, -35.0)),
                SimpleNamespace(position=vector(-140.0, 80.0, -35.0)),
            ]
        )

    def set_autopilot(self, enabled: bool) -> None:
        self.autopilot = enabled

    def apply_control(self, control: Any) -> None:
        self.control = control

    def get_transform(self) -> SimpleNamespace:
        if not hasattr(self, "_transform_call_count"):
            self._transform_call_count = 0
        self._transform_call_count += 1
        if self._transform_call_count == 1:
            # CARLA synchronous modda spawn sonrası ilk get_transform() çağrısı
            # henüz (0,0,0) döndürür.  Gerçek konum bir world.tick() sonrası gelir.
            return SimpleNamespace(
                location=vector(0.0, 0.0, 0.0),
                rotation=SimpleNamespace(roll=0.0, pitch=0.0, yaw=0.0),
            )
        return SimpleNamespace(
            location=vector(1.0, 2.0, 0.3),
            rotation=SimpleNamespace(roll=0.0, pitch=0.0, yaw=5.0),
        )

    def get_velocity(self) -> SimpleNamespace:
        return vector()

    def get_acceleration(self) -> SimpleNamespace:
        return vector()

    def get_angular_velocity(self) -> SimpleNamespace:
        return vector()

    def get_control(self) -> Any:
        return self.control

    def get_wheel_steer_angle(self, _wheel: Any) -> float:
        return 0.0

    def destroy(self) -> bool:
        self.destroy_calls += 1
        self.is_alive = False
        return True


class FakeSensor:
    def __init__(self, actor_id: int, blueprint: FakeBlueprint) -> None:
        self.id = actor_id
        self.blueprint = blueprint
        self.is_alive = True
        self.is_listening = False
        self.callback: Callable[[Any], None] | None = None

    def listen(self, callback: Callable[[Any], None]) -> None:
        self.callback = callback
        self.is_listening = True

    def stop(self) -> None:
        self.is_listening = False

    def destroy(self) -> bool:
        self.is_alive = False
        return True


class FakeWorld:
    def __init__(
        self,
        *,
        fail_sensor_index: int | None = None,
        emit_sensor_data: bool = True,
    ) -> None:
        self.blueprints = FakeBlueprintLibrary()
        self.original_settings = SimpleNamespace(
            synchronous_mode=False,
            fixed_delta_seconds=None,
        )
        self.settings = deepcopy(self.original_settings)
        self.frame = 0
        self.vehicle: FakeVehicle | None = None
        self.sensors: list[FakeSensor] = []
        self.fail_sensor_index = fail_sensor_index
        self.emit_sensor_data = emit_sensor_data
        self.map = SimpleNamespace(
            name="Carla/Maps/Town10HD_Opt",
            get_spawn_points=lambda: (SimpleNamespace(name="spawn-0"),),
        )

    def get_settings(self) -> Any:
        return deepcopy(self.settings)

    def apply_settings(self, settings: Any) -> int:
        self.settings = deepcopy(settings)
        return self.frame

    def get_blueprint_library(self) -> FakeBlueprintLibrary:
        return self.blueprints

    def get_map(self) -> Any:
        return self.map

    def try_spawn_actor(self, _blueprint: FakeBlueprint, _transform: Any) -> FakeVehicle:
        self.vehicle = FakeVehicle()
        return self.vehicle

    def spawn_actor(
        self,
        blueprint: FakeBlueprint,
        _transform: Any,
        *,
        attach_to: FakeVehicle,
        attachment_type: Any,
    ) -> FakeSensor:
        assert attach_to is self.vehicle
        assert attachment_type == "Rigid"
        if self.fail_sensor_index is not None and len(self.sensors) == self.fail_sensor_index:
            raise RuntimeError("injected sensor spawn failure")
        sensor = FakeSensor(200 + len(self.sensors), blueprint)
        self.sensors.append(sensor)
        return sensor

    def tick(self, _timeout: float) -> int:
        self.frame += 1
        fixed_delta = float(self.settings.fixed_delta_seconds)
        timestamp = self.frame * fixed_delta
        if not self.emit_sensor_data:
            return self.frame
        for sensor in self.sensors:
            sensor_tick = float(sensor.blueprint.attributes.get("sensor_tick", fixed_delta))
            stride = round(sensor_tick / fixed_delta)
            if self.frame % stride == 0 and sensor.callback is not None:
                sensor.callback(
                    SimpleNamespace(
                        frame=self.frame,
                        timestamp=timestamp,
                        raw_data=b"payload",
                    )
                )
        return self.frame

    def get_snapshot(self) -> SimpleNamespace:
        return SimpleNamespace(
            frame=self.frame,
            timestamp=SimpleNamespace(elapsed_seconds=self.frame * 0.02),
        )


class FakeCarlaModule:
    AttachmentType = SimpleNamespace(Rigid="Rigid")
    VehicleWheelLocation = SimpleNamespace(FL_Wheel="FL", FR_Wheel="FR")

    class Location:
        def __init__(self, *, x: float, y: float, z: float) -> None:
            self.x, self.y, self.z = x, y, z

    class Rotation:
        def __init__(self, *, roll: float, pitch: float, yaw: float) -> None:
            self.roll, self.pitch, self.yaw = roll, pitch, yaw

    class Transform:
        def __init__(self, location: Any, rotation: Any) -> None:
            self.location, self.rotation = location, rotation

    class VehicleControl:
        def __init__(
            self,
            *,
            throttle: float,
            steer: float,
            brake: float,
            hand_brake: bool,
        ) -> None:
            self.throttle = throttle
            self.steer = steer
            self.brake = brake
            self.hand_brake = hand_brake
            self.reverse = False
            self.gear = 0


class FakeAdapter:
    def __init__(self, world: FakeWorld) -> None:
        self.world = world
        self.carla_module = FakeCarlaModule
        self.server_info = SimpleNamespace(
            client_version="0.9.16",
            server_version="e78db150c",
            compatibility_version="0.9.16",
            map_name="Carla/Maps/Town10HD_Opt",
        )


def configuration_for_test(tmp_path: Path):
    configuration = load_configuration(Path("config/runtime/default.yaml"))
    recording = replace(
        configuration.phase1.recording,
        output_directory=tmp_path / "recordings",
    )
    return replace(
        configuration,
        phase1=replace(configuration.phase1, recording=recording),
    )


def test_phase1_runtime_spawns_synchronizes_records_and_cleans(tmp_path: Path) -> None:
    world = FakeWorld()
    runtime = CarlaPhase1Runtime(  # type: ignore[arg-type]
        FakeAdapter(world), configuration_for_test(tmp_path)
    )

    runtime.initialize()
    runtime.start()

    assert runtime.state is ComponentState.RUNNING
    assert runtime.sensor_count == 16
    assert world.settings.synchronous_mode is True
    assert world.settings.fixed_delta_seconds == pytest.approx(0.02)
    assert world.vehicle is not None
    assert world.vehicle.autopilot is False
    assert world.vehicle.control.brake == pytest.approx(1.0)
    assert world.vehicle.control.hand_brake is True

    first = runtime.tick()
    second = runtime.tick()
    # on_start() içinde bir başlatma tick'i atılır (frame=1).  Bu tick
    # sırasında sensörler henüz listen() ile kaydedilmemiş olduğundan
    # callback tetiklenmez.  sync_stride=2 olduğundan:
    #   frame=2 → synchronization_due (next=None) → first.synchronized alınır
    #   frame=3 → next_sync=4, frame < 4 → second.synchronized=None
    assert first.synchronized is not None
    assert first.synchronized.contract.metadata.simulation_frame == 2
    assert len(first.synchronized.measurements_by_sensor_id) == 16
    assert second.synchronized is None

    run_directory = runtime.recorder_run_directory
    assert run_directory is not None
    runtime.stop()

    assert runtime.state is ComponentState.STOPPED
    assert world.settings.synchronous_mode is False
    assert world.settings.fixed_delta_seconds is None
    assert world.vehicle.is_alive is False
    assert all(sensor.is_alive is False for sensor in world.sensors)
    manifest = json.loads((run_directory / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "COMPLETED"
    assert manifest["frame_count"] == 1
    assert len(manifest["sensors"]) == 16
    assert (run_directory / "frames.jsonl").read_text(encoding="utf-8").count("\n") == 1



def test_phase1_runtime_rolls_back_partial_sensor_spawn(tmp_path: Path) -> None:
    world = FakeWorld(fail_sensor_index=3)
    runtime = CarlaPhase1Runtime(  # type: ignore[arg-type]
        FakeAdapter(world), configuration_for_test(tmp_path)
    )

    runtime.initialize()
    with pytest.raises(Exception, match="sensör aktörü"):
        runtime.start()

    assert runtime.state is ComponentState.FAILED
    assert world.settings.synchronous_mode is False
    assert world.vehicle is not None and world.vehicle.is_alive is False
    assert len(world.sensors) == 3
    assert all(sensor.is_alive is False for sensor in world.sensors)
    assert world.vehicle.destroy_calls == 1

    # Orchestrator rollback calls stop after start failure. Cleanup must be idempotent.
    runtime.stop()
    assert world.vehicle.destroy_calls == 1


def test_phase1_runtime_marks_recorder_failed_after_sync_loss(tmp_path: Path) -> None:
    world = FakeWorld(emit_sensor_data=False)
    configuration = configuration_for_test(tmp_path)
    configuration = replace(
        configuration,
        phase1=replace(
            configuration.phase1,
            synchronization_timeout_seconds=0.001,
            maximum_consecutive_sync_misses=2,
        ),
    )
    runtime = CarlaPhase1Runtime(  # type: ignore[arg-type]
        FakeAdapter(world), configuration
    )

    runtime.initialize()
    runtime.start()
    runtime.tick()
    with pytest.raises(Exception, match="ortak frame"):
        runtime.tick()
    run_directory = runtime.recorder_run_directory
    assert run_directory is not None
    runtime.stop()

    manifest = json.loads((run_directory / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "FAILED"
    assert manifest["frame_count"] == 0
