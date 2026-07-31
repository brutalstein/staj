import logging
import time
from typing import Dict, Any, List

from autonomy.sensing.synchronization import SynchronizedMeasurements
from autonomy.contracts.localization import EgoState
from autonomy.contracts.perception import WorldModelSnapshot, SensorDegradationStatus

from autonomy.perception.preprocessing.camera import CameraPreprocessor
from autonomy.perception.preprocessing.lidar import LidarPreprocessor
from autonomy.perception.preprocessing.radar import RadarPreprocessor

from autonomy.perception.models.bev_fusion import BEVFusionModel
from autonomy.perception.models.rcbevdet import RCBEVDetModel
from autonomy.perception.models.map_tr_v2 import MapTRv2Model
from autonomy.perception.models.uniad_tracker import UniADTrackerModel

logger = logging.getLogger(__name__)

class PerceptionPipeline:
    """
    Main pipeline for multi-sensor BEV and World Model generation.
    Orchestrates preprocessors and perception models.
    """
    
    def __init__(self):
        # Preprocessors
        self.camera_prep = CameraPreprocessor()
        self.lidar_prep = LidarPreprocessor()
        self.radar_prep = RadarPreprocessor()
        
        # Models
        self.bev_fusion = BEVFusionModel()
        self.rcbevdet = RCBEVDetModel()
        self.map_tr = MapTRv2Model()
        self.tracker = UniADTrackerModel()
        
    def process(self, sensor_frame: SynchronizedMeasurements, ego_state: EgoState) -> WorldModelSnapshot:
        """
        Executes the perception pipeline for a single synchronized frame.
        """
        logger.debug(f"Perception pipeline processing frame {sensor_frame.contract.metadata.simulation_frame}")
        
        camera_features = []
        lidar_features = []
        radar_features = []
        
        # 1. Preprocessing & Sensor Modality Masking
        for measurement in sensor_frame.measurements_by_sensor_id.values():
            # We assume basic naming conventions for sensor_ids
            if "camera" in measurement.sensor_id:
                camera_features.append(self.camera_prep.process(measurement))
            elif "lidar" in measurement.sensor_id:
                lidar_features.append(self.lidar_prep.process(measurement))
            elif "radar" in measurement.sensor_id:
                radar_features.append(self.radar_prep.process(measurement))
                
        # Determine sensor degradation status
        status = SensorDegradationStatus(
            camera_available=len(camera_features) > 0,
            lidar_available=len(lidar_features) > 0,
            radar_available=len(radar_features) > 0
        )
        
        # 2. Sensor Fusion (Availability-aware)
        fused_bev_features = {}
        
        # Priority 1: BEVFusion (Camera + LiDAR)
        if status.camera_available and status.lidar_available:
            fused_bev_features = self.bev_fusion.fuse(camera_features, lidar_features)
        
        # Priority 2: RCBEVDet (Radar + Camera) if LiDAR is missing
        elif status.camera_available and status.radar_available:
            fused_bev_features = self.rcbevdet.infer(camera_features, radar_features)
            logger.warning("LiDAR unavailable, falling back to Radar-Camera BEV fusion.")
            
        elif status.camera_available:
            # Just camera features (mocking an implicit camera-only BEV encoder)
            fused_bev_features = {"bev_grid_valid": True, "source": "camera_only"}
            logger.warning("Only Camera available for BEV fusion.")
            
        else:
            logger.error("Insufficient sensors for full BEV perception.")
            fused_bev_features = {"bev_grid_valid": False}
            
        # 3. Map Extraction
        lane_boundaries = self.map_tr.infer(fused_bev_features)
        
        # 4. Multi-Object Tracking & Temporal Consistency
        tracked_objects = self.tracker.infer(fused_bev_features)
        
        # 5. Build WorldModelSnapshot
        snapshot = WorldModelSnapshot(
            timestamp=time.time(), # Mock timestamp, or use sensor_frame.contract.metadata.timestamp_seconds if available
            frame_id=sensor_frame.contract.metadata.simulation_frame,
            tracked_objects=tracked_objects,
            lane_boundaries=lane_boundaries,
            sensor_status=status
        )
        
        return snapshot
