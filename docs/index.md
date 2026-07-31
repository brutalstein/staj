# L4 Autonomy Architecture Portal

Bu portal koddan ayrı bir sunum değildir. Component, contract ve runtime kayıtlarının insan tarafından gezilebilir görünümüdür.

<div class="hero-grid">
  <div class="hero-card"><strong>Faz</strong><br>Faz 1 — Sensor & Time Platform</div>
  <div class="hero-card"><strong>CARLA</strong><br>0.9.16 ana / 0.9.15 uyumluluk</div>
  <div class="hero-card"><strong>Runtime</strong><br>50 Hz synchronous world</div>
  <div class="hero-card"><strong>Sensör</strong><br>16 actor, exact-frame sync</div>
</div>

## Default çalışma yolu

`Application → CARLA Phase 1 Runtime → Sensor Gateway → Frame Synchronizer → Recorder`

Ego aracı Faz 1 boyunca güvenli sabit fren durumundadır. Localization, world model, planning ve control sonraki fazlara aittir.
