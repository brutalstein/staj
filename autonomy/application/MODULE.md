---
module_id: "application"
module_name: "Autonomy Application"
owner: "platform"
status: "implemented"
schema_version: "1.0"
last_reviewed: "2026-07-31"
---

# Modül: Autonomy Application

## Amaç

Default çalışma yolunu tek bir akışta yürütür: konfigürasyonu kullanır, CARLA bağlantısını kurar, Faz 1 runtime servisini başlatır, synchronous tick döngüsünü sürdürür ve işletim sistemi sinyalinde bütün kaynakları kontrollü biçimde kapatır.

## Inputlar ve kaynakları

| Input | Kaynak |
|---|---|
| `ProjectConfiguration` | `autonomy.configuration` |
| `SIGINT` / `SIGTERM` | İşletim sistemi |
| CARLA bağlantısı | `CarlaAdapter` |

## İşlem

1. CARLA client/server uyumluluğunu doğrular.
2. `CarlaPhase1Runtime` servisini `ServiceOrchestrator` içine kaydeder.
3. Runtime initialize/start işlemlerini yürütür.
4. Ana thread üzerinde tek tick döngüsünü çalıştırır.
5. Sinyal veya hata durumunda ters sırada cleanup uygular.

## Outputlar ve tüketiciler

- Process exit code — launcher/CI
- Yapılandırılmış runtime logları — kullanıcı/operasyon
- `runtime/recordings/<run_id>/` — replay ve sonraki fazlar

## Parametreler

Doğrudan parametre tutmaz; bütün çalışma değerleri `config/runtime/default.yaml` ve referans verdiği Faz 1 dosyalarından gelir.

## Hata ve fallback davranışı

- CARLA veya Faz 1 hataları üst katmana açık exception olarak taşınır.
- Hata alan çalışma kaydı `FAILED` olarak sonlandırılır.
- Faz 1'de kontrolcü yoktur; ego actor başlangıçtan kapanışa kadar tam fren ve el freni durumunda tutulur.

## Testler

- `tests/test_phase1_runtime.py`
- `tests/test_phase1_carla_smoke.py`
- `tests/test_project_launcher.py`

## Lineage ve entegrasyon geçmişi

- Faz 0: bağlantı ve kontrollü bekleme döngüsü.
- Faz 1 / 0.2.0: default yol ego spawn, sensör suite, sync ve recorder çalıştırır.
