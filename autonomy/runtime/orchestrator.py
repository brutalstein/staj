from __future__ import annotations

from dataclasses import dataclass, field

from autonomy.runtime.lifecycle import BaseService


@dataclass
class ServiceOrchestrator:
    """Servisleri kayıt sırasıyla başlatır, ters sırayla kapatır."""

    services: list[BaseService] = field(default_factory=list)

    def register(self, service: BaseService) -> None:
        if any(existing.component_id == service.component_id for existing in self.services):
            raise ValueError(f"Aynı component_id iki kez kaydedilemez: {service.component_id}")
        self.services.append(service)

    def start_all(self) -> None:
        started: list[BaseService] = []
        try:
            for service in self.services:
                service.initialize()
                service.start()
                started.append(service)
        except Exception:
            for service in reversed(started):
                service.stop()
            raise

    def stop_all(self) -> None:
        errors: list[Exception] = []
        for service in reversed(self.services):
            try:
                service.stop()
            except Exception as exc:  # Bütün servislerin temizlenmesi denenmelidir.
                errors.append(exc)
        if errors:
            raise RuntimeError(f"{len(errors)} servis güvenli biçimde kapatılamadı.")
