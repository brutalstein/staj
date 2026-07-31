# Sensör Yerleşimi

Default topoloji:

- 6 çevresel RGB kamera — 25 Hz, 1280×720
- 1 adet 64 kanal 360° ray-cast LiDAR — 25 Hz
- 6 adet CARLA radar tabanlı 4D radar proxy — 25 Hz
- 2 GNSS — 50 Hz
- 1 IMU — 50 Hz
- Araç feedback — her 50 Hz world tick'inde

## Koordinat ve geometri

CARLA actor frame'i x-forward, y-right, z-up olarak kullanılır. Sensör pozları araç boyutuna sabit metre değerleriyle bağlanmaz:

\[
x_i=x_{rear\ axle}+r^x_i L_{wheelbase}
\]

\[
y_i=y_{bbox}+r^y_i W_{body}
\]

\[
z_i=z_{body\ bottom}+r^z_i H_{body}+h_i
\]

Rotation, layout içindeki roll/pitch/yaw derece değeridir. Çözümlenen transform actor-relative olarak `AttachmentType.Rigid` ile uygulanır.

## Runtime kaynakları

- Araç bounding box: CARLA actor instance
- Wheelbase/track: ilk dört `WheelPhysicsControl.position`
- Normalize layout: `config/sensors/layouts/tesla_model3_omnihd_v1.yaml`
- Gerçek çözülmüş pozlar: her run `manifest.json`

!!! warning "Radar modeli"
    CARLA `sensor.other.radar`, 4D radar entegrasyon arayüzünü geliştirmek için proxy olarak kullanılır. Gerçek imaging radar elevation/point-cloud fiziği iddia edilmez.
