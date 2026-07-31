# Sistem Mimarisi

```mermaid
flowchart LR
  CFG[Configuration] --> APP[Application]
  APP --> RT[CARLA Phase 1 Runtime]
  RT --> EGO[Tesla + Geometry]
  RT --> SF[Sensor Factory]
  SF --> GW[Sensor Gateway]
  GW --> SYNC[Frame Synchronizer]
  RT --> FB[Vehicle Feedback]
  SYNC --> REC[Recorder]
  FB --> REC
  SYNC --> LOC[Phase 2 Localization]
  LOC --> WM[Phase 3 World Model]
  WM --> PLAN[Phase 4 Planning]
  PLAN --> SAFE[Phase 5 Safety/Control]
  SAFE --> RT
```

??? success "Faz 1'de uygulananlar"
    Araç geometrisi, Tesla spawn, 16 sensor actor, synchronous tick, bounded buffer, exact-frame sync, vehicle feedback, recorder ve cleanup.

??? warning "Henüz uygulanmayanlar"
    Localization, world model, behavior/trajectory planning, Safety Cage ve controller.
