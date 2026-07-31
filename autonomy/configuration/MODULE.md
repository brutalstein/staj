---
module_id: "configuration"
module_name: "Konfigürasyon Yükleyici"
owner: "platform"
status: "implemented"
schema_version: "1.0"
last_reviewed: "2026-07-31"
---

# Modül: Konfigürasyon Yükleyici

## Amaç

Sürümlü YAML konfigürasyonunu tek noktadan yükler, sınırlarını doğrular ve çalışma kaydında kullanılacak hash'i üretir.

## Inputlar

- `config/runtime/default.yaml`: kullanıcı veya launcher tarafından seçilir.

## İşlem

YAML parse edilir; zorunlu alanlar, frekans/fixed-delta tutarlılığı ve özel CARLA build kimliklerinin desteklenen semantik sürümlere yönlenmesi doğrulanır. Son olarak SHA-256 hash hesaplanır.

## Output

- `ProjectConfiguration`

## Tüketiciler

- Project Launcher
- Autonomy Application
- CARLA Adapter
- Runtime Orchestrator

## Hata davranışı

Geçersiz dosyada `ConfigurationError` üretir ve uygulama başlatılmaz.

## Testler

- `tests/test_configuration.py`
