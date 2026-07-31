# Veri Akışı

```mermaid
flowchart TD
  Callback[CARLA SensorData] --> Buffer[BoundedSensorBuffer]
  Buffer --> Sync[SynchronizedMeasurements]
  Sync --> Contract[SynchronizedSensorFrame]
  Vehicle[Vehicle Feedback] --> Record[Run Recorder]
  Sync --> Record
  Contract --> Loc[Phase 2 LocalizationEstimate]
  Loc --> World[Phase 3 WorldModelSnapshot]
  World --> Intent[Phase 4 BehaviorIntent]
  Intent --> Safe[Phase 5 SafeTrajectory]
```

Callback payload'ı gateway içinde kopyalanmadan runtime nesnesi olarak tutulur. `RawSensorPacket` Faz 1'de metadata görünümüdür; gerçek payload sonraki işlem için `SynchronizedMeasurements.measurements_by_sensor_id` içindedir. Her ortak frame configuration hash, CARLA frame ve timestamp ile kaydedilir.
