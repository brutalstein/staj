# Sistem Mimarisi

```mermaid
flowchart LR
  MM[Mission / ODD] --> SIM[CARLA Platform]
  SIM --> SYNC[Sensor & Time]
  SYNC --> LOC[Localization]
  SYNC --> WM[World Model]
  LOC --> WM
  WM --> BEH[Behavior]
  BEH --> PLAN[Trajectory]
  PLAN --> SAFE[Safety Cage]
  SYNC --> SAFE
  LOC --> SAFE
  SAFE --> CTRL[Controller]
  CTRL --> SIM
```

??? info "Faz 0'da uygulananlar"
    Configuration, contracts, runtime lifecycle, CARLA bağlantı adaptörü ve launcher.

??? warning "Henüz uygulanmayanlar"
    Sensör aktörleri, lokalizasyon, world model, planning, safety ve control yalnızca plan/registry seviyesindedir.
