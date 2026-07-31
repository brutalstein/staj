---
module_id: "simulation"
module_name: "Simülasyon Adaptör Alanı"
owner: "simulation"
status: "implemented"
schema_version: "1.0"
last_reviewed: "2026-07-31"
---

# Modül: Simülasyon Adaptör Alanı

## Amaç

CARLA ve ileride eklenecek başka simülasyon sağlayıcılarının adaptörlerini ortak paket sınırı altında tutar.

## Inputlar

Simülasyon sağlayıcısına özgü konfigürasyonlar alt adaptörlere gelir.

## İşlem

Bu paket iş algoritması çalıştırmaz; sağlayıcıya özgü kodun çekirdek modüllere yayılmasını önleyen paket sınırıdır.

## Outputlar

Alt adaptörlerin tipleri ve bağlantı bilgileri.

## Tüketiciler

Application ve Simulation Orchestrator.

## Hata davranışı

Hatalar sağlayıcıya özgü adaptör tarafından açık exception tipleriyle üretilir.
