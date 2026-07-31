---
module_id: "sensing_domain"
module_name: "Sensing Domain"
owner: "perception-platform"
status: "implemented"
schema_version: "1.0"
last_reviewed: "2026-07-31"
---

# Modül Alanı: Sensing

## Amaç

CARLA callback thread'lerinden gelen ölçümleri bounded buffer ve frame synchronizer üzerinden sonraki otonomi katmanlarına taşır.

## Alt modüller

- `sensor_gateway`: callback izolasyonu ve bounded buffer
- `time_synchronizer`: aynı CARLA frame kimliğinde atomik çok-sensör görünümü

## Hata davranışı

Tampon taşması en eski frame'i deterministik düşürür ve sayaçla raporlar. Zorunlu sensörler ortak frame üretemezse runtime sınırlı denemeden sonra fail-fast davranır.

## Testler

- `tests/test_sensor_pipeline.py`
- `tests/test_phase1_runtime.py`
