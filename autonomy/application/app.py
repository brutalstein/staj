from __future__ import annotations

import logging
import signal
from dataclasses import dataclass, field
from threading import Event

from autonomy.configuration.loader import ProjectConfiguration
from autonomy.simulation.carla.adapter import CarlaAdapter

LOGGER = logging.getLogger(__name__)


@dataclass
class AutonomyApplication:
    """Faz 0 uygulaması: ortamı doğrular ve CARLA bağlantısını açık tutar."""

    configuration: ProjectConfiguration
    _stop_event: Event = field(default_factory=Event, init=False)

    def run(self) -> int:
        adapter = CarlaAdapter(self.configuration.carla)
        self._install_signal_handlers()
        try:
            info = adapter.connect()
            LOGGER.info(
                "CARLA bağlantısı hazır: server=%s, map=%s",
                info.server_version,
                info.map_name,
            )
            LOGGER.info(
                "Faz 0 runtime çalışıyor. Henüz araç veya sensör aktörü oluşturulmaz. "
                "Kapatmak için Ctrl+C kullanın."
            )
            while not self._stop_event.wait(timeout=0.5):
                pass
            return 0
        finally:
            adapter.disconnect()
            LOGGER.info("Uygulama kontrollü biçimde kapatıldı.")

    def _install_signal_handlers(self) -> None:
        def request_stop(signum: int, _frame: object) -> None:
            LOGGER.info("Kapatma sinyali alındı: %s", signum)
            self._stop_event.set()

        signal.signal(signal.SIGINT, request_stop)
        if hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, request_stop)
