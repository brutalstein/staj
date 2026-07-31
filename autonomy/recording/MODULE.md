---
module_id: "recorder"
module_name: "Run Recorder"
owner: "platform-data"
status: "implemented"
schema_version: "1.0"
last_reviewed: "2026-07-31"
---

# Modül: Run Recorder

## Amaç

Her Faz 1 çalışmasının tekrar üretilebilir manifestini ve senkron frame indeksini satır bazlı, kesintiye dayanıklı biçimde kaydeder.

## Inputlar ve kaynakları

- Configuration hash ve CARLA sürüm/harita bilgisi
- Runtime `VehicleGeometry`
- Spawn edilmiş sensör açıklamaları ve actor ID'leri
- `SynchronizedMeasurements`
- Araç transform/hız/ivme/actuation geri bildirimi

## İşlem

Run başlangıcında benzersiz dizin ve atomik `manifest.json` oluşturur. Her ortak frame'i `frames.jsonl` içine yazar. Konfigüre edilmiş aralıkta flush/manifest güncellemesi yapar. Kapanış durumunu `COMPLETED` veya `FAILED` olarak kaydeder.

## Outputlar ve tüketiciler

- `runtime/recordings/<run_id>/manifest.json`
- `runtime/recordings/<run_id>/frames.jsonl`
- Opsiyonel `raw/<sensor_id>/<frame>.bin`

## Parametreler

- `recording.enabled`
- `recording.output_directory`
- `recording.record_raw_data` (default `false`)
- `recording.flush_every_frames`

## Hata ve fallback davranışı

Dosya sistemi hataları `RecorderError` üretir ve runtime çalışmasını `FAILED` durumuna geçirir. Ham kayıt kapalıyken callback payload'ı diske kopyalanmaz.

## Testler

- `tests/test_phase1_runtime.py`
- `tests/test_phase1_carla_smoke.py`

## Lineage ve entegrasyon geçmişi

- Faz 1 / 0.2.0: manifest + JSONL frame indeksinin ilk default implementasyonu.
