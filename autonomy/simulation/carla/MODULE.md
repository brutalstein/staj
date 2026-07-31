---
module_id: "carla_adapter"
module_name: "CARLA Bağlantı Adaptörü"
owner: "simulation"
status: "implemented"
schema_version: "1.0"
last_reviewed: "2026-07-31"
---

# Modül: CARLA Bağlantı Adaptörü

## Amaç

CARLA Python API tiplerini otonomi çekirdeğinden izole eder; server bağlantısını ve sürüm eşleşmesini doğrular.

## Inputlar

| Input | Kaynak |
|---|---|
| `CarlaConfiguration` | configuration |
| CARLA Python API | Aktif Python ortamı |
| CARLA server | Kullanıcının açtığı süreç |

## İşlem

1. `carla` modülünü lazy import eder.
2. RPC bağlantısı kurar.
3. Client/server sürüm eşleşmesini doğrular.
4. Harita adını ve sürüm capability bilgisini üretir.

## Output

- `CarlaServerInfo`

## Tüketiciler

- Application
- İleride Simulation Orchestrator ve Sensor Factory

## Hata davranışı

Eksik API, kapalı server, sürüm uyuşmazlığı veya desteklenmeyen sürümde `CarlaConnectionError` üretir. Aktör oluşturmaz.

## Testler

- `tests/test_carla_adapter.py` içindeki mock bağlantı testleri
