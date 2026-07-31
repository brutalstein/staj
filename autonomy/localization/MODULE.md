# Lokalizasyon Modülü (Phase 2)

Bu modül, CARLA ortamından (veya donanımdan) gelen ham sensör verilerini (IMU, GNSS, Tekerlek Hızları) birleştirerek aracın anlık pozisyon, yönelim ve hız tahminini hesaplar.

## Mimari Özeti

- **Preprocessing:** 
  - `ImuPreprocessor`: CARLA Sol-El koordinat sistemini İç (ISO 8855/FLU) koordinatlara dönüştürür.
  - `GnssPreprocessor`: Enlem/Boylam'ı düzlemsel Kartezyen (X,Y) koordinatlara projekte eder.
  - `WheelOdometryProcessor`: Araç geri bildirimlerinden (vehicle feedback) longitudinal hız ve direksiyon açısını çıkarır.
- **Estimators:**
  - `DualGnssBaselineEstimator`: İki GNSS noktasından aracın Heading (Yönelim) açısını çıkarır.
  - `LeverArmCompensator`: Sensör montaj ofsetlerini telafi eder.
  - `BaselineEkfFilter`: Kinematik model kullanan hafif bir EKF (Extended Kalman Filter) tasarımıdır. 
- **Pipeline:** `LocalizationPipeline`, sensörlerin senkron karelerini işleyerek nihai `LocalizationEstimate` ve `EgoState` sözleşmelerini üretir.

## Sorumluluklar ve Kısıtlamalar

- Bu modül ground truth değerlerini kullanmamalıdır; sadece sensör algılarını işlemelidir.
- Gerçek dünya kütüphaneleri (FAST-LIO2 vb.) gelecekte `estimators` paketine entegre edilebilir.
