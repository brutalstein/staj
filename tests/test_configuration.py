from pathlib import Path

import pytest

from autonomy.configuration.loader import ConfigurationError, load_configuration


def test_default_configuration_is_consistent() -> None:
    configuration = load_configuration(Path("config/runtime/default.yaml"))
    assert configuration.runtime.simulation_frequency_hz == 50
    assert configuration.runtime.fixed_delta_seconds == 0.02
    assert set(configuration.carla.supported_versions) == {"0.9.15", "0.9.16"}
    assert dict(configuration.carla.server_version_aliases) == {"e78db150c": "0.9.16"}
    assert configuration.carla.resolve_version("e78db150c") == "0.9.16"
    assert configuration.carla.resolve_version("0.9.15") == "0.9.15"
    assert len(configuration.configuration_hash) == 64


def test_alias_target_must_be_supported(tmp_path: Path) -> None:
    config_path = tmp_path / "invalid.yaml"
    config_path.write_text(
        """
schema_version: "1.0"
carla:
  host: "127.0.0.1"
  rpc_port: 2000
  timeout_seconds: 3.0
  supported_versions: ["0.9.16"]
  server_version_aliases:
    custom-build: "0.9.17"
runtime:
  simulation_frequency_hz: 50
  fixed_delta_seconds: 0.02
  control_frequency_hz: 50
  log_level: "INFO"
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError, match="Geçersiz hedefler: 0.9.17"):
        load_configuration(config_path)
