#!/usr/bin/env python3
"""
Complete Trackpad Multi-Touch Gesture Visualizer
Pure Python with pygame - No browser needed!
"""

import asyncio
import time
import json
import platform
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from evdev import InputDevice, categorize, ecodes
import pygame
import sys
import os

# Colors for different fingers
COLORS = [
    (0, 255, 136),   # Green
    (255, 136, 0),   # Orange
    (136, 0, 255),   # Purple
    (0, 255, 255),   # Cyan
    (255, 0, 136),   # Pink
    (255, 255, 0),   # Yellow
    (0, 136, 255),   # Blue
    (255, 0, 0),     # Red
    (0, 255, 0),     # Lime
    (255, 0, 255),   # Magenta
]

@dataclass
class TouchPoint:
    """Single touch point"""
    x: float
    y: float
    timestamp: float
    timestamp_ns: int

@dataclass
class GestureQuality:
    """Quality metrics for a gesture"""
    is_valid: bool
    point_count: int
    duration: float
    min_points_met: bool
    min_duration_met: bool
    reason: Optional[str] = None

class GestureTrack:
    """Track for a single finger"""
    def __init__(self, finger_id: int, color: tuple):
        self.finger_id = finger_id
        self.points: List[TouchPoint] = []
        self.color = color
        self.is_active = True
        
    def add_point(self, x: float, y: float, timestamp: float, timestamp_ns: int):
        """Add a point to this track"""
        self.points.append(TouchPoint(x, y, timestamp, timestamp_ns))
    
    def calculate_stats(self) -> dict:
        """Calculate statistics for this gesture"""
        if len(self.points) < 2:
            return {}
        
        # Calculate velocities
        velocities = []
        for i in range(1, len(self.points)):
            dt = (self.points[i].timestamp - self.points[i-1].timestamp)
            if dt > 0:
                dx = self.points[i].x - self.points[i-1].x
                dy = self.points[i].y - self.points[i-1].y
                distance = (dx**2 + dy**2) ** 0.5
                velocity = distance / dt
                velocities.append(velocity)
        
        duration = self.points[-1].timestamp - self.points[0].timestamp
        
        return {
            'finger_id': self.finger_id,
            'points': len(self.points),
            'duration': f"{duration:.3f}s",
            'avg_velocity': f"{sum(velocities)/len(velocities):.2f}" if velocities else "0",
            'max_velocity': f"{max(velocities):.2f}" if velocities else "0",
        }
    
    def validate_quality(self, min_points: int = 10, min_duration: float = 0.1) -> GestureQuality:
        """Validate gesture quality based on minimum requirements"""
        point_count = len(self.points)
        duration = 0.0
        
        if point_count >= 2:
            duration = self.points[-1].timestamp - self.points[0].timestamp
        
        min_points_met = point_count >= min_points
        min_duration_met = duration >= min_duration
        is_valid = min_points_met and min_duration_met
        
        reason = None
        if not is_valid:
            if not min_points_met:
                reason = f"Too few points ({point_count} < {min_points})"
            elif not min_duration_met:
                reason = f"Too short ({duration:.3f}s < {min_duration}s)"
        
        return GestureQuality(
            is_valid=is_valid,
            point_count=point_count,
            duration=duration,
            min_points_met=min_points_met,
            min_duration_met=min_duration_met,
            reason=reason
        )


class FeatureExtractor:
    """Extract behavioral biometric features from gesture tracks"""
    
    def __init__(self):
        pass
    
    def calculate_velocity(self, points: List[TouchPoint]) -> List[float]:
        """
        Calculate velocity at each point.
        Velocity = distance / time between consecutive points.
        Requirements: 4.1
        """
        if len(points) < 2:
            return []
        
        velocities = []
        for i in range(1, len(points)):
            dt = points[i].timestamp - points[i-1].timestamp
            if dt > 0:
                dx = points[i].x - points[i-1].x
                dy = points[i].y - points[i-1].y
                distance = (dx**2 + dy**2) ** 0.5
                velocity = distance / dt
                velocities.append(velocity)
            else:
                # Handle zero time delta (same timestamp)
                velocities.append(0.0)
        
        return velocities
    
    def calculate_acceleration(self, velocities: List[float], points: List[TouchPoint]) -> List[float]:
        """
        Calculate acceleration from velocity changes.
        Acceleration = (velocity[i] - velocity[i-1]) / time_delta
        Requirements: 4.2
        """
        if len(velocities) < 2 or len(points) < 3:
            return []
        
        accelerations = []
        for i in range(1, len(velocities)):
            # Time delta between velocity measurements
            dt = points[i+1].timestamp - points[i].timestamp
            if dt > 0:
                dv = velocities[i] - velocities[i-1]
                acceleration = dv / dt
                accelerations.append(acceleration)
            else:
                accelerations.append(0.0)
        
        return accelerations
    
    def calculate_curvature(self, points: List[TouchPoint]) -> List[float]:
        """
        Calculate curvature (direction changes) at each point.
        Uses angle between consecutive vectors.
        Requirements: 4.3
        """
        if len(points) < 3:
            return []
        
        curvatures = []
        for i in range(1, len(points) - 1):
            # Vector from point i-1 to i
            v1_x = points[i].x - points[i-1].x
            v1_y = points[i].y - points[i-1].y
            
            # Vector from point i to i+1
            v2_x = points[i+1].x - points[i].x
            v2_y = points[i+1].y - points[i].y
            
            # Calculate magnitudes
            mag1 = (v1_x**2 + v1_y**2) ** 0.5
            mag2 = (v2_x**2 + v2_y**2) ** 0.5
            
            if mag1 > 0 and mag2 > 0:
                # Dot product
                dot = v1_x * v2_x + v1_y * v2_y
                # Cross product (z-component in 2D)
                cross = v1_x * v2_y - v1_y * v2_x
                
                # Angle using atan2 for signed angle
                import math
                angle = math.atan2(cross, dot)
                curvature = abs(angle)
                curvatures.append(curvature)
            else:
                # Zero-length vector, no curvature
                curvatures.append(0.0)
        
        return curvatures
    
    def calculate_path_length(self, points: List[TouchPoint]) -> float:
        """
        Calculate total path length (sum of distances between consecutive points).
        Requirements: 4.4
        """
        if len(points) < 2:
            return 0.0
        
        total_length = 0.0
        for i in range(1, len(points)):
            dx = points[i].x - points[i-1].x
            dy = points[i].y - points[i-1].y
            distance = (dx**2 + dy**2) ** 0.5
            total_length += distance
        
        return total_length
    
    def calculate_bounding_box(self, points: List[TouchPoint]) -> dict:
        """
        Calculate bounding box dimensions (min/max x and y).
        Requirements: 4.4
        """
        if not points:
            return {'min_x': 0, 'max_x': 0, 'min_y': 0, 'max_y': 0, 'width': 0, 'height': 0}
        
        x_coords = [p.x for p in points]
        y_coords = [p.y for p in points]
        
        min_x = min(x_coords)
        max_x = max(x_coords)
        min_y = min(y_coords)
        max_y = max(y_coords)
        
        return {
            'min_x': min_x,
            'max_x': max_x,
            'min_y': min_y,
            'max_y': max_y,
            'width': max_x - min_x,
            'height': max_y - min_y
        }
    
    def extract_spatial_features(self, track: GestureTrack) -> dict:
        """
        Extract all spatial features from a gesture track.
        Returns: velocities, accelerations, curvatures, path_length, bounding_box
        """
        points = track.points
        
        # Calculate all spatial features
        velocities = self.calculate_velocity(points)
        accelerations = self.calculate_acceleration(velocities, points)
        curvatures = self.calculate_curvature(points)
        path_length = self.calculate_path_length(points)
        bounding_box = self.calculate_bounding_box(points)
        
        return {
            'velocities': velocities,
            'accelerations': accelerations,
            'curvatures': curvatures,
            'path_length': path_length,
            'bounding_box': bounding_box
        }
    
    def calculate_rhythm_patterns(self, points: List[TouchPoint]) -> dict:
        """
        Calculate rhythm patterns (timing between strokes/segments).
        Analyzes temporal patterns in the gesture.
        Requirements: 4.5
        """
        if len(points) < 2:
            return {
                'inter_point_intervals': [],
                'avg_interval': 0.0,
                'interval_variance': 0.0,
                'rhythm_score': 0.0
            }
        
        # Calculate time intervals between consecutive points
        intervals = []
        for i in range(1, len(points)):
            interval = points[i].timestamp - points[i-1].timestamp
            intervals.append(interval)
        
        # Calculate statistics
        avg_interval = sum(intervals) / len(intervals) if intervals else 0.0
        
        # Calculate variance
        if len(intervals) > 1:
            variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)
        else:
            variance = 0.0
        
        # Rhythm score: lower variance = more consistent rhythm (0-1 scale)
        # Normalize by average to get coefficient of variation
        if avg_interval > 0:
            cv = (variance ** 0.5) / avg_interval
            rhythm_score = 1.0 / (1.0 + cv)  # Higher score = more consistent
        else:
            rhythm_score = 0.0
        
        return {
            'inter_point_intervals': intervals,
            'avg_interval': avg_interval,
            'interval_variance': variance,
            'rhythm_score': rhythm_score
        }
    
    def calculate_pressure_variations(self, points: List[TouchPoint]) -> dict:
        """
        Calculate pressure variations if pressure data is available.
        Requirements: 4.6
        """
        # Check if any points have pressure data
        pressures = [p.pressure for p in points if hasattr(p, 'pressure') and p.pressure is not None]
        
        if not pressures:
            return {
                'has_pressure': False,
                'pressures': [],
                'avg_pressure': 0.0,
                'max_pressure': 0.0,
                'min_pressure': 0.0,
                'pressure_variance': 0.0
            }
        
        avg_pressure = sum(pressures) / len(pressures)
        max_pressure = max(pressures)
        min_pressure = min(pressures)
        
        # Calculate variance
        if len(pressures) > 1:
            variance = sum((x - avg_pressure) ** 2 for x in pressures) / len(pressures)
        else:
            variance = 0.0
        
        return {
            'has_pressure': True,
            'pressures': pressures,
            'avg_pressure': avg_pressure,
            'max_pressure': max_pressure,
            'min_pressure': min_pressure,
            'pressure_variance': variance
        }
    
    def calculate_multi_finger_coordination(self, tracks: List[GestureTrack]) -> dict:
        """
        Calculate multi-finger coordination metrics.
        Analyzes how multiple fingers move together.
        Requirements: 4.6
        """
        if len(tracks) < 2:
            return {
                'finger_count': len(tracks),
                'has_multi_finger': False,
                'avg_finger_spacing': 0.0,
                'coordination_score': 0.0,
                'simultaneous_movement_ratio': 0.0
            }
        
        # Calculate average spacing between fingers
        # Use the first point of each track as reference
        finger_positions = []
        for track in tracks:
            if track.points:
                first_point = track.points[0]
                finger_positions.append((first_point.x, first_point.y))
        
        # Calculate pairwise distances
        distances = []
        for i in range(len(finger_positions)):
            for j in range(i + 1, len(finger_positions)):
                dx = finger_positions[i][0] - finger_positions[j][0]
                dy = finger_positions[i][1] - finger_positions[j][1]
                distance = (dx**2 + dy**2) ** 0.5
                distances.append(distance)
        
        avg_spacing = sum(distances) / len(distances) if distances else 0.0
        
        # Calculate coordination score based on timing overlap
        # Find the time range where all fingers are active
        if all(track.points for track in tracks):
            start_times = [track.points[0].timestamp for track in tracks]
            end_times = [track.points[-1].timestamp for track in tracks]
            
            latest_start = max(start_times)
            earliest_end = min(end_times)
            
            # Overlap duration
            overlap = max(0, earliest_end - latest_start)
            
            # Total duration (from first start to last end)
            total_duration = max(end_times) - min(start_times)
            
            # Coordination score: ratio of overlap to total duration
            coordination_score = overlap / total_duration if total_duration > 0 else 0.0
            
            # Simultaneous movement ratio (how much time all fingers moved together)
            simultaneous_ratio = coordination_score
        else:
            coordination_score = 0.0
            simultaneous_ratio = 0.0
        
        return {
            'finger_count': len(tracks),
            'has_multi_finger': True,
            'avg_finger_spacing': avg_spacing,
            'coordination_score': coordination_score,
            'simultaneous_movement_ratio': simultaneous_ratio
        }
    
    def extract_behavioral_features(self, track: GestureTrack, all_tracks: Optional[List[GestureTrack]] = None) -> dict:
        """
        Extract all behavioral features from a gesture track.
        Returns: rhythm patterns, pressure variations, multi-finger coordination
        """
        points = track.points
        
        # Calculate behavioral features
        rhythm = self.calculate_rhythm_patterns(points)
        pressure = self.calculate_pressure_variations(points)
        
        # Multi-finger coordination requires all tracks
        if all_tracks and len(all_tracks) > 1:
            coordination = self.calculate_multi_finger_coordination(all_tracks)
        else:
            coordination = self.calculate_multi_finger_coordination([track])
        
        return {
            'rhythm': rhythm,
            'pressure': pressure,
            'coordination': coordination
        }
    
    def normalize_value(self, value: float, min_val: float, max_val: float) -> float:
        """
        Normalize a value to 0-1 range.
        Handles edge cases where min == max.
        """
        if max_val == min_val:
            return 0.5  # Middle value if no range
        return (value - min_val) / (max_val - min_val)
    
    def build_feature_vector(self, track: GestureTrack, all_tracks: Optional[List[GestureTrack]] = None,
                            screen_width: float = 1920, screen_height: float = 1080) -> List[float]:
        """
        Build a 25-element normalized feature vector from a gesture track.
        All features are normalized to 0-1 range.
        Missing values (pressure, multi-finger) are handled with defaults.
        
        Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6
        
        Feature vector structure (25 elements):
        - Spatial features (10): path_length, bbox_width, bbox_height, avg_curvature, 
          max_curvature, curvature_variance, start_x, start_y, end_x, end_y
        - Temporal features (10): duration, avg_velocity, max_velocity, velocity_variance,
          avg_acceleration, max_acceleration, acceleration_variance, rhythm_score,
          avg_interval, interval_variance
        - Multi-finger features (5): finger_count, avg_finger_spacing, coordination_score,
          simultaneous_movement_ratio, avg_pressure
        """
        import math
        
        points = track.points
        if len(points) < 2:
            # Return zero vector for invalid tracks
            return [0.0] * 25
        
        # Extract all features
        spatial = self.extract_spatial_features(track)
        behavioral = self.extract_behavioral_features(track, all_tracks)
        
        # --- Spatial Features (10) ---
        
        # 1. Path length (normalize by screen diagonal)
        screen_diagonal = math.sqrt(screen_width**2 + screen_height**2)
        path_length_norm = min(1.0, spatial['path_length'] / screen_diagonal)
        
        # 2-3. Bounding box dimensions (normalize by screen dimensions)
        bbox_width_norm = min(1.0, spatial['bounding_box']['width'] / screen_width)
        bbox_height_norm = min(1.0, spatial['bounding_box']['height'] / screen_height)
        
        # 4-6. Curvature statistics (normalize by pi)
        curvatures = spatial['curvatures']
        if curvatures:
            avg_curvature = sum(curvatures) / len(curvatures)
            max_curvature = max(curvatures)
            curvature_variance = sum((c - avg_curvature) ** 2 for c in curvatures) / len(curvatures)
            
            avg_curvature_norm = min(1.0, avg_curvature / math.pi)
            max_curvature_norm = min(1.0, max_curvature / math.pi)
            curvature_variance_norm = min(1.0, curvature_variance / (math.pi ** 2))
        else:
            avg_curvature_norm = 0.0
            max_curvature_norm = 0.0
            curvature_variance_norm = 0.0
        
        # 7-10. Start and end positions (already normalized by screen dimensions)
        start_x_norm = min(1.0, max(0.0, points[0].x / screen_width))
        start_y_norm = min(1.0, max(0.0, points[0].y / screen_height))
        end_x_norm = min(1.0, max(0.0, points[-1].x / screen_width))
        end_y_norm = min(1.0, max(0.0, points[-1].y / screen_height))
        
        # --- Temporal Features (10) ---
        
        # 11. Duration (normalize by 5 seconds max)
        duration = points[-1].timestamp - points[0].timestamp
        duration_norm = min(1.0, duration / 5.0)
        
        # 12-14. Velocity statistics (normalize by screen diagonal per second)
        velocities = spatial['velocities']
        if velocities:
            avg_velocity = sum(velocities) / len(velocities)
            max_velocity = max(velocities)
            velocity_variance = sum((v - avg_velocity) ** 2 for v in velocities) / len(velocities)
            
            avg_velocity_norm = min(1.0, avg_velocity / screen_diagonal)
            max_velocity_norm = min(1.0, max_velocity / screen_diagonal)
            velocity_variance_norm = min(1.0, velocity_variance / (screen_diagonal ** 2))
        else:
            avg_velocity_norm = 0.0
            max_velocity_norm = 0.0
            velocity_variance_norm = 0.0
        
        # 15-17. Acceleration statistics (normalize by screen diagonal per second^2)
        accelerations = spatial['accelerations']
        if accelerations:
            avg_acceleration = sum(accelerations) / len(accelerations)
            max_acceleration = max(abs(a) for a in accelerations)
            acceleration_variance = sum((a - avg_acceleration) ** 2 for a in accelerations) / len(accelerations)
            
            avg_acceleration_norm = min(1.0, abs(avg_acceleration) / screen_diagonal)
            max_acceleration_norm = min(1.0, max_acceleration / screen_diagonal)
            acceleration_variance_norm = min(1.0, acceleration_variance / (screen_diagonal ** 2))
        else:
            avg_acceleration_norm = 0.0
            max_acceleration_norm = 0.0
            acceleration_variance_norm = 0.0
        
        # 18. Rhythm score (already 0-1)
        rhythm_score_norm = behavioral['rhythm']['rhythm_score']
        
        # 19-20. Interval statistics (normalize by 1 second)
        avg_interval = behavioral['rhythm']['avg_interval']
        interval_variance = behavioral['rhythm']['interval_variance']
        avg_interval_norm = min(1.0, avg_interval / 1.0)
        interval_variance_norm = min(1.0, interval_variance / 1.0)
        
        # --- Multi-finger Features (5) ---
        
        # 21. Finger count (normalize by 10 max fingers)
        finger_count = behavioral['coordination']['finger_count']
        finger_count_norm = min(1.0, finger_count / 10.0)
        
        # 22. Average finger spacing (normalize by screen diagonal)
        avg_spacing = behavioral['coordination']['avg_finger_spacing']
        avg_spacing_norm = min(1.0, avg_spacing / screen_diagonal)
        
        # 23. Coordination score (already 0-1)
        coordination_score_norm = behavioral['coordination']['coordination_score']
        
        # 24. Simultaneous movement ratio (already 0-1)
        simultaneous_ratio_norm = behavioral['coordination']['simultaneous_movement_ratio']
        
        # 25. Average pressure (normalize by 100 if available, else 0)
        if behavioral['pressure']['has_pressure']:
            avg_pressure = behavioral['pressure']['avg_pressure']
            avg_pressure_norm = min(1.0, avg_pressure / 100.0)
        else:
            avg_pressure_norm = 0.0  # Missing value handled as 0
        
        # Build the 25-element feature vector
        feature_vector = [
            # Spatial (10)
            path_length_norm,
            bbox_width_norm,
            bbox_height_norm,
            avg_curvature_norm,
            max_curvature_norm,
            curvature_variance_norm,
            start_x_norm,
            start_y_norm,
            end_x_norm,
            end_y_norm,
            # Temporal (10)
            duration_norm,
            avg_velocity_norm,
            max_velocity_norm,
            velocity_variance_norm,
            avg_acceleration_norm,
            max_acceleration_norm,
            acceleration_variance_norm,
            rhythm_score_norm,
            avg_interval_norm,
            interval_variance_norm,
            # Multi-finger (5)
            finger_count_norm,
            avg_spacing_norm,
            coordination_score_norm,
            simultaneous_ratio_norm,
            avg_pressure_norm
        ]
        
        return feature_vector
    
    def extract_all_features(self, track: GestureTrack, all_tracks: Optional[List[GestureTrack]] = None,
                            screen_width: float = 1920, screen_height: float = 1080) -> dict:
        """
        Extract all features (spatial, behavioral, and feature vector) from a gesture track.
        This is the main method to use for complete feature extraction.
        
        Returns a dictionary with:
        - spatial: spatial features (velocities, accelerations, curvatures, etc.)
        - behavioral: behavioral features (rhythm, pressure, coordination)
        - feature_vector: 25-element normalized feature vector
        """
        spatial = self.extract_spatial_features(track)
        behavioral = self.extract_behavioral_features(track, all_tracks)
        feature_vector = self.build_feature_vector(track, all_tracks, screen_width, screen_height)
        
        return {
            'spatial': spatial,
            'behavioral': behavioral,
            'feature_vector': feature_vector
        }

class TrackpadVisualizer:
    """Main visualizer class"""
    
    def __init__(self, device_path="/dev/input/event14", width=1200, height=800, 
                 min_points: int = 10, min_duration: float = 0.1, training_mode: bool = False,
                 target_samples: int = 50):
        self.device_path = device_path
        self.width = width
        self.height = height
        self.device = None
        
        # Quality validation thresholds
        self.min_points = min_points
        self.min_duration = min_duration
        
        # Trackpad dimensions
        self.abs_x_min = 0
        self.abs_x_max = 1
        self.abs_y_min = 0
        self.abs_y_max = 1
        
        # Device metadata
        self.device_name = None
        self.device_vendor = None
        self.device_product = None
        
        # Gesture tracking
        self.gesture_tracks: Dict[int, GestureTrack] = {}
        self.completed_tracks: List[GestureTrack] = []  # Tracks that are done but still visible
        self.is_capturing = False
        self.saved_gestures: List[GestureTrack] = []
        
        # Session management
        self.session_id = int(time.time())
        self.session_start_time = time.time()
        self.capture_count = 0
        self.valid_capture_count = 0
        self.invalid_capture_count = 0
        
        # Training mode (Requirements: 1.1-1.6, 3.1-3.6)
        self.training_mode = training_mode
        self.target_samples = target_samples
        self.training_samples_collected = 0
        self.last_feedback_message = ""
        self.last_feedback_time = 0
        self.feedback_color = (255, 255, 255)
        
        # Pygame
        self.screen = None
        self.clock = None
        self.font = None
        self.small_font = None
        self.large_font = None
    
    def validate_exported_data(self, data: dict) -> tuple[bool, List[str]]:
        """
        Validate exported JSON data structure, completeness, and feature ranges.
        
        Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
        
        Returns:
            tuple: (is_valid, list_of_errors)
        """
        errors = []
        
        # Verify JSON structure (Requirements: 3.1)
        if not isinstance(data, dict):
            errors.append("Data is not a dictionary")
            return False, errors
        
        # Check top-level keys
        required_top_keys = ['metadata', 'gestures']
        for key in required_top_keys:
            if key not in data:
                errors.append(f"Missing top-level key: {key}")
        
        if errors:
            return False, errors
        
        # Validate metadata structure (Requirements: 3.2)
        metadata = data.get('metadata', {})
        required_metadata_keys = [
            'session_id', 'capture_timestamp', 'device', 
            'screen_dimensions', 'trackpad_dimensions'
        ]
        for key in required_metadata_keys:
            if key not in metadata:
                errors.append(f"Missing metadata key: {key}")
        
        # Validate device info
        if 'device' in metadata:
            device = metadata['device']
            required_device_keys = ['name', 'vendor', 'product', 'path']
            for key in required_device_keys:
                if key not in device:
                    errors.append(f"Missing device key: {key}")
        
        # Validate dimensions
        if 'screen_dimensions' in metadata:
            screen = metadata['screen_dimensions']
            if 'width' not in screen or 'height' not in screen:
                errors.append("Missing screen dimensions (width/height)")
        
        if 'trackpad_dimensions' in metadata:
            trackpad = metadata['trackpad_dimensions']
            required_trackpad_keys = ['x_min', 'x_max', 'y_min', 'y_max']
            for key in required_trackpad_keys:
                if key not in trackpad:
                    errors.append(f"Missing trackpad dimension: {key}")
        
        # Validate gestures array (Requirements: 3.2, 3.3)
        gestures = data.get('gestures', [])
        if not isinstance(gestures, list):
            errors.append("Gestures is not a list")
            return False, errors
        
        if len(gestures) == 0:
            errors.append("No gestures in data")
        
        # Validate each gesture
        for i, gesture in enumerate(gestures):
            gesture_errors = self._validate_gesture(gesture, i)
            errors.extend(gesture_errors)
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def _validate_gesture(self, gesture: dict, index: int) -> List[str]:
        """
        Validate a single gesture's structure and data completeness.
        
        Requirements: 3.2, 3.3, 3.4
        """
        errors = []
        prefix = f"Gesture {index}"
        
        # Check required keys
        required_keys = ['gesture_id', 'finger_id', 'quality', 'points', 'features']
        for key in required_keys:
            if key not in gesture:
                errors.append(f"{prefix}: Missing key '{key}'")
        
        if errors:
            return errors
        
        # Validate quality metrics (Requirements: 3.4)
        quality = gesture.get('quality', {})
        required_quality_keys = [
            'is_valid', 'point_count', 'duration', 
            'min_points_met', 'min_duration_met'
        ]
        for key in required_quality_keys:
            if key not in quality:
                errors.append(f"{prefix}: Missing quality metric '{key}'")
        
        # Validate points array (Requirements: 3.2)
        points = gesture.get('points', [])
        if not isinstance(points, list):
            errors.append(f"{prefix}: Points is not a list")
        elif len(points) == 0:
            errors.append(f"{prefix}: No points in gesture")
        else:
            # Check first point structure
            first_point = points[0]
            required_point_keys = ['x', 'y', 'timestamp', 'timestamp_ns']
            for key in required_point_keys:
                if key not in first_point:
                    errors.append(f"{prefix}: Point missing key '{key}'")
        
        # Validate features structure (Requirements: 3.3)
        features = gesture.get('features', {})
        if not isinstance(features, dict):
            errors.append(f"{prefix}: Features is not a dictionary")
        else:
            # Check feature categories
            required_feature_keys = ['spatial', 'behavioral', 'feature_vector']
            for key in required_feature_keys:
                if key not in features:
                    errors.append(f"{prefix}: Missing feature category '{key}'")
            
            # Validate spatial features
            if 'spatial' in features:
                spatial = features['spatial']
                required_spatial = [
                    'path_length', 'bounding_box', 'velocities', 
                    'accelerations', 'curvatures'
                ]
                for key in required_spatial:
                    if key not in spatial:
                        errors.append(f"{prefix}: Missing spatial feature '{key}'")
            
            # Validate behavioral features
            if 'behavioral' in features:
                behavioral = features['behavioral']
                required_behavioral = ['rhythm', 'pressure', 'coordination']
                for key in required_behavioral:
                    if key not in behavioral:
                        errors.append(f"{prefix}: Missing behavioral feature '{key}'")
            
            # Validate feature vector
            if 'feature_vector' in features:
                feature_vector = features['feature_vector']
                if not isinstance(feature_vector, list):
                    errors.append(f"{prefix}: Feature vector is not a list")
                elif len(feature_vector) != 25:
                    errors.append(f"{prefix}: Feature vector has {len(feature_vector)} elements, expected 25")
                else:
                    # Validate feature ranges (Requirements: 3.6)
                    range_errors = self._validate_feature_ranges(feature_vector, index)
                    errors.extend(range_errors)
        
        return errors
    
    def _validate_feature_ranges(self, feature_vector: List[float], gesture_index: int) -> List[str]:
        """
        Validate that all features in the feature vector are in valid ranges (0-1).
        
        Requirements: 3.6
        """
        errors = []
        prefix = f"Gesture {gesture_index}"
        
        for i, value in enumerate(feature_vector):
            # Check if value is a number
            if not isinstance(value, (int, float)):
                errors.append(f"{prefix}: Feature {i} is not a number: {value}")
                continue
            
            # Check if value is in valid range (0-1)
            if value < 0.0 or value > 1.0:
                errors.append(f"{prefix}: Feature {i} out of range [0,1]: {value:.4f}")
            
            # Check for NaN or infinity
            if value != value:  # NaN check
                errors.append(f"{prefix}: Feature {i} is NaN")
            elif value == float('inf') or value == float('-inf'):
                errors.append(f"{prefix}: Feature {i} is infinite")
        
        return errors
        
    def open_device(self) -> bool:
        """Open the trackpad device and collect metadata"""
        try:
            self.device = InputDevice(self.device_path)
            self.device_name = self.device.name
            
            # Extract vendor and product IDs if available
            try:
                # Device path format: /dev/input/eventX
                # We can get more info from the device
                self.device_vendor = f"0x{self.device.info.vendor:04x}" if hasattr(self.device.info, 'vendor') else "unknown"
                self.device_product = f"0x{self.device.info.product:04x}" if hasattr(self.device.info, 'product') else "unknown"
            except:
                self.device_vendor = "unknown"
                self.device_product = "unknown"
            
            print(f"✓ Opened: {self.device_name}")
            print(f"  Vendor: {self.device_vendor}, Product: {self.device_product}")
            
            # Get trackpad dimensions
            caps = self.device.capabilities(absinfo=True)
            if ecodes.EV_ABS in caps:
                abs_info = caps[ecodes.EV_ABS]
                for code, info in abs_info:
                    if code == ecodes.ABS_MT_POSITION_X:
                        self.abs_x_min = info.min
                        self.abs_x_max = info.max
                    elif code == ecodes.ABS_MT_POSITION_Y:
                        self.abs_y_min = info.min
                        self.abs_y_max = info.max
            
            print(f"  X: {self.abs_x_min} - {self.abs_x_max}")
            print(f"  Y: {self.abs_y_min} - {self.abs_y_max}")
            return True
            
        except PermissionError:
            print(f"✗ Permission denied: {self.device_path}")
            print("  Run: sudo python3 trackpad_visualizer.py")
            return False
        except Exception as e:
            print(f"✗ Error: {e}")
            return False
    
    def init_pygame(self):
        """Initialize pygame with hardware acceleration and fullscreen"""
        pygame.init()
        
        # Get display info for fullscreen
        display_info = pygame.display.Info()
        self.width = display_info.current_w
        self.height = display_info.current_h
        
        # Create fullscreen window with hardware acceleration
        self.screen = pygame.display.set_mode(
            (self.width, self.height),
            pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF
        )
        pygame.display.set_caption("Trackpad Multi-Touch Visualizer")
        
        # Hide mouse cursor
        pygame.mouse.set_visible(False)
        
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.large_font = pygame.font.Font(None, 72)
        
        print(f"✓ Pygame initialized fullscreen ({self.width}x{self.height}) with cursor hidden")
    
    def normalize_coords(self, x: int, y: int) -> tuple:
        """Normalize and scale coordinates to screen"""
        norm_x = (x - self.abs_x_min) / (self.abs_x_max - self.abs_x_min)
        norm_y = (y - self.abs_y_min) / (self.abs_y_max - self.abs_y_min)
        
        # Scale to screen with margins
        margin = 50
        screen_x = margin + norm_x * (self.width - 2 * margin)
        screen_y = margin + norm_y * (self.height - 2 * margin)
        
        return screen_x, screen_y
    
    def provide_quality_feedback(self, all_tracks: List[GestureTrack]):
        """
        Provide quality feedback for training mode.
        Shows feedback messages for too fast, too slow, too short gestures.
        Validates ALL tracks together as one complete gesture.
        
        In training mode, we're more lenient:
        - Accept clicks/taps (as few as 2 points)
        - Accept very short durations (as low as 0.01s)
        - Only reject if track has < 2 points (no movement at all)
        
        Requirements: 1.1-1.6
        """
        if not self.training_mode:
            return False
        
        current_time = time.time()
        
        # Check if we have any tracks
        if not all_tracks:
            self.last_feedback_message = "✗ NO GESTURE DETECTED"
            self.feedback_color = (255, 0, 0)
            print(f"✗ {self.last_feedback_message}")
            self.last_feedback_time = current_time
            return False
        
        # In training mode, be very lenient - accept almost anything with at least 2 points
        # This allows clicks, taps, and short gestures to be part of the training data
        all_valid = True
        invalid_tracks = []
        
        for track in all_tracks:
            # Only reject if track has less than 2 points (no movement at all)
            if len(track.points) < 2:
                all_valid = False
                invalid_tracks.append(track)
        
        if all_valid:
            self.last_feedback_message = "✓ GOOD GESTURE!"
            self.feedback_color = (0, 255, 0)
            self.training_samples_collected += 1
            print(f"✓ Sample {self.training_samples_collected}/{self.target_samples} collected ({len(all_tracks)} finger(s))")
        else:
            # Only reject if tracks have no movement
            self.last_feedback_message = "✗ NO MOVEMENT DETECTED"
            self.feedback_color = (255, 0, 0)
            print(f"✗ {self.last_feedback_message} - {len(invalid_tracks)} track(s) with < 2 points")
        
        self.last_feedback_time = current_time
        return all_valid
    
    def get_training_progress(self) -> float:
        """
        Get training progress as a percentage (0-1).
        
        Requirements: 1.1-1.6
        """
        if not self.training_mode or self.target_samples == 0:
            return 0.0
        return min(1.0, self.training_samples_collected / self.target_samples)
    
    def is_training_complete(self) -> bool:
        """
        Check if training data collection is complete.
        
        Requirements: 1.1-1.6
        """
        return self.training_mode and self.training_samples_collected >= self.target_samples
    
    def auto_save_training_sample(self):
        """
        Auto-save after each successful capture in training mode.
        Saves incrementally to avoid data loss.
        
        Requirements: 3.1-3.6
        """
        if not self.training_mode:
            return
        
        # Save to training-specific filename
        filename = f"training_session_{self.session_id}.json"
        
        # Collect all valid tracks
        all_tracks = []
        for track in self.saved_gestures:
            quality = track.validate_quality(self.min_points, self.min_duration)
            if quality.is_valid:
                all_tracks.append(track)
        
        if not all_tracks:
            return
        
        # Build metadata
        metadata = {
            'session_id': self.session_id,
            'session_start_time': self.session_start_time,
            'capture_timestamp': time.time(),
            'training_mode': True,
            'target_samples': self.target_samples,
            'samples_collected': self.training_samples_collected,
            'progress': self.get_training_progress(),
            'device': {
                'name': self.device_name,
                'vendor': self.device_vendor,
                'product': self.device_product,
                'path': self.device_path
            },
            'screen_dimensions': {
                'width': self.width,
                'height': self.height
            },
            'trackpad_dimensions': {
                'x_min': self.abs_x_min,
                'x_max': self.abs_x_max,
                'y_min': self.abs_y_min,
                'y_max': self.abs_y_max,
                'x_range': self.abs_x_max - self.abs_x_min,
                'y_range': self.abs_y_max - self.abs_y_min
            },
            'quality_thresholds': {
                'min_points': self.min_points,
                'min_duration': self.min_duration
            },
            'system_info': {
                'platform': platform.system(),
                'platform_release': platform.release(),
                'platform_version': platform.version(),
                'machine': platform.machine()
            }
        }
        
        # Initialize feature extractor
        feature_extractor = FeatureExtractor()
        
        # Build gesture data
        gestures = []
        for track in all_tracks:
            stats = track.calculate_stats()
            quality = track.validate_quality(self.min_points, self.min_duration)
            
            # Extract all features
            features = feature_extractor.extract_all_features(
                track, 
                all_tracks, 
                self.width, 
                self.height
            )
            
            gesture_data = {
                'gesture_id': f"{self.session_id}_{track.finger_id}_{int(track.points[0].timestamp_ns)}",
                'finger_id': track.finger_id,
                'quality': {
                    'is_valid': quality.is_valid,
                    'point_count': quality.point_count,
                    'duration': quality.duration,
                    'min_points_met': quality.min_points_met,
                    'min_duration_met': quality.min_duration_met,
                    'reason': quality.reason
                },
                'stats': stats,
                'points': [
                    {
                        'x': p.x,
                        'y': p.y,
                        'timestamp': p.timestamp,
                        'timestamp_ns': p.timestamp_ns
                    }
                    for p in track.points
                ],
                'features': {
                    'spatial': {
                        'path_length': features['spatial']['path_length'],
                        'bounding_box': features['spatial']['bounding_box'],
                        'velocities': features['spatial']['velocities'],
                        'accelerations': features['spatial']['accelerations'],
                        'curvatures': features['spatial']['curvatures'],
                        'velocity_stats': {
                            'avg': sum(features['spatial']['velocities']) / len(features['spatial']['velocities']) if features['spatial']['velocities'] else 0,
                            'max': max(features['spatial']['velocities']) if features['spatial']['velocities'] else 0,
                            'min': min(features['spatial']['velocities']) if features['spatial']['velocities'] else 0
                        },
                        'acceleration_stats': {
                            'avg': sum(features['spatial']['accelerations']) / len(features['spatial']['accelerations']) if features['spatial']['accelerations'] else 0,
                            'max': max(features['spatial']['accelerations']) if features['spatial']['accelerations'] else 0,
                            'min': min(features['spatial']['accelerations']) if features['spatial']['accelerations'] else 0
                        },
                        'curvature_stats': {
                            'avg': sum(features['spatial']['curvatures']) / len(features['spatial']['curvatures']) if features['spatial']['curvatures'] else 0,
                            'max': max(features['spatial']['curvatures']) if features['spatial']['curvatures'] else 0,
                            'min': min(features['spatial']['curvatures']) if features['spatial']['curvatures'] else 0
                        }
                    },
                    'behavioral': {
                        'rhythm': features['behavioral']['rhythm'],
                        'pressure': features['behavioral']['pressure'],
                        'coordination': features['behavioral']['coordination']
                    },
                    'feature_vector': features['feature_vector']
                }
            }
            gestures.append(gesture_data)
        
        data = {
            'metadata': metadata,
            'gestures': gestures
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"💾 Auto-saved: {filename} ({len(gestures)} samples)")
        except Exception as e:
            print(f"❌ Auto-save error: {e}")
    
    def draw_ui(self):
        """Draw UI elements"""
        # Background
        self.screen.fill((26, 26, 46))
        
        # Title
        if self.training_mode:
            title = self.font.render("Training Mode - Gesture Collection", True, (255, 200, 0))
        else:
            title = self.font.render("Trackpad Multi-Touch Visualizer", True, (100, 255, 255))
        self.screen.blit(title, (20, 20))
        
        # Training mode: Show progress prominently
        if self.training_mode:
            # Progress bar
            progress = self.get_training_progress()
            bar_width = 600
            bar_height = 40
            bar_x = (self.width - bar_width) // 2
            bar_y = 80
            
            # Background bar
            pygame.draw.rect(self.screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
            
            # Progress fill
            fill_width = int(bar_width * progress)
            if fill_width > 0:
                color = (0, 255, 0) if progress >= 1.0 else (100, 200, 255)
                pygame.draw.rect(self.screen, color, (bar_x, bar_y, fill_width, bar_height))
            
            # Border
            pygame.draw.rect(self.screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 2)
            
            # Progress text
            progress_text = self.font.render(
                f"{self.training_samples_collected} / {self.target_samples} samples",
                True, (255, 255, 255)
            )
            text_rect = progress_text.get_rect(center=(self.width // 2, bar_y + bar_height + 30))
            self.screen.blit(progress_text, text_rect)
            
            # Feedback message (show for 3 seconds)
            if self.last_feedback_message and (time.time() - self.last_feedback_time) < 3.0:
                feedback = self.large_font.render(self.last_feedback_message, True, self.feedback_color)
                feedback_rect = feedback.get_rect(center=(self.width // 2, self.height // 2))
                
                # Semi-transparent background
                padding = 20
                bg_rect = feedback_rect.inflate(padding * 2, padding * 2)
                s = pygame.Surface((bg_rect.width, bg_rect.height))
                s.set_alpha(200)
                s.fill((20, 20, 30))
                self.screen.blit(s, bg_rect)
                
                self.screen.blit(feedback, feedback_rect)
            
            # Completion message
            if self.is_training_complete():
                complete_msg = self.large_font.render("TRAINING COMPLETE!", True, (0, 255, 0))
                complete_rect = complete_msg.get_rect(center=(self.width // 2, self.height // 2 + 100))
                self.screen.blit(complete_msg, complete_rect)
                
                save_msg = self.font.render("Press S to save or Q to quit", True, (200, 200, 200))
                save_rect = save_msg.get_rect(center=(self.width // 2, self.height // 2 + 160))
                self.screen.blit(save_msg, save_rect)
        
        # Status
        status_color = (0, 255, 0) if self.is_capturing else (128, 128, 128)
        status_text = "CAPTURING" if self.is_capturing else "READY"
        status = self.small_font.render(f"Status: {status_text}", True, status_color)
        self.screen.blit(status, (20, 60))
        
        # Active fingers
        finger_count = len(self.gesture_tracks)
        fingers = self.small_font.render(f"Active Fingers: {finger_count}", True, (255, 255, 255))
        self.screen.blit(fingers, (20, 90))
        
        # Session info (only in non-training mode)
        if not self.training_mode:
            session_time = time.time() - self.session_start_time
            session_info = self.small_font.render(
                f"Session: {self.capture_count} captures ({self.valid_capture_count} valid, {self.invalid_capture_count} invalid)",
                True, (200, 200, 200)
            )
            self.screen.blit(session_info, (20, 120))
        
        # Quality thresholds
        quality_info = self.small_font.render(
            f"Quality: min {self.min_points} points, {self.min_duration}s duration",
            True, (150, 150, 150)
        )
        self.screen.blit(quality_info, (20, 145 if not self.training_mode else 120))
        
        # Instructions
        if self.training_mode:
            if self.is_capturing:
                instructions = [
                    "Drawing gesture...",
                    "Press SPACE when done to save",
                    "(All fingers will be saved as ONE sample)",
                    "",
                    "Press Q or ESC to quit"
                ]
            else:
                instructions = [
                    "Press SPACE to start capturing",
                    "Draw your gesture (1 or more fingers)",
                    "Press SPACE again to save as ONE sample",
                    "",
                    "Press Q or ESC to quit"
                ]
        else:
            instructions = [
                "Press SPACE to start/stop capture",
                "Press C to clear",
                "Press S to save gestures",
                "Press Q or ESC to quit",
                "",
                "Touch trackpad with multiple fingers!"
            ]
        
        y = self.height - 150
        for instruction in instructions:
            text = self.small_font.render(instruction, True, (150, 150, 150))
            self.screen.blit(text, (20, y))
            y += 25
        
        # Saved gestures count
        if self.saved_gestures and not self.training_mode:
            saved = self.small_font.render(f"Saved Gestures: {len(self.saved_gestures)}", True, (100, 255, 100))
            self.screen.blit(saved, (self.width - 250, 60))
    
    def draw_gesture_track(self, track: GestureTrack, is_active: bool = True):
        """Draw a single gesture track"""
        if len(track.points) < 2:
            return
        
        # Use dimmer color for inactive tracks
        color = track.color if is_active else tuple(c // 2 for c in track.color)
        
        # Draw path - use integer coordinates for speed
        points = [(int(p.x), int(p.y)) for p in track.points]
        if len(points) >= 2:
            # Draw thicker line
            pygame.draw.lines(self.screen, color, False, points, 4)
        
        # Draw start point (green circle)
        start_pos = (int(track.points[0].x), int(track.points[0].y))
        pygame.draw.circle(self.screen, (0, 255, 0) if is_active else (0, 128, 0), start_pos, 8)
        
        # Draw end point (red circle for inactive, yellow for active)
        end_pos = (int(track.points[-1].x), int(track.points[-1].y))
        end_color = (255, 255, 0) if is_active else (255, 0, 0)
        pygame.draw.circle(self.screen, end_color, end_pos, 8)
        
        # Draw finger ID
        label = self.small_font.render(f"F{track.finger_id}", True, color)
        self.screen.blit(label, (end_pos[0] + 10, end_pos[1] - 10))
    
    def draw_stats_panel(self):
        """Draw statistics panel"""
        if not self.gesture_tracks:
            return
        
        panel_x = self.width - 300
        panel_y = 100
        panel_width = 280
        
        # Semi-transparent background
        s = pygame.Surface((panel_width, 400))
        s.set_alpha(200)
        s.fill((20, 20, 30))
        self.screen.blit(s, (panel_x, panel_y))
        
        # Title
        title = self.small_font.render("Gesture Stats", True, (100, 255, 255))
        self.screen.blit(title, (panel_x + 10, panel_y + 10))
        
        # Stats for each finger (only calculate if enough points)
        y = panel_y + 40
        for finger_id, track in sorted(self.gesture_tracks.items()):
            if len(track.points) < 2:
                continue
                
            # Finger header
            header = self.small_font.render(f"Finger {finger_id}:", True, track.color)
            self.screen.blit(header, (panel_x + 10, y))
            y += 25
            
            # Simple stats without full calculation
            points_text = self.small_font.render(f"  points: {len(track.points)}", True, (200, 200, 200))
            self.screen.blit(points_text, (panel_x + 10, y))
            y += 20
            
            if len(track.points) >= 2:
                duration = track.points[-1].timestamp - track.points[0].timestamp
                duration_text = self.small_font.render(f"  duration: {duration:.2f}s", True, (200, 200, 200))
                self.screen.blit(duration_text, (panel_x + 10, y))
                y += 20
            
            y += 10
    
    async def process_events(self):
        """Process trackpad events"""
        if not self.device:
            return
        
        current_slot = 0
        # Track LAST KNOWN position for each slot (persistent across frames)
        slot_positions = {}  # {slot_id: [x, y]}
        # Track which slots were updated in current frame
        slots_updated_this_frame = set()
        needs_redraw = True
        last_draw_time = time.time()
        
        # Draw initial UI immediately
        self.draw_ui()
        pygame.display.flip()
        
        print("\n✓ Ready! Touch your trackpad with multiple fingers")
        print("  Press SPACE to start capturing\n")
        
        # Create async task for device events
        async def handle_device_events():
            async for event in self.device.async_read_loop():
                # Process touch events
                if event.type == ecodes.EV_ABS:
                    if event.code == ecodes.ABS_MT_SLOT:
                        nonlocal current_slot
                        current_slot = event.value
                    
                    elif event.code == ecodes.ABS_MT_TRACKING_ID:
                        if event.value == -1:
                            # Finger lifted - mark as inactive but keep the track
                            if current_slot in self.gesture_tracks:
                                track = self.gesture_tracks[current_slot]
                                track.is_active = False
                                
                                # Move to completed tracks
                                self.completed_tracks.append(track)
                                
                                # In training mode, don't validate or print per-finger messages
                                # Validation happens when user presses SPACE to save
                                if not self.training_mode:
                                    # Normal mode: validate and show per-finger feedback
                                    quality = track.validate_quality(self.min_points, self.min_duration)
                                    
                                    if quality.is_valid:
                                        print(f"👆 Finger {current_slot} lifted - VALID ({quality.point_count} points, {quality.duration:.3f}s)")
                                        self.valid_capture_count += 1
                                    else:
                                        print(f"👆 Finger {current_slot} lifted - INVALID: {quality.reason}")
                                        self.invalid_capture_count += 1
                                    
                                    self.capture_count += 1
                                else:
                                    # Training mode: just show finger lifted (no validation yet)
                                    print(f"👆 Finger {current_slot} lifted")
                                
                                del self.gesture_tracks[current_slot]
                                # Clean up position tracking for this slot
                                if current_slot in slot_positions:
                                    del slot_positions[current_slot]
                                nonlocal needs_redraw
                                needs_redraw = True
                        else:
                            # New finger detected
                            if self.is_capturing:
                                # Always create a NEW track
                                color = COLORS[current_slot % len(COLORS)]
                                new_track = GestureTrack(current_slot, color)
                                self.gesture_tracks[current_slot] = new_track
                                print(f"👇 Finger {current_slot} detected")
                                needs_redraw = True
                    
                    elif event.code == ecodes.ABS_MT_POSITION_X:
                        # Initialize slot position if first time
                        if current_slot not in slot_positions:
                            slot_positions[current_slot] = [0, 0]
                        # Update X, keep existing Y
                        slot_positions[current_slot][0] = event.value
                        slots_updated_this_frame.add(current_slot)
                    
                    elif event.code == ecodes.ABS_MT_POSITION_Y:
                        # Initialize slot position if first time
                        if current_slot not in slot_positions:
                            slot_positions[current_slot] = [0, 0]
                        # Update Y, keep existing X
                        slot_positions[current_slot][1] = event.value
                        slots_updated_this_frame.add(current_slot)
                
                elif event.type == ecodes.EV_SYN and event.code == ecodes.SYN_REPORT:
                    # End of event frame - process slots that were updated
                    if self.is_capturing and slots_updated_this_frame:
                        timestamp = time.monotonic()
                        timestamp_ns = time.monotonic_ns()
                        
                        for slot_id in slots_updated_this_frame:
                            if slot_id in self.gesture_tracks and slot_id in slot_positions:
                                track = self.gesture_tracks[slot_id]
                                if track.is_active:
                                    x, y = slot_positions[slot_id]
                                    screen_x, screen_y = self.normalize_coords(x, y)
                                    track.add_point(screen_x, screen_y, timestamp, timestamp_ns)
                                    needs_redraw = True
                        
                        # Clear updated slots for next frame
                        slots_updated_this_frame.clear()
        
        # Start device event handler
        device_task = asyncio.create_task(handle_device_events())
        
        # Main event loop for pygame and rendering
        running = True
        while running:
            # Handle pygame events (keyboard, quit, etc.)
            for pg_event in pygame.event.get():
                if pg_event.type == pygame.QUIT:
                    running = False
                elif pg_event.type == pygame.KEYDOWN:
                    if pg_event.key == pygame.K_SPACE:
                        # Training mode: toggle capture and save complete gesture
                        if self.training_mode:
                            if not self.is_capturing:
                                # Start capturing
                                self.is_capturing = True
                                print(f"🎬 Training capture started ({self.training_samples_collected}/{self.target_samples})")
                                print(f"   Draw your gesture, then press SPACE again to save")
                                self.gesture_tracks.clear()
                                self.completed_tracks.clear()
                            else:
                                # Stop capturing and save as ONE sample
                                self.is_capturing = False
                                print(f"⏹️  Capture stopped")
                                
                                # Collect all tracks (active + completed) as ONE gesture
                                all_tracks = []
                                for track in self.gesture_tracks.values():
                                    all_tracks.append(track)
                                for track in self.completed_tracks:
                                    all_tracks.append(track)
                                
                                if all_tracks:
                                    # Validate and provide feedback for the complete gesture
                                    is_valid = self.provide_quality_feedback(all_tracks)
                                    
                                    if is_valid:
                                        # Save all tracks as one sample
                                        for track in all_tracks:
                                            self.saved_gestures.append(track)
                                        self.auto_save_training_sample()
                                else:
                                    print(f"   No gesture detected")
                                
                                # Clear for next sample
                                self.gesture_tracks.clear()
                                self.completed_tracks.clear()
                                print(f"   Ready for next sample ({self.training_samples_collected}/{self.target_samples})")
                        else:
                            # Normal mode: toggle capturing
                            self.is_capturing = not self.is_capturing
                            if self.is_capturing:
                                print("🎬 Started capturing")
                                self.gesture_tracks.clear()
                            else:
                                print("⏹️  Stopped capturing")
                                # Save only valid gestures to saved list
                                valid_count = 0
                                for track in self.gesture_tracks.values():
                                    quality = track.validate_quality(self.min_points, self.min_duration)
                                    if quality.is_valid:
                                        self.saved_gestures.append(track)
                                        valid_count += 1
                                # Also save completed tracks (already validated)
                                for track in self.completed_tracks:
                                    quality = track.validate_quality(self.min_points, self.min_duration)
                                    if quality.is_valid and track not in self.saved_gestures:
                                        self.saved_gestures.append(track)
                                        valid_count += 1
                                print(f"   Saved {valid_count} valid gestures")
                        needs_redraw = True
                    
                    elif pg_event.key == pygame.K_c:
                        self.gesture_tracks.clear()
                        self.completed_tracks.clear()
                        slot_positions.clear()
                        slots_updated_this_frame.clear()
                        print("🗑️  Cleared current gestures")
                        needs_redraw = True
                    
                    elif pg_event.key == pygame.K_s:
                        self.save_to_file()
                        needs_redraw = True
                    
                    elif pg_event.key == pygame.K_q or pg_event.key == pygame.K_ESCAPE:
                        running = False
            
            # Redraw at max 60 FPS
            current_time = time.time()
            if needs_redraw and (current_time - last_draw_time) > 0.016:  # ~60 FPS
                # Draw everything
                self.draw_ui()
                
                # Draw completed tracks (dimmed) - only last 10 to avoid clutter
                for track in self.completed_tracks[-10:]:
                    self.draw_gesture_track(track, False)
                
                # Draw active gesture tracks
                for track in self.gesture_tracks.values():
                    self.draw_gesture_track(track, track.is_active)
                
                # Draw stats panel
                self.draw_stats_panel()
                
                pygame.display.flip()
                needs_redraw = False
                last_draw_time = current_time
            
            # Small sleep to prevent CPU hogging
            await asyncio.sleep(0.001)
        
        # Cancel device task when exiting
        device_task.cancel()
        try:
            await device_task
        except asyncio.CancelledError:
            pass
    
    def save_to_file(self):
        """Save gestures to JSON file with comprehensive metadata, features, and quality validation
        
        Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
        """
        # Collect all tracks to save (active, completed, and saved)
        all_tracks = []
        
        # Add currently active tracks
        for track in self.gesture_tracks.values():
            if len(track.points) >= 2:
                all_tracks.append(track)
        
        # Add completed tracks
        for track in self.completed_tracks:
            if len(track.points) >= 2:
                all_tracks.append(track)
        
        # Add previously saved tracks
        for track in self.saved_gestures:
            if len(track.points) >= 2:
                all_tracks.append(track)
        
        if not all_tracks:
            print("⚠️  No gestures to save (need at least 2 points per gesture)")
            return
        
        # Build comprehensive metadata (Requirements: 3.1, 3.2)
        metadata = {
            'session_id': self.session_id,
            'session_start_time': self.session_start_time,
            'capture_timestamp': time.time(),
            'device': {
                'name': self.device_name,
                'vendor': self.device_vendor,
                'product': self.device_product,
                'path': self.device_path
            },
            'screen_dimensions': {
                'width': self.width,
                'height': self.height
            },
            'trackpad_dimensions': {
                'x_min': self.abs_x_min,
                'x_max': self.abs_x_max,
                'y_min': self.abs_y_min,
                'y_max': self.abs_y_max,
                'x_range': self.abs_x_max - self.abs_x_min,
                'y_range': self.abs_y_max - self.abs_y_min
            },
            'quality_thresholds': {
                'min_points': self.min_points,
                'min_duration': self.min_duration
            },
            'session_stats': {
                'total_captures': self.capture_count,
                'valid_captures': self.valid_capture_count,
                'invalid_captures': self.invalid_capture_count
            },
            'system_info': {
                'platform': platform.system(),
                'platform_release': platform.release(),
                'platform_version': platform.version(),
                'machine': platform.machine()
            }
        }
        
        # Initialize feature extractor
        feature_extractor = FeatureExtractor()
        
        # Build gesture data with quality validation and extracted features
        gestures = []
        valid_count = 0
        invalid_count = 0
        
        for track in all_tracks:
            stats = track.calculate_stats()
            quality = track.validate_quality(self.min_points, self.min_duration)
            
            if quality.is_valid:
                valid_count += 1
            else:
                invalid_count += 1
            
            # Extract all features for this gesture (Requirements: 3.3, 4.1-4.6)
            features = feature_extractor.extract_all_features(
                track, 
                all_tracks, 
                self.width, 
                self.height
            )
            
            # Build comprehensive gesture data structure
            gesture_data = {
                'gesture_id': f"{self.session_id}_{track.finger_id}_{int(track.points[0].timestamp_ns)}",
                'finger_id': track.finger_id,
                
                # Quality metrics (Requirements: 3.4)
                'quality': {
                    'is_valid': quality.is_valid,
                    'point_count': quality.point_count,
                    'duration': quality.duration,
                    'min_points_met': quality.min_points_met,
                    'min_duration_met': quality.min_duration_met,
                    'reason': quality.reason
                },
                
                # Basic statistics
                'stats': stats,
                
                # Raw gesture data - all points (Requirements: 3.2)
                'points': [
                    {
                        'x': p.x,
                        'y': p.y,
                        'timestamp': p.timestamp,
                        'timestamp_ns': p.timestamp_ns
                    }
                    for p in track.points
                ],
                
                # Extracted features (Requirements: 3.3, 4.1-4.6)
                'features': {
                    # Spatial features
                    'spatial': {
                        'path_length': features['spatial']['path_length'],
                        'bounding_box': features['spatial']['bounding_box'],
                        'velocities': features['spatial']['velocities'],
                        'accelerations': features['spatial']['accelerations'],
                        'curvatures': features['spatial']['curvatures'],
                        # Summary statistics
                        'velocity_stats': {
                            'avg': sum(features['spatial']['velocities']) / len(features['spatial']['velocities']) if features['spatial']['velocities'] else 0,
                            'max': max(features['spatial']['velocities']) if features['spatial']['velocities'] else 0,
                            'min': min(features['spatial']['velocities']) if features['spatial']['velocities'] else 0
                        },
                        'acceleration_stats': {
                            'avg': sum(features['spatial']['accelerations']) / len(features['spatial']['accelerations']) if features['spatial']['accelerations'] else 0,
                            'max': max(features['spatial']['accelerations']) if features['spatial']['accelerations'] else 0,
                            'min': min(features['spatial']['accelerations']) if features['spatial']['accelerations'] else 0
                        },
                        'curvature_stats': {
                            'avg': sum(features['spatial']['curvatures']) / len(features['spatial']['curvatures']) if features['spatial']['curvatures'] else 0,
                            'max': max(features['spatial']['curvatures']) if features['spatial']['curvatures'] else 0,
                            'min': min(features['spatial']['curvatures']) if features['spatial']['curvatures'] else 0
                        }
                    },
                    
                    # Behavioral features
                    'behavioral': {
                        'rhythm': features['behavioral']['rhythm'],
                        'pressure': features['behavioral']['pressure'],
                        'coordination': features['behavioral']['coordination']
                    },
                    
                    # Normalized feature vector (25 elements)
                    'feature_vector': features['feature_vector']
                }
            }
            gestures.append(gesture_data)
        
        # Complete data structure (Requirements: 3.1, 3.5, 3.6)
        data = {
            'metadata': metadata,
            'gestures': gestures
        }
        
        # Validate data before saving (Requirements: 3.2, 3.6)
        is_valid, validation_errors = self.validate_exported_data(data)
        
        if not is_valid:
            print(f"⚠️  Data validation found {len(validation_errors)} errors:")
            for error in validation_errors[:10]:  # Show first 10 errors
                print(f"   - {error}")
            if len(validation_errors) > 10:
                print(f"   ... and {len(validation_errors) - 10} more errors")
            print("   Saving anyway, but data may be incomplete or invalid")
        
        filename = f"gestures_session_{self.session_id}.json"
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"💾 Saved {len(gestures)} gestures to {filename}")
            print(f"   Valid: {valid_count}, Invalid: {invalid_count}")
            print(f"   Session ID: {self.session_id}")
            print(f"   Features extracted: spatial, behavioral, feature_vector")
            if is_valid:
                print(f"   ✓ Data validation passed")
            else:
                print(f"   ⚠️  Data validation failed with {len(validation_errors)} errors")
        except Exception as e:
            print(f"❌ Error saving file: {e}")
    
    async def run(self):
        """Main run loop"""
        if not self.open_device():
            return
        
        self.init_pygame()
        
        try:
            await self.process_events()
        except KeyboardInterrupt:
            print("\n✓ Stopped")
        finally:
            if self.device:
                self.device.close()
            pygame.quit()

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Trackpad Multi-Touch Gesture Visualizer with Training Mode"
    )
    parser.add_argument(
        '--training',
        action='store_true',
        help='Enable training mode for guided data collection'
    )
    parser.add_argument(
        '--samples',
        type=int,
        default=50,
        help='Number of training samples to collect (default: 50)'
    )
    parser.add_argument(
        '--min-points',
        type=int,
        default=10,
        help='Minimum points required for valid gesture (default: 10)'
    )
    parser.add_argument(
        '--min-duration',
        type=float,
        default=0.1,
        help='Minimum duration in seconds for valid gesture (default: 0.1)'
    )
    parser.add_argument(
        '--device',
        type=str,
        default='/dev/input/event14',
        help='Input device path (default: /dev/input/event14)'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    if args.training:
        print("Training Mode - Guided Gesture Collection")
        print(f"Target: {args.samples} samples")
    else:
        print("Trackpad Multi-Touch Gesture Visualizer")
    print("=" * 60)
    
    # Check if running as root
    if os.geteuid() != 0:
        print("\n⚠️  Warning: Not running as root")
        print("   Run: sudo python3 trackpad_visualizer.py\n")
    
    visualizer = TrackpadVisualizer(
        device_path=args.device,
        min_points=args.min_points,
        min_duration=args.min_duration,
        training_mode=args.training,
        target_samples=args.samples
    )
    
    if args.training:
        print(f"\n📚 Training Mode Active")
        print(f"   Target samples: {args.samples}")
        print(f"   Quality requirements: {args.min_points} points, {args.min_duration}s duration")
        print(f"   Auto-save: Enabled")
        print(f"\n   Instructions:")
        print(f"   1. Press SPACE to start capturing")
        print(f"   2. Draw your gesture on the trackpad")
        print(f"   3. System will provide feedback and auto-save")
        print(f"   4. Repeat until {args.samples} samples collected")
        print()
    
    try:
        asyncio.run(visualizer.run())
    except KeyboardInterrupt:
        print("\n✓ Shutdown complete")
        if args.training:
            print(f"   Collected {visualizer.training_samples_collected}/{args.samples} samples")

if __name__ == "__main__":
    main()
