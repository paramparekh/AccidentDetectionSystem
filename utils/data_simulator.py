"""
Data Simulator for Traffic Accident Detection System
Generates realistic GPS speed data and user reports for demonstration
"""

import numpy as np
from datetime import datetime, timedelta
import random
from config import Config


class Car:
    """Represents a single simulated car"""
    def __init__(self, car_id):
        self.id = car_id
        self.accident_active = False
        self.accident_start_time = None
        self.accident_duration = 0
        
        # Assign fixed random offsets for map visualization so cars don't overlap perfectly
        self.lat_offset = np.random.normal(0, 0.005)
        self.lon_offset = np.random.normal(0, 0.005)
        
    def check_accident_status(self):
        """Update accident status"""
        if self.accident_active:
            elapsed = (datetime.now() - self.accident_start_time).total_seconds()
            if elapsed >= self.accident_duration:
                self.accident_active = False
                return False
            return True
        else:
            # Random chance of new accident
            # Reduced probability since we now have multiple cars checkng every interval
            if random.random() < (Config.ACCIDENT_PROBABILITY / 2.0):
                self.accident_active = True
                self.accident_start_time = datetime.now()
                self.accident_duration = max(30, np.random.normal(
                    Config.ACCIDENT_DURATION_MEAN,
                    Config.ACCIDENT_DURATION_STD
                ))
                return True
            return False

    def inject_accident(self, duration):
        self.accident_active = True
        self.accident_start_time = datetime.now()
        self.accident_duration = duration

    def clear_accident(self):
        self.accident_active = False


class TrafficSimulator:
    def __init__(self, num_cars=None):
        self.current_time = datetime.now()
        # Initialize cars based on config
        target_cars = num_cars if num_cars is not None else Config.NUM_CARS
        self.cars = [Car(f"Car{i+1}") for i in range(target_cars)]
        
    def _get_time_of_day_factor(self, timestamp):
        """
        Returns speed multiplier based on time of day
        """
        hour = timestamp.hour
        if 7 <= hour < 9: return 0.7
        elif 17 <= hour < 19: return 0.65
        elif hour >= 23 or hour < 5: return 1.2
        else: return 1.0
    
    def generate_speed_data(self):
        """
        Generates realistic GPS speed data for ALL cars
        Returns: list of dicts
        """
        self.current_time = datetime.now()
        time_factor = self._get_time_of_day_factor(self.current_time)
        base_speed_target = Config.NORMAL_SPEED_MEAN * time_factor
        
        results = []
        
        for car in self.cars:
            is_accident = car.check_accident_status()
            
            if is_accident:
                speed = np.random.normal(Config.ACCIDENT_SPEED_MEAN, Config.ACCIDENT_SPEED_STD)
            else:
                speed = np.random.normal(base_speed_target, Config.NORMAL_SPEED_STD)
                speed += np.random.normal(0, Config.NOISE_LEVEL)
            
            speed = max(0, min(speed, 120))
            
            # Wiggle location slightly around the car's general area
            current_lat = Config.DEFAULT_LAT + car.lat_offset + np.random.normal(0, 0.0002)
            current_lon = Config.DEFAULT_LON + car.lon_offset + np.random.normal(0, 0.0002)
            
            results.append({
                'car_id': car.id,
                'timestamp': self.current_time.isoformat(),
                'speed': round(speed, 2),
                'location': {
                    'lat': current_lat,
                    'lon': current_lon
                },
                'confidence': round(random.uniform(0.75, 1.0), 2),
                'is_accident': is_accident
            })
            
        return results
    
    def generate_user_report(self):
        """
        Generates simulated user accident report from a random car if active
        """
        # Pick a random car that is in an accident
        accident_cars = [c for c in self.cars if c.accident_active]
        
        if accident_cars:
            car = random.choice(accident_cars)
            if random.random() < 0.4: # 40% chance of report if accident exists
                return {
                    'timestamp': datetime.now().isoformat(),
                    'type': 'accident',
                    'severity': random.choice(['minor', 'major']),
                    'location': {
                        'lat': Config.DEFAULT_LAT + car.lat_offset,
                        'lon': Config.DEFAULT_LON + car.lon_offset
                    },
                    'user_id': f'user_{random.randint(1000, 9999)}',
                    'car_id': car.id,
                    'description': f'Accident reported near {car.id}'
                }
        return None
    
    def get_status(self):
        """
        Returns status of all cars
        """
        status = {}
        for car in self.cars:
            if car.accident_active:
                elapsed = (datetime.now() - car.accident_start_time).total_seconds()
                status[car.id] = {
                    'accident_active': True,
                    'duration': round(elapsed, 1),
                    'remaining': round(car.accident_duration - elapsed, 1)
                }
            else:
                status[car.id] = {'accident_active': False}
        return status
    
    def inject_accident(self, duration=120, car_id=None):
        """
        Manually inject an accident
        """
        target_car = None
        if car_id:
            target_car = next((c for c in self.cars if c.id == car_id), None)
        
        if not target_car:
            # Pick random car not already in accident
            available_cars = [c for c in self.cars if not c.accident_active]
            if available_cars:
                target_car = random.choice(available_cars)
        
        if target_car:
            target_car.inject_accident(duration)
            return {
                'status': 'accident_injected',
                'car_id': target_car.id,
                'duration': duration
            }
        return {'status': 'failed', 'reason': 'no_cars_available'}
    
    def clear_accident(self, car_id=None):
        """
        Manually clear accident
        """
        if car_id:
            target_car = next((c for c in self.cars if c.id == car_id), None)
            if target_car:
                target_car.clear_accident()
                return {'status': 'cleared', 'car_id': car_id}
        else:
            # Clear all
            count = 0
            for car in self.cars:
                if car.accident_active:
                    car.clear_accident()
                    count += 1
            return {'status': 'cleared_all', 'count': count}

