from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from autonomy.configuration.loader import ProjectConfiguration
from autonomy.contracts.perception import WorldModelSnapshot
from autonomy.perception.pipeline import PerceptionPipeline
from autonomy.simulation.carla.adapter import CarlaAdapter
from autonomy.simulation.carla.phase2_runtime import CarlaPhase2Runtime, Phase2TickResult


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Phase3TickResult:
    phase2_result: Phase2TickResult
    world_model: WorldModelSnapshot | None


class CarlaPhase3Runtime(CarlaPhase2Runtime):
    """Faz 3 için genişletilmiş runtime: CarlaPhase2Runtime özelliklerini korur
    ve her frame için PerceptionPipeline çalıştırır.
    """

    def __init__(self, adapter: CarlaAdapter, configuration: ProjectConfiguration) -> None:
        super().__init__(adapter, configuration)
        self._perception_pipeline: PerceptionPipeline | None = None

    def on_initialize(self) -> None:
        super().on_initialize()
        self._perception_pipeline = PerceptionPipeline()

    def tick(self) -> Phase3TickResult:
        result_phase2 = super().tick()
        
        world_model = None
        
        # We need both synchronized sensor data (for camera/lidar/radar inputs) and ego state (for reference)
        sync_data = result_phase2.phase1_result.synchronized
        ego_state = result_phase2.ego_state
        
        if sync_data is not None and ego_state is not None and self._perception_pipeline is not None:
            try:
                world_model = self._perception_pipeline.process(
                    sensor_frame=sync_data,
                    ego_state=ego_state
                )
            except Exception as exc:
                LOGGER.error("Perception pipeline hatası: %s", exc, exc_info=True)
                
        return Phase3TickResult(result_phase2, world_model)
