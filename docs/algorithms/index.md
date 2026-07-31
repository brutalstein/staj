# Algoritmalar

Algoritmaların makine tarafından doğrulanan ana kaydı `config/algorithms/algorithm_registry.yaml` dosyasıdır.

## Statüler

- `baseline`: İlk doğrulanabilir uygulama
- `target`: Amaçlanan ana yöntem
- `fallback`: Güvenli sınırlı yöntem
- `planned_phase_*`: Henüz kodlanmadı
- `research_candidate`: Üretim yolunda değil

## Ana seçimler

??? abstract "Localization"
    FAST-LIO2 baseline, FAST-LIVO2 hedef ve robust factor-graph global düzeltme.

??? abstract "World Model"
    UniAD planning-oriented query yapısı, BEVFusion ve RCBEVDet tabanlı sensör özellikleri.

??? abstract "Behavior"
    Hierarchical State Machine; yalnızca belirsiz interaction alanlarında sınırlı POMDP belief.

??? abstract "Trajectory"
    UniAD/PLUTO tarzı adaylar, kısıtlı refinement ve Frenet fallback.

??? abstract "Safety"
    RSS, robust HOCBF-QP ve Simplex runtime assurance.

??? abstract "Control"
    RTI-NMPC; curvature-adaptive Pure Pursuit ve gain-scheduled PID fallback.
