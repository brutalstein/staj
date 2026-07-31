import unittest
from autonomy.perception.pipeline import PerceptionPipeline
from autonomy.contracts.sensor import SynchronizedSensorFrame
from autonomy.sensing.synchronization import SynchronizedMeasurements
from autonomy.sensing.gateway.buffer import SensorMeasurement
from autonomy.contracts.common import MessageMetadata
from autonomy.contracts.localization import EgoState

class TestPerceptionPipeline(unittest.TestCase):
    
    def setUp(self):
        self.pipeline = PerceptionPipeline()
        self.ego_state = EgoState(
            metadata=MessageMetadata(
                timestamp_seconds=1.0,
                simulation_frame=1,
                sequence_number=1,
                coordinate_frame="ego_rear_axle",
                source_module="test"
            ),
            position_xyz_m=(0.0, 0.0, 0.0),
            orientation_wxyz=(1.0, 0.0, 0.0, 0.0),
            linear_velocity_xyz_mps=(0.0, 0.0, 0.0),
            angular_velocity_xyz_radps=(0.0, 0.0, 0.0),
            acceleration_xyz_mps2=(0.0, 0.0, 0.0),
            steering_angle_rad=0.0
        )
        self.meta = MessageMetadata(
            timestamp_seconds=1.0,
            simulation_frame=1,
            sequence_number=1,
            coordinate_frame="world",
            source_module="test"
        )

    def test_nominal_all_sensors(self):
        # Create mock measurements for all sensors
        measurements = [
            SensorMeasurement(
                sensor_id="camera_front",
                sensor_type="rgb_camera",
                frame=1,
                timestamp_seconds=1.0,
                payload=b"mock_image_data",
                payload_size_bytes=len(b"mock_image_data"),
                encoding="carla.bgra8"
            ),
            SensorMeasurement(
                sensor_id="lidar_top",
                sensor_type="lidar_64_channel",
                frame=1,
                timestamp_seconds=1.0,
                payload=b"mock_lidar_data",
                payload_size_bytes=len(b"mock_lidar_data"),
                encoding="carla.lidar_xyz_intensity_f32"
            ),
            SensorMeasurement(
                sensor_id="radar_front",
                sensor_type="4d_radar_proxy",
                frame=1,
                timestamp_seconds=1.0,
                payload=b"mock_radar_data",
                payload_size_bytes=len(b"mock_radar_data"),
                encoding="carla.radar_detection_array"
            )
        ]
        
        contract = SynchronizedSensorFrame(
            metadata=self.meta,
            packets_by_sensor_id={},
            missing_sensor_ids=(),
            synchronization_tolerance_seconds=0.0
        )
        
        sync_frame = SynchronizedMeasurements(
            contract=contract,
            measurements_by_sensor_id={m.sensor_id: m for m in measurements}
        )
        
        snapshot = self.pipeline.process(sync_frame, self.ego_state)
        
        self.assertTrue(snapshot.sensor_status.camera_available)
        self.assertTrue(snapshot.sensor_status.lidar_available)
        self.assertTrue(snapshot.sensor_status.radar_available)
        self.assertFalse(snapshot.sensor_status.is_fully_degraded)
        
        # Test if tracks and lanes are populated
        self.assertGreater(len(snapshot.tracked_objects), 0)
        self.assertGreater(len(snapshot.lane_boundaries), 0)

    def test_lidar_degraded(self):
        # Drop lidar
        measurements = [
            SensorMeasurement(
                sensor_id="camera_front",
                sensor_type="rgb_camera",
                frame=1,
                timestamp_seconds=1.0,
                payload=b"mock_image_data",
                payload_size_bytes=len(b"mock_image_data"),
                encoding="carla.bgra8"
            ),
            SensorMeasurement(
                sensor_id="radar_front",
                sensor_type="4d_radar_proxy",
                frame=1,
                timestamp_seconds=1.0,
                payload=b"mock_radar_data",
                payload_size_bytes=len(b"mock_radar_data"),
                encoding="carla.radar_detection_array"
            )
        ]
        
        contract = SynchronizedSensorFrame(
            metadata=self.meta,
            packets_by_sensor_id={},
            missing_sensor_ids=("lidar_top",),
            synchronization_tolerance_seconds=0.0
        )
        
        sync_frame = SynchronizedMeasurements(
            contract=contract,
            measurements_by_sensor_id={m.sensor_id: m for m in measurements}
        )
        
        snapshot = self.pipeline.process(sync_frame, self.ego_state)
        
        self.assertTrue(snapshot.sensor_status.camera_available)
        self.assertFalse(snapshot.sensor_status.lidar_available)
        self.assertTrue(snapshot.sensor_status.radar_available)
        
        # Should fallback to RCBEVDet (Radar-Camera BEV detection)
        self.assertGreater(len(snapshot.tracked_objects), 0)
        self.assertGreater(len(snapshot.lane_boundaries), 0)
        
    def test_fully_degraded(self):
        # Drop all sensors
        measurements = []
        contract = SynchronizedSensorFrame(
            metadata=self.meta,
            packets_by_sensor_id={},
            missing_sensor_ids=("camera_front", "lidar_top", "radar_front"),
            synchronization_tolerance_seconds=0.0
        )
        sync_frame = SynchronizedMeasurements(
            contract=contract,
            measurements_by_sensor_id={}
        )
        
        snapshot = self.pipeline.process(sync_frame, self.ego_state)
        
        self.assertFalse(snapshot.sensor_status.camera_available)
        self.assertFalse(snapshot.sensor_status.lidar_available)
        self.assertFalse(snapshot.sensor_status.radar_available)
        self.assertTrue(snapshot.sensor_status.is_fully_degraded)
        
        # Should not produce tracks or lanes if no sensor available
        self.assertEqual(len(snapshot.tracked_objects), 0)
        self.assertEqual(len(snapshot.lane_boundaries), 0)

if __name__ == '__main__':
    unittest.main()
