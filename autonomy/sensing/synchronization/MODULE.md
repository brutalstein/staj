---
module_id: "time_synchronizer"
module_name: "Frame Synchronizer"
owner: "perception-platform"
status: "implemented"
schema_version: "1.0"
last_reviewed: "2026-07-31"
---

# Modül: Frame Synchronizer

## Amaç

Farklı sensor_tick oranlarına sahip zorunlu sensörleri aynı CARLA `frame` kimliğinde atomik bir görünüm olarak birleştirir.

## Inputlar ve kaynakları

- Sensor Gateway bounded buffer'ları
- Zorunlu sensor_id listesi — sensor layout
- Configuration hash ve coordinate frame — configuration

## İşlem

Belirlenen maksimum world frame'ini aşmayan ortak frame kümesi bulunur; en güncel ortak frame tüketilir. Timestamp yayılımı tolerans içinde doğrulanır ve `SynchronizedSensorFrame` sözleşmesi üretilir.

## Outputlar ve tüketiciler

- `SynchronizedMeasurements` — recorder, Faz 2 localization, Faz 3 world model
- `SynchronizedSensorFrame` — tipli modüller arası sözleşme

## Parametreler

- `phase1.synchronization_timeout_seconds`
- `phase1.maximum_consecutive_sync_misses`
- Sensor tick değerlerinden hesaplanan ortak stride

## Hata ve fallback davranışı

Timeout tek başına `None` döndürür; runtime ardışık miss sınırına kadar yeniden dener. Timestamp uyuşmazlığı veya buffer invariant ihlali fail-fast hatadır.

## Testler

- `tests/test_sensor_pipeline.py`
- `tests/test_phase1_runtime.py`
