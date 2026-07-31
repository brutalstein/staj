# Faz 0 Teslimat Raporu

**Sürüm:** 0.1.0  
**Tarih:** 2026-07-31

## Uygulanan kapsam

- Tipli veri sözleşmeleri
- YAML konfigürasyon yükleme ve hash üretimi
- Component/contract/algorithm/source registry
- Runtime servis yaşam döngüsü
- CARLA lazy-import bağlantı ve sürüm kontrol adaptörü
- Windows/Ubuntu proje başlatıcıları
- Windows/Ubuntu doküman portalı başlatıcıları
- MODULE.md zorunluluğu ve doğrulayıcı
- MkDocs Material portal iskeleti
- ODD ve sensör layout başlangıç konfigürasyonları
- Unit ve mock CARLA bağlantı testleri

## Kontroller

- `python tools/validate_project.py`: başarılı
- `python -m compileall -q autonomy tools tests`: başarılı
- `python -m pytest -q`: 5 test başarılı

## Ortam notu

Teslimatın zorunlu Python sürümü 3.11'dir. Paket üretim ortamı Python 3.13 olduğu için `project_launcher.py check` sürüm kontrolünde bilinçli olarak hata vermiştir. Bu davranış launcher gereksinimine uygundur; uygulama yanlış Python sürümünde başlatılmaz.

## Sonraki kronolojik faz

Faz 1:

1. `VehicleGeometryAdapter`
2. Tesla Model 3 actor spawn
3. Normalize sensör layoutunun mutlak CARLA transformlarına çevrilmesi
4. 6 kamera, 64 kanal LiDAR ve 6 radar vekili için Sensor Factory
5. Tek tick sahibi synchronous orchestrator
6. Bounded sensor buffer ve frame synchronizer
7. Recorder manifesti
8. Spawn/sync/cleanup CARLA smoke testleri
