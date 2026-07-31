import sys
from types import SimpleNamespace

from autonomy.configuration.loader import CarlaConfiguration
from autonomy.simulation.carla.adapter import CarlaAdapter


class FakeClient:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port

    def set_timeout(self, timeout: float) -> None:
        self.timeout = timeout

    def get_client_version(self) -> str:
        return "0.9.16"

    def get_server_version(self) -> str:
        return "0.9.16"

    def get_world(self):
        return SimpleNamespace(get_map=lambda: SimpleNamespace(name="Town10HD"))


def test_adapter_accepts_matching_versions(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "carla", SimpleNamespace(Client=FakeClient))
    configuration = CarlaConfiguration(
        host="127.0.0.1",
        rpc_port=2000,
        timeout_seconds=1.0,
        supported_versions=("0.9.15", "0.9.16"),
    )
    info = CarlaAdapter(configuration).connect()
    assert info.server_version == "0.9.16"
    assert info.map_name == "Town10HD"
