from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from autonomy.contracts.common import MessageMetadata


class LocalizationMode(StrEnum):
    NOMINAL = "NOMINAL"
    GNSS_DEGRADED = "GNSS_DEGRADED"
    LIDAR_DEGRADED = "LIDAR_DEGRADED"
    DEAD_RECKONING = "DEAD_RECKONING"
    UNRELIABLE = "UNRELIABLE"
    RECOVERING = "RECOVERING"


@dataclass(frozen=True, slots=True)
class EgoState:
    """Aracın iç ego koordinat sistemindeki dinamik durumu."""

    metadata: MessageMetadata
    position_xyz_m: tuple[float, float, float]
    orientation_wxyz: tuple[float, float, float, float]
    linear_velocity_xyz_mps: tuple[float, float, float]
    angular_velocity_xyz_radps: tuple[float, float, float]
    acceleration_xyz_mps2: tuple[float, float, float]
    steering_angle_rad: float


@dataclass(frozen=True, slots=True)
class LocalizationEstimate:
    """Global poz, hız ve belirsizlik tahmini."""

    metadata: MessageMetadata
    mode: LocalizationMode
    position_xyz_m: tuple[float, float, float]
    orientation_wxyz: tuple[float, float, float, float]
    velocity_xyz_mps: tuple[float, float, float]
    covariance_diagonal: tuple[float, ...]
    confidence: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence 0 ile 1 arasında olmalıdır.")
        if any(value < 0 for value in self.covariance_diagonal):
            raise ValueError("Kovaryans köşegen değerleri negatif olamaz.")
