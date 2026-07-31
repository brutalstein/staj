from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MessageMetadata:
    """Bütün çalışma zamanı mesajlarında taşınan izlenebilirlik bilgisi."""

    timestamp_seconds: float
    simulation_frame: int
    sequence_number: int
    coordinate_frame: str
    source_module: str
    schema_version: str = "1.0"
    configuration_hash: str = "unknown"

    def __post_init__(self) -> None:
        if self.timestamp_seconds < 0:
            raise ValueError("timestamp_seconds negatif olamaz.")
        if self.simulation_frame < 0:
            raise ValueError("simulation_frame negatif olamaz.")
        if self.sequence_number < 0:
            raise ValueError("sequence_number negatif olamaz.")
        if not self.coordinate_frame.strip():
            raise ValueError("coordinate_frame boş olamaz.")
        if not self.source_module.strip():
            raise ValueError("source_module boş olamaz.")
