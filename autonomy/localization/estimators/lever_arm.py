from __future__ import annotations

import math
from typing import Any


class LeverArmCompensator:
    """Sensör konumu ile aracın referans noktası (ego_rear_axle) arasındaki offseti (lever arm)
    aracın yönelimini kullanarak global koordinatlarda kompanze eder.
    """

    def __init__(self, sensor_offset_x: float, sensor_offset_y: float, sensor_offset_z: float) -> None:
        """
        Args:
            sensor_offset_x: Sensörün referans noktasına göre X eksenindeki konumu.
            sensor_offset_y: Sensörün referans noktasına göre Y eksenindeki konumu.
            sensor_offset_z: Sensörün referans noktasına göre Z eksenindeki konumu.
        """
        self._l_x = sensor_offset_x
        self._l_y = sensor_offset_y
        self._l_z = sensor_offset_z

    def compensate(
        self, 
        sensor_global_x: float, 
        sensor_global_y: float, 
        sensor_global_z: float, 
        roll_rad: float, 
        pitch_rad: float, 
        yaw_rad: float
    ) -> tuple[float, float, float]:
        """Sensörün global pozisyonundan aracın referans (rear_axle) global pozisyonunu hesaplar.
        
        P_rear = P_sensor - R(yaw, pitch, roll) * L
        """
        cy = math.cos(yaw_rad)
        sy = math.sin(yaw_rad)
        cp = math.cos(pitch_rad)
        sp = math.sin(pitch_rad)
        cr = math.cos(roll_rad)
        sr = math.sin(roll_rad)

        # Rotasyon matrisi (Z-Y-X kuralı)
        r00 = cy * cp
        r01 = cy * sp * sr - sy * cr
        r02 = cy * sp * cr + sy * sr
        
        r10 = sy * cp
        r11 = sy * sp * sr + cy * cr
        r12 = sy * sp * cr - cy * sr
        
        r20 = -sp
        r21 = cp * sr
        r22 = cp * cr
        
        # L vektörünü global koordinatlara çevir (R * L)
        dx = r00 * self._l_x + r01 * self._l_y + r02 * self._l_z
        dy = r10 * self._l_x + r11 * self._l_y + r12 * self._l_z
        dz = r20 * self._l_x + r21 * self._l_y + r22 * self._l_z
        
        return (
            sensor_global_x - dx,
            sensor_global_y - dy,
            sensor_global_z - dz
        )
