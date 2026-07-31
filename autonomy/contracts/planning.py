from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from autonomy.contracts.common import MessageMetadata


class Maneuver(StrEnum):
    LANE_KEEP = "LANE_KEEP"
    FOLLOW_VEHICLE = "FOLLOW_VEHICLE"
    APPROACH_STOP = "APPROACH_STOP"
    STOP = "STOP"
    YIELD = "YIELD"
    INTERSECTION = "INTERSECTION"
    LANE_CHANGE = "LANE_CHANGE"
    OBSTACLE_AVOIDANCE = "OBSTACLE_AVOIDANCE"
    PULL_OVER = "PULL_OVER"
    MINIMAL_RISK_MANEUVER = "MINIMAL_RISK_MANEUVER"
    EMERGENCY_STOP = "EMERGENCY_STOP"


@dataclass(frozen=True, slots=True)
class SpeedConstraintSet:
    """Behavior katmanının trajectory planner'a verdiği hız zarfı."""

    metadata: MessageMetadata
    desired_free_flow_speed_mps: float
    maximum_allowed_speed_mps: float
    minimum_allowed_speed_mps: float = 0.0
    stop_position_m: float | None = None
    follow_target_id: str | None = None
    required_time_headway_seconds: float | None = None
    reason_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        values = (
            self.desired_free_flow_speed_mps,
            self.maximum_allowed_speed_mps,
            self.minimum_allowed_speed_mps,
        )
        if any(value < 0 for value in values):
            raise ValueError("Hız kısıtları negatif olamaz.")
        if self.minimum_allowed_speed_mps > self.maximum_allowed_speed_mps:
            raise ValueError("Minimum hız maksimum hızdan büyük olamaz.")
        if self.required_time_headway_seconds is not None and self.required_time_headway_seconds <= 0:
            raise ValueError("required_time_headway_seconds pozitif olmalıdır.")


@dataclass(frozen=True, slots=True)
class BehaviorIntent:
    """Behavior Planner'ın fiziksel yörüngeden bağımsız manevra kararı."""

    metadata: MessageMetadata
    maneuver: Maneuver
    target_lane_id: str | None
    speed_constraints: SpeedConstraintSet
    must_yield: bool
    confidence: float
    reason_code: str

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence 0 ile 1 arasında olmalıdır.")
        if not self.reason_code.strip():
            raise ValueError("reason_code boş olamaz.")


@dataclass(frozen=True, slots=True)
class TrajectoryPoint:
    """Ego frame veya map frame içindeki zaman parametreli yörünge noktası."""

    time_seconds: float
    position_xy_m: tuple[float, float]
    yaw_rad: float
    speed_mps: float
    acceleration_mps2: float
    curvature_per_m: float

    def __post_init__(self) -> None:
        if self.time_seconds < 0:
            raise ValueError("time_seconds negatif olamaz.")
        if self.speed_mps < 0:
            raise ValueError("speed_mps negatif olamaz.")


@dataclass(frozen=True, slots=True)
class LongitudinalProfile:
    """Trajectory boyunca hedef hız, ivme ve jerk profilidir."""

    metadata: MessageMetadata
    time_seconds: tuple[float, ...]
    speed_mps: tuple[float, ...]
    acceleration_mps2: tuple[float, ...]
    jerk_mps3: tuple[float, ...]
    active_constraints: tuple[str, ...]

    def __post_init__(self) -> None:
        lengths = {
            len(self.time_seconds),
            len(self.speed_mps),
            len(self.acceleration_mps2),
            len(self.jerk_mps3),
        }
        if len(lengths) != 1:
            raise ValueError("LongitudinalProfile dizileri aynı uzunlukta olmalıdır.")
        if any(speed < 0 for speed in self.speed_mps):
            raise ValueError("speed_mps negatif olamaz.")


@dataclass(frozen=True, slots=True)
class SafeTrajectory:
    """Safety Cage tarafından kabul edilen veya düzeltilen yörünge."""

    metadata: MessageMetadata
    points: tuple[TrajectoryPoint, ...]
    longitudinal_profile: LongitudinalProfile
    safety_reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.points:
            raise ValueError("SafeTrajectory en az bir nokta içermelidir.")
