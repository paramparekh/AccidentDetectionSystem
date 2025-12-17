"""
Sequential Estimation Algorithms for Traffic Accident Detection
Implements: ARMA/ARIMA, CUSUM, SPRT, Page-Hinkley
"""

import numpy as np
from scipy import stats
from collections import deque
from statsmodels.tsa.arima.model import ARIMA
from config import Config


class ARIMAPredictor:
    """
    ARIMA model for time-series speed prediction
    """
    def __init__(self, order=(1, 0, 1)):
        self.order = order
        self.history = deque(maxlen=60)  # Keep last 60 readings
        self.model = None
        
    def update(self, speed):
        """Add new speed observation"""
        self.history.append(speed)
        
    def predict(self):
        """
        Predict next speed value using ARIMA
        Returns: predicted speed or current mean if insufficient data
        """
        if len(self.history) < 10:
            # Not enough data, return mean
            return np.mean(self.history) if self.history else Config.NORMAL_SPEED_MEAN
        
        try:
            # Fit ARIMA model
            model = ARIMA(list(self.history), order=self.order)
            fitted = model.fit()
            # Forecast next value
            forecast = fitted.forecast(steps=1)
            return float(forecast[0])
        except:
            # Fallback to moving average
            return np.mean(list(self.history)[-10:])


class CUSUMDetector:
    """
    Cumulative Sum (CUSUM) change detection
    Detects sustained decrease in speed (accident indicator)
    """
    def __init__(self, threshold=None, drift=None):
        self.threshold = threshold or Config.CUSUM_THRESHOLD
        self.drift = drift or Config.CUSUM_DRIFT
        self.cusum_stat = 0.0
        self.baseline = Config.NORMAL_SPEED_MEAN
        
    def update(self, speed, predicted_speed):
        """
        Update CUSUM statistic
        Returns: (cusum_value, is_alert)
        """
        # Calculate residual (negative when speed drops)
        residual = speed - predicted_speed
        
        # Update CUSUM (accumulate negative deviations)
        self.cusum_stat = max(0, self.cusum_stat - residual - self.drift)
        
        # Check threshold
        is_alert = self.cusum_stat > self.threshold
        
        return self.cusum_stat, is_alert
    
    def reset(self):
        """Reset CUSUM statistic"""
        self.cusum_stat = 0.0


class SPRTDetector:
    """
    Sequential Probability Ratio Test (SPRT)
    Tests hypothesis: H0 (normal) vs H1 (accident)
    """
    def __init__(self, threshold_upper=None, threshold_lower=None):
        self.threshold_upper = threshold_upper or Config.SPRT_THRESHOLD_UPPER
        self.threshold_lower = threshold_lower or Config.SPRT_THRESHOLD_LOWER
        self.log_likelihood_ratio = 0.0
        
        # Hypothesis parameters
        self.h0_mean = Config.NORMAL_SPEED_MEAN  # Normal traffic
        self.h0_std = Config.NORMAL_SPEED_STD
        self.h1_mean = Config.ACCIDENT_SPEED_MEAN  # Accident
        self.h1_std = Config.ACCIDENT_SPEED_STD
        
    def update(self, speed):
        """
        Update SPRT likelihood ratio
        Returns: (likelihood_ratio, decision)
        decision: 'accident', 'normal', or 'continue'
        """
        # Calculate likelihoods under both hypotheses
        p_h0 = stats.norm.pdf(speed, self.h0_mean, self.h0_std)
        p_h1 = stats.norm.pdf(speed, self.h1_mean, self.h1_std)
        
        # Avoid division by zero
        if p_h0 > 0:
            # Update log-likelihood ratio
            self.log_likelihood_ratio += np.log(p_h1 / p_h0)
        
        # Make decision
        if self.log_likelihood_ratio >= self.threshold_upper:
            decision = 'accident'
        elif self.log_likelihood_ratio <= self.threshold_lower:
            decision = 'normal'
        else:
            decision = 'continue'
        
        return self.log_likelihood_ratio, decision
    
    def reset(self):
        """Reset likelihood ratio"""
        self.log_likelihood_ratio = 0.0


class PageHinkleyDetector:
    """
    Page-Hinkley test for detecting changes in mean
    Detects both decreases (accidents) and increases (clearance)
    """
    def __init__(self, threshold=None, delta=None):
        self.threshold = threshold or Config.PAGE_HINKLEY_THRESHOLD
        self.delta = delta or Config.PAGE_HINKLEY_DELTA
        self.sum_diff = 0.0
        self.min_sum = 0.0
        self.baseline = Config.NORMAL_SPEED_MEAN
        
    def update(self, speed):
        """
        Update Page-Hinkley statistic
        Returns: (ph_stat, is_change_detected)
        """
        # Calculate difference from baseline
        diff = self.baseline - speed - self.delta
        
        # Update cumulative sum
        self.sum_diff += diff
        
        # Update minimum
        self.min_sum = min(self.min_sum, self.sum_diff)
        
        # Calculate test statistic
        ph_stat = self.sum_diff - self.min_sum
        
        # Check threshold
        is_change = ph_stat > self.threshold
        
        return ph_stat, is_change
    
    def reset(self, new_baseline=None):
        """Reset detector with optional new baseline"""
        if new_baseline:
            self.baseline = new_baseline
        self.sum_diff = 0.0
        self.min_sum = 0.0


class DetectorSuite:
    """
    Holds the state of detectors for a single car
    """
    def __init__(self, car_id):
        self.car_id = car_id
        self.arima = ARIMAPredictor()
        self.cusum = CUSUMDetector()
        self.sprt = SPRTDetector()
        self.page_hinkley = PageHinkleyDetector()
        
        self.speed_history = deque(maxlen=Config.BUFFER_SIZE)
        self.accident_active = False
        self.accident_start_time = None
        self.accident_id = None

    def reset_detectors(self):
        self.cusum.reset()
        self.sprt.reset()
        self.page_hinkley.reset()


class AccidentDetector:
    """
    Main accident detection pipeline
    Manages multiple DetectorSuite instances (one per car)
    """
    def __init__(self):
        # Dictionary mapping car_id -> DetectorSuite
        self.detectors = {}
        
    def get_or_create_suite(self, car_id):
        if car_id not in self.detectors:
            self.detectors[car_id] = DetectorSuite(car_id)
        return self.detectors[car_id]

    def reset_all(self):
        """Reset all detector suites"""
        for suite in self.detectors.values():
            suite.accident_active = False
            suite.reset_detectors()

    def reset_car(self, car_id):
        """Reset detectors for a specific car"""
        if car_id in self.detectors:
            self.detectors[car_id].accident_active = False
            self.detectors[car_id].reset_detectors()

    def process_speed(self, speed_data_list):
        """
        Process incoming speed data for MULTIPLE cars
        Returns: list of detection results
        """
        results = []
        
        # Ensure input is a list (handle legacy single-dict if necessary, though simulator is updated)
        if not isinstance(speed_data_list, list):
            speed_data_list = [speed_data_list]
            
        for data in speed_data_list:
            car_id = data.get('car_id', 'unknown')
            suite = self.get_or_create_suite(car_id)
            
            speed = data['speed']
            timestamp = data['timestamp']
            
            # Update history
            suite.speed_history.append(data)
            suite.arima.update(speed)
            
            # Get prediction
            predicted_speed = suite.arima.predict()
            
            # Run all detectors
            cusum_stat, cusum_alert = suite.cusum.update(speed, predicted_speed)
            sprt_ratio, sprt_decision = suite.sprt.update(speed)
            ph_stat, ph_alert = suite.page_hinkley.update(speed)
            
            # Voting mechanism
            alerts = [cusum_alert, sprt_decision == 'accident', ph_alert]
            vote_count = sum(alerts)
            
            # WARM-UP PERIOD
            has_enough_data = len(suite.speed_history) >= Config.MIN_SAMPLES_FOR_DETECTION
            
            # Determine if accident detected
            accident_detected = bool(has_enough_data and vote_count >= Config.REQUIRE_VOTES)
            
            confidence = vote_count / 3.0
            
            # Update accident state
            if accident_detected and not suite.accident_active:
                suite.accident_active = True
                suite.accident_start_time = timestamp
                suite.accident_id = f"acc_{car_id}_{int(np.random.random() * 1000)}"
                
            elif not accident_detected and suite.accident_active:
                # Check if cleared
                recent_speeds = [d['speed'] for d in list(suite.speed_history)[-5:]]
                if len(recent_speeds) >= 5 and np.mean(recent_speeds) > 40:
                    suite.accident_active = False
                    suite.reset_detectors()
            
            results.append({
                'car_id': car_id,
                'timestamp': timestamp,
                'speed': speed,
                'predicted_speed': round(predicted_speed, 2),
                'cusum_stat': round(cusum_stat, 2),
                'sprt_ratio': round(sprt_ratio, 2),
                'ph_stat': round(ph_stat, 2),
                'accident_detected': accident_detected,
                'accident_active': suite.accident_active,
                'accident_id': suite.accident_id,
                'confidence': round(confidence, 2)
            })
            
        return results
    
    def get_status(self):
        """Get status summary for all cars"""
        status = {}
        for car_id, suite in self.detectors.items():
            status[car_id] = {
                'accident_active': suite.accident_active,
                'history_len': len(suite.speed_history)
            }
        return status
