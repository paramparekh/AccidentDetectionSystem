"""
Data Simulator for Traffic Accident Detection System
Generates realistic GPS speed data and user reports for demonstration
"""

import numpy as np
from datetime import datetime, timedelta
import random
from config import Config


class TrafficSimulator:
    def __init__(self):
        self.current_time = datetime.now()
        self.accident_active = False
        self.accident_start_time = None
        self.accident_duration = 0
        self.accident_location = None
        
    def _get_time_of_day_factor(self, timestamp):
        """
        Returns speed multiplier based on time of day
        Rush hours (7-9 AM, 5-7 PM): slower
        Off-peak: faster
        """
        hour = timestamp.hour
        
        # Morning rush hour (7-9 AM)
        if 7 <= hour < 9:
            return 0.7
        # Evening rush hour (5-7 PM)
        elif 17 <= hour < 19:
            return 0.65
        # Late night (11 PM - 5 AM)
        elif hour >= 23 or hour < 5:
            return 1.2
        # Normal hours
        else:
            return 1.0
    
    def _should_inject_accident(self):
        """
        Determines if an accident should be injected
        """
        if self.accident_active:
            # Check if accident should end
            elapsed = (datetime.now() - self.accident_start_time).total_seconds()
            if elapsed >= self.accident_duration:
                self.accident_active = False
                return False
            return True
        else:
            # Random chance of new accident
            if random.random() < Config.ACCIDENT_PROBABILITY:
                self.accident_active = True
                self.accident_start_time = datetime.now()
                # Random accident duration
                self.accident_duration = max(30, np.random.normal(
                    Config.ACCIDENT_DURATION_MEAN,
                    Config.ACCIDENT_DURATION_STD
                ))
                return True
            return False
    
    def generate_speed_data(self):
        """
        Generates realistic GPS speed data
        Returns: dict with speed, location, timestamp, confidence
        """
        self.current_time = datetime.now()
        
        # Get base speed with time-of-day variation
        time_factor = self._get_time_of_day_factor(self.current_time)
        base_speed = Config.NORMAL_SPEED_MEAN * time_factor
        
        # Check for accident
        is_accident = self._should_inject_accident()
        
        if is_accident:
            # During accident: significant speed drop
            speed = np.random.normal(
                Config.ACCIDENT_SPEED_MEAN,
                Config.ACCIDENT_SPEED_STD
            )
        else:
            # Normal traffic with noise
            speed = np.random.normal(base_speed, Config.NORMAL_SPEED_STD)
            # Add GPS noise
            noise = np.random.normal(0, Config.NOISE_LEVEL)
            speed += noise
        
        # Ensure speed is non-negative and realistic
        speed = max(0, min(speed, 120))
        
        # Add small random variations to location (simulate moving vehicles)
        lat_offset = np.random.normal(0, 0.001)
        lon_offset = np.random.normal(0, 0.001)
        
        return {
            'timestamp': self.current_time.isoformat(),
            'speed': round(speed, 2),
            'location': {
                'lat': Config.DEFAULT_LAT + lat_offset,
                'lon': Config.DEFAULT_LON + lon_offset
            },
            'confidence': round(random.uniform(0.75, 1.0), 2),
            'is_accident': is_accident  # For debugging, won't be in real data
        }
    
    def generate_user_report(self):
        """
        Generates simulated user accident reports
        Returns: dict with report data or None
        """
        if self.accident_active:
            # 80% chance of user reporting actual accident
            if random.random() < 0.8:
                return {
                    'timestamp': datetime.now().isoformat(),
                    'type': 'accident',
                    'severity': random.choice(['minor', 'major', 'major']),  # bias toward major
                    'location': {
                        'lat': Config.DEFAULT_LAT,
                        'lon': Config.DEFAULT_LON
                    },
                    'user_id': f'user_{random.randint(1000, 9999)}',
                    'description': random.choice([
                        'Traffic stopped ahead',
                        'Multiple vehicles involved',
                        'Lane blocked',
                        'Heavy congestion'
                    ])
                }
        else:
            # 5% false positive rate
            if random.random() < 0.05:
                return {
                    'timestamp': datetime.now().isoformat(),
                    'type': 'accident',
                    'severity': 'minor',
                    'location': {
                        'lat': Config.DEFAULT_LAT,
                        'lon': Config.DEFAULT_LON
                    },
                    'user_id': f'user_{random.randint(1000, 9999)}',
                    'description': 'Possible slowdown'
                }
        
        return None
    
    def get_status(self):
        """
        Returns current simulation status
        """
        if self.accident_active:
            elapsed = (datetime.now() - self.accident_start_time).total_seconds()
            return {
                'accident_active': True,
                'duration': round(elapsed, 1),
                'remaining': round(self.accident_duration - elapsed, 1)
            }
        return {
            'accident_active': False
        }
    
    def inject_accident(self, duration=120):
        """
        Manually inject an accident for demonstration
        """
        self.accident_active = True
        self.accident_start_time = datetime.now()
        self.accident_duration = duration
        return {
            'status': 'accident_injected',
            'duration': duration
        }
    
    def clear_accident(self):
        """
        Manually clear current accident
        """
        self.accident_active = False
        return {
            'status': 'accident_cleared'
        }
