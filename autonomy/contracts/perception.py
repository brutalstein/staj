from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

@dataclass
class TrackedObject:
    """Represents a dynamically tracked object (vehicle, pedestrian, etc.)"""
    object_id: str
    class_name: str  # e.g., 'vehicle', 'pedestrian'
    position_x: float  # Ego-relative X (FLU)
    position_y: float  # Ego-relative Y (FLU)
    velocity_x: float
    velocity_y: float
    heading: float     # Radians
    confidence: float

@dataclass
class LaneBoundary:
    """Represents a detected lane boundary"""
    lane_id: str
    boundary_type: str # e.g., 'solid', 'dashed'
    points: List[Tuple[float, float]] # List of (X, Y) points in Ego-FLU coordinates
    confidence: float

@dataclass
class SensorDegradationStatus:
    """Mask representing the health/availability of sensor modalities"""
    camera_available: bool = True
    lidar_available: bool = True
    radar_available: bool = True
    
    @property
    def is_fully_degraded(self) -> bool:
        return not (self.camera_available or self.lidar_available or self.radar_available)

@dataclass
class WorldModelSnapshot:
    """
    The output of the perception pipeline: a fused representation of the ego vehicle's surroundings.
    """
    timestamp: float
    frame_id: int
    tracked_objects: List[TrackedObject] = field(default_factory=list)
    lane_boundaries: List[LaneBoundary] = field(default_factory=list)
    sensor_status: SensorDegradationStatus = field(default_factory=SensorDegradationStatus)
