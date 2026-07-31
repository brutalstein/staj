# L4 Autonomy Platform — Proje Bağlamı, Teknik Kararlar ve Uygulama Kuralları

> **Belge türü:** Kanonik proje bağlamı ve karar kaydı
> **Son güncelleme:** 31 Temmuz 2026
> **Proje:** CARLA tabanlı, ODD sınırlandırılmış Seviye 4 otonom sürüş araştırma platformu
> **Depo:** `https://github.com/brutalstein/staj`
> **Ana dal:** `main`
> **Birincil geliştirme ortamı:** Ubuntu / AILAB-1
> **Kanonik CARLA sürümü:** CARLA 0.9.16
> **Uyumluluk hedefi:** CARLA 0.9.15
> **Python:** Yalnızca Python 3.11
> **Başlangıç aracı:** Tesla Model 3

---

## 1. Belgenin amacı

Bu belge, proje hakkında alınmış teknik kararları, zorunlu çalışma kurallarını, mimari sınırları, mevcut implementasyon durumunu, bilinen sorunları ve sonraki fazların hedeflerini tek yerde toplar.

Yeni bir geliştirici veya kodlama ajanı bu belgeyi okumadan projede değişiklik yapmamalıdır.

Bu belge şu amaçlarla kullanılır:

1. Aynı kararların tekrar tartışılmasını önlemek.
2. Farklı modüllerde çelişkili mimariler oluşmasını engellemek.
3. Deneysel veya kullanılmayan kodun ana projeye girmesini önlemek.
4. Uygulanan ve yalnızca planlanan bileşenleri birbirinden ayırmak.
5. Sensör, algoritma, runtime ve güvenlik kararlarının gerekçelerini korumak.
6. Patch tabanlı geliştirme sürecinin kurallarını sabitlemek.
7. Seviye 4 araştırma iddiasının sınırlarını açık tutmak.
8. Her fazın hangi testlerle tamamlanmış sayılacağını belirlemek.

Bu belgede belirtilen kararlar varsayılan proje mimarisidir. Yeni bir karar mevcut bir kararı değiştiriyorsa değişiklik açıkça ADR, changelog ve bu belge üzerinde işlenmelidir.

---

# 2. Temel proje hedefi

Projenin hedefi, tanımlanmış Operational Design Domain, yani ODD içerisinde çalışan:

* algılama,
* lokalizasyon,
* dünya modeli,
* davranış planlama,
* yörünge planlama,
* runtime safety assurance,
* araç kontrolü,
* hata yönetimi,
* minimum risk manoeuvre,
* kayıt ve değerlendirme

bileşenlerini içeren bir **simülasyon tabanlı Seviye 4 araştırma prototipi** geliştirmektir.

Proje gerçek yol sertifikasyonu iddiasında bulunmaz.

Kullanılacak doğru ifade:

> **Simulation-based Level 4 research prototype in the declared ODD.**

Aşağıdaki ifadeler kullanılmamalıdır:

* Gerçek yol için sertifikalı Seviye 4 sistem
* Üretime hazır otonom araç
* Güvenliği kanıtlanmış gerçek araç sistemi
* Gerçek dünyada sürücüsüz çalışmaya hazır sistem

---

# 3. Değiştirilemez proje ilkeleri

## 3.1. Ana mimari doğrudan çalışmalıdır

Proje farklı demo modları veya birbirinden kopuk alternatif akışlar üzerine kurulmayacaktır.

```text
./run_project.sh start
```

komutu, o faz için uygulanmış olan ana mimariyi doğrudan çalıştırmalıdır.

Şunlar istenmemektedir:

* `legacy_mode`
* `experimental_mode`
* `new_mode`
* `phase1_mode`
* aynı iş için paralel eski ve yeni implementasyonlar
* ana runtime tarafından hiç çağrılmayan araştırma sınıfları
* yalnızca gelecekte kullanılabilir düşüncesiyle eklenmiş boş modüller
* kullanılmayan config seçenekleri
* birbirini tekrar eden controller, synchronizer veya sensor wrapper sınıfları

Bir modül uygulanmış olarak işaretleniyorsa ana runtime tarafından gerçekten kullanılmalıdır.

Henüz uygulanmayan algoritmalar:

* registry,
* dokümantasyon,
* roadmap

seviyesinde tutulabilir; ancak sahte veya boş implementasyon eklenmemelidir.

---

## 3.2. Gereksiz karmaşıklık eklenmeyecektir

Her ek sınıf veya servis için şu sorular cevaplanmalıdır:

1. Ana runtime bunu gerçekten kullanıyor mu?
2. Aynı işi yapan başka sınıf var mı?
3. Bu sorumluluk mevcut bir modüle doğal biçimde eklenebilir mi?
4. Testi var mı?
5. Hata ve cleanup davranışı tanımlı mı?
6. Dokümantasyonu ve registry kaydı var mı?

Bu soruların cevabı olumsuzsa kod eklenmemelidir.

---

## 3.3. Araştırma kodu ana projede atıl kalmayacaktır

Bir araştırma algoritması projeye eklendiğinde:

* giriş ve çıkış sözleşmeleri tanımlanmalı,
* ana veri akışına bağlanmalı,
* fallback davranışı belirlenmeli,
* testleri eklenmeli,
* konfigürasyonu sürümlenmeli,
* performans bütçesi ölçülmeli,
* dokümantasyon portalında görünmeli,
* kayıt ve replay sistemi tarafından izlenebilmelidir.

Bu şartları sağlamayan araştırma kodu ana runtime’a eklenmeyecektir.

---

## 3.4. CARLA ground truth normal algılama girdisi olmayacaktır

CARLA actor konumları, bounding box ground truth, trafik ışığı ground truth veya benzeri simulator truth bilgileri normal çalışma sırasında perception girdisi olarak kullanılamaz.

Ground truth yalnızca şu amaçlarla kullanılabilir:

* test oracle,
* metrik hesaplama,
* hata analizi,
* benchmark,
* offline doğrulama,
* simülasyon senaryosu değerlendirme.

Normal runtime algısı sensör verilerinden türetilmelidir.

---

## 3.5. Güvenlik algılama ve planlamadan bağımsız denetlenmelidir

Öğrenme tabanlı veya nominal algoritmaların çıkışı doğrudan araç actuator’larına gönderilmemelidir.

Uzun vadeli akış:

```text
World Model
    ↓
Behavior Planner
    ↓
Trajectory Planner
    ↓
Safety Cage
    ↓
Controller
    ↓
Vehicle Interface
```

Safety Cage nominal planlayıcıdan bağımsız olarak:

* RSS sınırları,
* robust Control Barrier Function kısıtları,
* Simplex/runtime assurance mantığı,
* minimum risk manoeuvre,
* emergency stop

uygulayabilmelidir.

---

# 5. Geliştirme ortamı

## 5.1. Birincil Linux ortamı

```text
Host: AILAB-1
Kullanıcı: superuser
OS: Ubuntu
Proje: /home/superuser/Desktop/carla
Conda environment: odd
Conda path: /home/superuser/miniconda3/envs/odd
Python: 3.11.15
Downloads: /home/superuser/Downloads
```

Repo:

```text
https://github.com/brutalstein/staj
```

Ana dal:

```text
main
```

---

## 5.2. CARLA kurulumu

CARLA kaynak dizini:

```text
/home/superuser/carla
```

CARLA server executable:

```text
/home/superuser/carla/Dist/CARLA_Shipping_e78db150c/LinuxNoEditor/CarlaUE4.sh
```

Kullanılan custom build kimliği:

```text
e78db150c
```

Bu build, kaynak commit ile eşleşmektedir:

```text
e78db150cfa7d196a1c939002f0d39ae3e1f42ce
```

Uyumluluk karşılığı:

```text
e78db150c → CARLA 0.9.16
```

Python 3.11 için yerel olarak üretilmiş wheel:

```text
/home/superuser/carla/PythonAPI/carla/dist/carla-0.9.16-cp311-cp311-linux_x86_64.whl
```

CARLA server’ın orijinal paketinde bulunan wheel Python 3.12 içindi. Proje Python 3.11 kullandığı için CPython 3.11 wheel kaynak koddan oluşturulmuştur.

---

## 5.3. Hedef platformlar

Kanonik benchmark platformu:

```text
Ubuntu 22.04
RTX 5090
Python 3.11
CARLA 0.9.16
```

İkincil uyumluluk hedefi:

```text
Windows 11
RTX 5070
Python 3.11
CARLA 0.9.16
```

Windows ve Ubuntu aynı:

* config şemalarını,
* veri sözleşmelerini,
* algoritma davranışlarını,
* kayıt formatlarını,
* test beklentilerini

kullanmalıdır.

---

# 6. CARLA sürüm politikası

Kanonik sürüm:

```text
0.9.16
```

Uyumluluk sürümü:

```text
0.9.15
```

Custom server build kimlikleri semantik sürüm listesine doğrudan eklenmez.

Doğru config modeli:

```yaml
supported_versions:
  - "0.9.15"
  - "0.9.16"

server_version_aliases:
  "e78db150c": "0.9.16"
```

`capabilities.py` yalnızca semantik sürümleri tanır.

Alias çözümü configuration katmanında yapılır:

```text
reported build/version
        ↓
server_version_aliases
        ↓
compatibility version
        ↓
capability lookup
```

Client ve server ham değerleri farklı olsa bile aynı compatibility version’a çözülüyorsa uyumlu kabul edilebilir.

Örnek:

```text
Client: e78db150c
Server: 0.9.16
Resolved client: 0.9.16
Resolved server: 0.9.16
Result: compatible
```

---

# 7. Proje fazları

## Faz 0 — Platform omurgası

Durum:

```text
Tamamlandı
```

Kapsam:

* Python paket omurgası
* Tipli veri sözleşmeleri
* YAML config loader
* Configuration hash
* CARLA adapter
* Client/server version doğrulaması
* Custom build alias desteği
* Runtime lifecycle
* Service orchestrator
* Launcher
* Doctor/check/install/start komutları
* Component registry
* Contract registry
* Algorithm registry
* Source registry
* MODULE.md zorunluluğu
* Proje validator
* MkDocs Material portalı
* Mermaid ve MathJax desteği
* Başlangıç ODD tanımları
* Tesla Model 3 araç profili
* Sensör layout başlangıç profili
* Unit ve mock testler

Faz 0 runtime yalnız CARLA’ya bağlanıyor ve bağlantıyı açık tutuyordu. Araç veya sensör actor oluşturmuyordu.

---

## Faz 1 — Araç, sensör ve senkron runtime

Durum:

```text
Ana implementasyon hazırlandı.
Gerçek CARLA üzerinde ilk çalışma yapıldı.
Wheel coordinate hatası bulundu.
Düzeltme patch'i hazırlandı.
Düzeltme sonrası gerçek CARLA sonucu ayrıca doğrulanmalıdır.
```

Kapsam:

* Tesla Model 3 spawn
* VehicleGeometryAdapter
* Araç geometrisine bağlı sensör transform çözümü
* Sensor Factory
* 16 CARLA sensor actor
* Vehicle feedback
* Synchronous world mode
* Tek tick sahibi runtime
* Bounded sensor buffer
* Frame synchronizer
* Recorder ve manifest
* Kısmi spawn rollback
* Actor cleanup
* World settings restore
* Default application entegrasyonu
* Lifecycle rollback sertleştirmesi
* Unit/mock/error-injection testleri
* Opt-in gerçek CARLA smoke testi
* Sensör kaynak ve gerekçe dokümantasyonu

---

## Faz 2 — Lokalizasyon ve vehicle state

Planlanan kapsam:

* IMU preprocessing
* Wheel odometry
* Steering/actuator feedback kullanımı
* GNSS preprocessing
* Dual-GNSS baseline estimator
* Lever-arm compensation
* Heading estimator
* FAST-LIO2 baseline
* FAST-LIVO2 hedef mimari
* Robust factor graph
* R-iSAM veya eşdeğer robust incremental smoothing
* Localization confidence
* Localization degradation modes
* Dead reckoning
* Recovery
* EgoState üretimi
* LocalizationEstimate üretimi

Dual GNSS kullanılmaya devam edecekse Faz 2’de algoritmik olarak kullanılmalıdır. Dual-GNSS heading uygulanmazsa ikinci GNSS kaldırılmalıdır. Yalnızca sensör sayısını artırmak için sistemde tutulmamalıdır.

---

## Faz 3 — Multi-sensor BEV ve dünya modeli

Planlanan kapsam:

* Kamera preprocessing
* LiDAR preprocessing
* Radar preprocessing
* Availability-aware sensor fusion
* BEVFusion baseline
* RCBEVDet radar-camera bileşenleri
* UniAD temporal world model
* Sensor modality masking
* Multi-object tracking
* MapTRv2 tabanlı map representation
* WorldModelSnapshot
* Sensor degradation awareness
* Temporal consistency

---

## Faz 4 — Davranış ve yörünge planlama

Planlanan kapsam:

* Hiyerarşik behavior planner
* Explicit driving state machine
* Bounded POMDP karar katmanı
* SpeedConstraintSet
* Kendi free-flow desired speed politikamız
* UniAD/PLUTO trajectory proposals
* Apollo EM / Frenet fallback
* Safe corridor
* Stop, yield, follow, lane change ve pull-over kararları
* Minimum risk manoeuvre talebi
* LongitudinalProfile
* TrajectoryCandidateSet

---

## Faz 5 — Safety Cage ve kontrol

Planlanan kapsam:

* RSS
* Robust CBF
* HOCBF-QP
* Simplex runtime safety assurance
* SafetyDecision
* SafeTrajectory
* Minimal risk manoeuvre
* Emergency stop
* RTI-NMPC nominal controller
* Pure Pursuit fallback
* Gain-scheduled PID fallback
* VehicleCommand
* Actuator limits
* Steering rate limits
* Acceleration and jerk constraints

---

## Faz 6 — Senaryo, hata enjeksiyonu ve benchmark

Planlanan kapsam:

* Scenario runner
* Scenic veya eşdeğer senaryo üretimi
* Sensor dropout
* Sensor delay
* Timestamp jitter
* GNSS jump
* IMU bias drift
* Radar degradation
* Camera occlusion
* Calibration fault
* Localization divergence
* Planner timeout
* Controller saturation
* Replay regression
* Multi-map benchmark
* Multi-weather benchmark
* Multi-seed benchmark
* Performance test
* Soak test
* Safety metric report
* Cross-version CARLA testi

---

# 8. Kanonik sistem mimarisi

Uzun vadeli ana mimari:

```text
Mission Manager
      ↓
ODD Manager
      ↓
CARLA Adapter
      ↓
Sensor Gateway
      ↓
Time Synchronizer
      ↓
Localization ─────────────────────────┐
      ↓                               │
Temporal BEV / World Model            │
      ↓                               │
Map / Route / Rules                   │
      ↓                               │
Behavior Planner                      │
      ↓                               │
Trajectory Planner                    │
      ↓                               │
Safety Cage ◄─────────────────────────┘
      ↓
Controller
      ↓
Vehicle Interface
      ↓
CARLA Vehicle
```

Observer-only bileşenler:

```text
Monitoring
Recorder
Evaluator
Dashboard
```

Observer bileşenleri kontrol zincirinin sahibi olamaz ve vehicle command üretemez.

---

## 8.1. Runtime ve model worker ayrımı

Uzun vadede iki izole çalışma ortamı kullanılacaktır.

### Runtime process

İçerik:

* CARLA API
* configuration
* contracts
* orchestration
* localization supervision
* Safety Cage
* controller
* recorder
* monitoring
* vehicle interface

### Model worker process

İçerik:

* PyTorch
* CUDA
* TensorRT
* OpenMMLab
* UniAD
* BEVFusion
* RCBEVDet
* MapTRv2
* GPU inference

Amaç:

* bağımlılık çatışmalarını azaltmak,
* model worker crash’inin Safety Cage ve kontrolü düşürmesini engellemek,
* inference timeout’unu açıkça yönetmek,
* runtime güvenlik katmanını model ortamından ayırmak.

Bu ayrım Faz 1’de zorunlu değildir; model entegrasyonu başladığında uygulanacaktır.

---

# 9. Faz 1 modül yapısı

## 9.1. Ana runtime

Dosya:

```text
autonomy/simulation/carla/phase1_runtime.py
```

Ana sınıf:

```text
CarlaPhase1Runtime
```

Sorumlulukları:

* CARLA world settings’i okumak
* synchronous mode’u açmak
* fixed delta ayarlamak
* Tesla actor spawn etmek
* araç geometrisini çıkarmak
* sensörleri spawn etmek
* aracı güvenli durumda tutmak
* world tick üretmek
* sensör frame’lerini eşlemek
* vehicle feedback üretmek
* recorder’a yazmak
* kapanışta kaynakları temizlemek
* world settings’i eski hâline döndürmek

Ana world tick sahibi yalnızca bu runtime’dır.

Aynı process içinde ikinci bir modül:

```python
world.tick()
```

çağırmamalıdır.

---

## 9.2. VehicleGeometryAdapter

Dosya:

```text
autonomy/simulation/carla/geometry.py
```

Ana sınıf:

```text
VehicleGeometryAdapter
```

Amaç:

* araç boyutlarını sabit Tesla ölçülerinden okumamak,
* CARLA actor instance üzerinden gerçek runtime geometrisini çıkarmak,
* sensör yerleşimini araçtan bağımsız hâle getirmek.

Çıkarılan bilgiler:

* bounding box center
* bounding box extent
* body length
* body width
* body height
* wheel positions
* wheelbase
* front track width
* rear track width
* rear axle reference
* wheel coordinate reference
* wheel scale

Sensör transformları `ego_rear_axle` referansında çözümlenir.

Araç geometrisi manuel olarak config içine sabitlenmemelidir.

---

## 9.3. Sensor Factory

Dosya:

```text
autonomy/simulation/carla/sensor_factory.py
```

Ana sınıf:

```text
CarlaSensorFactory
```

Sorumlulukları:

* config’ten sensör tanımlarını almak
* CARLA blueprint seçmek
* blueprint attribute’larını uygulamak
* resolved pose üretmek
* sensor actor spawn etmek
* rigid attachment kullanmak
* callback’i Sensor Gateway’e bağlamak
* spawn yarıda kalırsa oluşmuş sensörleri temizlemek

Sensor Factory doğrudan world tick sahibi değildir.

---

## 9.4. Sensor Gateway

Dosya alanı:

```text
autonomy/sensing/gateway/
```

Temel bileşenler:

```text
BoundedSensorBuffer
SensorGateway
SensorMeasurement
```

Kurallar:

* Her sensörün buffer kapasitesi sınırlıdır.
* Sınırsız queue kullanılmaz.
* Eski veriler kontrollü düşürülebilir.
* Drop sayısı kaydedilir.
* Callback thread exception’ları sessizce yutulmaz.
* Callback hatası ana runtime’a sensor_id ile aktarılır.
* Sensor callback içinde ağır inference yapılmaz.

Varsayılan buffer kapasitesi:

```yaml
sensor_buffer_capacity: 8
```

Bu değer config’in kaynak doğrusu olmalıdır.

---

## 9.5. Frame Synchronizer

Dosya alanı:

```text
autonomy/sensing/synchronization/
```

Ana sınıf:

```text
FrameSynchronizer
```

Kurallar:

* Veri eşleme CARLA `frame` numarası üzerinden yapılır.
* “Son gelen sensör verisi” yaklaşımı kullanılmaz.
* Farklı frekanslar için stride veya beklenen-frame modeli kullanılır.
* Aynı ortak frame bulunamazsa sınırlı timeout uygulanır.
* Eksik sensör durumu açıkça raporlanır.
* Eski ve tüketilmiş frame’ler buffer’dan temizlenir.
* SynchronizedSensorFrame sözleşmesi üretilir.
* Timeout sonsuz beklemeye dönüşmez.

---

## 9.6. Recorder

Dosya alanı:

```text
autonomy/recording/
```

Ana sınıf:

```text
RunRecorder
```

Varsayılan çıktı:

```text
runtime/recordings/
```

Her run için kaydedilecek bilgiler:

* run_id
* Git commit
* CARLA client version
* CARLA server version
* CARLA compatibility version
* map
* configuration hash
* sensor layout hash
* vehicle profile hash
* ODD profile hash
* random seed
* Python version
* GPU bilgisi
* başlangıç zamanı
* bitiş zamanı
* çalışma sonucu
* araç geometrisi
* wheel position reference
* wheel position scale
* resolved sensor poses
* sensor frame metadata
* dropped frame counts
* exception bilgisi
* message lineage

Çalışma durumları:

```text
RUNNING
COMPLETED
FAILED
```

Raw kamera, LiDAR veya radar payload kaydı varsayılan olarak kapalı tutulabilir:

```yaml
record_raw_data: false
```

Ama metadata ve manifest her koşulda kaydedilmelidir.

---

# 10. Default çalışma davranışı

```bash
./run_project.sh start
```

çalıştırıldığında:

1. Python sürümü doğrulanır.
2. Aktif conda/venv doğrulanır.
3. Config yüklenir.
4. Registry ve MODULE.md doğrulanır.
5. CARLA bağlantısı kurulur.
6. Client/server alias çözümü yapılır.
7. Harita okunur.
8. Synchronous mode açılır.
9. Tesla Model 3 spawn edilir.
10. Araç geometrisi çıkarılır.
11. Sensörler spawn edilir.
12. Recorder başlatılır.
13. Runtime tick döngüsüne girilir.
14. Sensörler senkronize edilir.
15. Vehicle feedback kaydedilir.
16. `Ctrl+C` veya `SIGTERM` ile kontrollü kapanılır.
17. Sensörler durdurulur ve destroy edilir.
18. Ego actor destroy edilir.
19. World settings restore edilir.
20. Recorder sonucu tamamlanır.

Faz 1’de araç hareket ettirilmez.

Güvenli başlangıç durumu:

```text
Autopilot: kapalı
Throttle: 0
Brake: 1
Hand brake: açık
```

Faz 1’de controller uygulanmış değildir. Aracın hareket ettirilmesi Faz 1 kapsamına dahil değildir.

---

# 11. Sensör topolojisi

## 11.1. CARLA sensor actor sayısı

Toplam:

```text
16 sensor actor
```

Dağılım:

```text
6 RGB kamera
1 adet 64 kanallı LiDAR
6 radar proxy
2 GNSS
1 IMU
```

Bunlara ek olarak vehicle actor’dan okunacak actor feedback:

* wheel state
* steering state
* velocity
* acceleration
* angular velocity
* actuator state

CARLA sensor actor değildir; ego vehicle üzerinden okunur.

---

# 12. Sensör seçimi ve kaynak gerekçeleri

## 12.1. Bu topoloji tek bir makaleden alınmamıştır

Sensör sayısı ve yerleşimi tek bir akademik makaleden birebir kopyalanmamıştır.

Topoloji aşağıdaki kaynakların ve proje ihtiyaçlarının sentezidir:

* nuScenes sensör topolojisi
* UniAD’ın kullandığı nuScenes çevresel kamera düzeni
* BEVFusion kamera–LiDAR fusion yaklaşımı
* RCBEVDet radar–kamera fusion yaklaşımı
* FAST-LIO2 LiDAR–IMU odometri gereksinimleri
* FAST-LIVO2 LiDAR–IMU–kamera odometri hedefi
* dual-antenna GNSS/INS heading literatürü
* CARLA’nın desteklediği sensor actor modelleri
* proje ODD’si
* failure injection ve sensor degradation hedefleri
* 360° çevresel kapsama ihtiyacı

Her sensör parametresi şu üç kategoriden biriyle işaretlenmelidir:

1. **Literatür uyumlu karar**
2. **CARLA model kısıtı**
3. **Projeye özel mühendislik başlangıç değeri**

Kesin montaj açıları, FoV değerleri veya range değerleri literatürden birebir alınmış gibi sunulmamalıdır.

---

## 12.2. Altı RGB kamera

Kamera düzeni:

```text
camera_front
camera_front_left
camera_front_right
camera_rear_left
camera_rear_right
camera_rear
```

Başlangıç yaw yerleşimi:

```text
front:         0°
front-left:   +60°
front-right:  -60°
rear-left:   +120°
rear-right:  -120°
rear:         180°
```

CARLA’nın coordinate convention’ı dikkate alınmalıdır. YAML dosyası kaynak doğrudur.

Altı kamera tercihinin gerekçeleri:

* nuScenes altı çevresel kamera kullanır.
* UniAD nuScenes üzerinde geliştirilmiş ve değerlendirilmiştir.
* Çevresel 360° görünüm temporal BEV için uygundur.
* Tek ön kamera kör bölgeler oluşturur.
* Yan ve arka kameralar lane change, merging ve rear object awareness için gereklidir.
* Overlap, cross-camera association ve calibration kontrolüne imkân verir.

Kesin yaw, pitch ve FoV değerleri nuScenes calibration verilerinden birebir alınmamıştır.

Bunlar:

* 360° coverage,
* yeterli overlap,
* self-occlusion azaltımı,
* GPU bütçesi,
* CARLA araç geometrisi

dikkate alınarak belirlenen proje başlangıç değerleridir.

Bu değerler ileride şu testlerle doğrulanmalıdır:

* angular coverage
* blind-zone analysis
* self-occlusion
* cross-camera overlap
* object recall by azimuth
* lane visibility
* night/rain performance
* calibration perturbation test

---

## 12.3. Tek 64 kanallı LiDAR

LiDAR:

```text
lidar_roof
```

Başlangıç konumu:

```text
x = rear axle’dan wheelbase’in yaklaşık %45’i
y = araç merkezi
z = araç yüksekliği + yaklaşık 0.10 m
```

Kesin kaynak:

```text
config/sensors/layouts/tesla_model3_omnihd_v1.yaml
```

LiDAR tercihinin gerekçeleri:

* FAST-LIO2 için LiDAR–IMU odometri girdisi
* FAST-LIVO2 için LiDAR–IMU–kamera odometri girdisi
* BEVFusion için geometrik 3B bilgi
* Kameradan bağımsız depth referansı
* Radar ve camera detection doğrulaması
* Map ve localization için stabil geometri
* Ground separation
* Free-space ve obstacle validation

Tek LiDAR kararı nuScenes ile uyumludur; ancak **64 kanal seçimi projeye özel yüksek çözünürlüklü baseline kararıdır**.

64 kanal değeri nuScenes sensörünün birebir kopyası değildir.

---

## 12.4. Altı radar proxy

Radar düzeni:

```text
radar_front
radar_front_left
radar_front_right
radar_rear_left
radar_rear_right
radar_rear
```

Başlangıç yaw yerleşimi:

```text
front:          0°
front-left:    +55°
front-right:   -55°
rear-left:    +145°
rear-right:   -145°
rear:          180°
```

Radarların gerekçeleri:

* düşük görünürlükte kamera desteği
* radial velocity
* relative motion
* uzunlamasına takip
* cut-in/cut-out algısı
* merging
* yan yaklaşan araç
* arka yaklaşan araç
* RCBEVDet tipi radar-camera BEV fusion
* sensör modality degradation testleri

nuScenes beş radar kullanır.

Projede altı radar seçilmiştir. Altıncı rear-center radar:

* ön–arka simetri,
* arka merkez kapsaması,
* rear collision awareness

için eklenmiş projeye özel karardır.

Bu nedenle altı radarın nuScenes’ten birebir alındığı iddia edilmemelidir.

---

## 12.5. CARLA radar sınırlaması

CARLA radar sensörü gerçek üretim sınıfı imaging 4D radar değildir.

CARLA radarının sağladığı temel ölçümler:

* azimuth
* altitude
* depth/range
* radial velocity

Gerçek 4D radar özelliklerinin tamamı modellenmez:

* gerçek antenna array
* beamforming
* range-Doppler-angle cube
* RCS davranışı
* multipath
* ghost target
* interference
* realistic clutter
* elevation çözünürlüğü
* firmware filtering

Bu nedenle proje içindeki doğru isim:

```text
4d_radar_proxy
```

Bu isim, sensörün 4D radar fusion arayüzünü temsil eden bir CARLA proxy olduğunu belirtir.

Gerçek 4D radar performansı iddia edilmemelidir.

---

## 12.6. IMU

IMU gerekçeleri:

* angular velocity
* linear acceleration
* orientation propagation
* dead reckoning
* FAST-LIO2
* FAST-LIVO2
* GNSS/INS fusion
* localization dropout recovery
* motion compensation
* high-rate vehicle dynamics

Faz 2’de IMU için en az şu modeller bulunmalıdır:

* bias
* bias random walk
* noise density
* scale-factor error
* timestamp jitter
* dropout
* saturation

CARLA’nın ideal veya basit noise modeli gerçek IMU’nun tam fiziksel karşılığı değildir.

---

## 12.7. İki GNSS sensörü

GNSS sensörleri:

```text
gnss_primary
gnss_secondary
```

İki GNSS tercihinin hedefi:

* yalnızca yedeklilik değildir,
* iki anten arasındaki bilinen baseline üzerinden heading üretmektir,
* düşük hızda veya araç hareketsizken course-over-ground yerine heading sağlamaktır,
* GNSS/INS fusion’da yaw observability’yi iyileştirmektir.

Baseline:

[
\mathbf{b}
==========

## \mathbf{p}_{secondary}

\mathbf{p}_{primary}
]

Anten yerleşimi araç gövdesine göre bilindiğinde baseline yönünden araç heading’i türetilebilir.

Ancak önemli sınırlama:

CARLA `sensor.other.gnss` şu bilgileri üretir:

* latitude
* longitude
* altitude
* basit bias/noise parametreleri

CARLA gerçek dual-antenna GNSS compass için gereken şu verileri üretmez:

* carrier phase
* integer ambiguity
* RTK fix
* shared satellite observation
* raw pseudorange
* raw phase
* antenna clock correlation

Bu nedenle mevcut iki CARLA GNSS sensörü gerçek dual-antenna GNSS compass simülasyonu değildir.

Faz 1’de iki GNSS:

* spawn edilir,
* senkronize edilir,
* kaydedilir,
* sensor health tarafından izlenebilir.

Faz 1’de dual-GNSS heading hesaplanmaz.

Faz 2’de iki seçenekten biri zorunludur:

### Seçenek A — Dual GNSS kullanılacak

Uygulanması gerekenler:

* `DualGnssBaselineEstimator`
* world/local coordinate dönüşümü
* lever-arm calibration
* antenna baseline calibration
* heading covariance
* GNSS noise correlation modeli
* IMU fusion
* stationary heading testleri
* jump/dropout rejection
* degraded-mode handling

### Seçenek B — Dual GNSS kullanılmayacak

İkinci GNSS kaldırılır.

İkinci GNSS algoritmik değer üretmeden sonsuza kadar sistemde tutulmamalıdır.

---

# 13. Sensor layout kaynak doğrusu

Sensör topolojisinin kaynak doğrusu:

```text
config/sensors/layouts/tesla_model3_omnihd_v1.yaml
```

Araç profilinin kaynak doğrusu:

```text
config/vehicles/tesla_model3.yaml
```

Runtime konfigürasyonunun kaynak doğrusu:

```text
config/runtime/default.yaml
```

Kod içinde sensör sayısı, FoV, range, transform veya frekans için ikinci bir hard-code listesi oluşturulmamalıdır.

Kod, YAML tanımlarını tipli configuration nesnelerine dönüştürmeli ve yalnız bu nesneleri kullanmalıdır.

---

# 14. Araç geometrisi ve koordinat sistemi

## 14.1. Referans frame

Ana ego referans frame:

```text
ego_rear_axle
```

Sensör pozları bu frame’e göre tanımlanır.

CARLA attachment sırasında transform parent vehicle actor’a göre local transform olmalıdır.

---

## 14.2. WheelPhysicsControl.position sorunu

Gerçek CARLA çalışmasında şu hata görülmüştür:

```text
WARNING: attempting to destroy an actor that is already dead
[HATA] lidar_roof: x konumu araç zarfının dışında.
```

Kök neden:

Mock testler `WheelPhysicsControl.position` değerlerini actor-local santimetre kabul etmişti.

Custom CARLA build’de bu değerler world-space santimetre olarak raporlandı.

Kod world-space değerleri doğrudan local kabul ettiği için:

* wheelbase yanlış hesaplandı,
* rear axle referansı yanlış oldu,
* sensör local x konumu dünya koordinatı etkisi taşıdı,
* LiDAR araç zarfının dışında göründü.

---

## 14.3. Zorunlu çözüm

VehicleGeometryAdapter şu adayları değerlendirmelidir:

```text
actor_local
world_to_actor
```

Ölçek adayları:

```text
1.0
0.01
```

`0.01`, santimetreden metreye dönüşümdür.

World-space adayları:

```python
vehicle.get_transform().inverse_transform(...)
```

veya eşdeğer matematikle actor-local frame’e çevrilmelidir.

Doğru aday şu geometrik kontrollerle seçilmelidir:

* wheelbase / body length oranı
* track / body width oranı
* bounding box zarfı
* ön aks hizası
* arka aks hizası
* sol/sağ teker simetrisi
* fiziksel olarak makul wheelbase
* fiziksel olarak makul track width

Teker listesi sırasına güvenilmemelidir.

Manifest şu alanları kaydetmelidir:

```text
wheel_position_reference
wheel_position_scale
```

Beklenen örnek:

```text
wheel_position_reference = world_to_actor
wheel_position_scale = 0.01
```

---

# 15. Cleanup ve lifecycle kuralları

## 15.1. Cleanup idempotent olmalıdır

Aynı actor için birden fazla kez:

```python
destroy()
```

çağrılmamalıdır.

Cleanup tekrar çağrıldığında:

* actor referansı daha önce temizlenmişse işlem yapmamalı,
* actor `is_alive` destekliyorsa kontrol edilmeli,
* sensor callback durdurulmalı,
* sensörler ego araçtan önce temizlenmeli,
* actor listesi temizlenmeli,
* world settings yalnız bir kez restore edilmeli.

---

## 15.2. Temizleme sırası

Önerilen sıra:

```text
1. Sensor callbacks stop
2. Sensor actors destroy
3. Ego vehicle destroy
4. World settings restore
5. Recorder finalize
6. Adapter disconnect
```

Hata durumunda recorder:

```text
FAILED
```

olarak kapanmalıdır.

---

## 15.3. ServiceOrchestrator rollback

Önceki lifecycle açığı:

Bir servis `initialize()` veya `start()` sırasında hata verirse kısmen oluşturduğu kaynaklar cleanup listesine her zaman girmiyordu.

Doğru davranış:

* initialize başlamış servis cleanup kapsamına alınmalı,
* start sırasında hata veren servis `FAILED` olmalı,
* servisler ters sırada kapatılmalı,
* bir cleanup hatası diğer cleanup işlemlerini durdurmamalı,
* ana exception korunmalı,
* cleanup exception’ları raporlanmalıdır.

---

# 16. Synchronous CARLA kuralları

Runtime ayarları:

```yaml
simulation_frequency_hz: 50
fixed_delta_seconds: 0.02
control_frequency_hz: 50
```

İlişki:

[
\Delta t = \frac{1}{f_{simulation}}
]

50 Hz için:

[
\Delta t = 0.02,s
]

Kurallar:

* `synchronous_mode = true`
* `fixed_delta_seconds = 0.02`
* Tek bir world tick owner
* Sensor callback’leri tick üretmez
* Recorder tick üretmez
* Dashboard tick üretmez
* Inference worker tick üretmez
* Shutdown sırasında eski world settings restore edilir

CARLA Traffic Manager kullanılacaksa ileride onun synchronous mode ayarı da ana orchestrator tarafından yönetilmelidir.

---

# 17. Veri sözleşmeleri

Temel sözleşmeler:

```text
MessageMetadata
RawSensorPacket
SynchronizedSensorFrame
SensorHealth
EgoState
LocalizationEstimate
BehaviorIntent
SpeedConstraintSet
LongitudinalProfile
SafeTrajectory
SafetyDecision
RuntimeHealth
```

Her mesajda bulunması gereken metadata:

* timestamp
* simulation frame
* sequence number
* coordinate frame
* source module
* schema version
* configuration hash

Hiçbir modül yalnızca anonim dictionary ile kritik veri taşımamalıdır.

Sözleşme değişikliği:

* schema version,
* registry,
* test,
* docs

güncellemesi gerektirir.

---

# 18. ODD kararları

Başlangıç ODD profilleri:

## Urban nominal

```text
Maksimum hız: 50 km/h
Yol: urban, residential, intersection
Hava: clear, cloudy, light rain, wet road
Map gerekli
Degraded mode zorunlu değil
```

## Urban adverse

```text
Maksimum hız: 35 km/h
Urban nominal profilini genişletir
Hava: heavy rain, fog, low sun, night rain
Map gerekli
Degraded mode gerekli
```

## Arterial

```text
Maksimum hız: 80 km/h
Yol: multi-lane urban, divided arterial, highway entry/exit
Hava: clear, cloudy, light rain
Map gerekli
Degraded mode gerekli
```

ODD dışına çıkıldığında sistem:

* ODD violation üretmeli,
* nominal sürüşe devam etmemeli,
* güvenli fallback veya MRM başlatmalıdır.

---

# 19. Hız politikası

Araç doğrudan speed-limit değerini takip etmeyecektir.

Behavior katmanı:

```text
SpeedConstraintSet
```

üretir.

En az şu hızlar ayrılmalıdır:

* desired free-flow speed
* maximum allowed speed
* minimum allowed speed
* curvature limit
* visibility limit
* traffic-rule limit
* lead-vehicle limit
* safety-cage limit
* actuator limit

Temel ilişki:

```text
target_speed =
minimum(
    desired_free_flow_speed,
    legal_speed_limit,
    curvature_limit,
    visibility_limit,
    lead_vehicle_limit,
    safety_limit
)
```

Hız seçimi reason code taşımalıdır.

---

# 20. Lokalizasyon hedef mimarisi

Kanonik hedef:

```text
LiDAR + IMU
    ↓
FAST-LIO2 baseline
    ↓
FAST-LIVO2 target
    ↓
Robust incremental factor graph
    ↑
GNSS / dual-GNSS / wheel / steering
```

Degraded modlar:

```text
NOMINAL
GNSS_DEGRADED
LIDAR_DEGRADED
DEAD_RECKONING
UNRELIABLE
RECOVERING
```

Localization confidence ve covariance zorunludur.

Planlayıcı yalnız pose almamalı; pose belirsizliğini de almalıdır.

---

# 21. World model hedef mimarisi

Kanonik hedef:

```text
6 cameras
1 LiDAR
6 radar proxies
Localization
Map context
    ↓
Availability-aware temporal BEV
    ↓
WorldModelSnapshot
```

Ana hedef algoritmalar:

* UniAD
* BEVFusion
* RCBEVDet
* MapTRv2

Kurallar:

* Bir sensör kaybolduğunda tüm model çökmemeli.
* Availability mask bulunmalı.
* Sensor health fusion girdisi olmalı.
* Sensor stale data kullanılmamalı.
* Temporal state reset davranışı tanımlı olmalı.
* Model timeout Safety Cage’e iletilmeli.

---

# 22. Davranış planlama hedefi

Behavior planner açık durumlar üretmelidir.

Örnek manevralar:

```text
LANE_KEEP
FOLLOW_VEHICLE
APPROACH_STOP
STOP
YIELD
INTERSECTION
LANE_CHANGE
OBSTACLE_AVOIDANCE
PULL_OVER
MINIMAL_RISK_MANEUVER
EMERGENCY_STOP
```

Planlayıcı kararları:

* reason code
* confidence
* target lane
* yield zorunluluğu
* speed constraints
* ODD state
* health state

taşımalıdır.

Kara kutu ağın doğrudan steering/throttle üretmesi ana mimari değildir.

---

# 23. Yörünge planlama hedefi

Nominal trajectory proposal kaynakları:

* PLUTO
* UniAD planning query

Deterministik fallback:

* Apollo EM
* Frenet quintic polynomial
* safe corridor refinement

Her trajectory noktası:

* time
* x/y
* yaw
* speed
* acceleration
* curvature

taşımalıdır.

Yörünge:

* kinematik olarak uygulanabilir,
* collision-free,
* jerk sınırlı,
* curvature sınırlı,
* ODD ve trafik kurallarına uygun

olmalıdır.

---

# 24. Safety Cage hedefi

Safety Cage nominal planlayıcıdan bağımsızdır.

Kullanılacak yapı:

```text
RSS
+
Robust CBF / HOCBF-QP
+
Simplex runtime assurance
```

Safety Cage şunları yapabilmelidir:

* trajectory kabul
* trajectory düzeltme
* speed envelope daraltma
* emergency brake
* minimal risk manoeuvre
* nominal controller yerine fallback controller seçme

Safety Cage’in yalnızca bir `if TTC < threshold` bloğu olması yeterli değildir.

---

# 25. Controller hedefi

Nominal controller:

```text
RTI-NMPC
```

Hedef implementation:

```text
acados / SQP-RTI
```

Fallback:

```text
Pure Pursuit
Gain-scheduled PID
```

Controller girdileri:

* SafeTrajectory
* LocalizationEstimate
* vehicle feedback
* actuator limits
* road curvature
* current speed

Controller çıkışı:

```text
VehicleCommand
```

Sınırlar:

* steering angle
* steering rate
* throttle
* brake
* acceleration
* jerk
* lateral acceleration

---

# 26. Navigation ve harita politikası

CARLA içerisinde sürülebilir rota için kaynak doğru:

```text
CARLA map topology
OpenDRIVE
Lane graph
A* / Dijkstra
```

Harici bir harita servisi araç kontrolü için authoritative kaynak olmamalıdır.

Google Maps veya benzeri servis ileride kullanılırsa yalnızca:

* kullanıcı arayüzü,
* canlı görselleştirme,
* heading-up display,
* rota karşılaştırma,
* dış rota overlay

amaçlarıyla kullanılmalıdır.

Harici API anahtarı:

* config veya environment üzerinden sağlanmalı,
* Git deposuna commit edilmemeli,
* loglarda gösterilmemelidir.

---

# 27. Dokümantasyon kuralları

Her uygulanmış Python paketinde:

```text
MODULE.md
```

zorunludur.

MODULE.md en az şu alanları içermelidir:

* module_id
* module_name
* owner
* status
* schema_version
* last_reviewed
* amaç
* girdiler
* işlem
* çıktılar
* tüketiciler
* algoritma
* hata davranışı
* fallback
* testler
* performans bütçesi
* kapsam dışı

Dokümantasyon portalı:

```text
MkDocs Material
Mermaid
MathJax
```

kullanır.

Three.js tabanlı sensör/araç görselleştirmesi planlanmıştır; ancak gerçek geometri verisiyle beslenmeden sahte 3B model eklenmemelidir.

---

# 28. Registry kuralları

Registry dosyaları:

```text
config/architecture/components.yaml
config/contracts/contracts.yaml
config/algorithms/algorithm_registry.yaml
config/sources/sources.yaml
```

Kurallar:

* ID’ler benzersiz olmalı.
* Uygulanmış modül `implemented` olarak işaretlenmeli.
* Planlanan modül doğru fazla işaretlenmeli.
* Algoritma kaynak referansları sources registry’de bulunmalı.
* Aynı source ID iki kez tanımlanmamalı.
* Aynı algorithm ID iki kez tanımlanmamalı.
* Bilinmeyen producer/consumer bulunmamalı.
* Uygulanmış Python paketinde MODULE.md olmalı.

Daha önce `RTI_NMPC_ACADOS` source ID’sinin iki kez tanımlandığı görülmüştür. Duplicate doğrulaması zorunludur.

---

# 29. Temel literatür ve kaynak yönleri

Kaynak registry’de en az şu araştırma yönleri izlenmelidir:

* UniAD
* BEVFusion
* RCBEVDet
* FAST-LIO2
* FAST-LIVO2
* Robust incremental smoothing / R-iSAM
* PLUTO
* Apollo EM Motion Planner
* Hierarchical/POMDP behavior planning
* RSS
* Control Barrier Functions
* Simplex runtime assurance
* SAE J3016
* CARLA synchronous mode documentation
* acados / SQP-RTI
* nuScenes sensor topology
* dual-antenna GNSS/INS heading
* MapTRv2

Kaynak kayıtları yalnız başlık listesi değildir.

Her source kaydı:

* kullanan modülleri,
* kullanım amacını,
* status seviyesini

belirtmelidir.

---

# 30. Test politikası

Bir faz yalnız unit test geçtiği için tamamlanmış sayılmaz.

Zorunlu test kategorileri:

1. Unit test
2. Contract test
3. Configuration test
4. Integration test
5. Mock CARLA test
6. Real CARLA smoke test
7. Cleanup test
8. Error injection test
9. Replay test
10. Scenario regression
11. Performance test
12. Soak test
13. Cross-version test
14. Documentation/registry validation
15. Compile test
16. Static analysis
17. Patch apply test

---

## 30.1. Test komutu

ROS 2 workspace ortamı pytest plugin autoload’a karışmaktadır.

Normal:

```bash
python -m pytest -q
```

komutu, proje dışındaki:

```text
launch_pytest
launch_testing
```

pluginlerini yüklemeye çalışmıştır.

Bu plugin zincirinde `lark` eksik olduğu için proje testlerinden bağımsız hata oluşmuştur.

Projeyi dış pytest pluginlerinden izole eden komut:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q
```

Bu ortamda tercih edilen test komutudur.

`lark` kurmak proje testleri için zorunlu çözüm değildir. Sorun harici pytest plugin autoload kaynaklıdır.

---

## 30.2. Genel doğrulama komutu

```bash
cd /home/superuser/Desktop/carla && \
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q && \
python -m compileall -q autonomy tools tests && \
python tools/validate_project.py
```

Ruff kuruluysa:

```bash
python -m ruff check .
python -m ruff format --check .
```

---

## 30.3. Gerçek CARLA smoke testi

CARLA server açıkken:

```bash
CARLA_SMOKE_TEST=1 \
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
python -m pytest -q -m carla_smoke tests/test_phase1_carla_smoke.py
```

Testin doğrulaması gerekenler:

* CARLA bağlantısı
* Tesla spawn
* sensörlerin spawn edilmesi
* beklenen sensor actor sayısı
* en az iki ortak frame
* recorder manifesti
* sensor cleanup
* ego cleanup
* world settings restore
* actor leak olmaması
* warning veya traceback olmaması

---

# 31. Kalite ve tamamlanma kapıları

Bir faz şu şartlar sağlanmadan tamamlanmış kabul edilmez:

* Kod ana runtime tarafından kullanılıyor.
* Atıl sınıf veya kullanılmayan config yok.
* Duplicate implementasyon yok.
* Unit testler başarılı.
* Mock integration testleri başarılı.
* Gerçek CARLA smoke testi başarılı.
* Cleanup testi başarılı.
* Hata enjeksiyon testi başarılı.
* Registry validator başarılı.
* MODULE.md kayıtları güncel.
* README güncel.
* Changelog güncel.
* Delivery report güncel.
* Compileall başarılı.
* Ruff başarılı veya neden çalıştırılamadığı açık.
* Patch temiz bazda `git am` ile uygulanmış.
* Patch sonrası testler yeniden çalıştırılmış.
* Run manifesti oluşturulmuş.
* Gerçek sistem çıktısı kullanıcı tarafından doğrulanmış.

---

# 32. Faz 0 sırasında bulunan ve düzeltilen sorunlar

## 32.1. Launcher import sorunu

İlk launcher, PyYAML henüz kurulmadan configuration loader import ediyordu.

Sonuç:

```text
install/check komutu dependency kurulmadan açılmayabiliyordu
```

Çözüm:

* project importları environment kontrolünden sonra lazy olarak yapıldı.
* `install` komutu config loader importuna bağımlı olmaktan çıkarıldı.

---

## 32.2. Ctrl+C mantığının yanlış yere eklenmesi

İlk düzeltmede Ctrl+C process supervision:

```text
run_install()
```

içine eklenmişti.

Bu yanlıştı.

Doğru çözüm:

* `run_install()` sade `pip install` akışına döndürüldü.
* Ctrl+C yönetimi yalnız autonomy application subprocess’ine taşındı.
* Graceful wait uygulandı.
* Timeout sonrası terminate ve kill fallback’i eklendi.
* Launcher traceback üretmeden kapanacak şekilde test eklendi.

---

## 32.3. CARLA custom build’in supported_versions’a eklenmesi

İlk çözüm:

```yaml
supported_versions:
  - 0.9.15
  - 0.9.16
  - e78db150c
```

şeklindeydi.

Bu yanlıştı.

Build hash semantik sürüm değildir.

Doğru çözüm:

```yaml
supported_versions:
  - 0.9.15
  - 0.9.16

server_version_aliases:
  e78db150c: 0.9.16
```

---

## 32.4. `.gitignore` runtime kuralı

İlk `.gitignore` kuralı:

```text
runtime/
```

olduğu için şu kaynak kod/config dizinlerini de yanlışlıkla ignore ediyordu:

```text
autonomy/runtime/
config/runtime/
```

Doğru kural:

```text
/runtime/
```

Yalnız proje kökündeki runtime çıktıları ignore edilir.

---

# 33. Faz 1 sırasında bulunan sorunlar

## 33.1. LiDAR araç zarfı hatası

Görülen hata:

```text
[HATA] lidar_roof: x konumu araç zarfının dışında.
```

Kök neden:

* wheel position coordinate reference yanlış varsayıldı,
* world-space santimetre değerleri local frame gibi kullanıldı,
* mock test gerçek CARLA davranışını modellemedi.

Düzeltme:

* world/local adayları
* metre/santimetre adayları
* inverse transform
* geometrik scoring
* manifestte reference/scale
* gerçek hata durumunu kapsayan regresyon testi

---

## 33.2. Actor already dead warning

Görülen warning:

```text
attempting to destroy an actor that is already dead
```

Kök neden:

* hata sırasında actor bir kez destroy edildi,
* lifecycle cleanup actor’ü ikinci kez destroy etmeye çalıştı.

Düzeltme:

* idempotent cleanup
* actor reference temizleme
* alive kontrolü
* ikinci stop çağrısı regresyon testi

---

# 34. Patch ve commit geçmişi

Önemli başlangıç commitleri:

```text
d1ee52946d3f81ca02c53ed43788df4a81457576
first commit
```

```text
1c139b92b18f4e254129ef676cd97c48a708eacf
fix launcher
```

Bu committe Ctrl+C düzeltmesi yanlış fonksiyona uygulanmıştı.

Daha sonra uygulanan launcher patch commit’i:

```text
e5898af78270cac89e0f7506fe8803061674c114
Fix launcher signal handling and bootstrap
```

Runtime config ve alias düzeltme commit’i:

```text
3991e145dfe913cba7e6b5ced618b99eb6bd15c3
Track runtime configuration and resolve CARLA build aliases
```

Faz 1 patch:

```text
0003-Implement-complete-CARLA-Phase-1-runtime.patch
```

Wheel coordinate ve sensör kaynak dokümantasyonu düzeltme patch’i:

```text
0004-Fix-CARLA-wheel-coordinates-and-document-sensor-rationale.patch
```

Bu belge hazırlanırken `0004` patch’inin kullanıcı sisteminde gerçek CARLA sonucu henüz ayrıca paylaşılmamıştır. Uygulama sonrası `git log`, test ve runtime sonucu güncellenmelidir.

---

# 35. Faz 1 doğrulama durumu

Assistant-side unit/mock doğrulaması sırasında raporlanan durum:

```text
27 test başarılı
1 gerçek CARLA smoke testi skip
compileall başarılı
registry/MODULE doğrulaması başarılı
git am başarılı
git diff --check başarılı
```

Bu sonuçlar gerçek CARLA server testinin yerine geçmez.

Gerçek sistemde doğrulanması gereken çıktı:

```text
Ego geometrisi:
wheelbase=...
tracks=(..., ...)
wheel_reference=world_to_actor
scale=0.010
```

Sonrasında şu hata görülmemelidir:

```text
lidar_roof: x konumu araç zarfının dışında
```

Şu warning de görülmemelidir:

```text
attempting to destroy an actor that is already dead
```

---

# 36. Phase 2 öncesi zorunlu kontrol listesi

Faz 2’ye başlamadan önce:

* [ ] `0004` patch uygulanmış olmalı.
* [ ] Unit/mock testlerinin tamamı geçmeli.
* [ ] Real CARLA smoke testi geçmeli.
* [ ] `./run_project.sh start` hatasız açılmalı.
* [ ] 16 sensör başarıyla spawn olmalı.
* [ ] Ego geometry logu fiziksel olarak makul olmalı.
* [ ] LiDAR araç zarfı hatası olmamalı.
* [ ] Actor already dead warning olmamalı.
* [ ] `Ctrl+C` sonrası traceback olmamalı.
* [ ] Sensör actor leak olmamalı.
* [ ] Ego actor leak olmamalı.
* [ ] World settings restore edilmeli.
* [ ] Manifest `COMPLETED` olmalı.
* [ ] Hata durumunda manifest `FAILED` olmalı.
* [ ] `runtime/recordings/` içinde run kaydı oluşmalı.
* [ ] Sensör source/rationale dokümanı portalda görünmeli.
* [ ] Duplicate source kayıtları bulunmamalı.
* [ ] Git çalışma ağacı temiz olmalı.
* [ ] Son commit GitHub’a pushlanmalı.

---

# 37. Yasaklanan uygulamalar

Aşağıdaki uygulamalar projede yapılmamalıdır:

* CARLA ground truth’u normal perception girdisi yapmak
* Aynı işi yapan paralel modüller bırakmak
* Kullanılmayan config parametresi eklemek
* Sonsuz queue kullanmak
* Sonsuz sensor wait kullanmak
* Sensor callback içinde ağır inference yapmak
* Birden fazla world tick owner oluşturmak
* Cleanup exception’ını sessizce yutmak
* Actor’ü birden fazla kez destroy etmek
* World settings’i restore etmeden çıkmak
* Hard-coded Tesla boyutu kullanmak
* Sensör transformunu dünya koordinatında attach etmek
* Mock testi gerçek CARLA davranışı sanmak
* Gerçek CARLA testi olmadan fazı tamamen doğrulandı ilan etmek
* Build hash’i semantik sürüm listesine eklemek
* API key commit etmek
* Model worker crash’ini controller process’ine taşımak
* Planned modül için boş class eklemek
* Dashboard’a kontrol yetkisi vermek
* Safety Cage’i nominal planner’ın içine gömmek
* Tek bir TTC eşiğini bütün Safety Cage olarak sunmak
* İki GNSS’yi algoritmik kullanım olmadan kalıcı olarak taşımak
* CARLA radarını gerçek production 4D imaging radar olarak tanıtmak

---

# 38. Komut referansı

## Ortamı etkinleştirme

```bash
conda activate odd
```

## Proje dizini

```bash
cd /home/superuser/Desktop/carla
```

## Ortam kontrolü

```bash
./run_project.sh check
```

## CARLA doctor

CARLA server açıkken:

```bash
./run_project.sh doctor
```

## Default runtime

```bash
./run_project.sh start
```

## Test

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q
```

## Tam statik doğrulama

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q && \
python -m compileall -q autonomy tools tests && \
python tools/validate_project.py
```

## Gerçek CARLA smoke testi

```bash
CARLA_SMOKE_TEST=1 \
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
python -m pytest -q -m carla_smoke tests/test_phase1_carla_smoke.py
```

## Doküman portalı

```bash
./run_docs.sh
```

Varsayılan adres:

```text
http://127.0.0.1:8000
```

## Patch uygulama

```bash
git am /home/superuser/Downloads/<patch-name>.patch
```

## Hatalı patch uygulamasını iptal etme

```bash
git am --abort
```

## Git durumu

```bash
git status
git log --oneline --decorate -10
```

---

# 39. Önceki ve artık geçerli olmayan tasarım fikirleri

Daha önce kamera/radar ağırlıklı, LiDAR içermeyen bir sensör topolojisi değerlendirilmiştir.

Bu eski yaklaşımda:

* 6 kamera,
* 5 radar,
* GNSS,
* IMU,
* wheel/steering feedback,
* D-FINE,
* Anchor3DLane++,
* radar-camera lifting

gibi fikirler bulunuyordu.

Bu tasarım mevcut kanonik baseline değildir.

Mevcut baseline:

```text
6 kamera
1×64 kanal LiDAR
6 radar proxy
2 GNSS
1 IMU
vehicle feedback
```

ve uzun vadeli:

* FAST-LIO2/FAST-LIVO2,
* BEVFusion,
* RCBEVDet,
* UniAD,
* MapTRv2

mimarisidir.

Eski camera/radar-only yaklaşım mevcut ana mimariye karıştırılmamalıdır.

---

# 40. Karar özeti

Projenin güncel yönü aşağıdaki gibi özetlenir:

```text
Python 3.11
CARLA 0.9.16 canonical
CARLA 0.9.15 compatibility
Custom build alias: e78db150c → 0.9.16
Tesla Model 3
Runtime-derived vehicle geometry
6 RGB cameras
1×64-channel LiDAR
6 CARLA radar proxies
2 GNSS with mandatory Phase 2 use-or-remove gate
1 IMU
Vehicle feedback
50 Hz synchronous runtime
Single world tick owner
Bounded buffers
Exact frame synchronization
Manifest/JSONL recording
No normal-runtime simulator ground truth
No dead code
No duplicate architecture
Default runtime only
Patch-only delivery
MODULE.md and registries mandatory
Real CARLA validation mandatory
Level 4 claim limited to declared ODD simulation research
```

---

# 41. Son bağlayıcı not

Bu proje için başarı ölçütü yalnızca kodun çalışması değildir.

Başarılı kabul edilmesi için sistem:

* mimari olarak tutarlı,
* runtime tarafından gerçekten kullanılan,
* hatada güvenli kapanan,
* kayıt üretip yeniden incelenebilen,
* bilimsel kaynakları izlenebilir,
* sensör ve algoritma sınırlamalarını dürüstçe açıklayan,
* testleri tekrar üretilebilir,
* gerçek CARLA üzerinde doğrulanmış,
* ODD dışına çıktığında güvenli davranan

bir bütün olmalıdır.

Yeni bir özellik eklenirken önce mevcut mimarideki doğru yer belirlenmeli, ardından kod, test, config, registry ve dokümantasyon birlikte güncellenmelidir.
