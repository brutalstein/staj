from __future__ import annotations

import math
from typing import Any


class WheelOdometryProcessor:
    """Araç hız ve dönüş verilerinden basit odometri hesaplamaları yapar."""

    def process(self, vehicle_feedback: dict[str, Any]) -> dict[str, float]:
        """Vehicle feedback sözlüğünden ileri yönlü (longitudinal) hızı ve direksiyon açısını çıkarır.
        
        CARLA feedback'inde linear_velocity_mps (X, Y, Z) dünya (veya ego) koordinatlarındadır.
        CARLA'da X ekseni ileri yönlüdür.
        """
        velocity = vehicle_feedback.get("linear_velocity_mps", {"x": 0.0, "y": 0.0, "z": 0.0})
        # Basitlik adına, CARLA'nın ego aracının kendi x-y eksenindeki hızını veya
        # direkt speed_mps alanını kullanabiliriz. (Zorunlu bir ileri sürüş varsayımı).
        # Gerçek bir wheel odometry, tekerlek açısal hızından türetilmelidir, 
        # ancak faz 2'de speed_mps vekil olarak kullanılıyor.
        speed_mps = vehicle_feedback.get("speed_mps", 0.0)
        
        actuation = vehicle_feedback.get("actuation", {})
        # Eğer reverse ise hız negatiftir.
        if actuation.get("reverse", False):
            speed_mps = -speed_mps
            
        steering_angle_deg = actuation.get("steering_angle_deg", 0.0)
        if steering_angle_deg is None:
            steering_angle_deg = 0.0
            
        steering_angle_rad = math.radians(steering_angle_deg)
        
        return {
            "longitudinal_velocity_mps": speed_mps,
            "steering_angle_rad": steering_angle_rad,
        }
