from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping

from autonomy.contracts.common import MessageMetadata


class SensorStatus(StrEnum):
    NOMINAL = "NOMINAL"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class RawSensorPacket:
    """Ham sensör verisinin kopyalanmadan taşınan metadata sözleşmesi."""

    metadata: MessageMetadata
    sensor_id: str
    sensor_type: str
    shared_memory_name: str | None
    payload_size_bytes: int
    encoding: str

    def __post_init__(self) -> None:
        if not self.sensor_id.strip():
            raise ValueError("sensor_id boş olamaz.")
        if self.payload_size_bytes < 0:
            raise ValueError("payload_size_bytes negatif olamaz.")
        if self.payload_size_bytes > 0 and not self.shared_memory_name:
            raise ValueError("Payload varsa shared_memory_name belirtilmelidir.")


@dataclass(frozen=True, slots=True)
class SynchronizedSensorFrame:
    """Çok oranlı sensör paketlerinin aynı zaman penceresinde eşlenmiş görünümü."""

    metadata: MessageMetadata
    packets_by_sensor_id: Mapping[str, RawSensorPacket]
    missing_sensor_ids: tuple[str, ...]
    synchronization_tolerance_seconds: float

    def __post_init__(self) -> None:
        if self.synchronization_tolerance_seconds < 0:
            raise ValueError("Senkronizasyon toleransı negatif olamaz.")
        object.__setattr__(self, "packets_by_sensor_id", MappingProxyType(dict(self.packets_by_sensor_id)))


@dataclass(frozen=True, slots=True)
class SensorHealth:
    """Bir sensörün veri tazeliği ve sağlık durumunu raporlar."""

    metadata: MessageMetadata
    sensor_id: str
    status: SensorStatus
    data_age_seconds: float
    confidence: float
    reason_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.data_age_seconds < 0:
            raise ValueError("data_age_seconds negatif olamaz.")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence 0 ile 1 arasında olmalıdır.")
