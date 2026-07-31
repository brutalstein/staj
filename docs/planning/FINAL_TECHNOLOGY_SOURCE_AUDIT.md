# Nihai Teknoloji ve Kaynak Denetimi

**Tarih:** 2026-07-31  
**Proje hedefi:** Tanımlı ODD içerisinde insan müdahalesi beklemeyen Seviye 4 araştırma sistemi  
**Kural:** Hakemli/yayımlanmış kaynaklar çekirdek dayanak; yalnızca ön baskı olan kaynaklar destekleyici veya araştırma adayıdır.

---

## 1. Kaynak durum sınıfları

- **CORE:** Üretim hedefindeki mimari veya algoritmanın ana dayanağı.
- **SUPPORTING:** CORE tasarımı tamamlayan, fakat tek başına ana dayanak olmayan çalışma.
- **RESEARCH_CANDIDATE:** Deney dalında ölçülecek; kapalı çevrim üstünlüğü kanıtlanmadan ana sisteme alınmayacak.
- **STANDARD_VALIDATION:** Seviye 4 tanımı, ODD ve doğrulama yöntemi.

---

## 2. Çekirdek kaynaklar

### Full-stack ve BEV

1. **Planning-Oriented Autonomous Driving (UniAD)** — CVPR 2023  
   Rol: Tracking, mapping, prediction, occupancy ve planning arasında planning-oriented query mimarisi.  
   Durum: CORE.

2. **UniAD 2.0** — OpenDriveLab yazılım sürümü, 2025  
   Rol: Güncel framework, nuPlan/NAVSIM entegrasyon yönü.  
   Durum: CORE SOFTWARE BASELINE. Ayrı akademik makale değildir.

3. **BEVFusion: Multi-Task Multi-Sensor Fusion with Unified Bird's-Eye View Representation** — ICRA 2023  
   DOI: 10.1109/ICRA48891.2023.10160968  
   Rol: Kamera ve LiDAR özelliklerinin ortak BEV uzayında birleştirilmesi.  
   Durum: CORE.

4. **RCBEVDet: Radar-Camera Fusion in Bird's Eye View for 3D Object Detection** — CVPR 2024  
   Rol: RadarBEVNet, RCS-aware radar encoding ve kamera-radar BEV fusion.  
   Durum: CORE RADAR REFERENCE.

5. **FusionAD: Multi-modality Fusion for Prediction and Planning Tasks of Autonomous Driving** — arXiv 2308.01006  
   Rol: Kamera-LiDAR fusion'ın prediction ve planning görevlerine taşınması.  
   Durum: SUPPORTING; ana mimari kanıtı değildir.

### Lokalizasyon

6. **FAST-LIO2: Fast Direct LiDAR-Inertial Odometry** — IEEE Transactions on Robotics, 2022  
   DOI: 10.1109/TRO.2022.3141876  
   Rol: Hakemli, gerçek zamanlı LiDAR-IMU yerel odometri baseline'ı.  
   Durum: CORE BASELINE.

7. **FAST-LIVO2: Fast, Direct LiDAR-Inertial-Visual Odometry** — arXiv 2408.14035, 2024  
   Rol: LiDAR, IMU ve kamera ESIKF füzyonu; hedef lokalizasyon front-end'i.  
   Durum: SUPPORTING/TARGET; FAST-LIO2'nin yerine geçmesi CARLA ve replay testleriyle onaylanacak.

8. **Robust Incremental Smoothing and Mapping (riSAM)** — arXiv 2209.14359, 2022  
   Rol: GNSS, odometri ve harita faktörleri için robust incremental factor-graph yaklaşımı.  
   Durum: SUPPORTING ALGORITHM BASIS.

### Harita, davranış ve planlama

9. **MapTRv2: An End-to-End Framework for Online Vectorized HD Map Construction** — IJCV, 2025  
   DOI: 10.1007/s11263-024-02235-z  
   Rol: Online vektörel yol ve şerit haritası.  
   Durum: CORE.

10. **PLUTO: Pushing the Limit of Imitation Learning-based Planning for Autonomous Driving** — arXiv 2404.14327, 2024  
    Rol: Longitudinal-lateral aware plan queries ve closed-loop nuPlan planning.  
    Durum: SUPPORTING/TARGET PLANNER BASIS.

11. **Baidu Apollo EM Motion Planner** — arXiv 1807.08048, 2018  
    Rol: Path-speed ayrımı, Frenet, DP + spline QP; açıklanabilir ve ayarlanabilir fallback planlama.  
    Durum: CORE CLASSICAL FALLBACK.

12. **BoT-Drive: Hierarchical Behavior and Trajectory Planning using POMDPs** — arXiv 2409.18411, 2024  
    Rol: Merge, cut-in ve belirsiz kavşak etkileşimlerinde sınırlı belief planning.  
    Durum: SUPPORTING; tüm behavior planner POMDP yapılmayacak.

### Güvenlik ve runtime assurance

13. **Responsibility-Sensitive Safety (RSS)** — arXiv 1708.06374  
    Rol: Boylamsal ve yanal güvenli mesafe zarfı.  
    Durum: CORE FOUNDATIONAL.

14. **Control Barrier Functions and Input-to-State Safety with Application to Automated Vehicles** — arXiv 2206.03568, 2022  
    Rol: Bozulmalara dayanıklı CBF safety filtering.  
    Durum: CORE SAFETY BASIS.

15. **Runtime Safety Assurance for Learning-enabled Control of Autonomous Driving Vehicles (Simplex-Drive)** — arXiv 2109.13446, 2021  
    Rol: Nominal ve doğrulanabilir fallback arasında runtime switching.  
    Durum: CORE RUNTIME ASSURANCE BASIS.

### Kontrol ve hız

16. **Traffic Flow Dynamics: Data, Models and Simulation, 2nd Edition** — Springer, 2025  
    DOI: 10.1007/978-3-031-93922-8  
    Rol: IDM/IDM+, car-following ve lane-changing modelleri.  
    Durum: CORE LONGITUDINAL BASELINE.

17. **RTI-NMPC / SQP-RTI and acados literature**  
    Rol: Güvenli yörüngenin gerçek zamanlı constrained tracking'i.  
    Durum: CORE CONTROL BASIS.

### Test ve Seviye 4 doğrulama

18. **Bench2Drive** — NeurIPS 2024 Datasets and Benchmarks Track  
    Rol: CARLA'da 44 etkileşimli senaryo, çeşitli hava ve kasabalarda closed-loop değerlendirme.  
    Durum: CORE BENCHMARK.

19. **Collision Avoidance Testing of the Waymo Automated Driving System** — SAE 2026-01-0519  
    Rol: Level 4 responder conflict ve scenario-database güvenlik değerlendirme yöntemi.  
    Durum: CORE SYSTEM VALIDATION REFERENCE.

20. **SAE J3016_202104**  
    Rol: Level 4 tanımı ve DDT/fallback sorumluluğu.  
    Durum: STANDARD_VALIDATION.

21. **ISO 34503:2023**  
    Rol: ODD taxonomy ve formatı.  
    Durum: STANDARD_VALIDATION.

22. **ISO 34505:2025**  
    Rol: Senaryo değerlendirme ve test-case generation.  
    Durum: STANDARD_VALIDATION.

23. **ISO/TS 5083:2025**  
    Rol: Level 3/4 ADS safety design, verification ve validation.  
    Durum: STANDARD_VALIDATION.

---

## 3. Araştırma adayları ve güncel izleme listesi

1. **Availability-aware Sensor Fusion via Unified Canonical Space for 4D Radar, LiDAR, and Camera** — 2025  
   Kullanım: Sensör kaybına dayanıklı fusion.  
   Durum: RESEARCH_CANDIDATE; arXiv.

2. **RCGDet3D** — 2026  
   Kullanım: Daha hafif ve hızlı 4D radar-camera feature encoding.  
   Durum: RESEARCH_CANDIDATE; çok yeni.

3. **ProDrive** — CVPR Workshop 2026  
   Kullanım: Ego-environment co-evolution ve proactive planning.  
   Durum: RESEARCH_CANDIDATE.

4. **CogDriver** — CVPR 2026  
   Kullanım: Temporal decision coherence ve planning jitter azaltma.  
   Durum: RESEARCH_CANDIDATE.

5. **KnowVal** — CVPR 2026  
   Kullanım: Knowledge/value-guided trajectory assessment.  
   Durum: RESEARCH_CANDIDATE; Safety Cage'in yerine geçmez.

6. **ActiveAD** — CVPR 2026  
   Kullanım: Planning-oriented active learning ve veri seçimi.  
   Durum: RESEARCH_CANDIDATE FOR TRAINING PIPELINE.

7. **PerlAD** — 2026  
   Kullanım: Longitudinal speed optimization için pseudo-simulation RL.  
   Durum: RESEARCH_CANDIDATE; güvenli hız planlayıcının yerine doğrudan alınmaz.

8. **BridgeDrive**  
   Kullanım: Diffusion planning.  
   Durum: RESEARCH_CANDIDATE ONLY; v1 üretim yolundan çıkarılmıştır.

9. **RCBEVDet++**  
   Kullanım: Gelişmiş radar-camera BEV fusion.  
   Durum: RESEARCH_CANDIDATE; çekirdek kaynak olarak kabul edilen hakemli sürüm RCBEVDet CVPR 2024'tür.

---

## 4. Hız karar mimarisi

Araç başka bir aracın hızını doğrudan kopyalamaz. Kendi planlanan hızı vardır.

### 4.1 Davranış hız politikası

**Girdiler**

- Harita hız sınırı
- ODD maksimum hızı
- Rota ve manevra
- Yol eğriliği
- Görüş ve hava
- Trafik ışığı/stop/yield
- Yaya, bisiklet ve çapraz trafik
- Lead vehicle track
- Aktör prediction
- Lokalizasyon ve sensör sağlığı
- Araç dinamik ve konfor limitleri

**Çıktı**

`SpeedConstraintSet`

- `desired_free_flow_speed_mps`
- `maximum_allowed_speed_mps`
- `minimum_allowed_speed_mps`
- `stop_position_m`
- `follow_target_id`
- `required_time_headway_seconds`
- `reason_codes`

### 4.2 Hız tavanı

\[
v_{ceiling}(t)=\min\{
v_{map},
v_{ODD},
v_{curve},
v_{visibility},
v_{rule},
v_{interaction},
v_{health},
v_{vehicle}
\}
\]

Bu ifade bir nihai komut değildir; trajectory optimizer'ın izin verilen zarfıdır.

### 4.3 Lead vehicle davranışı

Lead vehicle uzaktaysa ego araç kendi free-flow hızını sürdürür.

Lead vehicle güvenli takip bölgesine girdiyse:

- relative speed,
- current gap,
- desired time headway,
- braking capability,
- RSS minimum safe distance,
- lead prediction

kullanılarak hız profili azaltılır.

IDM+ bağımsız baseline ve karşılaştırma modeli olarak kullanılır. Ana sistemde trajectory optimizer, tüm aktör tahminlerini ve occupancy'yi kullanarak \(v(t)\), \(a(t)\) ve jerk profilini üretir.

### 4.4 Nihai akış

```text
ODD + Route + Map + Rules + World Model
→ Behavior Speed Policy
→ SpeedConstraintSet
→ Longitudinal/Trajectory Optimizer
→ LongitudinalProfile v(t), a(t), jerk(t)
→ Safety Cage
→ SafeTrajectory
→ RTI-NMPC
→ throttle / brake
```

### 4.5 Örnekler

- Yol limiti 50 km/h, yol açık: araç yaklaşık kendi hedef hızında gider.
- Öndeki araç 30 km/h ve yeterince yakın: güvenli aralıkla 30 km/h çevresine iner.
- Öndeki araç 30 km/h fakat çok uzakta: hemen 30 km/h'ye düşmez.
- Keskin viraj: önde araç olmasa da eğrilik ve yanal ivme nedeniyle yavaşlar.
- Sis/yağmur: ODD ve görünürlük hız tavanını düşürür.
- Yaya veya kırmızı ışık: stop line/conflict point'te hız sıfıra planlanır.
- Yan şeritteki araç: yalnızca predicted conflict veya lane-change etkileşimi varsa hızı etkiler.

---

## 5. Simülasyon Seviye 4 kabul kapısı

Sistem ancak aşağıdaki koşullar sağlanırsa “tanımlı ODD içinde Seviye 4 araştırma prototipi” olarak raporlanır:

1. Sürüş ajanı CARLA ground-truth aktör konumlarını normal input olarak kullanmaz.
2. Tam DDT'yi kendi yürütür: algılama, OEDR, planlama, direksiyon, hızlanma ve fren.
3. İnsan müdahalesi beklemeden ODD fallback ve MRM gerçekleştirir.
4. ODD sınırını ve sistem sağlığını sürekli izler.
5. Kritik senaryolar birden fazla harita, konum, hava ve seed ile çalıştırılır.
6. Sensör kaybı, gecikme, kalibrasyon ve lokalizasyon hataları enjekte edilir.
7. Güvenlik kriterleri yalnızca route completion'a dayanmaz.
8. ISO 34503/34505 tabanlı coverage ve Waymo CAT benzeri responder-conflict kataloğu tutulur.
9. Ana rapor CARLA 0.9.16 kanonik ortamında üretilir.
10. Sonuç açıkça “simulation-based Level 4 research prototype in the declared ODD” şeklinde adlandırılır; yol kullanım sertifikasyonu iddia edilmez.

