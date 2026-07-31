from pathlib import Path

from autonomy.configuration.loader import load_configuration


def test_default_configuration_is_consistent() -> None:
    configuration = load_configuration(Path("config/runtime/default.yaml"))
    assert configuration.runtime.simulation_frequency_hz == 50
    assert configuration.runtime.fixed_delta_seconds == 0.02
    assert set(configuration.carla.supported_versions) == {"0.9.15", "0.9.16"}
    assert len(configuration.configuration_hash) == 64
