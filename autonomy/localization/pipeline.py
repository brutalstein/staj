from __future__ import annotations

import math
import time
from typing import Any

from autonomy.contracts.common import MessageMetadata
from autonomy.contracts.localization import EgoState, LocalizationEstimate, LocalizationMode
from autonomy.sensing.synchronization import SynchronizedMeasurements
from autonomy.localization.estimators.baseline_filter import BaselineEkfFilter
from autonomy.localization.estimators.dual_gnss_heading import DualGnssBaselineEstimator
from autonomy.localization.estimators.lever_arm import LeverArmCompensator
from autonomy.localization.preprocessing.gnss import GnssPreprocessor
from autonomy.localization.preprocessing.imu import ImuPreprocessor
from autonomy.localization.preprocessing.odometry import WheelOdometryProcessor


class LocalizationPipeline:
    """CARLA SynchronizedMeasurements verilerini işleyip EgoState ve LocalizationEstimate üretir."""

    def __init__(self, configuration_hash: str) -> None:
        self._configuration_hash = configuration_hash
        self._imu_preprocessor = ImuPreprocessor()
        self._gnss_preprocessor = GnssPreprocessor()
        self._odometry_processor = WheelOdometryProcessor()
        
        # Dual GNSS baseline: Primary (Y=-0.12), Secondary (Y=0.12)
        # TODO: Sensör layout'tan dinamik yapılandırılmalıdır.
        self._dual_gnss_estimator = DualGnssBaselineEstimator(
            primary_offset_y_m=-0.12, 
            secondary_offset_y_m=0.12
        )
        
        # Lever Arm Compensators (GNSS'den Ego Merkezine)
        # Tesla Model 3 wheelbase = 3.005 m, ratio = 0.45 => X = 1.35225 m
        self._primary_lever_arm = LeverArmCompensator(1.35225, -0.12, 1.0)
        self._secondary_lever_arm = LeverArmCompensator(1.35225, 0.12, 1.0)
        
        self._ekf = BaselineEkfFilter()
        self._last_timestamp_seconds: float | None = None
        self._sequence_number = 0
        
        self._consecutive_gnss_drops = 0

    def process(self, sync_data: SynchronizedMeasurements, feedback: dict[str, Any]) -> tuple[LocalizationEstimate, EgoState]:
        timestamp = sync_data.contract.metadata.timestamp_seconds
        dt = 0.0
        if self._last_timestamp_seconds is not None:
            dt = timestamp - self._last_timestamp_seconds
        self._last_timestamp_seconds = timestamp
        
        measurements = sync_data.measurements_by_sensor_id
        
        # 1. Odometry (Velocity and Steering)
        odometry_data = self._odometry_processor.process(feedback)
        
        # 2. IMU Preprocessing
        imu_meas = measurements.get("imu_center")
        if imu_meas is not None:
            imu_data = self._imu_preprocessor.process(imu_meas)
            a_x = imu_data["acceleration_xyz_mps2"][0]
            omega_z = imu_data["angular_velocity_xyz_radps"][2]
        else:
            # Fallback to zeros if IMU is missing
            a_x = 0.0
            omega_z = 0.0

        # EKF Predict step
        self._ekf.predict(a_x, omega_z, dt)
        
        # EKF Update step (Odometry)
        v = odometry_data["longitudinal_velocity_mps"]
        self._ekf.update_velocity(v, r_v=0.1)
        
        # 3. GNSS Preprocessing & Dual GNSS Heading
        gnss_pri_meas = measurements.get("gnss_primary")
        gnss_sec_meas = measurements.get("gnss_secondary")
        
        gnss_valid = False
        if gnss_pri_meas is not None and gnss_sec_meas is not None:
            pri_data = self._gnss_preprocessor.process(gnss_pri_meas)
            sec_data = self._gnss_preprocessor.process(gnss_sec_meas)
            
            # Heading estimation
            yaw_gnss = self._dual_gnss_estimator.estimate(pri_data, sec_data)
            if yaw_gnss is not None:
                self._ekf.update_yaw(yaw_gnss, r_yaw=0.05)
                
            # Current EKF orientation
            _, _, ekf_yaw, _ = self._ekf.get_state()
            
            # Lever arm compensation for primary GNSS
            # Basitlik için pitch ve roll 0 varsayılıyor. İstenirse EKF'ye eklenebilir.
            rear_x, rear_y, rear_z = self._primary_lever_arm.compensate(
                pri_data["position_x_m"],
                pri_data["position_y_m"],
                pri_data["position_z_m"],
                0.0, 0.0, ekf_yaw
            )
            
            self._ekf.update_gnss(rear_x, rear_y, r_x=1.0, r_y=1.0)
            gnss_valid = True
            
        if gnss_valid:
            self._consecutive_gnss_drops = 0
            mode = LocalizationMode.NOMINAL
        else:
            self._consecutive_gnss_drops += 1
            mode = LocalizationMode.DEAD_RECKONING
            if self._consecutive_gnss_drops > 100:
                mode = LocalizationMode.UNRELIABLE

        # Final State Extraction
        ex, ey, eyaw, ev = self._ekf.get_state()
        cov_diag = self._ekf.get_covariance()
        
        # Construct Metadata
        metadata = MessageMetadata(
            timestamp_seconds=timestamp,
            simulation_frame=sync_data.contract.metadata.simulation_frame,
            sequence_number=self._sequence_number,
            coordinate_frame="ego_rear_axle",
            source_module="localization_pipeline",
            configuration_hash=self._configuration_hash,
        )
        self._sequence_number += 1
        
        # EgoState
        ego_state = EgoState(
            metadata=metadata,
            position_xyz_m=(ex, ey, 0.0), # Basitleştirilmiş Z=0
            orientation_wxyz=(math.cos(eyaw/2), 0.0, 0.0, math.sin(eyaw/2)), # Quaternion Z rotasyonu
            linear_velocity_xyz_mps=(ev, 0.0, 0.0),
            angular_velocity_xyz_radps=(0.0, 0.0, omega_z),
            acceleration_xyz_mps2=(a_x, 0.0, 0.0),
            steering_angle_rad=odometry_data["steering_angle_rad"]
        )
        
        # LocalizationEstimate
        loc_est = LocalizationEstimate(
            metadata=metadata,
            mode=mode,
            position_xyz_m=(ex, ey, 0.0),
            orientation_wxyz=(math.cos(eyaw/2), 0.0, 0.0, math.sin(eyaw/2)),
            velocity_xyz_mps=(ev, 0.0, 0.0),
            covariance_diagonal=cov_diag,
            confidence=0.9 if mode == LocalizationMode.NOMINAL else 0.5
        )
        
        return loc_est, ego_state
