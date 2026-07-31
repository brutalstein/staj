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

Runtime, araç ve sensör layout YAML dosyalarını tek bir tipli `ProjectConfiguration` nesnesine dönüştürür; dosyalar arası referansları ve çalışma zamanı invariantlarını uygulama başlamadan doğrular.

## Inputlar ve kaynakları

- `config/runtime/default.yaml`
- `config/vehicles/tesla_model3.yaml`
- `config/sensors/layouts/tesla_model3_omnihd_v1.yaml`

## İşlem

- CARLA build alias ve semantik sürüm hedeflerini doğrular.
- Synchronous frekans/fixed-delta tutarlılığını kontrol eder.
- Araç blueprint/reference-frame ile sensör layout eşleşmesini doğrular.
- Sensör kimliklerini, tiplerini, normalize pozlarını, attribute'larını ve tick katlarını doğrular.
- Faz 1 topolojisini 6 RGB + 1 LiDAR + 6 radar proxy + 2 GNSS + 1 IMU olarak sabitler.
- Üç kaynak dosyanın içeriğini kapsayan SHA-256 configuration hash üretir.

## Outputlar ve tüketiciler

- `ProjectConfiguration` — application, CARLA adapter, Phase 1 runtime, recorder

## Parametreler

Bütün parametrelerin ana kaydı YAML dosyalarıdır. Python kodunda araç boyutu veya sensör pozu sabitlenmez.

## Hata ve fallback davranışı

Geçersiz veya eksik değerlerde `ConfigurationError` üretilir; actor oluşturulmadan süreç durur. Geçersiz değer için sessiz varsayılan veya otomatik düzeltme uygulanmaz.

## Testler

- `tests/test_configuration.py`
- `tests/test_phase1_configuration.py`

## Lineage ve entegrasyon geçmişi

- Faz 0: ana runtime YAML ve CARLA sürüm alias'ları.
- Faz 1 / 0.2.0: referanslı araç/layout yükleme, topoloji doğrulaması ve birleşik hash.
