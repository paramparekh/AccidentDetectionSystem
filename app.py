"""
Flask Application for Real-Time Traffic Accident Detection
"""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import time
import threading
from datetime import datetime

from config import Config
from utils.data_simulator import TrafficSimulator
from models.sequential_estimators import AccidentDetector

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialize components
simulator = TrafficSimulator()
detector = AccidentDetector()

# Global state
active_accidents = []
accident_history = []
simulation_running = False


def data_stream_worker():
    """
    Background worker that generates and processes data
    Runs every UPDATE_INTERVAL seconds
    """
    global simulation_running
    
    while simulation_running:
        try:
            # Generate speed data
            speed_data = simulator.generate_speed_data()
            
            # Generate user report (may be None)
            user_report = simulator.generate_user_report()
            
            # Process through detector
            detection_result = detector.process_speed(speed_data)
            
            # Check for new accident
            if detection_result['accident_detected'] and not any(
                a['id'] == detection_result['accident_id'] for a in active_accidents
            ):
                # New accident detected
                accident = {
                    'id': detection_result['accident_id'],
                    'location': speed_data['location'],
                    'detected_at': detection_result['timestamp'],
                    'initial_speed': speed_data['speed'],
                    'detection_methods': [],
                    'confidence': detection_result['confidence'],
                    'status': 'active'
                }
                
                # Add detection methods
                if detection_result['cusum_alert']:
                    accident['detection_methods'].append('CUSUM')
                if detection_result['sprt_alert']:
                    accident['detection_methods'].append('SPRT')
                if detection_result['ph_alert']:
                    accident['detection_methods'].append('Page-Hinkley')
                if user_report:
                    accident['detection_methods'].append('User Report')
                
                active_accidents.append(accident)
                
                # Emit accident alert
                socketio.emit('accident_alert', accident)
            
            # Check for cleared accidents
            if not detection_result['accident_active'] and active_accidents:
                # Clear all active accidents
                for accident in active_accidents:
                    accident['status'] = 'cleared'
                    accident['cleared_at'] = detection_result['timestamp']
                    accident_history.append(accident)
                    
                    # Emit clearance notification
                    socketio.emit('accident_cleared', {
                        'id': accident['id'],
                        'cleared_at': detection_result['timestamp']
                    })
                
                active_accidents.clear()
            
            # Prepare update payload
            update_data = {
                'timestamp': detection_result['timestamp'],
                'speed': detection_result['speed'],
                'predicted_speed': detection_result['predicted_speed'],
                'cusum_stat': detection_result['cusum_stat'],
                'sprt_ratio': detection_result['sprt_ratio'],
                'ph_stat': detection_result['ph_stat'],
                'accident_detected': detection_result['accident_detected'],
                'confidence': detection_result['confidence'],
                'active_accidents': active_accidents,
                'user_report': user_report,
                'simulator_status': simulator.get_status()
            }
            
            # Emit update to all connected clients
            socketio.emit('traffic_update', update_data)
            
            # Sleep for update interval
            time.sleep(Config.UPDATE_INTERVAL / Config.SIMULATION_SPEED)
            
        except Exception as e:
            print(f"Error in data stream: {e}")
            time.sleep(1)


@app.route('/')
def index():
    """Serve main dashboard"""
    return render_template('index.html')


@app.route('/api/status')
def get_status():
    """Get current system status"""
    return jsonify({
        'simulation_running': simulation_running,
        'active_accidents': active_accidents,
        'detector_status': detector.get_status(),
        'simulator_status': simulator.get_status(),
        'config': {
            'update_interval': Config.UPDATE_INTERVAL,
            'simulation_speed': Config.SIMULATION_SPEED,
            'cusum_threshold': Config.CUSUM_THRESHOLD,
            'sprt_threshold': Config.SPRT_THRESHOLD_UPPER
        }
    })


@app.route('/api/history')
def get_history():
    """Get accident history"""
    return jsonify({
        'history': accident_history[-20:]  # Last 20 accidents
    })


@app.route('/api/inject-accident', methods=['POST'])
def inject_accident():
    """Manually inject an accident for demonstration"""
    data = request.json or {}
    duration = data.get('duration', 120)
    
    result = simulator.inject_accident(duration)
    return jsonify(result)


@app.route('/api/clear-accident', methods=['POST'])
def clear_accident():
    """Manually clear current accident"""
    result = simulator.clear_accident()
    return jsonify(result)


@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f'Client connected: {request.sid}')
    emit('connection_response', {'status': 'connected'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f'Client disconnected: {request.sid}')


@socketio.on('start_simulation')
def handle_start_simulation():
    """Start data simulation"""
    global simulation_running
    
    if not simulation_running:
        simulation_running = True
        # Start background worker thread
        thread = threading.Thread(target=data_stream_worker, daemon=True)
        thread.start()
        emit('simulation_status', {'running': True})
        print('Simulation started')


@socketio.on('stop_simulation')
def handle_stop_simulation():
    """Stop data simulation"""
    global simulation_running
    simulation_running = False
    emit('simulation_status', {'running': False})
    print('Simulation stopped')


@socketio.on('update_config')
def handle_update_config(data):
    """Update configuration parameters"""
    if 'simulation_speed' in data:
        Config.SIMULATION_SPEED = float(data['simulation_speed'])
    if 'noise_level' in data:
        Config.NOISE_LEVEL = float(data['noise_level'])
    if 'cusum_threshold' in data:
        Config.CUSUM_THRESHOLD = float(data['cusum_threshold'])
        detector.cusum.threshold = Config.CUSUM_THRESHOLD
    
    emit('config_updated', {'status': 'success'})


if __name__ == '__main__':
    print("=" * 60)
    print("Traffic Accident Detection System - Demo Mode")
    print("=" * 60)
    print(f"Server starting on http://localhost:5000")
    print("Open your browser and navigate to the URL above")
    print("=" * 60)
    
    # Run with SocketIO
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False)
