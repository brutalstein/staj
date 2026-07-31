# Sensör Yerleşimi

Başlangıç topolojisi:

- 6 çevresel RGB kamera
- 1 adet 64 kanal 360° LiDAR
- 6 adet 4D radar vekili
- Çift GNSS
- IMU ve araç geri bildirimi

## Matematiksel tanım

\[
{}^{E}T_{S_i}=
\begin{bmatrix}
R_i&t_i\\
0&1
\end{bmatrix}
\]

\[
R_i=R_z(\psi_i)R_y(\theta_i)R_x(\phi_i)
\]

LiDAR başlangıç konumu:

\[
t_L=[0.45B,\ 0,\ H+0.10]^T
\]

!!! note "3B görünüm"
    Three.js tabanlı araç ve FoV görünümü Faz 1'de gerçek VehicleGeometryAdapter çıktısıyla bağlanacaktır. Faz 0'da sahte araç geometrisi eklenmemiştir.
