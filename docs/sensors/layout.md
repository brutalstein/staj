# Sensör Yerleşimi ve Kaynak İzlenebilirliği

Default topoloji:

- 6 çevresel RGB kamera — 25 Hz, 1280×720
- 1 adet 64 kanal 360° ray-cast LiDAR — 25 Hz
- 6 adet CARLA radar tabanlı 4D radar proxy — 25 Hz
- 2 GNSS — 50 Hz
- 1 IMU — 50 Hz
- Araç feedback — her 50 Hz world tick'inde

Bu topoloji tek bir yayından kopyalanmamıştır. Sensör **sayısı**, **modalite seçimi**, **yerleşim açıları** ve **CARLA parametreleri** için farklı kökenler vardır. Aşağıdaki ayrım zorunludur:

- **Literatür dayanağı:** Modalitenin veya yaklaşık topolojinin araştırma gerekçesi.
- **CARLA kısıtı:** Simülatörün gerçekten üretebildiği veri ve desteklediği attribute'lar.
- **Proje kararı:** Bu araç ve ODD için seçilen başlangıç montajı, FoV, frekans veya menzil.

## Karar-kaynak matrisi

| Karar | Köken | Neden |
|---|---|---|
| 6 çevresel kamera | nuScenes ve UniAD uyumu | nuScenes veri toplama platformu altı kamerayla çevresel görüş sağlar; UniAD nuScenes çoklu kamera girdileri üzerinde değerlendirilir. Bu sayı gelecekteki UniAD/BEV world-model hattıyla veri biçimi uyumunu korur. |
| Kamera yaw/FoV değerleri | Proje kararı | `0°, ±60°, ±120°, 180°` ve 80–115° FoV değerleri bir makaleden kopyalanmamıştır. Bindirmeli 360° başlangıç kapsaması için seçilmiştir ve coverage/occlusion testleriyle kalibre edilecektir. |
| 1 çatı LiDAR | nuScenes, BEVFusion, FAST-LIO2/FAST-LIVO2 | Tek 360° LiDAR geometrik derinlik, lokalizasyon, haritalama ve kamera-LiDAR BEV fusion için ortak referans üretir. |
| 64 kanal ve LiDAR parametreleri | Proje kararı + CARLA sensor API | 64 kanal, 120 m menzil ve FoV değerleri yüksek düşey çözünürlüklü simülasyon baseline'ıdır; nuScenes donanımının birebir kopyası değildir. |
| 6 radar | RCBEVDet + proje kararı | Radar-kamera BEV fusion literatürle desteklenir. nuScenes beş radar kullanır; altıncı arka-merkez radar simetrik ön/arka kapsama için projeye özel eklenmiştir. |
| `4d_radar_proxy` adı | CARLA kısıtı | CARLA radarı azimut, irtifa açısı, menzil ve radyal hız üretir; gerçek imaging 4D radarın anten dizisi, RCS ve beamforming fiziğini modellemez. Bu nedenle gerçek 4D radar iddiası yapılmaz. |
| 2 GNSS | Dual-antenna GNSS/INS literatürü | İki anten arasındaki baseline ileride heading gözlemi ve GNSS/IMU fusion için kullanılacaktır. Her iki akış Faz 1'de spawn edilir, senkronize edilir ve kaydedilir. |
| Dual-GNSS heading sınırlaması | CARLA kısıtı | CARLA GNSS yalnız latitude/longitude/altitude ve basit bias/noise üretir; carrier phase, integer ambiguity veya RTK çözümü üretmez. Faz 1 gerçek dual-antenna GNSS compass doğruluğu iddia etmez. |
| IMU | FAST-LIO2/FAST-LIVO2 ve GNSS/INS | Yüksek oranlı ivme/açısal hız, Faz 2 lokalizasyon ve kısa süreli dead-reckoning için zorunlu girdidir. |

## Kamera yerleşimi

| Sensör | Yaw | FoV | İşlev |
|---|---:|---:|---|
| `camera_front` | 0° | 80° | Uzunlamasına ön görüş ve trafik öğeleri |
| `camera_front_left/right` | ±60° | 110° | Ön çapraz bindirme, kavşak ve şerit komşuluğu |
| `camera_rear_left/right` | ±120° | 110° | Arka çapraz bindirme ve kör bölge |
| `camera_rear` | 180° | 115° | Arka merkez kapsama |

Açı işaretleri CARLA'nın x-forward, y-right, z-up sol-elli actor frame'ine göredir. Yerleşim, algılama performansı ölçülmeden “optimum” kabul edilmez. Faz 1 yalnız deterministik ve araç-geometrisine bağlı başlangıç kalibrasyonu sağlar.

## LiDAR ve radar yerleşimi

LiDAR çatı merkezine yakın yerleştirilir; amaç araç gövdesi self-occlusion'ını azaltmak ve tüm modaliteler için tek geometrik referans sağlamaktır. Radarlar ön merkez, ön köşeler, arka köşeler ve arka merkez olarak dağıtılır. Altı radarlı düzen, nuScenes topolojisinin birebir kopyası değildir.

## Neden iki GNSS?

İki GNSS akışının hedefi yedek iki bağımsız konum tahmini üretmekten önce, antenler arasındaki bilinen baseline'ı Faz 2'de heading gözlemine dönüştürmektir. Gerçek sistemde bu işlem carrier-phase tabanlı dual-antenna yönelim çözümüne dayanır. CARLA bu fiziksel katmanı modellemediği için:

1. Faz 1 iki sensörü yalnız toplar, frame'e eşler ve manifestte izler.
2. Faz 2'de ayrı bir `DualGnssBaselineEstimator` olmadan “GNSS heading” üretilmez.
3. Simülasyon sonucu gerçek RTK/dual-antenna donanım doğruluğu olarak raporlanmaz.
4. İkinci GNSS ileride kullanılmayacaksa topolojiden kaldırılmalıdır; sahte bir heading üretmek için kullanılmayacaktır.

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

### WheelPhysicsControl koordinat normalizasyonu

CARLA dokümantasyonu sensör attach transformlarının parent actor'a göre local olduğunu belirtir. Buna karşılık `WheelPhysicsControl.position` bazı CARLA/PhysX build'lerinde dünya koordinatında ve santimetre ölçeğinde raporlanabilir. `VehicleGeometryAdapter` bu nedenle iki adımı uygular:

1. Tekerler arası translation-invariant mesafeden metre/santimetre ölçeğini belirler.
2. Hem actor-local hem de `vehicle.get_transform().inverse_transform(...)` ile world-to-actor adayını hesaplar; bounding box, wheelbase ve track tutarlılığı en yüksek adayı seçer.

Seçilen referans (`actor_local` veya `world_to_actor`) ve ölçek her run manifestindeki `geometry` alanına yazılır. Böylece özel CARLA build davranışı görünür ve yeniden üretilebilir kalır.

## Runtime kaynakları

- Araç bounding box: CARLA actor instance
- Wheelbase/track: normalize edilmiş ilk dört `WheelPhysicsControl.position`
- Normalize layout: `config/sensors/layouts/tesla_model3_omnihd_v1.yaml`
- Gerçek çözülmüş pozlar: her run `manifest.json`
- Kaynak registry: `config/sources/sources.yaml`

## Kaynak kimlikleri

- `NUSCENES_2020`
- `UNIAD_2023`
- `BEVFUSION_2023`
- `RCBEVDET_2024`
- `FAST_LIO2_2022`
- `FAST_LIVO2_2024`
- `DUAL_GNSS_INS_2024`
- `CARLA_SENSOR_REFERENCE_0916`
- `CARLA_COORDINATES_DOCUMENTATION`

!!! warning "Bilimsel iddia sınırı"
    Bu sayfa literatür temelli modalite seçimini, projeye özel montaj kararından ayırır. Exact açı, FoV, kanal, menzil ve sensör sayılarının tamamının tek bir yayından geldiği iddia edilmez.
