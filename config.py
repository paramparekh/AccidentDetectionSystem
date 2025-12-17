"""
Configuration settings for Traffic Accident Detection System
"""

class Config:
    # Flask settings
    SECRET_KEY = 'dev-secret-key-change-in-production'
    DEBUG = True
    
    # Simulation settings
    SIMULATION_SPEED = 1.0  # 1x real-time
    UPDATE_INTERVAL = 2.0  # seconds between updates
    NOISE_LEVEL = 5.0  # GPS noise in mph
    ACCIDENT_PROBABILITY = 0.03  # Probability of accident per interval (3% = ~1 accident per 67 seconds)
    
    # Traffic parameters
    NORMAL_SPEED_MEAN = 60.0  # mph
    NORMAL_SPEED_STD = 10.0  # mph
    ACCIDENT_SPEED_MEAN = 15.0  # mph during accident
    ACCIDENT_SPEED_STD = 5.0  # mph
    ACCIDENT_DURATION_MEAN = 120.0  # seconds
    ACCIDENT_DURATION_STD = 30.0  # seconds
    
    # Detection algorithm parameters
    CUSUM_THRESHOLD = 10.0
    CUSUM_DRIFT = 2.0
    SPRT_THRESHOLD_UPPER = 5.0
    SPRT_THRESHOLD_LOWER = 0.2
    PAGE_HINKLEY_THRESHOLD = 8.0
    PAGE_HINKLEY_DELTA = 2.0
    
    # Data buffer settings
    BUFFER_SIZE = 300  # seconds of history to keep
    MIN_SAMPLES_FOR_DETECTION = 10  # minimum samples before detection (20 seconds warm-up)
    
    # Detection confidence
    MIN_CONFIDENCE = 0.7
    REQUIRE_VOTES = 2  # out of 3 tests must agree
    
    # Map settings (default location: San Francisco)
    DEFAULT_LAT = 37.7749
    DEFAULT_LON = -122.4194
    MAP_ZOOM = 13
