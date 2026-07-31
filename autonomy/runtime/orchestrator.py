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
        activated: list[BaseService] = []
        try:
            for service in self.services:
                # initialize/on_start kısmi kaynak ayırmış olabilir; hata veren servis de
                # rollback listesine baştan alınır.
                activated.append(service)
                service.initialize()
                service.start()
        except Exception as exc:
            cleanup_errors: list[str] = []
            for service in reversed(activated):
                try:
                    service.stop()
                except Exception as cleanup_exc:
                    cleanup_errors.append(f"{service.component_id}: {cleanup_exc}")
            if cleanup_errors:
                exc.add_note("Rollback hataları: " + "; ".join(cleanup_errors))
            raise

    def stop_all(self) -> None:
        errors: list[Exception] = []
        for service in reversed(self.services):
            try:
                service.stop()
            except Exception as exc:  # Bütün servislerin temizlenmesi denenmelidir.
                errors.append(exc)
        if errors:
            details = "; ".join(str(error) for error in errors)
            raise RuntimeError(
                f"{len(errors)} servis güvenli biçimde kapatılamadı: {details}"
            )
