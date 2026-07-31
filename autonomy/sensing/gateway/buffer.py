from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from threading import Condition, RLock
from typing import Any


@dataclass(frozen=True, slots=True)
class SensorMeasurement:
    sensor_id: str
    sensor_type: str
    frame: int
    timestamp_seconds: float
    payload: Any
    payload_size_bytes: int
    encoding: str


class BoundedSensorBuffer:
    """Frame kimliğine göre erişilen, en eski veriyi deterministik düşüren tampon."""

    def __init__(self, capacity: int) -> None:
        if capacity < 2:
            raise ValueError("Sensor buffer kapasitesi en az 2 olmalıdır.")
        self._capacity = capacity
        self._measurements: OrderedDict[int, SensorMeasurement] = OrderedDict()
        self._lock = RLock()
        self._dropped_count = 0

    @property
    def dropped_count(self) -> int:
        with self._lock:
            return self._dropped_count

    def put(self, measurement: SensorMeasurement) -> None:
        with self._lock:
            if measurement.frame in self._measurements:
                self._measurements.pop(measurement.frame)
            self._measurements[measurement.frame] = measurement
            while len(self._measurements) > self._capacity:
                self._measurements.popitem(last=False)
                self._dropped_count += 1

    def frames(self, maximum_frame: int | None = None) -> set[int]:
        with self._lock:
            frames = set(self._measurements)
        if maximum_frame is not None:
            frames = {frame for frame in frames if frame <= maximum_frame}
        return frames

    def pop(self, frame: int) -> SensorMeasurement | None:
        with self._lock:
            return self._measurements.pop(frame, None)

    def discard_through(self, frame: int) -> None:
        with self._lock:
            for old_frame in tuple(self._measurements):
                if old_frame <= frame:
                    self._measurements.pop(old_frame, None)


class SensorGateway:
    """Sensör aktörlerinin callback thread'leri ile senkronizasyon katmanını ayırır."""

    def __init__(self, buffer_capacity: int) -> None:
        self._buffer_capacity = buffer_capacity
        self._buffers: dict[str, BoundedSensorBuffer] = {}
        self._sensor_types: dict[str, str] = {}
        self._callback_errors: dict[str, str] = {}
        self._condition = Condition(RLock())

    @property
    def sensor_ids(self) -> tuple[str, ...]:
        with self._condition:
            return tuple(self._buffers)

    def register_sensor(self, sensor_id: str, sensor_type: str) -> BoundedSensorBuffer:
        if not sensor_id.strip() or not sensor_type.strip():
            raise ValueError("sensor_id ve sensor_type boş olamaz.")
        with self._condition:
            if sensor_id in self._buffers:
                raise ValueError(f"Sensor gateway içinde tekrarlanan sensor_id: {sensor_id}")
            buffer = BoundedSensorBuffer(self._buffer_capacity)
            self._buffers[sensor_id] = buffer
            self._sensor_types[sensor_id] = sensor_type
            return buffer

    def callback_for(self, sensor_id: str):
        with self._condition:
            if sensor_id not in self._buffers:
                raise KeyError(f"Kayıtlı olmayan sensor_id: {sensor_id}")
            sensor_type = self._sensor_types[sensor_id]
            buffer = self._buffers[sensor_id]

        def receive(data: Any) -> None:
            try:
                raw_data = getattr(data, "raw_data", None)
                try:
                    payload_size = len(raw_data) if raw_data is not None else 0
                except TypeError:
                    payload_size = 0
                measurement = SensorMeasurement(
                    sensor_id=sensor_id,
                    sensor_type=sensor_type,
                    frame=int(data.frame),
                    timestamp_seconds=float(data.timestamp),
                    payload=data,
                    payload_size_bytes=payload_size,
                    encoding=self._encoding_for(sensor_type),
                )
                buffer.put(measurement)
            except Exception as exc:
                with self._condition:
                    self._callback_errors[sensor_id] = (
                        f"{type(exc).__name__}: {exc}"
                    )
                    self._condition.notify_all()
                return
            with self._condition:
                self._condition.notify_all()

        return receive

    def buffer(self, sensor_id: str) -> BoundedSensorBuffer:
        with self._condition:
            try:
                return self._buffers[sensor_id]
            except KeyError as exc:
                raise KeyError(f"Kayıtlı olmayan sensor_id: {sensor_id}") from exc

    def raise_if_callback_failed(self) -> None:
        with self._condition:
            errors = dict(self._callback_errors)
        if errors:
            details = "; ".join(
                f"{sensor_id}: {message}"
                for sensor_id, message in sorted(errors.items())
            )
            raise RuntimeError(f"Sensör callback hatası: {details}")

    def dropped_counts(self) -> dict[str, int]:
        with self._condition:
            items = tuple(self._buffers.items())
        return {sensor_id: buffer.dropped_count for sensor_id, buffer in items}

    def wait_for_update(self, timeout_seconds: float) -> None:
        with self._condition:
            self._condition.wait(timeout=max(0.0, timeout_seconds))

    def clear(self) -> None:
        with self._condition:
            self._buffers.clear()
            self._sensor_types.clear()
            self._callback_errors.clear()
            self._condition.notify_all()

    @staticmethod
    def _encoding_for(sensor_type: str) -> str:
        return {
            "rgb_camera": "carla.bgra8",
            "lidar_64_channel": "carla.lidar_xyz_intensity_f32",
            "4d_radar_proxy": "carla.radar_detection_array",
            "gnss": "carla.gnss_measurement",
            "imu": "carla.imu_measurement",
        }[sensor_type]
