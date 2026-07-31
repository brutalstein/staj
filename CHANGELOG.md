# Değişiklik Günlüğü

## 0.2.0 — 2026-07-31

- Faz 1 default CARLA runtime uygulandı.
- Tesla Model 3 deterministik spawn ve güvenli başlangıç freni eklendi.
- Runtime bounding-box/wheel tabanlı `VehicleGeometryAdapter` eklendi.
- 6 RGB, 1×64 kanal LiDAR, 6 radar proxy, çift GNSS ve IMU sensör factory'si eklendi.
- Tek-owner synchronous world tick, bounded callback buffer ve exact-frame synchronizer eklendi.
- Manifest/JSONL recorder, actor cleanup ve world settings restore eklendi.
- Lifecycle rollback açığı giderildi.
- Faz 1 unit, mock, hata enjeksiyonu ve opt-in gerçek CARLA smoke testleri eklendi.
- Registry, modül kayıtları ve mimari portal güncellendi.

## 0.1.0 — 2026-07-31

- Faz 0 proje omurgası oluşturuldu.
- Tipli sözleşmeler, config loader ve runtime lifecycle eklendi.
- CARLA 0.9.15/0.9.16 bağlantı ve sürüm kontrolü eklendi.
- Windows/Ubuntu proje ve doküman başlatıcıları eklendi.
- Component, contract, algorithm ve source registry oluşturuldu.
- MODULE.md doğrulaması ve başlangıç testleri eklendi.
