from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from autonomy.contracts.common import MessageMetadata


class ComponentState(StrEnum):
    CREATED = "CREATED"
    INITIALIZING = "INITIALIZING"
    READY = "READY"
    RUNNING = "RUNNING"
    DEGRADED = "DEGRADED"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class RuntimeHealth:
    """Bir bileşenin çalışma durumu, heartbeat ve hata nedenleri."""

    metadata: MessageMetadata
    component_id: str
    state: ComponentState
    heartbeat_age_seconds: float
    reason_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.heartbeat_age_seconds < 0:
            raise ValueError("heartbeat_age_seconds negatif olamaz.")
