# ADR-0001 — Platform omurgası önce kurulacak

- **Durum:** Kabul edildi
- **Tarih:** 2026-07-31

## Bağlam

UniAD, lokalizasyon, planning ve control katmanları farklı bağımlılık ve frekanslara sahiptir. Veri sözleşmeleri ve yaşam döngüsü kurulmadan doğrudan model entegrasyonu hata kaynağını belirsizleştirir.

## Karar

İlk fazda contracts, configuration, registry, runtime lifecycle, launcher, CARLA adapter ve yaşayan doküman omurgası uygulanacaktır. Henüz uygulanmayan modüller için boş sınıf yazılmayacaktır.

## Sonuç

Yeni algoritmalar mevcut tipli sözleşmelerin arkasına eklenir. Modül dokümanı ve registry güncellenmeden entegrasyon tamamlanmış sayılmaz.
