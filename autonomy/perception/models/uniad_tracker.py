import logging
import uuid
import random
from typing import Dict, Any, List
from autonomy.contracts.perception import TrackedObject

logger = logging.getLogger(__name__)

class UniADTrackerModel:
    """
    Mock baseline for UniAD (Unified Autonomous Driving) tracking component.
    """
    
    def __init__(self):
        self.inference_count = 0
        # Keep track of mock objects to simulate persistence
        self._mock_objects: List[TrackedObject] = []
        
    def _initialize_mock_objects(self):
        if not self._mock_objects:
            self._mock_objects = [
                TrackedObject(
                    object_id=str(uuid.uuid4())[:8],
                    class_name="vehicle",
                    position_x=10.0,
                    position_y=0.0,
                    velocity_x=5.0,
                    velocity_y=0.0,
                    heading=0.0,
                    confidence=0.9
                ),
                TrackedObject(
                    object_id=str(uuid.uuid4())[:8],
                    class_name="pedestrian",
                    position_x=5.0,
                    position_y=3.0,
                    velocity_x=0.5,
                    velocity_y=-1.0,
                    heading=-1.57,
                    confidence=0.85
                )
            ]
            
    def infer(self, bev_features: Dict[str, Any]) -> List[TrackedObject]:
        """
        Extracts and tracks dynamic objects from BEV features over time.
        
        Args:
            bev_features: The fused BEV feature map
            
        Returns:
            List of detected and tracked TrackedObject instances.
        """
        self.inference_count += 1
        self._initialize_mock_objects()
        
        # Simulate motion
        for obj in self._mock_objects:
            obj.position_x += obj.velocity_x * 0.1  # assuming ~10Hz
            obj.position_y += obj.velocity_y * 0.1
            
            # introduce small noise
            obj.position_x += random.uniform(-0.1, 0.1)
            obj.position_y += random.uniform(-0.1, 0.1)
            
        if bev_features.get("bev_grid_valid") or bev_features.get("detection_valid"):
            return self._mock_objects
        return []
