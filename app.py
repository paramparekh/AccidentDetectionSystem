"""
Flask Application for Real-Time Traffic Accident Detection
"""

import eventlet
eventlet.monkey_patch()

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
socketio = SocketIO(app, cors_allowed_origins="*")

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
            # Generate speed data for ALL cars (returns list)
            speed_data_list = simulator.generate_speed_data()
            
            # Generate user report (may be None)
            user_report = simulator.generate_user_report()
            
            # Process through detector (returns list of results)
            detection_results = detector.process_speed(speed_data_list)
            
            # Check each car for new accidents
            for i, result in enumerate(detection_results):
                car_id = result['car_id']
                
                if result['accident_detected'] and not any(
                    a['id'] == result['accident_id'] for a in active_accidents
                ):
                    # New accident detected for this car
                    accident = {
                        'id': result['accident_id'],
                        'car_id': car_id,
                        'location': speed_data_list[i]['location'],
                        'detected_at': result['timestamp'],
                        'initial_speed': result['speed'],
                        'detection_methods': ['CUSUM', 'SPRT', 'Page-Hinkley'],  # Simplified
                        'confidence': result['confidence'],
                        'status': 'active'
                    }
                    
                    if user_report and user_report.get('car_id') == car_id:
                        accident['detection_methods'].append('User Report')
                    
                    active_accidents.append(accident)
                    
                    # Emit accident alert
                    socketio.emit('accident_alert', accident)
            
            # Check for cleared accidents
            cleared_ids = []
            for accident in active_accidents:
                # Find corresponding detection result
                car_result = next((r for r in detection_results if r.get('accident_id') == accident['id']), None)
                if car_result and not car_result['accident_active']:
                    accident['status'] = 'cleared'
                    accident['cleared_at'] = car_result['timestamp']
                    accident_history.append(accident)
                    cleared_ids.append(accident['id'])
                    
                    # Emit clearance notification
                    socketio.emit('accident_cleared', {
                        'id': accident['id'],
                        'car_id': accident['car_id'],
                        'cleared_at': car_result['timestamp']
                    })
            
            # Remove cleared accidents
            active_accidents[:] = [a for a in active_accidents if a['id'] not in cleared_ids]
            
            # Prepare update payload with ALL car data
            update_data = {
                'timestamp': detection_results[0]['timestamp'] if detection_results else datetime.now().isoformat(),
                'cars': detection_results,  # List of all car states
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
            import traceback
            traceback.print_exc()
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
    car_id = data.get('car_id', None)
    
    result = simulator.inject_accident(duration, car_id)
    return jsonify(result)


@app.route('/api/clear-accident', methods=['POST'])
def clear_accident():
    """Manually clear current accident"""
    data = request.json or {}
    car_id = data.get('car_id', None)
    
    result = simulator.clear_accident(car_id)
    
    # Synchronize detector state
    if car_id:
        detector.reset_car(car_id)
    else:
        detector.reset_all()
        
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
        socketio.emit('simulation_status', {'running': True})
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
    import os
    port = int(os.environ.get('PORT', 5000))
    print("=" * 60)
    print("Traffic Accident Detection System - Production Mode")
    print("=" * 60)
    print(f"Server starting on port {port}")
    print("=" * 60)
    
    # Run with SocketIO
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
