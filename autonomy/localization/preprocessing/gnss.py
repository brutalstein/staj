from __future__ import annotations

import math
from typing import Any

from autonomy.sensing.gateway.buffer import SensorMeasurement


class GnssPreprocessor:
    """CARLA GNSS (Enlem, Boylam, İrtifa) verilerini yerel Metrik (X, Y, Z) koordinatlara dönüştürür.
    
    Önceden tanımlanmış bir referans noktası (origin_lat, origin_lon) kullanılır.
    Town haritaları için varsayılan referans genellikle (0.0, 0.0) alınır veya
    ilk gelen veri origin kabul edilir.
    """
    
    EARTH_RADIUS_M = 6371000.0

    def __init__(self, origin_lat: float | None = None, origin_lon: float | None = None) -> None:
        self._origin_lat = origin_lat
        self._origin_lon = origin_lon

    def process(self, measurement: SensorMeasurement) -> dict[str, Any]:
        if measurement.sensor_type != "gnss":
            raise ValueError(f"Beklenmeyen sensör tipi GNSS için: {measurement.sensor_type}")
            
        payload = measurement.payload
        lat = float(payload.latitude)
        lon = float(payload.longitude)
        alt = float(payload.altitude)
        
        if self._origin_lat is None or self._origin_lon is None:
            self._origin_lat = lat
            self._origin_lon = lon
            
        # Basit Equirectangular Projection
        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon)
        origin_lat_rad = math.radians(self._origin_lat)
        origin_lon_rad = math.radians(self._origin_lon)
        
        # dx, dy hesaplaması (Kuzey=X, Doğu=Y veya East-North-Up kuralına göre)
        # ROS ENU: X=East, Y=North, Z=Up
        # Araç içi lokalizasyon: X=Forward, Y=Left. Harita koordinatları için East/North kullanabiliriz
        # ve araç başlangıç pozuna göre transforme edebiliriz.
        # CARLA world: X=East, Y=South? Aslında Town'lar keyfi oryante edilebilir.
        # Biz burada X=East, Y=North varsayalım ve Baseline EKF'de harita yönelimini ayarlayalım.
        x_east_m = (lon_rad - origin_lon_rad) * self.EARTH_RADIUS_M * math.cos(origin_lat_rad)
        y_north_m = (lat_rad - origin_lat_rad) * self.EARTH_RADIUS_M
        
        return {
            "sensor_id": measurement.sensor_id,
            "timestamp_seconds": measurement.timestamp_seconds,
            "latitude": lat,
            "longitude": lon,
            "altitude": alt,
            "position_x_m": x_east_m,
            "position_y_m": y_north_m,
            "position_z_m": alt,
        }
