# Otonom Sürüş Projesi — Algoritma Seçim Temeli

> Durum: Mimari algoritma baseline'ı  
> Güncelleme: 2026-07-31  
> Kural: Aynı işi yapan ikinci bir üretim algoritması, ölçülebilir gereksinim olmadan eklenmez.

## 1. Portal hiyerarşisi

```text
Sistem
└── Alan
    └── Modül
        └── Alt modül
            └── Algoritma
                ├── Amaç
                ├── Inputlar ve kaynakları
                ├── Matematiksel yöntem
                ├── Outputlar ve tüketicileri
                ├── ODD profilleri
                ├── Parametreler
                ├── Kaynak makaleler
                ├── Hesaplama bütçesi
                ├── Hata biçimleri
                ├── Fallback
                ├── Testler
                ├── Kod dosyaları
                └── Sürüm geçmişi
```

Portalın en alt katmanı algoritma kaydıdır. Kullanıcı algoritmaya bastığında hangi veriyi aldığı, ne yaptığı, ne ürettiği ve çıktının nereye dağıtıldığı gösterilir.

## 2. Algoritma matrisi

### ALG-ODD-001 — ODD üyelik ve degradation yöneticisi

- **Ana yöntem:** Kural tabanlı set-membership değerlendirmesi.
- **Ek yöntem:** Sensör ve lokalizasyon güvenine bağlı confidence-aware degradation.
- **Girdi:** Hava, görünürlük, yol türü, hız, harita uygunluğu, SensorHealth, LocalizationEstimate, RuntimeHealth.
- **Çıktı:** `ODDStatus`, izin verilen hız ve manevra kümesi, degradation seviyesi.
- **Tüketiciler:** Behavior Planner, Safety Cage, Mission Manager.
- **Fallback:** `MINIMAL_RISK_MANEUVER`.
- **ODD:** Tümü.
- **Gerekçe:** ODD sınırları denetlenebilir ve deterministik olmalıdır; öğrenilmiş sınıflandırıcı tek karar kaynağı yapılmaz.

### ALG-SIM-001 — Deterministik CARLA orkestrasyonu

- **Ana yöntem:** Synchronous mode, fixed time-step, tek tick sahibi, sabit seed.
- **Girdi:** ScenarioDefinition, RuntimeConfiguration.
- **Çıktı:** Simülasyon frame'i, sensör tetikleri, ground-truth test oracle'ı.
- **Tüketiciler:** Sensor Gateway, Scenario Evaluator.
- **Fallback:** Kaynakları temizleyip kontrollü kapanış.
- **ODD:** Tümü.

### ALG-SYNC-001 — Bounded multi-rate sensor synchronization

- **Ana yöntem:** Frame-indexed watermark synchronizer.
- **İşlem:** Her modalite için bounded ring buffer; hedef frame/timestamp çevresinde toleranslı eşleme; timeout sonunda modalite maskesi.
- **Girdi:** RawSensorPacket.
- **Çıktı:** SynchronizedSensorFrame.
- **Tüketiciler:** Localization, BEV fusion, Safety Perception, Recorder.
- **Fallback:** Eski veri kullanmak yerine eksik modalite bildirimi.
- **ODD:** Tümü.

### ALG-CAL-001 — Kalibrasyon doğrulama ve drift izleme

- **Ana yöntem:** Projeksiyon/geometrik residual, Mahalanobis gate, EWMA/CUSUM değişim tespiti.
- **Başlangıç kalibrasyonu:** Hedef tabanlı offline kalibrasyon.
- **Araştırma yükseltmesi:** LiDAR-camera online transformer calibration; radar-camera için 4D-CAAL.
- **Çıktı:** CalibrationHealth ve geçerli extrinsic sürümü.
- **Tüketiciler:** Sensor Gateway, Fusion, Safety Cage.
- **Fallback:** Son doğrulanmış extrinsic + hız azaltma/degraded mode.

### ALG-LOC-001 — Yerel odometri

- **Target:** FAST-LIVO2; LiDAR, IMU ve seçilmiş ön kamera ile doğrudan ESIKF füzyonu.
- **Baseline:** FAST-LIO2.
- **Girdi:** IMU, LiDAR, ön kamera, calibration.
- **Çıktı:** Yüksek frekanslı local odometry ve kovaryans.
- **Tüketiciler:** Global localization backend, ego motion compensation.
- **Fallback:** IMU + wheel dead reckoning.
- **ODD:** Tümü; tünel ve GNSS kaybında kritik.

### ALG-LOC-002 — Global lokalizasyon backend'i

- **Ana yöntem:** Robust incremental factor graph; riSAM/iSAM2 yaklaşımı.
- **Faktörler:** Local odometry, IMU preintegration, dual-GNSS, wheel odometry, map matching.
- **GNSS:** Trust score ile adaptif ağırlık.
- **Çıktı:** LocalizationEstimate, covariance, localization mode.
- **Tüketiciler:** World Model, Behavior, Planner, Safety, Controller.
- **Fallback:** Yerel odometri; kovaryans sınırında MRM.
- **ODD:** Tümü.

### ALG-BEV-CAM-001 — Kamera BEV encoder

- **Ana yöntem:** Temporal multi-view transformer ve planning-oriented query arayüzü.
- **Girdi:** Altı kamera, intrinsic/extrinsic, ego motion.
- **Çıktı:** Camera BEV features.
- **Tüketici:** Availability-aware fusion.
- **Fallback:** Kamera modalite maskesi.
- **ODD:** Tümü.

### ALG-BEV-LIDAR-001 — LiDAR encoder

- **Ana yöntem:** Sparse voxel/pillar encoding ve BEV projection.
- **Girdi:** 64 kanal point cloud.
- **Çıktı:** Geometrik LiDAR BEV features.
- **Tüketiciler:** Fusion, localization, safety near-field.
- **Fallback:** LiDAR modalite maskesi.
- **ODD:** Tümü.

### ALG-BEV-RADAR-001 — 4D radar encoder

- **Ana yöntem:** RadarBEVNet tipi point/transformer dual stream ve RCS-aware BEV encoding.
- **Girdi:** Range, azimuth, elevation, radial velocity, RCS, confidence.
- **Çıktı:** Radar BEV features ve bağımsız radar measurements.
- **Tüketiciler:** Fusion ve Safety Tracker.
- **Fallback:** Klasik radar track hattı.
- **ODD:** Tümü; yağmur, sis, gece ve örtülü aktörlerde öncelikli.

### ALG-FUS-001 — Availability-aware multi-sensor fusion

- **Ana yöntem:** Kamera, LiDAR ve 4D radar özelliklerini ortak canonical/BEV uzayında birleştiren availability-aware cross-attention.
- **Girdi:** Üç modalitenin BEV features, modalite health/mask.
- **Çıktı:** Unified Temporal BEV.
- **Tüketiciler:** UniAD tracking, mapping, prediction, occupancy ve planning heads.
- **Fallback:** Mevcut modalitelerle masked fusion; tek modalite kaybında ağın çökmesine izin verilmez.
- **ODD:** Tümü; adverse ODD'de zorunlu.

### ALG-TRACK-001 — Öğrenilmiş temporal tracking

- **Ana yöntem:** UniAD query-based track propagation.
- **Çıktı:** TrackedObjectSet ve agent queries.
- **Tüketiciler:** Prediction, Behavior, Planner, Dashboard.
- **Fallback/bağımsız yol:** IMM-UKF + global nearest-neighbor association ile radar/LiDAR safety tracks.
- **ODD:** Tümü.

### ALG-MAP-001 — Online vektörel harita

- **Ana yöntem:** MapTRv2.
- **Girdi:** Unified BEV, calibration, ego pose.
- **Çıktı:** Lane divider, road boundary, centerline ve crossing polylines.
- **Tüketiciler:** Route, Traffic Rules, Behavior, Planner, Safety.
- **Doğrulama:** Statik HD map ile geometric consistency gate.
- **Fallback:** Statik HD map + güven azaltma.
- **ODD:** Tümü.

### ALG-RULE-001 — Trafik kuralı durumu

- **Ana yöntem:** Lane-linked TrafficRuleGraph ve deterministik temporal state machine.
- **Girdi:** Harita eşlemeli levha/ışık tespitleri, route, stop line.
- **Çıktı:** TrafficRuleState.
- **Tüketiciler:** Behavior, Planner, Safety.
- **Fallback:** Belirsiz kritik kuralda kontrollü yavaşlama/duruş.
- **ODD:** Urban ve arterial.

### ALG-PRED-001 — Çok modlu hareket tahmini

- **Ana yöntem:** UniAD motion transformer ve agent-map queries.
- **Girdi:** Agent queries, VectorMap, ego intent.
- **Çıktı:** Her aktör için çok modlu trajectory distribution.
- **Tüketiciler:** Behavior, Trajectory Planner, Safety.
- **Fallback:** Constant-turn-rate-and-velocity modeli, büyütülmüş belirsizlik.
- **ODD:** Tümü.

### ALG-BEH-001 — Hibrit behavior planning

- **Ana yöntem:** Hierarchical State Machine.
- **Belirsiz etkileşim:** Bayesian belief/POMDP yaklaşımı; merge, unprotected turn, cut-in ve occlusion için sınırlı kullanılır.
- **Girdi:** WorldModelSnapshot, route, rules, ODD, health.
- **Çıktı:** BehaviorIntent.
- **Tüketiciler:** Trajectory Planner, Safety Cage, Recorder.
- **Fallback:** Öncelik sıralı güvenli kurallar.
- **ODD:** Tümü.

### ALG-PLAN-001 — Multi-modal trajectory generation

- **Ana yöntem:** UniAD/PLUTO tarzı longitudinal-lateral query proposals.
- **Refinement:** Yol sınırı, dinamik limit, hız ve konfor kısıtlı SQP/spline refinement.
- **Girdi:** BehaviorIntent, WorldModel, predictions, occupancy, map.
- **Çıktı:** TrajectoryCandidateSet.
- **Tüketici:** Safety Cage.
- **Fallback:** Frenet koordinatında quintic polynomial safe-corridor trajectory.
- **Araştırma adayı:** BridgeDrive diffusion policy; yalnızca kapalı çevrim ve gecikme üstünlüğü kanıtlanırsa.
- **ODD:** Tümü.

### ALG-SAFE-001 — Safety Cage

- **Katman 1:** RSS longitudinal/lateral safe-distance envelope.
- **Katman 2:** Robust high-order CBF-QP trajectory/control filter.
- **Katman 3:** Simplex runtime assurance ve nominal/fallback arbitration.
- **Girdi:** Candidates, safety tracks, near-field obstacles, rules, localization, health.
- **Çıktı:** SafeTrajectory ve SafetyDecision.
- **Tüketiciler:** Controller, Recorder, Dashboard.
- **Fallback:** MRM veya emergency stop.
- **ODD:** Tümü.

### ALG-CTRL-001 — Nominal trajectory control

- **Ana yöntem:** RTI-NMPC, önce kinematik bisiklet modeli.
- **Solver:** acados sınıfı SQP-RTI.
- **Girdi:** SafeTrajectory, EgoState, vehicle model.
- **Çıktı:** VehicleCommand.
- **Tüketici:** Vehicle Adapter.
- **Fallback:** Curvature-adaptive Pure Pursuit + gain-scheduled speed PID.
- **ODD:** Tümü; arterial profile daha uzun horizon kullanır.

### ALG-HEALTH-001 — Sensor ve runtime anomaly detection

- **Ana yöntem:** Innovation/residual Mahalanobis gating, EWMA/CUSUM, heartbeat ve deadline watchdog.
- **Girdi:** Sensor residuals, queue age, latency, process heartbeat.
- **Çıktı:** SensorHealth ve RuntimeHealth.
- **Tüketiciler:** ODD Manager, Fusion, Safety Cage, Launcher.
- **Fallback:** Degraded mode veya MRM.
- **ODD:** Tümü.

### ALG-SCEN-001 — Senaryo üretimi

- **Ana yöntem:** ScenarioRunner atomics + Scenic constrained probabilistic programming.
- **Girdi:** ODD, scenario schema, parameter ranges, seed.
- **Çıktı:** Reproducible concrete scenario.
- **Tüketiciler:** Orchestrator, Evaluator.
- **ODD:** Tümü.

### ALG-STRESS-001 — Corner-case keşfi

- **İlk yöntem:** Adaptive Stress Testing + Monte Carlo Tree Search.
- **Yükseltme:** Simülatör çağrı bütçesi ve fayda doğrulanırsa DRL.
- **Alternatif basit arama:** Latin Hypercube, boundary-value ve CMA-ES.
- **Çıktı:** Minimal tehlikeli parametre seti ve replayable seed.
- **Tüketici:** Regression catalog.
- **ODD:** Tümü.

### ALG-TUNE-001 — Parametre ayarı

- **Aşama 1:** Tek-parametre duyarlılık ve Latin Hypercube taraması.
- **Aşama 2:** Güvenlik kısıtlı çok amaçlı Bayesian optimization.
- **Amaçlar:** Güvenlik, ilerleme, konfor, kural uyumu, gecikme.
- **Kural:** Safety limitleri optimize edilmez; sabit zorunlu kısıtlardır.
- **Çıktı:** Sürümlü config adayı ve Pareto raporu.
- **Tüketici:** İnsan review ve regression pipeline.

### ALG-EVAL-001 — Senaryo bazlı doğrulama

- **Çerçeve:** ISO 34502 mantığı.
- **Kapalı çevrim:** Bench2Drive yetenek/scenario metrikleri.
- **Proje metrikleri:** Collision, TTC, clearance, rule violation, route completion, jerk, intervention, timeout, uncertainty ve ODD exit.
- **Çıktı:** ScenarioReport ve AlgorithmScorecard.
- **Tüketiciler:** Portal, CI, tuning, release gate.

## 3. Seçilen temel yayınlar

1. Hu et al., **Planning-Oriented Autonomous Driving (UniAD)**, CVPR 2023.
2. OpenDriveLab, **UniAD 2.0**, 2025 release.
3. Ye et al., **FusionAD**, 2023.
4. Liu et al., **BEVFusion: Multi-Task Multi-Sensor Fusion with Unified BEV**, ICRA 2023 / arXiv revision 2024.
5. Paek and Kong, **Availability-aware Sensor Fusion via Unified Canonical Space for 4D Radar, LiDAR, and Camera**, 2025.
6. Lin et al., **RCBEVDet++**, 2024.
7. Zheng et al., **FAST-LIVO2**, 2024.
8. McGann et al., **riSAM**, 2022.
9. Liao et al., **MapTRv2**, IJCV 2024.
10. Jin et al., **BoT-Drive**, 2024.
11. Cheng et al., **PLUTO**, 2024.
12. Liu et al., **BridgeDrive**, 2025 — research candidate.
13. Alan et al., **Control Barrier Functions and Input-to-State Safety with Application to Automated Vehicles**, 2022.
14. Cohen et al., **Safety-Critical Control via Reduced-Order Models**, 2024.
15. Chen et al., **Simplex-Drive**, 2021.
16. Jia et al., **Bench2Drive**, 2024.
17. Scenic 2/3 publications and CARLA integration.
18. Koren et al., **Adaptive Stress Testing for Autonomous Vehicles**, 2019; multi-lane extension, 2024.
19. ISO 34502:2022.
