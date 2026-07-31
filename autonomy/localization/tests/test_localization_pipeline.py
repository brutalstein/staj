import math
import unittest
from typing import Any

from autonomy.contracts.common import MessageMetadata
from autonomy.contracts.localization import LocalizationMode
from autonomy.contracts.sensor import RawSensorPacket, SynchronizedSensorFrame
from autonomy.localization.pipeline import LocalizationPipeline
from autonomy.sensing.gateway.buffer import SensorMeasurement
from autonomy.sensing.synchronization import SynchronizedMeasurements



class TestLocalizationPipeline(unittest.TestCase):
    def setUp(self) -> None:
        self.pipeline = LocalizationPipeline("test_hash")

    def _create_mock_measurements(self, timestamp: float, v: float, exclude_gnss: bool = False) -> SynchronizedMeasurements:
        metadata = MessageMetadata(
            timestamp_seconds=timestamp,
            simulation_frame=1,
            sequence_number=1,
            coordinate_frame="ego_rear_axle",
            source_module="test",
            configuration_hash="test",
        )
        
        class MockPayload:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
                    
        class MockVector3D:
            def __init__(self, x, y, z):
                self.x = x
                self.y = y
                self.z = z
        
        # GNSS Primary mock (lat=0, lon=0, alt=0)
        gnss_pri = SensorMeasurement(
            sensor_id="gnss_primary",
            sensor_type="gnss",
            frame=1,
            timestamp_seconds=timestamp,
            payload=MockPayload(latitude=0.0, longitude=0.0, altitude=0.0),
            payload_size_bytes=100,
            encoding="carla.gnss_measurement"
        )
        
        # GNSS Secondary mock
        gnss_sec = SensorMeasurement(
            sensor_id="gnss_secondary",
            sensor_type="gnss",
            frame=1,
            timestamp_seconds=timestamp,
            payload=MockPayload(latitude=0.000001, longitude=0.0, altitude=0.0),
            payload_size_bytes=100,
            encoding="carla.gnss_measurement"
        )
        
        # IMU mock
        imu = SensorMeasurement(
            sensor_id="imu_center",
            sensor_type="imu",
            frame=1,
            timestamp_seconds=timestamp,
            payload=MockPayload(
                accelerometer=MockVector3D(0.0, 0.0, 9.81),
                gyroscope=MockVector3D(0.0, 0.0, 0.0),
                compass=0.0
            ),
            payload_size_bytes=100,
            encoding="carla.imu_measurement"
        )
        
        measurements_by_id = {
            "imu_center": imu
        }
        if not exclude_gnss:
            measurements_by_id["gnss_primary"] = gnss_pri
            measurements_by_id["gnss_secondary"] = gnss_sec
            
        contract = SynchronizedSensorFrame(
            metadata=metadata,
            packets_by_sensor_id={},
            missing_sensor_ids=(),
            synchronization_tolerance_seconds=0.01
        )
        
        return SynchronizedMeasurements(contract=contract, measurements_by_sensor_id=measurements_by_id)

    def test_pipeline_nominal(self) -> None:
        sync_data = self._create_mock_measurements(1.0, 5.0)
        feedback = {"speed_mps": 5.0, "steering_angle_rad": 0.1}
        
        loc_est, ego_state = self.pipeline.process(sync_data, feedback)
        
        self.assertEqual(loc_est.mode, LocalizationMode.NOMINAL)
        self.assertGreater(ego_state.linear_velocity_xyz_mps[0], 4.5)
        self.assertGreater(loc_est.velocity_xyz_mps[0], 4.5)
        
    def test_pipeline_dead_reckoning(self) -> None:
        sync_data = self._create_mock_measurements(1.0, 5.0, exclude_gnss=True)
        
        feedback = {"speed_mps": 5.0, "steering_angle_rad": 0.1}
        
        loc_est, ego_state = self.pipeline.process(sync_data, feedback)
        
        self.assertEqual(loc_est.mode, LocalizationMode.DEAD_RECKONING)

if __name__ == "__main__":
    unittest.main()
