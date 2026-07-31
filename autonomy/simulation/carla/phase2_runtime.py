from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from autonomy.configuration.loader import ProjectConfiguration
from autonomy.contracts.localization import EgoState, LocalizationEstimate
from autonomy.localization.pipeline import LocalizationPipeline
from autonomy.simulation.carla.adapter import CarlaAdapter
from autonomy.simulation.carla.phase1_runtime import CarlaPhase1Runtime, Phase1TickResult


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Phase2TickResult:
    phase1_result: Phase1TickResult
    localization_estimate: LocalizationEstimate | None
    ego_state: EgoState | None


class CarlaPhase2Runtime(CarlaPhase1Runtime):
    """Faz 2 için genişletilmiş runtime: CarlaPhase1Runtime özelliklerini korur
    ve her frame için LocalizationPipeline çalıştırır.
    """

    def __init__(self, adapter: CarlaAdapter, configuration: ProjectConfiguration) -> None:
        super().__init__(adapter, configuration)
        self._localization_pipeline: LocalizationPipeline | None = None

    def on_initialize(self) -> None:
        super().on_initialize()
        self._localization_pipeline = LocalizationPipeline(
            configuration_hash=self._configuration.configuration_hash
        )

    def tick(self) -> Phase2TickResult:
        result_phase1 = super()._tick_once()
        
        loc_est = None
        ego_state = None
        
        if result_phase1.synchronized is not None and self._localization_pipeline is not None:
            # Senkron veri geldiyse lokalizasyon çalıştır
            try:
                loc_est, ego_state = self._localization_pipeline.process(
                    result_phase1.synchronized, 
                    result_phase1.vehicle_feedback
                )
            except Exception as exc:
                LOGGER.error("Localization pipeline hatası: %s", exc, exc_info=True)
                
        return Phase2TickResult(result_phase1, loc_est, ego_state)
