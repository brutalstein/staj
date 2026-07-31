# Otonom Sürüş Projesi — Dondurulmuş Planlama Temeli

> Durum: Uygulama öncesi mimari temel  
> Dil: Python 3.11  
> Ana simülatör: CARLA 0.9.16  
> Uyumluluk hedefi: CARLA 0.9.15  
> Ana araç: Tesla Model 3  
> Ana işletim sistemleri: Ubuntu 22.04 ve Windows 11

---

## 1. Proje hedefi

Tanımlı ODD sınırları içinde çalışan, araştırma amaçlı Seviye 4 otonom sürüş mimarisi kurulacaktır.

Temel ilkeler:

- Öğrenilmiş algılama, tahmin ve planlama çekirdeği UniAD yaklaşımını temel alır.
- Davranış seçimi açık ve denetlenebilir bir Behavior Planner tarafından yapılır.
- Öğrenilmiş planlama çıktısı bağımsız Safety Cage tarafından doğrulanır.
- Kontrol katmanı güvenlikten geçmiş yörüngeyi takip eder.
- Her bileşenin girdileri, yaptığı işlem, çıktıları ve çıktı tüketicileri açıkça tanımlanır.
- Mevcut kod aynı işi yapıyorsa ikinci bir implementasyon yazılmaz.
- Kod içi açıklamalar ve geliştirici dokümantasyonu Türkçe olur.
- Değişken, sınıf ve veri alanları açık İngilizce teknik adlar ve birim ekleri kullanır.
- Ağırlıklar, eşikler ve model profilleri kod içine gömülmez; sürümlü konfigürasyonlarda tutulur.
- Güvenlik veya mimari hata yalnızca ağırlık değiştirerek gizlenmez.

---

## 2. Platform ve bağımlılık kararı

### 2.1 İşletim sistemleri

| Platform | Rol | Durum |
|---|---|---|
| Ubuntu 22.04 | Ana geliştirme, yüksek doğruluk inference, tam benchmark | Kanonik Linux platformu |
| Windows 11 | Kompakt inference, geliştirme, dashboard ve analiz | Kanonik Windows platformu |

Ubuntu 24.04 ilk sürümde ana platform yapılmaz. CARLA 0.9.16 UE4 paketleri ve kaynak derleme dokümantasyonu Ubuntu 20.04/22.04 üzerinde test edildiğini belirtir.

### 2.2 Python

- Zorunlu seri: Python 3.11
- Önerilen sabit sürüm: Python 3.11.15
- Proje kısıtı: `>=3.11,<3.12`
- Başlatıcı desteklenmeyen Python sürümünde kontrollü kapanır.

### 2.3 CARLA matrisi

| Bileşen | Ana profil | Uyumluluk profili |
|---|---|---|
| CARLA Server | 0.9.16 | 0.9.15 |
| CARLA Python API | 0.9.16 | 0.9.15 |
| ScenarioRunner | 0.9.16 | 0.9.15 |
| Tam benchmark | Evet | Hayır |
| Smoke/regresyon | Evet | Evet |

Kural: Server, Python API ve ScenarioRunner aynı sürümde olmak zorundadır.

### 2.4 AI ortamı

Bağımlılık çakışmalarını sınırlandırmak için iki çalışma katmanı kullanılır:

1. **Runtime ortamı**
   - CARLA Python API
   - Konfigürasyon ve sözleşmeler
   - Senaryo orkestrasyonu
   - Safety Cage
   - Controller
   - Loglama ve kayıt
   - Doküman üretimi

2. **Model ortamı**
   - PyTorch
   - CUDA
   - TensorRT/ONNX
   - UniAD/OpenMMLab uyarlaması
   - Kamera, LiDAR ve radar encoder'ları

Model worker ayrı süreç olarak çalışır. Runtime, OpenMMLab iç detaylarına bağımlı olmaz. Bu ayrım yalnızca gerçek bağımlılık çatışmasını ve model çökmesinin güvenlik katmanını etkilemesini önlemek için kullanılır.

### 2.5 GPU profilleri

#### `high_accuracy`

- Platform: RTX 5090, 32 GB
- Tam sensör girişi
- Daha yüksek görüntü ve BEV çözünürlüğü
- Daha uzun temporal pencere
- FP16/BF16
- Ana benchmark profili

#### `compact`

- Platform: RTX 5070, 8 GB
- Aynı sensör topolojisi
- Küçük backbone
- Daha kısa temporal pencere
- Daha seyrek voxel/radar temsili
- TensorRT FP16, doğrulanırsa INT8
- Distillation ile üretilmiş model

Sensör kalitesi platforma göre düşürülmez; işleme profili küçültülür.

---

## 3. Sistem mimarisi

```text
Mission Manager
→ ODD Manager
→ CARLA Simulation Adapter
→ Sensor Gateway ve Time Synchronizer
→ Localization
→ Multi-Sensor Temporal BEV
→ UniAD World Model
→ Map / Route / Traffic Rules
→ Explicit Hybrid Behavior Planner
→ Trajectory Planner
→ Safety Cage
→ Controller
→ Vehicle Interface
→ Monitoring / Recorder / Scenario Evaluator
```

### 3.1 Bağımlılık yönü

- `contracts` hiçbir uygulama modülüne bağımlı olmaz.
- `simulation` model, behavior, safety veya control iç detaylarını bilmez.
- `world_model`, `behavior` paketine bağımlı olmaz.
- `behavior`, `control` paketine bağımlı olmaz.
- `control`, doğrudan CARLA sınıfları kabul etmez.
- CARLA tipleri yalnızca `simulation/carla` ve `vehicle/carla` adaptörlerinde bulunur.
- Safety Cage, nominal planner'dan bağımsız veri yollarına erişebilir.
- Dashboard ve recorder yalnızca gözlemci olur; sürüş kararlarını değiştiremez.

---

## 4. Proje paket yapısı

```text
project/
├── autonomy/
│   ├── contracts/
│   ├── application/
│   ├── simulation/
│   │   └── carla/
│   ├── sensors/
│   ├── synchronization/
│   ├── localization/
│   ├── perception/
│   ├── world_model/
│   ├── mapping/
│   ├── routing/
│   ├── traffic_rules/
│   ├── behavior/
│   ├── planning/
│   ├── safety/
│   ├── control/
│   ├── vehicle/
│   ├── runtime/
│   ├── monitoring/
│   ├── recording/
│   └── evaluation/
├── config/
│   ├── architecture/
│   ├── contracts/
│   ├── runtime/
│   ├── sensors/
│   ├── vehicles/
│   ├── odd/
│   ├── scenarios/
│   ├── models/
│   ├── behavior/
│   ├── planning/
│   ├── safety/
│   └── control/
├── docs/
├── tests/
├── tools/
├── run_project.ps1
├── run_project.sh
├── run_docs.ps1
└── run_docs.sh
```

Her birinci taraf modül dizininde zorunlu `MODULE.md` bulunur.

---

## 5. Ortak veri sözleşmeleri

### 5.1 Zorunlu üst bilgiler

Bütün çalışma zamanı mesajlarında uygun olduğu ölçüde aşağıdaki alanlar bulunur:

- `timestamp_seconds`
- `simulation_frame`
- `sequence_number`
- `coordinate_frame`
- `source_module`
- `data_age_seconds`
- `confidence`
- `schema_version`
- `configuration_hash`
- Belirsizlik veya kovaryans

### 5.2 Temel sözleşmeler

| Sözleşme | Üretici | Ana tüketiciler |
|---|---|---|
| `RawSensorPacket` | Sensor Gateway | Synchronizer, Recorder |
| `SynchronizedSensorFrame` | Time Synchronizer | Localization, Perception, Safety Perception |
| `SensorHealth` | Sensor Health Monitor | ODD Manager, Safety Cage, Dashboard |
| `LocalizationEstimate` | Localization | World Model, Planner, Safety, Controller |
| `EgoState` | Vehicle State Estimator | Behavior, Planner, Safety, Controller |
| `TrackedObjectSet` | World Model | Behavior, Planner, Safety |
| `OccupancyForecast` | World Model | Planner, Safety |
| `VectorMap` | Mapping | Route, Behavior, Planner |
| `TrafficRuleState` | Traffic Rules | Behavior, Planner, Safety |
| `WorldModelSnapshot` | World Model | Behavior, Planner, Safety, Dashboard |
| `BehaviorIntent` | Behavior Planner | Trajectory Planner, Safety, Recorder |
| `TrajectoryCandidateSet` | Trajectory Planner | Safety Cage |
| `SafeTrajectory` | Safety Cage | Controller, Recorder |
| `VehicleCommand` | Controller | Vehicle Adapter, Safety Monitor |
| `RuntimeHealth` | Runtime Supervisor | ODD Manager, Safety Cage, Launcher |

Sözleşmeler `dataclass(frozen=True)` veya eşdeğer değişmez tiplerle tanımlanır. Büyük ham veriler mesaj içine kopyalanmaz; shared-memory referansı taşınır.

---

## 6. Süreç ve haberleşme mimarisi

### 6.1 Süreçler

| Süreç | Sorumluluk |
|---|---|
| Orchestrator | Tek CARLA tick sahibi, yaşam döngüsü |
| Sensor Gateway | Sensör callback'leri, shared memory |
| Localization Worker | Lokalizasyon füzyonu |
| Model Worker | BEV ve UniAD world model |
| Decision Worker | Behavior ve trajectory planning |
| Safety-Control Worker | Safety Cage ve kontrol |
| Recorder-Monitor Worker | Kayıt, dashboard, metrik |

İlk sürümde gereksiz süreç çoğaltılmaz. Ölçüm sonucunda bir süreç darboğaz oluşturursa ayrıştırılır.

### 6.2 Taşıma

- Büyük kamera ve nokta bulutu: shared memory + değişmez metadata
- Küçük sözleşmeler: sınırlı `multiprocessing.Queue`
- Her kuyruk bounded olur.
- Eski veri birikmesine izin verilmez.
- Güvenlik ve kontrol mesajları en son değer semantiği kullanabilir.
- ROS 2 çekirdek zorunluluk değildir; gerçek araç ve dağıtık sistem adaptörü olarak eklenir.

### 6.3 Yaşam döngüsü

```text
CREATED → INITIALIZING → READY → RUNNING → DEGRADED → STOPPING → STOPPED
                                      └→ FAILED
```

Heartbeat, maksimum mesaj yaşı ve hazır olma kontrolü zorunludur.

---

## 7. Zamanlama ve performans bütçesi

### 7.1 Simülasyon

- Synchronous mode: açık
- Fixed delta: `0.02 s` başlangıç değeri
- Simülasyon/kontrol: 50 Hz
- Physics substep: `0.01 s` veya daha küçük
- Tek `world.tick()` sahibi: Orchestrator
- Traffic Manager synchronous mode: açık
- Her tekrar öncesi world reload ve sabit seed

### 7.2 Hedef frekanslar

| Bileşen | Hedef |
|---|---:|
| IMU ve vehicle state | 50–100 Hz |
| Kamera | 20 Hz |
| 4D radar vekili | 20 Hz |
| 64 kanal LiDAR | 10 Hz |
| GNSS | 10 Hz |
| Localization | 50 Hz |
| World Model | 10–20 Hz |
| Behavior Planner | 10 Hz |
| Trajectory Planner | 10–20 Hz |
| Safety Cage | 50 Hz |
| Controller | 50 Hz |

### 7.3 Başlangıç veri yaşı sınırları

| Veri | Maksimum yaş |
|---|---:|
| Vehicle state | 40 ms |
| Localization | 60 ms |
| Radar safety track | 100 ms |
| World model | 150 ms |
| Behavior intent | 250 ms |
| Safe trajectory | 120 ms |
| Vehicle command | 40 ms |

Bu değerler ilk benchmark sonuçlarına göre sürümlü biçimde değiştirilebilir.

---

## 8. Koordinat sistemleri

### 8.1 İç sistem

- Orijin: arka aks merkezi
- `+x`: ileri
- `+y`: sol
- `+z`: yukarı
- Açı birimi: radyan
- Mesafe: metre
- Hız: m/s
- Zaman: saniye

### 8.2 CARLA dönüşümü

CARLA/Unreal:

- `+x`: ileri
- `+y`: sağ
- `+z`: yukarı

İç sisteme dönüşüm tek adaptörde yapılır:

\[
x_E=x_C,\qquad y_E=-y_C,\qquad z_E=z_C
\]

Hiçbir iş mantığı modülü CARLA'nın sağ-yönlü `y` eksenini görmez.

### 8.3 Dönüşüm ağı

```text
world
└── map
    └── ego_rear_axle
        ├── imu
        ├── lidar_roof
        ├── camera_front
        ├── camera_front_left
        ├── camera_front_right
        ├── camera_rear_left
        ├── camera_rear_right
        ├── camera_rear
        ├── radar_front
        ├── radar_front_left
        ├── radar_front_right
        ├── radar_rear_left
        ├── radar_rear_right
        └── radar_rear
```

---

## 9. Sensör sistemi

### 9.1 Dondurulmuş topoloji

- 6 çevresel RGB kamera
- 1 adet 64 kanallı 360° LiDAR
- 6 adet 4D imaging radar
- 2 GNSS anteni
- 1 otomotiv sınıfı IMU
- Tekerlek odometrisi ve araç geri bildirimi

### 9.2 LiDAR

Başlangıç yerleşimi:

\[
t_L =
\begin{bmatrix}
0.45B\\
0\\
H+0.10
\end{bmatrix}
\]

- Tavan ön-orta
- Roll/pitch/yaw: 0
- 64 kanal
- 360° yatay FoV
- Hedef tarama: 10 Hz
- Dikey FoV cihaz seçimiyle kesinleştirilir
- CARLA ray-cast LiDAR gerçek cihazın kontrollü vekilidir

### 9.3 Kameralar

| Kamera | Yaw | Başlangıç pitch | HFOV hedefi |
|---|---:|---:|---:|
| Front | 0° | -2° | 70–90° |
| Front-left | +60° | -4° | 100–120° |
| Front-right | -60° | -4° | 100–120° |
| Rear-left | +120° | -5° | 100–120° |
| Rear-right | -120° | -5° | 100–120° |
| Rear | 180° | -4° | 110–120° |

- Komşu kamera örtüşmesi: en az 20°, hedef 30–40°
- Global shutter ve HDR gerçek donanım şartnamesinde tercih edilir
- CARLA kamera çözünürlüğü iki GPU profiline göre değişir

### 9.4 Radarlar

- Ön merkez: 0°
- Ön-sol: +55°
- Ön-sağ: -55°
- Arka-sol: +145°
- Arka-sağ: -145°
- Arka merkez: 180°

Gerçek 4D radar sözleşmesi:

- range
- azimuth
- elevation
- radial velocity
- RCS
- confidence
- timestamp

CARLA stok radarı gerçek imaging radar fiziğini sağlamaz. İlk aşamada geometrik/hız vekili olarak kullanılır; gürültü, false alarm, dropout ve multipath etkileri ayrı fault model ile eklenir.

---

## 10. VehicleGeometryAdapter

Ana araç `vehicle.tesla.model3` olur fakat sensör layout Tesla'ya sabitlenmez.

Girdiler:

- Bounding box
- Tekerlek konumları
- Dingil mesafesi
- Genişlik
- Yükseklik
- Arka aks merkezi
- Kaporta yüzeyi

Çıktılar:

- Mutlak sensör transformları
- Montaj geçerlilik raporu
- Kaporta çakışmaları
- Yakın alan kör hacmi
- Kamera/radar örtüşme raporu
- Layout sürümü

Araç değişim akışı:

```text
Normalize layout
→ Araç geometrisine ölçekleme
→ Kaporta çakışma testi
→ Ray-casting
→ FoV ve kör hacim analizi
→ Onay veya açık hata
```

Geçersiz layout sessizce düzeltilmez.

---

## 11. Lokalizasyon

### 11.1 Girdiler

- IMU
- GNSS/çift anten heading
- LiDAR odometrisi
- Tekerlek odometrisi
- Direksiyon açısı
- Harita eşleştirme

### 11.2 Durum vektörü

\[
x =
[p_x,p_y,p_z,v_x,v_y,v_z,q_{wxyz},b_a,b_g]^T
\]

Ek alanlar:

- Kovaryans
- Kaynak sağlıkları
- Localization mode
- Veri yaşı
- Reset/recovery nedeni

### 11.3 Çıktı

`LocalizationEstimate`

### 11.4 Modlar

- `NOMINAL`
- `GNSS_DEGRADED`
- `LIDAR_DEGRADED`
- `DEAD_RECKONING`
- `UNRELIABLE`
- `RECOVERING`

`UNRELIABLE` durumu Safety Cage ve ODD Manager tarafından hız azaltma veya Minimal Risk Manoeuvre tetikler.

---

## 12. Multi-Sensor BEV ve UniAD uyarlaması

### 12.1 Girdiler

- Altı kamera
- 64 kanal LiDAR
- Altı radar
- Ego motion
- Kalibrasyon
- Temporal geçmiş

### 12.2 Yapı

```text
Camera Encoder
LiDAR Voxel/Pillar Encoder
Radar Encoder
        ↓
Ortak Temporal BEV
        ↓
Tracking
Vector Map
Motion Prediction
Occupancy
Planning Features
```

### 12.3 Çıktılar

- `TrackedObjectSet`
- `OccupancyForecast`
- `VectorMap`
- `PredictionSet`
- `WorldModelSnapshot`
- Modül güven ve belirsizlikleri

### 12.4 Profil farkları

| Özellik | High accuracy | Compact |
|---|---|---|
| Kamera çözünürlüğü | Yüksek | Orta |
| Backbone | Büyük | Küçük |
| Temporal pencere | Uzun | Kısa |
| BEV grid | İnce | Daha kaba |
| LiDAR voxel | Yoğun | Seyrek |
| Quantization | FP16/BF16 | FP16, doğrulanırsa INT8 |

Model çıktıları Safety Cage tarafından kesin gerçek kabul edilmez.

---

## 13. Behavior Planner

### 13.1 Durumlar

- `LANE_KEEP`
- `FOLLOW_VEHICLE`
- `APPROACH_STOP`
- `STOP`
- `YIELD`
- `INTERSECTION`
- `LANE_CHANGE`
- `OBSTACLE_AVOIDANCE`
- `PULL_OVER`
- `MINIMAL_RISK_MANEUVER`
- `EMERGENCY_STOP`

### 13.2 Girdiler

- WorldModelSnapshot
- EgoState
- LocalizationEstimate
- GlobalRoute
- TrafficRuleState
- ODDStatus
- RuntimeHealth

### 13.3 Çıktı

`BehaviorIntent`

### 13.4 Geçiş kuralları

Her geçiş şunları içerir:

- Giriş koşulu
- Çıkış koşulu
- Öncelik
- Histerezis
- Minimum durum süresi
- Timeout
- Gerekli veri güveni
- Reason code

Acil durumlar normal davranışlardan yüksek önceliklidir. Büyük tek bir `if/elif` zinciri kullanılmaz; küçük kural fonksiyonları tek bir durum yöneticisi tarafından birleştirilir.

---

## 14. Trajectory Planner

### 14.1 Girdiler

- BehaviorIntent
- WorldModelSnapshot
- OccupancyForecast
- PredictionSet
- VectorMap
- EgoState
- LocalizationEstimate

### 14.2 Adaylar

- Şerit merkezli
- Takip
- Duruş
- Şerit değişimi
- Kaçınma
- Güvenli kenara çekilme

### 14.3 Maliyet

\[
J =
w_cJ_{collision}
+w_lJ_{lane}
+w_pJ_{progress}
+w_fJ_{comfort}
+w_sJ_{speed}
+w_rJ_{rule}
+w_uJ_{uncertainty}
\]

Kural:

- Çarpışmama, yol sınırı ve dinamik uygulanabilirlik yalnızca maliyet ağırlığı değildir; zorunlu kısıt olarak da uygulanır.
- Her terim normalize edilir.
- Ağırlıkların birimi, aralığı ve etkilediği senaryolar katalogda tutulur.
- Ağırlık değişikliği tüm regresyon paketinde test edilir.

### 14.4 Çıktı

`TrajectoryCandidateSet`

Her aday:

- Pozisyon, heading, hız, ivme ve eğrilik dizisi
- Maliyet terimleri
- Kısıt ihlalleri
- Güven
- Üretim nedeni

taşır.

---

## 15. Safety Cage

### 15.1 Girdiler

- TrajectoryCandidateSet
- EgoState
- LocalizationEstimate
- Radar safety tracks
- LiDAR near-field obstacles
- TrafficRuleState
- Drivable corridor
- RuntimeHealth
- SensorHealth

### 15.2 Kontroller

- TTC
- RSS boylamsal/yatay güvenlik
- Yol ve şerit sınırı
- Hız sınırı
- Kırmızı ışık/stop çizgisi
- Dinamik uygulanabilirlik
- Veri yaşı ve güven
- Lokalizasyon kovaryansı
- Planner timeout
- Controller sağlık durumu
- CBF uygulanabilirliği

### 15.3 Çıktı

- `ACCEPT`
- `MODIFY`
- `REJECT_AND_FALLBACK`

ve `SafeTrajectory`.

Her karar reason code, ölçülen değer ve eşik taşır.

### 15.4 Fallback

- Kontrollü hız azaltma
- Güvenli duruş
- Şerit içinde duruş
- Uygunsa yol kenarına çekilme
- Acil fren

---

## 16. Controller

### 16.1 Nominal

- RTI-NMPC
- Başlangıç modeli: kinematik bisiklet
- Yüksek hız/limit testleri gerektirirse dinamik bisiklet modele geçiş
- Kontrol frekansı: 50 Hz

### 16.2 Kısıtlar

- Direksiyon açısı ve hızı
- İvme ve fren
- Yanal ivme
- Longitudinal/lateral jerk
- Lastik ve yol tutunma sınırı
- Aktüatör gecikmesi

### 16.3 Fallback

- Pure Pursuit veya Stanley
- Hız PID
- Ayrı güvenli duruş kontrolü

Aynı işi yapan iki fallback kontrolcüsü tutulmaz; senaryo sonuçlarına göre biri seçilip diğeri kaldırılır.

### 16.4 Çıktı

`VehicleCommand`

CARLA dönüşümü yalnızca `CarlaVehicleAdapter` içinde yapılır.

---

## 17. Konfigürasyon ve tuning

### 17.1 Kategoriler

- runtime
- sensors
- localization
- models
- behavior
- planning
- safety
- control
- scenarios

### 17.2 Parametre kataloğu

Her parametre:

- Kimlik
- Açıklama
- Birim
- Varsayılan
- Minimum/maksimum
- Güvenlik kritik durumu
- Kullanan modül
- Değişiklikte yeniden başlatma gereksinimi
- Kaynak/referans
- Son değişiklik nedeni

taşır.

### 17.3 Tuning akışı

```text
Hata gözlemi
→ Veri lineage ile sorumlu katmanı bulma
→ Parametre duyarlılık analizi
→ Sınırlı deney
→ Senaryo paketi
→ Güvenlik regresyonu
→ Yeni config sürümü
```

Her deney configuration hash ve seed ile kaydedilir.

---

## 18. ODD ve senaryolar

### 18.1 ODD profilleri

- `urban_nominal_v1`
- `urban_adverse_v1`
- `arterial_v1`

### 18.2 Senaryo tanımı

Her senaryo:

- ODD
- Harita ve spawn noktaları
- Aktörler
- Trigger
- Parametre aralıkları
- Seed
- Fault injection
- Beklenen behavior
- Beklenen safety action
- Pass/fail kriterleri
- Metrikler

içerir.

### 18.3 Kritik başlangıç senaryoları

- Örtülü noktadan ani yaya
- Yaya geçidi
- Bisikletli kör nokta
- Öndeki aracın ani freni
- Agresif cut-in
- Karşı şerit istilası
- Kırmızı ışık ihlali yapan çapraz araç
- Korumasız sol dönüş
- Yol çalışması/kapalı şerit
- Kamera frame drop
- LiDAR dropout
- Radar false target
- GNSS kaybı/sıçraması
- Planner gecikmesi
- Kalibrasyon sapması

---

## 19. Kayıt, veri lineage ve hata analizi

### 19.1 Her çalışma kaydı

- run_id
- Git commit
- CARLA sürümü
- ScenarioRunner sürümü
- Python ve paket lock hash
- Model/checkpoint
- Config hash
- Sensor layout ve calibration sürümü
- ODD/senaryo sürümü
- Seed
- GPU bilgisi
- Başlangıç ve bitiş zamanı

### 19.2 Mesaj lineage

Her önemli çıktı:

- Üretici modül
- Kullanılan input sequence numaraları
- Input yaşları
- Config sürümü
- Model sürümü
- Karar nedeni

taşır.

Bu bilgi, “bu fren komutu hangi yaya tespitinden ve hangi behavior kararından geldi?” sorusuna cevap verir.

### 19.3 Kayıt türleri

- Yapılandırılmış JSONL olay logu
- Ham sensör manifesti
- Karar ve safety event logu
- Metrik zaman serisi
- CARLA recorder
- İnsan okunabilir scenario report

---

## 20. Test planı

| Katman | Amaç |
|---|---|
| Unit | Saf hesap ve durum geçişleri |
| Contract | Şema, birim, frame ve üretici/tüketici |
| Configuration | Aralıklar ve bilinmeyen alanlar |
| Integration | Modül zincirleri |
| Replay | Aynı girdiden tekrarlanabilir karar |
| CARLA smoke | Spawn, sensor, tick, cleanup |
| Scenario regression | Davranış ve güvenlik |
| Fault injection | Sensör/compute bozulmaları |
| Performance | FPS, gecikme, VRAM |
| Soak | Uzun süreli kaynak sızıntısı |
| Cross-version | 0.9.15 ve 0.9.16 güvenlik sonucu |

Tam benchmark 0.9.16 Ubuntu RTX 5090 üzerinde raporlanır.

---

## 21. Yaşayan dokümantasyon ve kayıt sistemi

### 21.1 Her modülde `MODULE.md`

Her birinci taraf modülün dizininde zorunludur.

Örnek:

```text
autonomy/behavior/MODULE.md
autonomy/planning/MODULE.md
autonomy/safety/MODULE.md
```

Bu dosya aşağıdakileri açıkça kaydeder:

- Modülün amacı ve kapsam dışı işleri
- Gelen inputlar ve kaynakları
- Modülün yaptığı işlemler
- Üretilen outputlar
- Output tüketicileri
- Durum ve yaşam döngüsü
- Parametreler
- Hata/fallback davranışı
- Loglar ve metrikler
- Testler
- Entegrasyon geçmişi
- Akademik/mühendislik kaynakları

### 21.2 Tekrarı önleme

Input/output tabloları elle ikinci kez tutulmaz. Asıl kaynak:

```text
config/architecture/components.yaml
config/contracts/
```

olur.

`MODULE.md` içindeki otomatik bölümler jeneratör tarafından güncellenir:

```html
<!-- AUTO:INPUTS:START -->
<!-- AUTO:INPUTS:END -->
```

İnsan tarafından yazılan “neden”, algoritma, sınırlamalar ve karar geçmişi korunur.

### 21.3 Diğer kayıtlar

- `docs/decisions/ADR-xxxx.md`: mimari kararlar ve alternatifler
- `CHANGELOG.md`: sürüm seviyesinde kullanıcıya etkiler
- `docs/integration/`: dış sistem entegrasyonları
- `runtime/reports/`: deney ve senaryo sonuçları
- Git history: kod değişiminin kesin kaydı

Aynı bilgi beş farklı yerde elle tekrarlanmaz.

### 21.4 CI doğrulaması

CI şu durumlarda hata verir:

- `MODULE.md` eksik
- Tanımsız input/output
- Üreticisi olmayan zorunlu input
- Bilinmeyen output tüketicisi
- Kod modülü ile `module_id` uyuşmuyor
- Sözleşme sürümü eski
- Generated Markdown bölümü güncel değil
- Birim veya koordinat frame'i eksik
- Kritik output için test bağlantısı yok

---

## 22. Doküman portalı

- Material for MkDocs
- Mermaid
- MathJax
- Three.js
- Katmanlı progressive disclosure
- 3B sensör layout
- Araç seçimi
- Normalize ve mutlak transformlar
- Input/output veri akış grafiği
- Kaynak ve karar ilişkisi
- Test ve sürüm matrisi

Portal, `MODULE.md`, contracts ve config kayıtlarından üretilir.

---

## 23. Başlatıcılar

### Windows

- `run_project.ps1`
- `run_docs.ps1`

### Ubuntu

- `run_project.sh`
- `run_docs.sh`

Ortak gerçek implementasyon:

- `tools/project_launcher.py`
- `tools/docs_portal.py`

Başlatıcı kontrolleri:

- Python
- Sanal ortam
- Paket lock
- CARLA server
- CARLA API/server eşleşmesi
- ScenarioRunner
- GPU/CUDA/model profili
- Config ve contracts
- Model dosyaları
- Port ve süreç kilidi
- Temiz kapanış

---

## 24. Lisans ve kaynak politikası

Her harici kaynak için:

- İsim ve sürüm
- Lisans
- Resmî kaynak
- Projede kullanım biçimi
- Değişiklik yapıldıysa açıklama
- Model/veri kullanım kısıtları

kaydedilir.

Kod, model checkpoint, veri seti ve 3B araç modeli lisansları ayrı değerlendirilir.

---

## 25. Uygulama fazları

### Faz 0 — İskelet ve sözleşmeler

- Paket yapısı
- Contracts
- Component registry
- `MODULE.md` validator
- Config loader
- Launcher
- Docs portal iskeleti

### Faz 1 — CARLA ve sensör platformu

- CarlaSimulationAdapter
- VehicleGeometryAdapter
- Tesla spawn
- Sensör suite
- Sync/tick
- Recorder
- İlk smoke testler

### Faz 2 — Lokalizasyon ve vehicle state

- EgoState
- LocalizationEstimate
- Sağlık/degraded modlar

### Faz 3 — Perception ve world model

- Önce basit doğrulanabilir baseline
- Ardından Multi-Sensor BEV ve UniAD uyarlaması

### Faz 4 — Behavior ve trajectory

- Durum makinesi
- Aday trajectory
- Maliyet ve config sistemi

### Faz 5 — Safety ve control

- Safety Cage
- Fallback
- NMPC ve kontrol adapteri

### Faz 6 — Senaryo ve hata enjeksiyonu

- Kritik 15+ senaryo
- Fault modelleri
- Regresyon raporu

### Faz 7 — Model optimizasyonu

- RTX 5090 high_accuracy
- RTX 5070 compact
- TensorRT
- Distillation/quantization

### Faz 8 — Dayanıklılık ve gerçek araç hazırlığı

- Soak test
- HIL
- ROS 2 adapter
- Gerçek sensör kalibrasyon sözleşmesi

---

## 26. Definition of Done

Bir modül tamamlanmış sayılmaz, eğer:

- Input/output sözleşmesi yoksa
- Üretici ve tüketiciler tanımlı değilse
- `MODULE.md` güncel değilse
- Parametreleri sürümlü değilse
- Hata ve fallback davranışı tanımlı değilse
- Metrikleri ve logları yoksa
- Unit/contract/integration testi yoksa
- Doküman portalında görünmüyorsa
- Başlatıcı kontrollü biçimde doğrulayamıyorsa
---

## 27. Modül bazlı algoritma seçimi

### 27.1 Algoritma seçim ilkeleri

Her modül için algoritma seçimi aşağıdaki alanlarla kayıt altına alınır:

- Algoritma kimliği ve sürümü
- Ana görev
- Girdi ve çıktı sözleşmeleri
- Output tüketicileri
- Desteklenen ODD profilleri
- Matematiksel temel
- Akademik veya mühendislik kaynağı
- Ayarlanabilir parametreler
- Hesaplama bütçesi
- Bilinen hata biçimleri
- Fallback davranışı
- Kabul ve regresyon testleri
- Uygulama dosyaları

Aynı sorumluluk için birden fazla algoritma aynı anda üretim yolunda tutulmaz. Yeni algoritma ancak mevcut algoritmaya karşı aynı senaryo paketi üzerinde ölçülebilir üstünlük gösterirse onun yerini alır.

### 27.2 Algoritma profilleri

- `baseline`: İlk çalışan, anlaşılır ve doğrulanabilir sürüm.
- `target`: Tam mimarinin amaçlanan ana algoritması.
- `fallback`: Nominal algoritma kullanılamadığında çalışan sınırlı ve güvenli yöntem.
- `research_candidate`: Üretim yolunda değildir; yalnızca deney dalında benchmark edilir.

### 27.3 Dondurulan algoritma matrisi

| Modül | Ana algoritma | Fallback / bağımsız yol | ODD |
|---|---|---|---|
| ODD Manager | Kural tabanlı set-membership + confidence-aware degradation | Minimal Risk Manoeuvre | Tümü |
| Simulation Orchestrator | CARLA synchronous fixed-step deterministik tick | Kontrollü kapanış | Tümü |
| Sensor Synchronizer | Frame-indexed watermark + bounded approximate-time eşleme | Eksik modalite maskesi | Tümü |
| Calibration Monitor | Residual/Mahalanobis tabanlı drift izleme | Son doğrulanmış kalibrasyon + degraded mode | Tümü |
| Localization Front-end | FAST-LIVO2 ESIKF | FAST-LIO2 / IMU-wheel dead reckoning | Tümü |
| Localization Back-end | Robust factor graph, riSAM/iSAM2 yaklaşımı; GNSS ve wheel faktörleri | Yerel odometri | Tümü |
| Camera Encoder | Temporal multi-view transformer / UniAD uyumlu BEV encoder | Kamera modalitesi maskesi | Tümü |
| LiDAR Encoder | Sparse voxel/pillar BEV encoder | LiDAR modalitesi maskesi | Tümü |
| Radar Encoder | RadarBEVNet ve RCS-aware BEV encoding | Klasik radar safety tracker | Tümü, özellikle adverse |
| Multi-Sensor Fusion | Availability-aware unified BEV/canonical fusion | Kalan sensörlerle masked fusion | Tümü |
| Learned Tracking | UniAD query-based temporal tracking | IMM-UKF + global nearest-neighbor safety tracker | Tümü |
| Online Mapping | MapTRv2 + HD map consistency gate | Statik HD map | Tümü |
| Traffic Rules | Lane-linked rule graph + deterministik durum tahmini | Harita kuralı + güvenli duruş | Urban/arterial |
| Motion Prediction | UniAD multi-modal motion transformer | Constant-turn-rate-and-velocity tahmini | Tümü |
| Behavior Planner | Hierarchical state machine + Bayesian/POMDP interaction belief | Öncelik tabanlı güvenli kural seti | Tümü |
| Trajectory Planner | UniAD/PLUTO tarzı longitudinal-lateral query proposals + constrained refinement | Frenet/quintic güvenli koridor üretimi | Tümü |
| Safety Cage | RSS + robust HOCBF-QP + Simplex runtime assurance | Emergency/MRM controller | Tümü |
| Nominal Controller | RTI-NMPC, kinematik bisiklet modeli | Curvature-adaptive Pure Pursuit + gain-scheduled PID | Tümü |
| Sensor/Runtime Health | Innovation residuals + EWMA/CUSUM + deadline watchdog | Degraded/MRM | Tümü |
| Scenario Generation | ScenarioRunner + Scenic constrained probabilistic sampling | Sabit regresyon senaryoları | Tümü |
| Corner-case Search | Adaptive Stress Testing; önce MCTS, gerekirse DRL | Latin Hypercube / boundary search | Tümü |
| Parameter Tuning | Duyarlılık taraması + constrained multi-objective Bayesian optimization | Elle sürümlenmiş güvenli profil | Tümü |
| Evaluation | ISO 34502 senaryo çerçevesi + Bench2Drive kapalı çevrim metrikleri | Proje güvenlik metrikleri | Tümü |

### 27.4 ODD'ye göre algoritma davranışı

Ayrı algoritma kopyaları oluşturulmaz. Aynı algoritma, sürümlü ODD profilleriyle farklılaştırılır.

#### `urban_nominal_v1`

- Kısa ve orta planlama ufku
- Yaya, bisiklet, kavşak ve trafik kuralı önceliği
- Behavior Planner'da açık kural geçişleri
- Normal modalite ağırlıkları
- Düşük ve orta hız NMPC profili

#### `urban_adverse_v1`

- Availability-aware fusion zorunlu
- Radar ve LiDAR güveni kamera güveninden bağımsız değerlendirilir
- Görüş ve sensör sağlığına bağlı hız düşürme
- Daha büyük belirsizlik marjları
- Şerit değiştirme ve karmaşık manevralarda daha yüksek kabul eşiği
- ODD dışı durumda MRM

#### `arterial_v1`

- Daha uzun prediction ve planning horizon
- Uzun menzil ön radar önceliği
- Cut-in, merge ve lane-change için interaction belief
- Hız ve eğrilik uyarlamalı NMPC
- Daha uzun RSS response-time mesafeleri

### 27.5 Araştırma yükseltmeleri

Aşağıdakiler doğrudan v1 üretim yoluna eklenmez:

- BridgeDrive veya başka diffusion planner
- Öğrenilmiş online kinematik model
- Tam neural calibration
- VLM tabanlı behavior/planning
- End-to-end doğrudan actuator control

Bu yöntemler aynı input/output sözleşmesinin arkasında deneysel olarak değerlendirilir. Ana algoritmayı ancak kapalı çevrim güvenlik, gecikme, açıklanabilirlik ve iki GPU profili kriterlerinde üstünlük gösterirse değiştirir.

### 27.6 Algoritma Definition of Done

Bir algoritma seçilmiş sayılmaz, eğer:

- Kaynağı ve seçim gerekçesi yoksa
- Girdi/output sözleşmeleri tanımsızsa
- ODD kapsamı belirtilmemişse
- Parametreleri ve geçerli aralıkları yoksa
- Bilinen hata biçimleri ve fallback'i yoksa
- Hesaplama bütçesi ölçülmemişse
- Unit, replay ve ilgili CARLA senaryo testleri yoksa
- Portalın algoritma katmanında görünmüyorsa
