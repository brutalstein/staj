# ADR-0002 — Faz 1 tek-owner synchronous runtime kullanacak

- **Durum:** Kabul edildi
- **Tarih:** 2026-07-31

## Bağlam

Sensor callback'leri farklı oranlarda çalışır. Birden fazla modülün `world.tick()` çağırması simülasyon zamanını belirsizleştirir; sınırsız callback kuyrukları da gecikme ve bellek büyümesi oluşturur.

## Karar

- `CarlaPhase1Runtime` world tick'in tek sahibidir.
- Bütün sensor_tick değerleri fixed delta'nın tam katıdır.
- Her sensör sabit kapasiteli frame buffer kullanır.
- Synchronizer yalnızca aynı CARLA frame kimliğini birleştirir.
- Araç/sensör/settings kaynakları tek lifecycle servisine aittir.
- Default recorder ham payload yerine metadata + frame indeksini kaydeder.

## Sonuçlar

Veri akışı deterministik ve bounded olur. Ortak frame üretmeyen zorunlu sensör fail-fast hata üretir. Daha ileri approximate-time veya fault-tolerant fusion davranışları ancak ayrı gerekçe ve testlerle sonraki fazlarda eklenebilir.
