import sys
from types import SimpleNamespace

import pytest

from autonomy.configuration.loader import CarlaConfiguration
from autonomy.simulation.carla.adapter import CarlaAdapter, CarlaConnectionError


class FakeClient:
    client_version = "0.9.16"
    server_version = "0.9.16"

    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port

    def set_timeout(self, timeout: float) -> None:
        self.timeout = timeout

    def get_client_version(self) -> str:
        return self.client_version

    def get_server_version(self) -> str:
        return self.server_version

    def get_world(self):
        return SimpleNamespace(get_map=lambda: SimpleNamespace(name="Town10HD"))


def configuration(**overrides: object) -> CarlaConfiguration:
    values: dict[str, object] = {
        "host": "127.0.0.1",
        "rpc_port": 2000,
        "timeout_seconds": 1.0,
        "supported_versions": ("0.9.15", "0.9.16"),
        "server_version_aliases": {},
    }
    values.update(overrides)
    return CarlaConfiguration(**values)  # type: ignore[arg-type]


def test_adapter_accepts_matching_versions(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "carla", SimpleNamespace(Client=FakeClient))

    info = CarlaAdapter(configuration()).connect()

    assert info.server_version == "0.9.16"
    assert info.compatibility_version == "0.9.16"
    assert info.capabilities.version == "0.9.16"
    assert info.map_name == "Town10HD"


def test_adapter_resolves_custom_build_alias(monkeypatch) -> None:
    class CustomBuildClient(FakeClient):
        client_version = "e78db150c"
        server_version = "e78db150c"

    monkeypatch.setitem(sys.modules, "carla", SimpleNamespace(Client=CustomBuildClient))

    info = CarlaAdapter(
        configuration(server_version_aliases={"e78db150c": "0.9.16"})
    ).connect()

    assert info.client_version == "e78db150c"
    assert info.server_version == "e78db150c"
    assert info.compatibility_version == "0.9.16"
    assert info.capabilities.version == "0.9.16"


def test_adapter_compares_resolved_versions(monkeypatch) -> None:
    class MixedReportingClient(FakeClient):
        client_version = "e78db150c"
        server_version = "0.9.16"

    monkeypatch.setitem(sys.modules, "carla", SimpleNamespace(Client=MixedReportingClient))

    info = CarlaAdapter(
        configuration(server_version_aliases={"e78db150c": "0.9.16"})
    ).connect()

    assert info.compatibility_version == "0.9.16"


def test_adapter_rejects_alias_without_configuration(monkeypatch) -> None:
    class CustomBuildClient(FakeClient):
        client_version = "e78db150c"
        server_version = "e78db150c"

    monkeypatch.setitem(sys.modules, "carla", SimpleNamespace(Client=CustomBuildClient))

    with pytest.raises(CarlaConnectionError, match="Desteklenmeyen CARLA sürümü"):
        CarlaAdapter(configuration()).connect()
