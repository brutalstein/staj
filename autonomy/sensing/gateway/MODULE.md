---
module_id: "sensor_gateway"
module_name: "Sensor Gateway"
owner: "perception-platform"
status: "implemented"
schema_version: "1.0"
last_reviewed: "2026-07-31"
---

# Modül: Sensor Gateway

## Amaç

CARLA sensor callback'lerini ana tick thread'inden ayırır ve her sensor_id için sabit kapasiteli frame tamponunda tutar.

## Inputlar ve kaynakları

- CARLA `SensorData` callback nesneleri — Sensor Factory
- sensor_id/sensor_type kayıtları — doğrulanmış layout

## İşlem

Callback içinde frame, timestamp, encoding ve payload boyutu çıkarılır; payload kopyalanmadan runtime nesnesiyle birlikte ilgili `BoundedSensorBuffer` içine konur. Kapasite aşılırsa en eski frame düşürülür.

## Outputlar ve tüketiciler

- `SensorMeasurement` — time synchronizer/recorder
- Dropped-frame sayaçları — Phase 1 vehicle feedback/operasyon

## Parametreler

- `phase1.sensor_buffer_capacity`

## Hata ve fallback davranışı

Kayıtsız veya tekrarlanan sensör kimliği reddedilir. Buffer taşması süreci durdurmaz; en eski frame düşürülür. Ortak frame kaybı üst synchronizer tarafından değerlendirilir.

## Testler

- `tests/test_sensor_pipeline.py`
- `tests/test_phase1_runtime.py`
