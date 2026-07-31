from __future__ import annotations

import logging
import signal
from dataclasses import dataclass, field
from threading import Event

from autonomy.configuration.loader import ProjectConfiguration
from autonomy.runtime import ServiceOrchestrator
from autonomy.simulation.carla.adapter import CarlaAdapter, CarlaConnectionError
from autonomy.simulation.carla.phase3_runtime import CarlaPhase3Runtime

LOGGER = logging.getLogger(__name__)


@dataclass
class AutonomyApplication:
    """Faz 3 uygulaması: ego, sensör, synchronous tick, recorder, lokalizasyon ve algı (perception)."""

    configuration: ProjectConfiguration
    _stop_event: Event = field(default_factory=Event, init=False)

    def run(self) -> int:
        self._stop_event.clear()
        self._install_signal_handlers()
        adapter = CarlaAdapter(self.configuration.carla)
        orchestrator = ServiceOrchestrator()
        runtime: CarlaPhase3Runtime | None = None
        try:
            info = adapter.connect()
            LOGGER.info(
                "CARLA bağlantısı hazır: client=%s server=%s compatibility=%s map=%s",
                info.client_version,
                info.server_version,
                info.compatibility_version,
                info.map_name,
            )
            runtime = CarlaPhase3Runtime(adapter, self.configuration)
            orchestrator.register(runtime)
            orchestrator.start_all()
            LOGGER.info(
                "Faz 3 runtime çalışıyor. Ego güvenli fren durumunda; kapatmak için Ctrl+C."
            )
            while not self._stop_event.is_set():
                result = runtime.tick()
                p1_res = result.phase2_result.phase1_result
                synchronized = p1_res.synchronized
                if (
                    synchronized is not None
                    and synchronized.contract.metadata.sequence_number % 25 == 0
                ):
                    loc_msg = ""
                    perc_msg = ""
                    
                    if result.phase2_result.localization_estimate is not None:
                        lx, ly, _ = result.phase2_result.localization_estimate.position_xyz_m
                        loc_msg = f" loc=(x:{lx:.1f}, y:{ly:.1f})"
                        
                    if result.world_model is not None:
                        perc_msg = f" objects={len(result.world_model.tracked_objects)} lanes={len(result.world_model.lane_boundaries)}"
                        
                    LOGGER.info(
                        "Senkron frame=%s sequence=%s sensors=%s speed=%.2fm/s%s%s",
                        synchronized.contract.metadata.simulation_frame,
                        synchronized.contract.metadata.sequence_number,
                        len(synchronized.measurements_by_sensor_id),
                        p1_res.vehicle_feedback["speed_mps"],
                        loc_msg,
                        perc_msg
                    )
            orchestrator.stop_all()
            LOGGER.info("Uygulama kontrollü biçimde kapatıldı.")
            return 0
        except Exception as exc:
            if runtime is not None and runtime.state.value != "STOPPED":
                try:
                    orchestrator.stop_all()
                except Exception:
                    LOGGER.exception("Hata sonrası runtime cleanup tamamlanamadı.")
            if isinstance(exc, CarlaConnectionError):
                raise
            raise CarlaConnectionError("Faz 3 uygulama yaşam döngüsü başarısız.") from exc
        finally:
            adapter.disconnect()

    def _install_signal_handlers(self) -> None:
        def request_stop(signum: int, _frame: object) -> None:
            LOGGER.info("Kapatma sinyali alındı: %s", signum)
            self._stop_event.set()

        signal.signal(signal.SIGINT, request_stop)
        if hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, request_stop)
