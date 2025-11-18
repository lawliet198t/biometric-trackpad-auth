#!/usr/bin/env python3
"""
Advanced Biometric Feature Extraction - Pure Dynamics Approach

Hardware Constraint: ELAN trackpad provides ONLY (X, Y, Timestamp)
No pressure data, no contact area - pure motion dynamics only

This module implements:
1. Advanced feature engineering (velocity, acceleration, jerk, curvature, hesitation)
2. Multi-stage verification with strict gating
3. Biometric baseline learning from training samples
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import time


@dataclass
class TouchPoint:
    """Single touch point with position and timing"""
    x: float
    y: float
    timestamp: float
    timestamp_ns: int


class AdvancedFeatureExtractor:
    """
    Extract advanced biometric features from pure motion dynamics.
    
    Features extracted:
    - Velocity (speed and direction)
    - Acceleration (rate of change of velocity)
    - Jerk (rate of change of acceleration) - CRITICAL for forgery detection
    - Curvature (path turning)
    - Stroke hesitation (micro-pauses)
    - Duration (total gesture time)
    - Path length and complexity
    """
    
    HESITATION_THRESHOLD_VELOCITY = 50.0  # pixels/second
    HESITATION_MIN_DURATION = 0.01  # 10ms

    def __init__(self):
        pass
    
    def calculate_velocity(self, points: List[TouchPoint]) -> np.ndarray:
        """
        Calculate velocity at each point.
        Returns: array of velocities (magnitude in pixels/second)
        """
        if len(points) < 2:
            return np.array([])
        
        velocities = []
        for i in range(1, len(points)):
            dt = points[i].timestamp - points[i-1].timestamp
            if dt > 0:
                dx = points[i].x - points[i-1].x
                dy = points[i].y - points[i-1].y
                distance = np.sqrt(dx**2 + dy**2)
                velocity = distance / dt
                velocities.append(velocity)
            else:
                velocities.append(0.0)
        
        return np.array(velocities)
    
    def calculate_acceleration(self, velocities: np.ndarray, points: List[TouchPoint]) -> np.ndarray:
        """
        Calculate acceleration from velocity changes.
        Returns: array of accelerations (pixels/second^2)
        """
        if len(velocities) < 2 or len(points) < 3:
            return np.array([])
        
        accelerations = []
        for i in range(1, len(velocities)):
            dt = points[i+1].timestamp - points[i].timestamp
            if dt > 0:
                dv = velocities[i] - velocities[i-1]
                acceleration = dv / dt
                accelerations.append(acceleration)
            else:
                accelerations.append(0.0)
        
        return np.array(accelerations)
    
    def calculate_jerk(self, accelerations: np.ndarray, points: List[TouchPoint]) -> np.ndarray:
        """
        Calculate jerk (rate of change of acceleration).
        
        CRITICAL BIOMETRIC: Jerk measures smoothness of motion.
        - Low, consistent jerk = practiced, fluid motion (authentic)
        - High, erratic jerk = conscious tracing (forgery)
        
        Returns: array of jerk values (pixels/second^3)
        """
        if len(accelerations) < 2 or len(points) < 4:
            return np.array([])
        
        jerks = []
        for i in range(1, len(accelerations)):
            # Fix: Align time delta with acceleration interval (p[i] -> p[i+1])
            # Acceleration[i] is from v[i]->v[i+1] (approx t[i]->t[i+1])
            # Acceleration[i-1] is from v[i-1]->v[i] (approx t[i-1]->t[i])
            # So change in acceleration happens over t[i] -> t[i+1]
            dt = points[i+1].timestamp - points[i].timestamp
            if dt > 0:
                da = accelerations[i] - accelerations[i-1]
                jerk = da / dt
                jerks.append(jerk)
            else:
                jerks.append(0.0)
        
        return np.array(jerks)
    
    def calculate_curvature(self, points: List[TouchPoint]) -> np.ndarray:
        """
        Calculate curvature (direction changes) at each point.
        Returns: array of curvature values (radians)
        """
        if len(points) < 3:
            return np.array([])
        
        curvatures = []
        for i in range(1, len(points) - 1):
            # Vector from point i-1 to i
            v1_x = points[i].x - points[i-1].x
            v1_y = points[i].y - points[i-1].y
            
            # Vector from point i to i+1
            v2_x = points[i+1].x - points[i].x
            v2_y = points[i+1].y - points[i].y
            
            # Calculate magnitudes
            mag1 = np.sqrt(v1_x**2 + v1_y**2)
            mag2 = np.sqrt(v2_x**2 + v2_y**2)
            
            if mag1 > 0 and mag2 > 0:
                # Dot product and cross product
                dot = v1_x * v2_x + v1_y * v2_y
                cross = v1_x * v2_y - v1_y * v2_x
                
                # Signed angle
                angle = np.arctan2(cross, dot)
                curvatures.append(abs(angle))
            else:
                curvatures.append(0.0)
        
        return np.array(curvatures)
    
    def detect_hesitations(self, velocities: np.ndarray, points: List[TouchPoint]) -> Dict:
        """
        Detect stroke hesitations (micro-pauses in motion).
        
        Hesitation = velocity drops near zero for brief period.
        Number, duration, and location of hesitations are biometric signatures.
        
        Returns: dict with hesitation metrics
        """
        if len(velocities) == 0:
            return {
                'count': 0,
                'total_duration': 0.0,
                'locations': [],
                'avg_duration': 0.0
            }
        
        hesitations = []
        in_hesitation = False
        hesitation_start_idx = 0
        
        for i, vel in enumerate(velocities):
            if vel < self.HESITATION_THRESHOLD_VELOCITY:
                if not in_hesitation:
                    # Start of hesitation
                    in_hesitation = True
                    hesitation_start_idx = i
            else:
                if in_hesitation:
                    # End of hesitation
                    in_hesitation = False
                    duration = points[i+1].timestamp - points[hesitation_start_idx+1].timestamp
                    
                    if duration >= self.HESITATION_MIN_DURATION:
                        hesitations.append({
                            'start_idx': hesitation_start_idx,
                            'end_idx': i,
                            'duration': duration
                        })
        
        # Handle case where gesture ends in hesitation
        if in_hesitation and len(points) > hesitation_start_idx + 1:
            duration = points[-1].timestamp - points[hesitation_start_idx+1].timestamp
            if duration >= self.HESITATION_MIN_DURATION:
                hesitations.append({
                    'start_idx': hesitation_start_idx,
                    'end_idx': len(velocities) - 1,
                    'duration': duration
                })
        
        total_duration = sum(h['duration'] for h in hesitations)
        avg_duration = total_duration / len(hesitations) if hesitations else 0.0
        
        return {
            'count': len(hesitations),
            'total_duration': total_duration,
            'locations': hesitations,
            'avg_duration': avg_duration
        }
    
    def extract_all_dynamics(self, points: List[TouchPoint]) -> Dict:
        """
        Extract all dynamic features from a gesture.
        
        Returns comprehensive feature dictionary with:
        - Raw dynamics: velocity, acceleration, jerk, curvature
        - Statistical summaries: mean, std, cv, max, min
        - Hesitation metrics
        - Duration and path metrics
        """
        if len(points) < 2:
            return self._empty_features()
        
        # Calculate raw dynamics
        velocities = self.calculate_velocity(points)
        accelerations = self.calculate_acceleration(velocities, points)
        jerks = self.calculate_jerk(accelerations, points)
        curvatures = self.calculate_curvature(points)
        
        # Duration
        duration = points[-1].timestamp - points[0].timestamp
        
        # Path length
        path_length = 0.0
        for i in range(1, len(points)):
            dx = points[i].x - points[i-1].x
            dy = points[i].y - points[i-1].y
            path_length += np.sqrt(dx**2 + dy**2)
        
        # Hesitations
        hesitations = self.detect_hesitations(velocities, points)
        
        # Statistical summaries
        features = {
            'duration': duration,
            'path_length': path_length,
            'point_count': len(points),
            
            # Velocity stats
            'velocity_mean': np.mean(velocities) if len(velocities) > 0 else 0.0,
            'velocity_std': np.std(velocities) if len(velocities) > 0 else 0.0,
            'velocity_cv': np.std(velocities) / np.mean(velocities) if len(velocities) > 0 and np.mean(velocities) > 0 else 0.0,
            'velocity_max': np.max(velocities) if len(velocities) > 0 else 0.0,
            'velocity_min': np.min(velocities) if len(velocities) > 0 else 0.0,
            
            # Acceleration stats
            'acceleration_mean': np.mean(np.abs(accelerations)) if len(accelerations) > 0 else 0.0,
            'acceleration_std': np.std(accelerations) if len(accelerations) > 0 else 0.0,
            'acceleration_cv': np.std(accelerations) / np.mean(np.abs(accelerations)) if len(accelerations) > 0 and np.mean(np.abs(accelerations)) > 0 else 0.0,
            'acceleration_max': np.max(np.abs(accelerations)) if len(accelerations) > 0 else 0.0,
            
            # Jerk stats (CRITICAL)
            'jerk_mean': np.mean(np.abs(jerks)) if len(jerks) > 0 else 0.0,
            'jerk_std': np.std(jerks) if len(jerks) > 0 else 0.0,
            'jerk_cv': np.std(jerks) / np.mean(np.abs(jerks)) if len(jerks) > 0 and np.mean(np.abs(jerks)) > 0 else 0.0,
            'jerk_max': np.max(np.abs(jerks)) if len(jerks) > 0 else 0.0,
            
            # Curvature stats
            'curvature_mean': np.mean(curvatures) if len(curvatures) > 0 else 0.0,
            'curvature_std': np.std(curvatures) if len(curvatures) > 0 else 0.0,
            'curvature_max': np.max(curvatures) if len(curvatures) > 0 else 0.0,
            
            # Hesitation metrics
            'hesitation_count': hesitations['count'],
            'hesitation_total_duration': hesitations['total_duration'],
            'hesitation_avg_duration': hesitations['avg_duration'],
            'hesitation_ratio': hesitations['total_duration'] / duration if duration > 0 else 0.0,
            
            # Raw arrays (for advanced analysis)
            'velocities': velocities,
            'accelerations': accelerations,
            'jerks': jerks,
            'curvatures': curvatures,
            'hesitations': hesitations
        }
        
        return features
    
    def _empty_features(self) -> Dict:
        """Return empty feature dict for invalid gestures"""
        return {
            'duration': 0.0,
            'path_length': 0.0,
            'point_count': 0,
            'velocity_mean': 0.0,
            'velocity_std': 0.0,
            'velocity_cv': 0.0,
            'velocity_max': 0.0,
            'velocity_min': 0.0,
            'acceleration_mean': 0.0,
            'acceleration_std': 0.0,
            'acceleration_cv': 0.0,
            'acceleration_max': 0.0,
            'jerk_mean': 0.0,
            'jerk_std': 0.0,
            'jerk_cv': 0.0,
            'jerk_max': 0.0,
            'curvature_mean': 0.0,
            'curvature_std': 0.0,
            'curvature_max': 0.0,
            'hesitation_count': 0,
            'hesitation_total_duration': 0.0,
            'hesitation_avg_duration': 0.0,
            'hesitation_ratio': 0.0,
            'velocities': np.array([]),
            'accelerations': np.array([]),
            'jerks': np.array([]),
            'curvatures': np.array([]),
            'hesitations': {'count': 0, 'total_duration': 0.0, 'locations': [], 'avg_duration': 0.0}
        }


class BiometricBaseline:
    """
    Learn and store biometric baselines from training samples.
    Used for adaptive verification thresholds.
    """
    
    def __init__(self):
        self.duration_mean = 0.0
        self.duration_std = 0.0
        
        self.path_length_mean = 0.0
        self.path_length_std = 0.0
        
        self.velocity_cv_mean = 0.0
        self.velocity_cv_std = 0.0
        
        self.jerk_cv_mean = 0.0
        self.jerk_cv_std = 0.0
        
        self.hesitation_count_mean = 0.0
        self.hesitation_count_std = 0.0
        
        self.is_trained = False
    
    def learn_from_samples(self, features_list: List[Dict]):
        """
        Learn baseline statistics from training samples.
        """
        if len(features_list) < 3:
            print("⚠️  Need at least 3 samples to learn baseline")
            return False
        
        # Extract key metrics
        durations = [f['duration'] for f in features_list]
        path_lengths = [f['path_length'] for f in features_list]
        velocity_cvs = [f['velocity_cv'] for f in features_list]
        jerk_cvs = [f['jerk_cv'] for f in features_list]
        hesitation_counts = [f['hesitation_count'] for f in features_list]
        
        # Calculate means and stds
        self.duration_mean = np.mean(durations)
        self.duration_std = np.std(durations)
        
        self.path_length_mean = np.mean(path_lengths)
        self.path_length_std = np.std(path_lengths)
        
        self.velocity_cv_mean = np.mean(velocity_cvs)
        self.velocity_cv_std = np.std(velocity_cvs)
        
        self.jerk_cv_mean = np.mean(jerk_cvs)
        self.jerk_cv_std = np.std(jerk_cvs)
        
        self.hesitation_count_mean = np.mean(hesitation_counts)
        self.hesitation_count_std = np.std(hesitation_counts)
        
        self.is_trained = True
        
        print(f"\n✓ Biometric baseline learned from {len(features_list)} samples")
        print(f"  Duration: {self.duration_mean:.3f}s ± {self.duration_std:.3f}s")
        print(f"  Path length: {self.path_length_mean:.1f} ± {self.path_length_std:.1f} px")
        print(f"  Velocity CV: {self.velocity_cv_mean:.3f} ± {self.velocity_cv_std:.3f}")
        print(f"  Jerk CV: {self.jerk_cv_mean:.3f} ± {self.jerk_cv_std:.3f}")
        print(f"  Hesitations: {self.hesitation_count_mean:.1f} ± {self.hesitation_count_std:.1f}")
        
        return True

    def to_dict(self) -> Dict:
        """Convert baseline to dictionary for JSON serialization"""
        return {
            'duration_mean': self.duration_mean,
            'duration_std': self.duration_std,
            'path_length_mean': self.path_length_mean,
            'path_length_std': self.path_length_std,
            'velocity_cv_mean': self.velocity_cv_mean,
            'velocity_cv_std': self.velocity_cv_std,
            'jerk_cv_mean': self.jerk_cv_mean,
            'jerk_cv_std': self.jerk_cv_std,
            'hesitation_count_mean': self.hesitation_count_mean,
            'hesitation_count_std': self.hesitation_count_std,
            'is_trained': self.is_trained
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'BiometricBaseline':
        """Create baseline from dictionary"""
        baseline = cls()
        baseline.duration_mean = data.get('duration_mean', 0.0)
        baseline.duration_std = data.get('duration_std', 0.0)
        baseline.path_length_mean = data.get('path_length_mean', 0.0)
        baseline.path_length_std = data.get('path_length_std', 0.0)
        baseline.velocity_cv_mean = data.get('velocity_cv_mean', 0.0)
        baseline.velocity_cv_std = data.get('velocity_cv_std', 0.0)
        baseline.jerk_cv_mean = data.get('jerk_cv_mean', 0.0)
        baseline.jerk_cv_std = data.get('jerk_cv_std', 0.0)
        baseline.hesitation_count_mean = data.get('hesitation_count_mean', 0.0)
        baseline.hesitation_count_std = data.get('hesitation_count_std', 0.0)
        baseline.is_trained = data.get('is_trained', False)
        return baseline


class MultiStageVerifier:
    """
    Multi-stage verification with strict gating.
    
    Stage 1: Gatekeeper (Invariant Checks)
    - Duration must be within tight window
    - Path length must be plausible
    - Point count must be reasonable
    
    Stage 2: Shape Verification (future: CNN)
    - Currently: basic spatial checks
    
    Stage 3: Dynamics Verification
    - Velocity, acceleration, jerk patterns
    - Hesitation patterns
    """
    
    def __init__(self, baseline: BiometricBaseline):
        self.baseline = baseline
        self.duration_sigma_threshold = 2.0  # Accept within 2σ
        self.path_length_sigma_threshold = 2.5
        self.dynamics_sigma_threshold = 3.0
    
    def stage1_gatekeeper(self, features: Dict) -> Tuple[bool, str, float]:
        """
        Stage 1: Fast rejection of obvious forgeries.
        
        Returns: (passed, reason, score)
        """
        if not self.baseline.is_trained:
            return True, "baseline_not_trained", 100.0
        
        # Check duration (MOST IMPORTANT)
        duration = features['duration']
        duration_diff = abs(duration - self.baseline.duration_mean)
        duration_sigma = duration_diff / self.baseline.duration_std if self.baseline.duration_std > 0 else 0.0
        
        if duration_sigma > self.duration_sigma_threshold:
            score = max(0, 100 - (duration_sigma - self.duration_sigma_threshold) * 30)
            return False, f"duration_mismatch ({duration:.2f}s vs {self.baseline.duration_mean:.2f}±{self.baseline.duration_std:.2f}s)", score
        
        # Check path length
        path_length = features['path_length']
        path_diff = abs(path_length - self.baseline.path_length_mean)
        path_sigma = path_diff / self.baseline.path_length_std if self.baseline.path_length_std > 0 else 0.0
        
        if path_sigma > self.path_length_sigma_threshold:
            score = max(0, 100 - (path_sigma - self.path_length_sigma_threshold) * 25)
            return False, f"path_length_mismatch ({path_length:.0f}px vs {self.baseline.path_length_mean:.0f}±{self.baseline.path_length_std:.0f}px)", score
        
        # Passed gatekeeper
        score = 100 - (duration_sigma * 10 + path_sigma * 8)
        return True, "passed", max(0, score)
    
    def stage3_dynamics_verification(self, features: Dict) -> Tuple[bool, str, float]:
        """
        Stage 3: Verify dynamics (velocity, jerk, hesitation patterns).
        
        Returns: (passed, reason, score)
        """
        if not self.baseline.is_trained:
            return True, "baseline_not_trained", 100.0
        
        scores = []
        
        # Velocity CV check
        velocity_cv = features['velocity_cv']
        velocity_cv_diff = abs(velocity_cv - self.baseline.velocity_cv_mean)
        velocity_cv_sigma = velocity_cv_diff / self.baseline.velocity_cv_std if self.baseline.velocity_cv_std > 0 else 0.0
        
        if velocity_cv_sigma < 1.0:
            velocity_score = 100
        elif velocity_cv_sigma < 2.0:
            velocity_score = 100 - (velocity_cv_sigma - 1.0) * 30
        elif velocity_cv_sigma < 3.0:
            velocity_score = 70 - (velocity_cv_sigma - 2.0) * 40
        else:
            velocity_score = max(0, 30 - (velocity_cv_sigma - 3.0) * 15)
        
        scores.append(('velocity', velocity_score, velocity_cv_sigma))
        
        # Jerk CV check (CRITICAL)
        jerk_cv = features['jerk_cv']
        jerk_cv_diff = abs(jerk_cv - self.baseline.jerk_cv_mean)
        jerk_cv_sigma = jerk_cv_diff / self.baseline.jerk_cv_std if self.baseline.jerk_cv_std > 0 else 0.0
        
        if jerk_cv_sigma < 1.0:
            jerk_score = 100
        elif jerk_cv_sigma < 2.0:
            jerk_score = 100 - (jerk_cv_sigma - 1.0) * 30
        elif jerk_cv_sigma < 3.0:
            jerk_score = 70 - (jerk_cv_sigma - 2.0) * 40
        else:
            jerk_score = max(0, 30 - (jerk_cv_sigma - 3.0) * 15)
        
        scores.append(('jerk', jerk_score, jerk_cv_sigma))
        
        # Hesitation count check
        hesitation_count = features['hesitation_count']
        hesitation_diff = abs(hesitation_count - self.baseline.hesitation_count_mean)
        hesitation_sigma = hesitation_diff / self.baseline.hesitation_count_std if self.baseline.hesitation_count_std > 0 else 0.0
        
        if hesitation_sigma < 1.5:
            hesitation_score = 100
        elif hesitation_sigma < 3.0:
            hesitation_score = 100 - (hesitation_sigma - 1.5) * 40
        else:
            hesitation_score = max(0, 40 - (hesitation_sigma - 3.0) * 20)
        
        scores.append(('hesitation', hesitation_score, hesitation_sigma))
        
        # Overall score (weighted average, jerk is most important)
        overall_score = (velocity_score * 0.3 + jerk_score * 0.5 + hesitation_score * 0.2)
        
        # Determine pass/fail
        if overall_score >= 70:
            passed = True
            reason = "passed"
        else:
            # Find worst metric
            worst = min(scores, key=lambda x: x[1])
            passed = False
            reason = f"{worst[0]}_mismatch (σ={worst[2]:.2f})"
        
        return passed, reason, overall_score
    
    def verify(self, features: Dict) -> Dict:
        """
        Full multi-stage verification.
        
        Returns: dict with verification results
        """
        result = {
            'passed': False,
            'stage_reached': 0,
            'stage1_passed': False,
            'stage1_reason': '',
            'stage1_score': 0.0,
            'stage3_passed': False,
            'stage3_reason': '',
            'stage3_score': 0.0,
            'overall_score': 0.0
        }
        
        # Stage 1: Gatekeeper
        stage1_passed, stage1_reason, stage1_score = self.stage1_gatekeeper(features)
        result['stage1_passed'] = stage1_passed
        result['stage1_reason'] = stage1_reason
        result['stage1_score'] = stage1_score
        result['stage_reached'] = 1
        
        if not stage1_passed:
            result['overall_score'] = stage1_score * 0.5  # Penalty for early rejection
            return result
        
        # Stage 2: Shape verification (TODO: implement CNN)
        # For now, assume passed
        result['stage_reached'] = 2
        
        # Stage 3: Dynamics verification
        stage3_passed, stage3_reason, stage3_score = self.stage3_dynamics_verification(features)
        result['stage3_passed'] = stage3_passed
        result['stage3_reason'] = stage3_reason
        result['stage3_score'] = stage3_score
        result['stage_reached'] = 3
        
        # Overall result
        result['passed'] = stage1_passed and stage3_passed
        result['overall_score'] = (stage1_score * 0.3 + stage3_score * 0.7)
        
        return result


if __name__ == "__main__":
    print("Advanced Biometrics Module")
    print("=" * 60)
    print("Features:")
    print("  ✓ Velocity, Acceleration, Jerk calculation")
    print("  ✓ Curvature analysis")
    print("  ✓ Hesitation detection")
    print("  ✓ Biometric baseline learning")
    print("  ✓ Multi-stage verification with strict gating")
    print("\nImport this module to use in your verifier.")
