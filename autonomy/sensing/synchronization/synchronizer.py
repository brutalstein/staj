from __future__ import annotations

from dataclasses import dataclass
from time import monotonic
from types import MappingProxyType
from typing import Mapping

from autonomy.contracts.common import MessageMetadata
from autonomy.contracts.sensor import RawSensorPacket, SynchronizedSensorFrame
from autonomy.sensing.gateway import SensorGateway, SensorMeasurement


@dataclass(frozen=True, slots=True)
class SynchronizedMeasurements:
    contract: SynchronizedSensorFrame
    measurements_by_sensor_id: Mapping[str, SensorMeasurement]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "measurements_by_sensor_id",
            MappingProxyType(dict(self.measurements_by_sensor_id)),
        )


class FrameSynchronizer:
    """Zorunlu sensörlerin aynı simulation frame verisini atomik olarak toplar."""

    def __init__(
        self,
        gateway: SensorGateway,
        required_sensor_ids: tuple[str, ...],
        coordinate_frame: str,
        configuration_hash: str,
        timestamp_tolerance_seconds: float = 1e-6,
    ) -> None:
        if not required_sensor_ids:
            raise ValueError("En az bir zorunlu sensör olmalıdır.")
        if len(set(required_sensor_ids)) != len(required_sensor_ids):
            raise ValueError("required_sensor_ids tekrarlı değer içeremez.")
        self._gateway = gateway
        self._required_sensor_ids = required_sensor_ids
        self._coordinate_frame = coordinate_frame
        self._configuration_hash = configuration_hash
        self._timestamp_tolerance_seconds = timestamp_tolerance_seconds
        self._last_frame = -1
        self._sequence = 0

    @property
    def last_frame(self) -> int:
        return self._last_frame

    def collect(
        self,
        maximum_frame: int,
        timeout_seconds: float,
    ) -> SynchronizedMeasurements | None:
        deadline = monotonic() + timeout_seconds
        while True:
            self._gateway.raise_if_callback_failed()
            common_frame = self._latest_common_frame(maximum_frame)
            if common_frame is not None:
                return self._consume(common_frame)
            remaining = deadline - monotonic()
            if remaining <= 0:
                return None
            self._gateway.wait_for_update(min(remaining, 0.01))

    def _latest_common_frame(self, maximum_frame: int) -> int | None:
        frame_sets = [
            self._gateway.buffer(sensor_id).frames(maximum_frame)
            for sensor_id in self._required_sensor_ids
        ]
        common_frames = set.intersection(*frame_sets)
        candidates = [frame for frame in common_frames if frame > self._last_frame]
        return max(candidates) if candidates else None

    def _consume(self, frame: int) -> SynchronizedMeasurements:
        measurements: dict[str, SensorMeasurement] = {}
        for sensor_id in self._required_sensor_ids:
            measurement = self._gateway.buffer(sensor_id).pop(frame)
            if measurement is None:
                raise RuntimeError(
                    f"Frame {frame} ortak görünmesine rağmen {sensor_id} tamponunda bulunamadı."
                )
            measurements[sensor_id] = measurement

        timestamps = [measurement.timestamp_seconds for measurement in measurements.values()]
        spread = max(timestamps) - min(timestamps)
        if spread > self._timestamp_tolerance_seconds:
            raise RuntimeError(
                f"Frame {frame} sensör timestamp yayılımı toleransı aşıyor: {spread:.9f}s."
            )
        timestamp = max(timestamps)
        metadata = MessageMetadata(
            timestamp_seconds=timestamp,
            simulation_frame=frame,
            sequence_number=self._sequence,
            coordinate_frame=self._coordinate_frame,
            source_module="time_synchronizer",
            configuration_hash=self._configuration_hash,
        )
        packets = {
            sensor_id: RawSensorPacket(
                metadata=metadata,
                sensor_id=sensor_id,
                sensor_type=measurement.sensor_type,
                shared_memory_name=None,
                payload_size_bytes=0,
                encoding=f"{measurement.encoding};runtime-object",
            )
            for sensor_id, measurement in measurements.items()
        }
        contract = SynchronizedSensorFrame(
            metadata=metadata,
            packets_by_sensor_id=packets,
            missing_sensor_ids=(),
            synchronization_tolerance_seconds=self._timestamp_tolerance_seconds,
        )
        for sensor_id in self._gateway.sensor_ids:
            self._gateway.buffer(sensor_id).discard_through(frame)
        self._last_frame = frame
        self._sequence += 1
        return SynchronizedMeasurements(contract, measurements)
