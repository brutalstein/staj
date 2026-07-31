# L4 Autonomy Platform — Faz 0

Bu depo, CARLA tabanlı ve tanımlı ODD içerisinde çalışacak Seviye 4 araştırma sisteminin ilk kodlama fazıdır.

Bu fazda bulunanlar:

- Tipli çalışma zamanı veri sözleşmeleri
- Sürümlü YAML konfigürasyonları
- Component, contract ve algorithm registry
- Modül yaşam döngüsü ve orchestrator
- CARLA 0.9.15/0.9.16 bağlantı adaptörü
- Windows ve Ubuntu proje başlatıcıları
- Windows ve Ubuntu doküman portalı başlatıcıları
- Her uygulanan modülde `MODULE.md`
- Registry ve doküman tutarlılık doğrulayıcısı
- Birim ve sözleşme testleri
- Yaşayan mimari portalı için MkDocs iskeleti

Bu fazda özellikle bulunmayanlar:

- UniAD model entegrasyonu
- FAST-LIO2/FAST-LIVO2 implementasyonu
- Behavior Planner
- Trajectory Planner
- Safety Cage
- NMPC

Bu modüller henüz kodlanmadığı için boş sınıflar veya sahte implementasyonlar eklenmemiştir. Planları registry ve dokümanlarda tutulur.

## Ortam oluşturma

### Windows

```powershell
conda create -n autonomy-carla-0916-py311 python=3.11 -y
conda activate autonomy-carla-0916-py311
python -m pip install -e ".[dev,docs]"
```

### Ubuntu

```bash
conda create -n autonomy-carla-0916-py311 python=3.11 -y
conda activate autonomy-carla-0916-py311
python -m pip install -e '.[dev,docs]'
```

CARLA Python API ayrıca kullanılan CARLA sürümüyle eşleşecek biçimde kurulmalıdır.

## Ortam kontrolü

```powershell
.\run_project.ps1 check
```

```bash
./run_project.sh check
```

## Projeyi başlatma

CARLA server önce kullanıcı tarafından açılmalıdır.

```powershell
.\run_project.ps1 start
```

```bash
./run_project.sh start
```

CARLA server kapalıysa uygulama aktör oluşturmadan, Türkçe hata mesajıyla kapanır.

## Doküman portalı

```powershell
.\run_docs.ps1
```

```bash
./run_docs.sh
```

Varsayılan adres: `http://127.0.0.1:8000`

## Test

```bash
python -m pytest
python tools/validate_project.py
```

## Faz sırası

1. Faz 0 — Sözleşmeler, registry, runtime, launcher ve doküman omurgası
2. Faz 1 — CARLA araç/sensör oluşturma ve senkronizasyon
3. Faz 2 — Lokalizasyon ve vehicle state
4. Faz 3 — Multi-sensor BEV ve world model
5. Faz 4 — Behavior ve trajectory planning
6. Faz 5 — Safety Cage ve kontrol
7. Faz 6 — Senaryo, hata enjeksiyonu ve benchmark
