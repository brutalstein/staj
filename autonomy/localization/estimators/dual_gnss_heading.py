from __future__ import annotations

import math
from typing import Any


class DualGnssBaselineEstimator:
    """İki GNSS anteni (primary ve secondary) arasındaki baz hattını kullanarak aracın yönelimini (Heading) hesaplar."""

    def __init__(self, primary_offset_y_m: float = -0.2, secondary_offset_y_m: float = 0.2) -> None:
        """
        Args:
            primary_offset_y_m: Primary GNSS'in ego-rear-axle y-eksenindeki konumu.
            secondary_offset_y_m: Secondary GNSS'in ego-rear-axle y-eksenindeki konumu.
        """
        # Ego frame'deki baseline açısı.
        # Eğer primary'den secondary'ye olan vektör, ego'nun Y ekseni üzerindeyse, 
        # offset 90 derece (pi/2) veya -90 derecedir.
        dy_ego = secondary_offset_y_m - primary_offset_y_m
        dx_ego = 0.0 # Varsayılan olarak X hizalarının aynı olduğunu kabul ediyoruz.
        self._baseline_angle_ego = math.atan2(dy_ego, dx_ego)

    def estimate(self, gnss_primary: dict[str, Any], gnss_secondary: dict[str, Any]) -> float | None:
        """İki GNSS noktasından global yönelimi (Yaw) radyan cinsinden döndürür."""
        dx_global = gnss_secondary["position_x_m"] - gnss_primary["position_x_m"]
        dy_global = gnss_secondary["position_y_m"] - gnss_primary["position_y_m"]
        
        # Eğer araç hareket etmiyorsa ve ölçüm gürültüsü yüksekse hesaplama kararsız olabilir.
        # Bu basit modelde doğrudan atan2 kullanıyoruz.
        baseline_length = math.hypot(dx_global, dy_global)
        if baseline_length < 0.01:
            return None # Mesafe çok kısaysa geçersiz.
            
        baseline_angle_global = math.atan2(dy_global, dx_global)
        
        # Aracın Heading açısı = Global Baseline Açısı - Ego Baseline Açısı
        yaw_rad = baseline_angle_global - self._baseline_angle_ego
        
        # -pi ile pi arasına normalize edelim
        yaw_rad = (yaw_rad + math.pi) % (2 * math.pi) - math.pi
        
        return yaw_rad
