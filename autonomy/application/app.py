from __future__ import annotations

import logging
import signal
from dataclasses import dataclass, field
from threading import Event

from autonomy.configuration.loader import ProjectConfiguration
from autonomy.runtime import ServiceOrchestrator
from autonomy.simulation.carla.adapter import CarlaAdapter, CarlaConnectionError
from autonomy.simulation.carla.phase1_runtime import CarlaPhase1Runtime

LOGGER = logging.getLogger(__name__)


@dataclass
class AutonomyApplication:
    """Faz 1 default uygulaması: ego, sensör, synchronous tick ve recorder."""

    configuration: ProjectConfiguration
    _stop_event: Event = field(default_factory=Event, init=False)

    def run(self) -> int:
        self._stop_event.clear()
        self._install_signal_handlers()
        adapter = CarlaAdapter(self.configuration.carla)
        orchestrator = ServiceOrchestrator()
        runtime: CarlaPhase1Runtime | None = None
        try:
            info = adapter.connect()
            LOGGER.info(
                "CARLA bağlantısı hazır: client=%s server=%s compatibility=%s map=%s",
                info.client_version,
                info.server_version,
                info.compatibility_version,
                info.map_name,
            )
            runtime = CarlaPhase1Runtime(adapter, self.configuration)
            orchestrator.register(runtime)
            orchestrator.start_all()
            LOGGER.info(
                "Faz 1 runtime çalışıyor. Ego güvenli fren durumunda; kapatmak için Ctrl+C."
            )
            while not self._stop_event.is_set():
                result = runtime.tick()
                synchronized = result.synchronized
                if (
                    synchronized is not None
                    and synchronized.contract.metadata.sequence_number % 25 == 0
                ):
                    LOGGER.info(
                        "Senkron frame=%s sequence=%s sensors=%s speed=%.2fm/s",
                        synchronized.contract.metadata.simulation_frame,
                        synchronized.contract.metadata.sequence_number,
                        len(synchronized.measurements_by_sensor_id),
                        result.vehicle_feedback["speed_mps"],
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
            raise CarlaConnectionError("Faz 1 uygulama yaşam döngüsü başarısız.") from exc
        finally:
            adapter.disconnect()

    def _install_signal_handlers(self) -> None:
        def request_stop(signum: int, _frame: object) -> None:
            LOGGER.info("Kapatma sinyali alındı: %s", signum)
            self._stop_event.set()

        signal.signal(signal.SIGINT, request_stop)
        if hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, request_stop)
