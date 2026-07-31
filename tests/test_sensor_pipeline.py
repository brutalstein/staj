from types import SimpleNamespace

import pytest

from autonomy.sensing.gateway import BoundedSensorBuffer, SensorGateway, SensorMeasurement
from autonomy.sensing.synchronization import FrameSynchronizer


def measurement(sensor_id: str, frame: int, timestamp: float | None = None) -> SensorMeasurement:
    return SensorMeasurement(
        sensor_id=sensor_id,
        sensor_type="imu",
        frame=frame,
        timestamp_seconds=float(frame) if timestamp is None else timestamp,
        payload=SimpleNamespace(frame=frame),
        payload_size_bytes=0,
        encoding="carla.imu_measurement",
    )


def test_bounded_sensor_buffer_drops_oldest_frame() -> None:
    buffer = BoundedSensorBuffer(capacity=2)
    buffer.put(measurement("imu", 1))
    buffer.put(measurement("imu", 2))
    buffer.put(measurement("imu", 3))

    assert buffer.frames() == {2, 3}
    assert buffer.dropped_count == 1


def test_synchronizer_consumes_latest_common_frame() -> None:
    gateway = SensorGateway(buffer_capacity=4)
    first = gateway.register_sensor("first", "imu")
    second = gateway.register_sensor("second", "gnss")
    first.put(measurement("first", 1, 0.02))
    second.put(measurement("second", 1, 0.02))
    first.put(measurement("first", 2, 0.04))
    second.put(measurement("second", 2, 0.04))
    synchronizer = FrameSynchronizer(
        gateway,
        ("first", "second"),
        "ego_rear_axle",
        "config-hash",
    )

    result = synchronizer.collect(maximum_frame=2, timeout_seconds=0.01)

    assert result is not None
    assert result.contract.metadata.simulation_frame == 2
    assert set(result.measurements_by_sensor_id) == {"first", "second"}
    assert first.frames() == set()
    assert second.frames() == set()


def test_synchronizer_rejects_timestamp_spread() -> None:
    gateway = SensorGateway(buffer_capacity=4)
    first = gateway.register_sensor("first", "imu")
    second = gateway.register_sensor("second", "gnss")
    first.put(measurement("first", 4, 0.08))
    second.put(measurement("second", 4, 0.081))
    synchronizer = FrameSynchronizer(
        gateway,
        ("first", "second"),
        "ego_rear_axle",
        "config-hash",
    )

    with pytest.raises(RuntimeError, match="timestamp yayılımı"):
        synchronizer.collect(maximum_frame=4, timeout_seconds=0.01)


def test_synchronizer_surfaces_callback_thread_error() -> None:
    gateway = SensorGateway(buffer_capacity=4)
    gateway.register_sensor("imu", "imu")
    callback = gateway.callback_for("imu")
    callback(SimpleNamespace(timestamp=0.02))
    synchronizer = FrameSynchronizer(
        gateway,
        ("imu",),
        "ego_rear_axle",
        "config-hash",
    )

    with pytest.raises(RuntimeError, match="imu: AttributeError"):
        synchronizer.collect(maximum_frame=1, timeout_seconds=0.01)
