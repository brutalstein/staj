# L4 Autonomy Platform — Faz 1

CARLA tabanlı, tanımlı ODD içerisinde geliştirilen simulation-based SAE Level 4 araştırma platformu. Default çalışma yolu artık yalnızca bağlantı kontrolü yapmaz; ego aracı ve bütün Faz 1 sensörlerini oluşturur, synchronous world tick üretir, aynı frame verilerini birleştirir ve çalışma manifestini kaydeder.

## Uygulanan default mimari

- Python 3.11
- CARLA 0.9.16 ana sürüm, 0.9.15 uyumluluk profili
- Özel CARLA build kimliği → semantik sürüm alias desteği
- Tesla Model 3 deterministik ego spawn
- Runtime `VehicleGeometryAdapter`
- 6 RGB kamera
- 1 adet 64 kanallı ray-cast LiDAR
- 6 adet CARLA radar tabanlı 4D radar proxy
- Çift GNSS ve 1 IMU
- Araç transform, hız, ivme, açısal hız, steering ve actuator feedback
- Tek-owner CARLA synchronous tick
- Sensor callback gateway ve bounded frame buffer
- Exact CARLA-frame synchronizer
- Manifest + JSONL recorder
- Actor cleanup ve world settings restore

Faz 1'de localization, world model, planning ve controller henüz uygulanmaz. Bu nedenle ego actor autopilot'a verilmez ve güvenli tam fren/el freni durumunda tutulur.

## Ortam

```bash
conda create -n odd python=3.11 -y
conda activate odd
python -m pip install -e '.[dev,docs]'
```

CARLA Python API, kullanılan server build'iyle aynı kaynak/dağıtımdan kurulmalıdır.

## Kontrol

```bash
./run_project.sh check
./run_project.sh doctor
```

## Default runtime

CARLA server açıkken:

```bash
./run_project.sh start
```

Runtime sırasıyla synchronous mode'u açar, Tesla'yı spawn eder, 16 sensörü rigid bağlar ve ortak frame kayıtlarını üretir. `Ctrl+C` ile sensörler ve araç yok edilir, önceki world settings geri yüklenir.

Default kayıt dizini:

```text
runtime/recordings/<run_id>/
├── manifest.json
└── frames.jsonl
```

Ham sensör verisi default olarak diske yazılmaz. `record_raw_data: true` yalnızca açıkça gerektiğinde kullanılmalıdır.

## Test

ROS 2 pytest eklentilerinden izole unit/mock suite:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q
python -m compileall -q autonomy tools tests
python tools/validate_project.py
```

Gerçek CARLA smoke testi:

```bash
CARLA_SMOKE_TEST=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
python -m pytest -q -m carla_smoke tests/test_phase1_carla_smoke.py
```

Smoke test ego + 16 sensör spawn, en az iki ortak frame, recorder ve cleanup akışını gerçek server üzerinde doğrular.

## Konfigürasyonun ana kaynakları

- `config/runtime/default.yaml`
- `config/vehicles/tesla_model3.yaml`
- `config/sensors/layouts/tesla_model3_omnihd_v1.yaml`

Araç boyutları elle girilmez. Bounding box ve wheel positions runtime CARLA actor instance'ından çıkarılır. Üç dosyanın içeriği tek configuration hash içinde izlenir.

## Doküman portalı

```bash
./run_docs.sh
```

Varsayılan adres: `http://127.0.0.1:8000`

## Faz sırası

1. Faz 0 — Sözleşmeler, registry, runtime ve bağlantı omurgası — **tamamlandı**
2. Faz 1 — Araç/sensör oluşturma, synchronous tick, sync ve recorder — **tamamlandı**
3. Faz 2 — Localization ve vehicle state
4. Faz 3 — Multi-sensor BEV ve world model
5. Faz 4 — Behavior ve trajectory planning
6. Faz 5 — Safety Cage ve control
7. Faz 6 — Senaryo, hata enjeksiyonu ve benchmark
