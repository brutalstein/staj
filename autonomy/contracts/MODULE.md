---
module_id: "contracts"
module_name: "Veri Sözleşmeleri"
owner: "platform"
status: "implemented"
schema_version: "1.0"
last_reviewed: "2026-07-31"
---

# Modül: Veri Sözleşmeleri

## 1. Amaç

Modüller arasında taşınan veriyi tip, birim, koordinat frame'i, sürüm ve lineage alanlarıyla açık hâle getirir.

## 2. Kapsam dışı

İş algoritması çalıştırmaz, CARLA sınıfları taşımaz ve çalışma zamanı mesaj kuyruğunu yönetmez.

## 3. Inputlar

Bu modül veri tüketmez. Diğer modüllerin kullanacağı sözleşmeleri tanımlar.

## 4. İşlem

`dataclass(frozen=True, slots=True)` tabanlı değişmez sözleşmeler oluşturur ve temel sınır doğrulaması yapar.

## 5. Outputlar ve tüketiciler

- `RawSensorPacket`: synchronization ve recording
- `LocalizationEstimate`: world model, behavior, planning, safety ve control
- `SpeedConstraintSet`: trajectory planning
- `BehaviorIntent`: trajectory planning ve safety
- `SafeTrajectory`: control
- `SafetyDecision`: monitoring ve recording

## 6. Algoritmalar

Algoritma içermez. Sözleşme doğrulama kuralları uygular.

## 7. Hata davranışı

Geçersiz birim aralığı veya eksik kimlik oluşturma aşamasında `ValueError` üretir. Hata sessizce düzeltilmez.

## 8. Testler

- `tests/test_contracts.py`
