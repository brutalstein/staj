from dataclasses import dataclass, field

from autonomy.contracts.runtime import ComponentState
from autonomy.runtime.lifecycle import BaseService
from autonomy.runtime.orchestrator import ServiceOrchestrator


@dataclass
class DummyService(BaseService):
    events: list[str] = field(default_factory=list)

    def on_initialize(self) -> None:
        self.events.append("initialize")

    def on_start(self) -> None:
        self.events.append("start")

    def on_stop(self) -> None:
        self.events.append("stop")


def test_service_lifecycle() -> None:
    service = DummyService("dummy")
    orchestrator = ServiceOrchestrator()
    orchestrator.register(service)
    orchestrator.start_all()
    assert service.state == ComponentState.RUNNING
    orchestrator.stop_all()
    assert service.state == ComponentState.STOPPED
    assert service.events == ["initialize", "start", "stop"]
