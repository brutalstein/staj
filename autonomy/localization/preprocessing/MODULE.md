# Preprocessing Modülü

Bu modül, CARLA ortamından alınan sensör verilerinin (IMU, GNSS, Odometri vb.) lokalizasyon algoritmasının beklediği standart birimlere ve koordinat sistemlerine dönüştürülmesini sağlar.
IMU için Sol-El -> Sağ-El dönüşümleri, GNSS için projeksiyon ve odometri için ön işleme adımları burada yapılır.
