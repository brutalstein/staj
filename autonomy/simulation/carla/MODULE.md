---
module_id: "carla_adapter"
module_name: "CARLA Platform ve Faz 1 Runtime"
owner: "simulation"
status: "implemented"
schema_version: "1.0"
last_reviewed: "2026-07-31"
---

# Modül: CARLA Platform ve Faz 1 Runtime

## Amaç

CARLA Python API tiplerini çekirdekten izole eder; bağlantı/sürüm doğrulaması, ego actor yaşam döngüsü, runtime araç geometrisi, sensör actor factory'si ve tek-owner synchronous tick akışını sağlar.

## Inputlar ve kaynakları

| Input | Kaynak |
|---|---|
| `CarlaConfiguration` | configuration |
| `Phase1Configuration` | configuration |
| CARLA Python API ve server | Aktif ortam / kullanıcı süreci |
| Araç bounding box ve wheel physics | CARLA ego actor |

## İşlem

1. Client/server build kimliklerini uyumluluk sürümüne çözer.
2. Tesla Model 3 actor'ünü deterministik spawn sırasıyla oluşturur.
3. Bounding box ve dört wheel position'dan body, axle, wheelbase ve track geometrisini çıkarır.
4. Normalize layout'u actor-relative `carla.Transform` değerlerine dönüştürür.
5. 16 sensörü `AttachmentType.Rigid` ile ego actor'e bağlar.
6. World settings'i kaydeder, synchronous mode + fixed delta uygular ve tek tick sahibi olur.
7. Tick sonunda vehicle feedback, ortak sensör frame'i ve recorder girdisi üretir.
8. Kapanışta sensörleri, ego actor'ü ve world settings'i ters sırada temizler/geri yükler.

## Outputlar ve tüketiciler

- `CarlaServerInfo` — application/recorder
- `VehicleGeometry` — sensor factory/recorder
- `Phase1TickResult` — application ve sonraki fazlar
- CARLA sensor callback'leri — sensor gateway

## Parametreler

Araç ve sensör değerleri yalnızca YAML konfigürasyonundan gelir. Boyutlar runtime actor üzerinden çıkarılır. Radar aktörleri CARLA ray-cast radarının **4D radar proxy** kullanımıdır; gerçek imaging-radar sinyal modeli iddia edilmez.

## Hata ve fallback davranışı

- Blueprint, spawn, geometry, sensor, sync veya tick hatası fail-fast davranır.
- Kısmi spawn edilen actor'lar aynı hata yolunda temizlenir.
- Hata durumunda recorder `FAILED` olur ve orijinal world settings geri yüklenir.
- Kontrolcü Faz 1 kapsamı dışında olduğundan araç tam fren/el freni ile sabit tutulur.

## Testler

- `tests/test_carla_adapter.py`
- `tests/test_vehicle_geometry.py`
- `tests/test_phase1_runtime.py`
- `tests/test_phase1_carla_smoke.py` (`CARLA_SMOKE_TEST=1`)

## Kaynaklar

- CARLA Python API actor/sensor belgeleri
- CARLA sensor reference ve coordinate-system belgeleri
- CARLA synchronous mode belgeleri

## Lineage ve entegrasyon geçmişi

- Faz 0: lazy import, RPC ve sürüm doğrulama.
- Faz 1 / 0.2.0: default ego/sensor/sync/recorder runtime.

## Wheel geometry compatibility

`WheelPhysicsControl.position` değeri build'e göre actor-local/world ve metre/santimetre varyantı gösterebildiği için doğrudan kullanılmaz. Tekerler arası mesafe ile ölçek belirlenir; world adayı actor transformunun `inverse_transform` işlemiyle local frame'e çevrilir; bounding box/wheelbase/track tutarlılığı en yüksek aday seçilir.
