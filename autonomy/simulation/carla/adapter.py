from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from types import ModuleType
from typing import Any

from autonomy.configuration.loader import CarlaConfiguration
from autonomy.simulation.carla.capabilities import CarlaCapabilities, capabilities_for


class CarlaConnectionError(RuntimeError):
    """CARLA Python API veya server bağlantısı hazır olmadığında üretilir."""


@dataclass(frozen=True, slots=True)
class CarlaServerInfo:
    client_version: str
    server_version: str
    map_name: str
    capabilities: CarlaCapabilities


class CarlaAdapter:
    """CARLA sınıflarını otonomi çekirdeğinden izole eden bağlantı adaptörü."""

    def __init__(self, configuration: CarlaConfiguration) -> None:
        self._configuration = configuration
        self._carla_module: ModuleType | None = None
        self._client: Any = None
        self._world: Any = None
        self._server_info: CarlaServerInfo | None = None

    @property
    def server_info(self) -> CarlaServerInfo:
        if self._server_info is None:
            raise CarlaConnectionError("CARLA bağlantısı henüz kurulmadı.")
        return self._server_info

    def connect(self) -> CarlaServerInfo:
        try:
            self._carla_module = import_module("carla")
        except ModuleNotFoundError as exc:
            raise CarlaConnectionError(
                "CARLA Python API bulunamadı. Kullanılan CARLA server sürümüyle "
                "eşleşen Python API paketini aktif ortama kurun."
            ) from exc

        try:
            self._client = self._carla_module.Client(
                self._configuration.host,
                self._configuration.rpc_port,
            )
            self._client.set_timeout(self._configuration.timeout_seconds)
            client_version = str(self._client.get_client_version())
            server_version = str(self._client.get_server_version())
            self._world = self._client.get_world()
            map_name = str(self._world.get_map().name)
        except Exception as exc:
            raise CarlaConnectionError(
                f"CARLA sunucusuna bağlanılamadı: {self._configuration.host}:"
                f"{self._configuration.rpc_port}. Önce CarlaUE4.exe veya CarlaUE4.sh "
                "sunucusunu açın."
            ) from exc

        if client_version != server_version:
            raise CarlaConnectionError(
                "CARLA Python API ve server sürümleri eşleşmiyor. "
                f"Python API={client_version}, server={server_version}."
            )
        if server_version not in self._configuration.supported_versions:
            raise CarlaConnectionError(
                f"Desteklenmeyen CARLA sürümü: {server_version}. "
                f"Desteklenenler: {', '.join(self._configuration.supported_versions)}"
            )

        self._server_info = CarlaServerInfo(
            client_version=client_version,
            server_version=server_version,
            map_name=map_name,
            capabilities=capabilities_for(server_version),
        )
        return self._server_info

    def disconnect(self) -> None:
        self._server_info = None
        self._world = None
        self._client = None
        self._carla_module = None
