from dataclasses import replace
import os
from pathlib import Path

import pytest

from autonomy.configuration.loader import load_configuration
from autonomy.simulation.carla.adapter import CarlaAdapter
from autonomy.simulation.carla.phase1_runtime import CarlaPhase1Runtime


pytestmark = pytest.mark.carla_smoke


@pytest.mark.skipif(
    os.environ.get("CARLA_SMOKE_TEST") != "1",
    reason="Gerçek CARLA smoke testi CARLA_SMOKE_TEST=1 ile etkinleştirilir.",
)
def test_real_carla_phase1_spawn_sync_and_cleanup(tmp_path: Path) -> None:
    configuration = load_configuration(Path("config/runtime/default.yaml"))
    configuration = replace(
        configuration,
        phase1=replace(
            configuration.phase1,
            recording=replace(
                configuration.phase1.recording,
                output_directory=tmp_path / "recordings",
                record_raw_data=False,
            ),
        ),
    )
    adapter = CarlaAdapter(configuration.carla)
    runtime = None
    try:
        adapter.connect()
        runtime = CarlaPhase1Runtime(adapter, configuration)
        runtime.initialize()
        runtime.start()
        synchronized_count = 0
        for _ in range(8):
            if runtime.tick().synchronized is not None:
                synchronized_count += 1
        assert runtime.sensor_count == 16
        assert synchronized_count >= 2
    finally:
        if runtime is not None:
            runtime.stop()
        adapter.disconnect()
