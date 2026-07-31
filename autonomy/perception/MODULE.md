# Perception Modülü

Bu modül, L4 otonom sürüş sisteminin çevresel algılama ve dünya modelleme bileşenlerini içerir.

## Sorumluluklar
- **Kamera, LiDAR, Radar Ön İşleme:** Sensör verilerini BEV (Bird's Eye View) özellik ağlarına (feature maps) dönüştürür.
- **Sensor Fusion:** BEVFusion ve RCBEVDet gibi stratejiler kullanarak Modalite-Farkındalıklı füzyon gerçekleştirir.
- **Harita Çıkarımı:** MapTRv2 üzerinden yol şeritlerini, sınırları ve kavşak geometrilerini algılar.
- **Nesne Takibi:** UniAD tabanlı takipçi ile çevredeki araç ve yayaların hızlarını, yönelimlerini ve gelecek konumlarını tutarlı şekilde takip eder.
- **Degradation Awareness:** Eğer bir veya daha fazla sensör bozulursa (örneğin LiDAR koparsa), kalan sensörlerle (Radar+Kamera) yoluna devam edebilmesi için düşürülmüş kapasitede (fallback) füzyon kararları alır.

## Modül Sınırları
- Perception modülü, hiçbir şekilde doğrudan actuator kontrol komutu üretmez.
- Perception, sensör okumalarını `SynchronizedSensorFrame` tipinde alır ve birleştirilmiş `WorldModelSnapshot` oluşturur.

## Bileşenler
- `pipeline.py`: Ana orkestratör `PerceptionPipeline` burada yer alır.
- `preprocessing/`: Ham sensör verisini algoritmaların beklediği özellik matrislerine dönüştürür.
- `models/`: Füzyon (BEVFusion), Harita (MapTRv2), Takip (UniAD Tracker) modellerinin kural tabanlı (heuristic baseline) uygulamalarını içerir. İlerleyen safhalarda PyTorch ve TensorRT inferans motorları ile değiştirilebilir.

## Kullanım Sözleşmeleri (Contracts)
- `WorldModelSnapshot`: Çevrenin anlık görüntüsü.
- `TrackedObject`: Dinamik nesne tanımları.
- `LaneBoundary`: Statik yol sınırları.
- `SensorDegradationStatus`: Sensörlerin çevrimiçi durumu.
