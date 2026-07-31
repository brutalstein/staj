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

Konfigürasyonu alır, CARLA adaptörünü başlatır ve kontrollü kapanışı yönetir.

## Inputlar

- `ProjectConfiguration` — configuration modülü
- OS sinyalleri — işletim sistemi

## İşlem

CARLA bağlantısını kurar; `SIGINT`/`SIGTERM` sinyallerinde stop event üretir.

## Outputlar

- Process exit code
- Yapılandırılmış log

## Tüketiciler

- `tools/project_launcher.py`
- İşletim sistemi veya CI

## Kapsam dışı

Faz 0'da araç, sensör veya kontrol aktörü oluşturmaz.
