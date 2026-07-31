from dataclasses import dataclass, field

import pytest

from autonomy.contracts.runtime import ComponentState
from autonomy.runtime import BaseService, ServiceOrchestrator


@dataclass
class FailingStartService(BaseService):
    cleanup_calls: int = field(default=0, init=False)

    def on_initialize(self) -> None:
        pass

    def on_start(self) -> None:
        raise RuntimeError("start failed")

    def on_stop(self) -> None:
        self.cleanup_calls += 1


def test_orchestrator_cleans_service_that_fails_during_start() -> None:
    service = FailingStartService("failing")
    orchestrator = ServiceOrchestrator([service])

    with pytest.raises(RuntimeError, match="start failed"):
        orchestrator.start_all()

    assert service.cleanup_calls == 1
    assert service.state is ComponentState.STOPPED
