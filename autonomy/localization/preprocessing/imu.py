from __future__ import annotations

import math
from typing import Any

from autonomy.sensing.gateway.buffer import SensorMeasurement


class ImuPreprocessor:
    """CARLA IMU ölçümlerini iç koordinat sistemine (X-forward, Y-left, Z-up) dönüştürür.
    
    CARLA (Unreal) Sol-El kuralını (X-forward, Y-right, Z-up) kullanır.
    Dönüşüm:
        x_out = x_in
        y_out = -y_in
        z_out = z_in
        
    Gyro için açısal hızlar da (roll, pitch, yaw) aynı kurala göre ters çevrilir.
    """

    def process(self, measurement: SensorMeasurement) -> dict[str, Any]:
        """IMU verisini dönüştürür ve bir sözlük (veya dataclass objesi) olarak döndürür."""
        if measurement.sensor_type != "imu":
            raise ValueError(f"Beklenmeyen sensör tipi IMU için: {measurement.sensor_type}")
            
        payload = measurement.payload
        
        # CARLA IMU Measurement attributes:
        # accelerometer: carla.Vector3D (m/s^2)
        # gyroscope: carla.Vector3D (rad/s)
        # compass: float (rad) - Heading relative to North
        
        # Accelerometer: X forward, Y right, Z up -> X forward, Y left, Z up
        ax = float(payload.accelerometer.x)
        ay = float(payload.accelerometer.y)
        az = float(payload.accelerometer.z)
        
        accel_xyz = (ax, -ay, az)
        
        # Gyroscope: Roll (X), Pitch (Y), Yaw (Z)
        # CARLA uses left-handed rotations. So we flip Y and Z angular velocities.
        gx = float(payload.gyroscope.x)
        gy = float(payload.gyroscope.y)
        gz = float(payload.gyroscope.z)
        
        # Actually, for right-handed coordinate system (FLU):
        # angular_velocity around X (Roll) is positive CCW. CARLA Roll is positive clockwise.
        # So gyro_xyz = (gx, -gy, -gz)
        gyro_xyz = (gx, -gy, -gz)
        
        # Compass (heading)
        # In CARLA, compass is 0 at North, increases clockwise.
        compass_rad = float(payload.compass)
        yaw_rad = -compass_rad
        # normalize between -pi and pi
        yaw_rad = (yaw_rad + math.pi) % (2 * math.pi) - math.pi
        
        return {
            "sensor_id": measurement.sensor_id,
            "timestamp_seconds": measurement.timestamp_seconds,
            "acceleration_xyz_mps2": accel_xyz,
            "angular_velocity_xyz_radps": gyro_xyz,
            "compass_yaw_rad": yaw_rad,
        }
