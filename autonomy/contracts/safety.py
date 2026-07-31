from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from autonomy.contracts.common import MessageMetadata


class SafetyAction(StrEnum):
    ACCEPT = "ACCEPT"
    MODIFY = "MODIFY"
    REJECT_AND_FALLBACK = "REJECT_AND_FALLBACK"


@dataclass(frozen=True, slots=True)
class SafetyDecision:
    """Safety Cage kararını ölçülen değer ve eşikle birlikte açıklar."""

    metadata: MessageMetadata
    action: SafetyAction
    reason_code: str
    measured_value: float | None
    required_minimum: float | None
    details: str

    def __post_init__(self) -> None:
        if not self.reason_code.strip():
            raise ValueError("reason_code boş olamaz.")
