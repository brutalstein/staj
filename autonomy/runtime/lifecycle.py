from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from threading import RLock

from autonomy.contracts.runtime import ComponentState


class LifecycleError(RuntimeError):
    """Bir servis geçersiz yaşam döngüsü geçişi yaptığında üretilir."""


_ALLOWED_TRANSITIONS: dict[ComponentState, set[ComponentState]] = {
    ComponentState.CREATED: {ComponentState.INITIALIZING, ComponentState.STOPPED},
    ComponentState.INITIALIZING: {ComponentState.READY, ComponentState.FAILED},
    ComponentState.READY: {ComponentState.RUNNING, ComponentState.STOPPING},
    ComponentState.RUNNING: {
        ComponentState.DEGRADED,
        ComponentState.STOPPING,
        ComponentState.FAILED,
    },
    ComponentState.DEGRADED: {
        ComponentState.RUNNING,
        ComponentState.STOPPING,
        ComponentState.FAILED,
    },
    ComponentState.STOPPING: {ComponentState.STOPPED, ComponentState.FAILED},
    ComponentState.STOPPED: set(),
    ComponentState.FAILED: {ComponentState.STOPPING, ComponentState.STOPPED},
}


@dataclass
class BaseService(ABC):
    """Bütün çalışma zamanı servisleri için açık yaşam döngüsü temeli."""

    component_id: str
    _state: ComponentState = field(default=ComponentState.CREATED, init=False)
    _lock: RLock = field(default_factory=RLock, init=False, repr=False)

    @property
    def state(self) -> ComponentState:
        return self._state

    def transition_to(self, new_state: ComponentState) -> None:
        with self._lock:
            if new_state not in _ALLOWED_TRANSITIONS[self._state]:
                raise LifecycleError(
                    f"{self.component_id}: geçersiz yaşam döngüsü geçişi "
                    f"{self._state} -> {new_state}."
                )
            self._state = new_state

    def initialize(self) -> None:
        self.transition_to(ComponentState.INITIALIZING)
        try:
            self.on_initialize()
        except Exception:
            self._state = ComponentState.FAILED
            raise
        self.transition_to(ComponentState.READY)

    def start(self) -> None:
        self.transition_to(ComponentState.RUNNING)
        try:
            self.on_start()
        except Exception:
            self._state = ComponentState.FAILED
            raise

    def stop(self) -> None:
        if self._state in {ComponentState.STOPPED, ComponentState.CREATED}:
            self._state = ComponentState.STOPPED
            return
        if self._state != ComponentState.STOPPING:
            self.transition_to(ComponentState.STOPPING)
        try:
            self.on_stop()
        finally:
            self._state = ComponentState.STOPPED

    @abstractmethod
    def on_initialize(self) -> None:
        """Servisin kaynaklarını doğrular ve hazırlar."""

    def on_start(self) -> None:
        """Servis RUNNING durumuna geçtiğinde çağrılır."""

    @abstractmethod
    def on_stop(self) -> None:
        """Servisin sahip olduğu kaynakları güvenli biçimde temizler."""
