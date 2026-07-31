---
module_id: "runtime"
module_name: "Runtime Yaşam Döngüsü"
owner: "platform"
status: "implemented"
schema_version: "1.0"
last_reviewed: "2026-07-31"
---

# Modül: Runtime Yaşam Döngüsü

## Amaç

Kaynak sahibi servislerin initialize, start, stop ve hata rollback sırasını deterministik olarak yönetir.

## Inputlar ve kaynakları

- Uygulama tarafından kaydedilen `BaseService` örnekleri
- Servislerin `on_initialize`, `on_start`, `on_stop` implementasyonları

## İşlem

Servisler kayıt sırasıyla initialize/start edilir. Initialize veya start sırasında hata veren servis dahil, kısmen etkinleşmiş bütün servisler ters sırada durdurulur. Normal kapanışta da aynı ters sıra kullanılır.

## Outputlar ve tüketiciler

- `ComponentState` — application/monitoring
- Başlatma veya cleanup sonucu — application

## Hata ve fallback davranışı

- Geçersiz state geçişi `LifecycleError` üretir.
- Rollback sırasında diğer servislerin temizliği devam eder.
- Cleanup hataları ana exception üzerine not olarak veya toplu `RuntimeError` olarak raporlanır.

## Testler

- `tests/test_runtime.py`
- `tests/test_runtime_rollback.py`

## Lineage ve entegrasyon geçmişi

- Faz 0: temel state machine ve orchestrator.
- Faz 1 / 0.2.0: initialize/start sırasında kısmi kaynak ayıran hatalı servisin de rollback kapsamına alınması.
