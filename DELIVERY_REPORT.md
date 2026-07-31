# Faz 1 Teslimat Raporu

**Sürüm:** 0.2.0
**Tarih:** 2026-07-31
**Baz commit:** `3991e145dfe913cba7e6b5ced618b99eb6bd15c3`

## Uygulanan kapsam

1. Runtime araç geometrisi çıkarımı
2. Tesla Model 3 deterministik actor spawn
3. Normalize layout → CARLA relative transform çözümü
4. 16 sensörlü default sensor factory
5. Tek-owner synchronous world tick
6. Bounded callback buffer ve dropped-frame sayaçları
7. Exact simulation-frame synchronizer
8. Vehicle/actuator feedback
9. Manifest + JSONL recorder
10. Kısmi spawn rollback, actor cleanup ve world settings restore
11. Default application entegrasyonu
12. Registry ve yaşayan dokümantasyon güncellemesi

## Güvenlik sınırı

Faz 1 bir sürüş kontrolcüsü içermez. Ego actor autopilot'a verilmez; throttle 0, brake 1 ve hand brake açık tutulur. Radarlar CARLA radar actor'ünün 4D radar proxy kullanımıdır; gerçek imaging-radar sinyal modeli değildir.

## Doğrulama katmanları

- Konfigürasyon/topoloji invariant testleri
- Geometry ve wheel-unit testleri
- Buffer taşması ve timestamp uyuşmazlığı testleri
- Lifecycle rollback testi
- 16 sensörlü mock CARLA end-to-end runtime testi
- Kısmi sensor-spawn hata enjeksiyonu
- Recorder manifest/frame kontrolü
- Opt-in gerçek CARLA spawn/sync/cleanup smoke testi
- Unit/mock test suite: **26 passed, 1 opt-in CARLA smoke skipped**
- Python compileall
- Registry ve MODULE.md doğrulaması
- Temiz checkout üzerinde `git am` provası

Gerçek CARLA smoke testi donanım/sunucu gerektirdiği için teslimat ortamında otomatik çalıştırılmaz; kullanıcı sisteminde `CARLA_SMOKE_TEST=1` ile çalıştırılır.

## Faz 2 giriş koşulu

Faz 2 başlamadan gerçek CARLA smoke testinin başarıyla tamamlanması, manifestte 16 sensor actor kaydı bulunması ve kapanıştan sonra world settings/actor temizliğinin doğrulanması gerekir.
