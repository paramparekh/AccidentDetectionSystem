/**
 * Traffic Accident Detection Dashboard - Main JavaScript
 * Handles WebSocket connections, real-time updates, and UI interactions
 */

// Global variables
let socket;
let map;
let marker;
let circle;
let speedChart;
let isMonitoring = false;

// Chart data
const maxDataPoints = 30;
const chartData = {
    labels: [],
    speeds: [],
    predicted: [],
    cusum: []
};

/**
 * Initialize the application
 */
document.addEventListener('DOMContentLoaded', () => {
    initializeMap();
    initializeChart();
    initializeSocket();
    initializeControls();
});

/**
 * Initialize Leaflet map
 */
function initializeMap() {
    // Create map centered on default location
    map = L.map('map').setView([37.7749, -122.4194], 13);
    
    // Add tile layer (dark theme)
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
        maxZoom: 19
    }).addTo(map);
    
    // Add marker for road segment
    marker = L.marker([37.7749, -122.4194]).addTo(map);
    marker.bindPopup('<b>Highway 101</b><br>Monitoring Point');
    
    // Add circle to show monitoring area
    circle = L.circle([37.7749, -122.4194], {
        color: '#10b981',
        fillColor: '#10b981',
        fillOpacity: 0.2,
        radius: 500
    }).addTo(map);
}

/**
 * Initialize Chart.js speed chart
 */
function initializeChart() {
    const ctx = document.getElementById('speedChart').getContext('2d');
    
    speedChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: chartData.labels,
            datasets: [
                {
                    label: 'Actual Speed',
                    data: chartData.speeds,
                    borderColor: '#00d4ff',
                    backgroundColor: 'rgba(0, 212, 255, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true
                },
                {
                    label: 'Predicted Speed (ARIMA)',
                    data: chartData.predicted,
                    borderColor: '#7c3aed',
                    backgroundColor: 'transparent',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    tension: 0.4,
                    fill: false
                },
                {
                    label: 'CUSUM Statistic',
                    data: chartData.cusum,
                    borderColor: '#f59e0b',
                    backgroundColor: 'transparent',
                    borderWidth: 1,
                    tension: 0.4,
                    fill: false,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    display: true,
                    labels: {
                        color: '#94a3b8',
                        font: {
                            size: 11
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(26, 35, 71, 0.9)',
                    titleColor: '#ffffff',
                    bodyColor: '#94a3b8',
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 1
                }
            },
            scales: {
                x: {
                    display: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    },
                    ticks: {
                        color: '#64748b',
                        maxRotation: 0,
                        autoSkip: true,
                        maxTicksLimit: 8
                    }
                },
                y: {
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Speed (mph)',
                        color: '#94a3b8'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    },
                    ticks: {
                        color: '#64748b'
                    }
                },
                y1: {
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'CUSUM',
                        color: '#94a3b8'
                    },
                    grid: {
                        drawOnChartArea: false
                    },
                    ticks: {
                        color: '#64748b'
                    }
                }
            },
            animation: {
                duration: 300
            }
        }
    });
}

/**
 * Initialize Socket.IO connection
 */
function initializeSocket() {
    socket = io();
    
    socket.on('connect', () => {
        console.log('Connected to server');
        showNotification('Connected to server', 'System ready', 'success');
    });
    
    socket.on('disconnect', () => {
        console.log('Disconnected from server');
        showNotification('Disconnected', 'Connection lost', 'danger');
    });
    
    socket.on('traffic_update', (data) => {
        updateDashboard(data);
    });
    
    socket.on('accident_alert', (accident) => {
        handleAccidentAlert(accident);
    });
    
    socket.on('accident_cleared', (data) => {
        handleAccidentCleared(data);
    });
    
    socket.on('simulation_status', (data) => {
        isMonitoring = data.running;
        updateControlButtons();
    });
}

/**
 * Initialize control buttons
 */
function initializeControls() {
    document.getElementById('startBtn').addEventListener('click', startMonitoring);
    document.getElementById('stopBtn').addEventListener('click', stopMonitoring);
    document.getElementById('injectBtn').addEventListener('click', injectAccident);
    document.getElementById('clearBtn').addEventListener('click', clearAccident);
}

/**
 * Start monitoring
 */
function startMonitoring() {
    socket.emit('start_simulation');
    isMonitoring = true;
    updateControlButtons();
    showNotification('Monitoring Started', 'Real-time traffic monitoring active', 'success');
}

/**
 * Stop monitoring
 */
function stopMonitoring() {
    socket.emit('stop_simulation');
    isMonitoring = false;
    updateControlButtons();
    showNotification('Monitoring Stopped', 'Traffic monitoring paused', 'warning');
}

/**
 * Inject accident for demo
 */
function injectAccident() {
    fetch('/api/inject-accident', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ duration: 120 })
    })
    .then(response => response.json())
    .then(data => {
        showNotification('Accident Injected', 'Demo accident scenario activated', 'warning');
    });
}

/**
 * Clear accident
 */
function clearAccident() {
    fetch('/api/clear-accident', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        showNotification('Accident Cleared', 'Manually cleared accident', 'success');
    });
}

/**
 * Update control buttons state
 */
function updateControlButtons() {
    document.getElementById('startBtn').disabled = isMonitoring;
    document.getElementById('stopBtn').disabled = !isMonitoring;
    document.getElementById('injectBtn').disabled = !isMonitoring;
    document.getElementById('clearBtn').disabled = !isMonitoring;
}

/**
 * Update dashboard with new data
 */
function updateDashboard(data) {
    // Update statistics
    document.getElementById('currentSpeed').textContent = `${data.speed} mph`;
    document.getElementById('predictedSpeed').textContent = `${data.predicted_speed} mph`;
    document.getElementById('cusumStat').textContent = data.cusum_stat.toFixed(2);
    document.getElementById('sprtRatio').textContent = data.sprt_ratio.toFixed(2);
    document.getElementById('confidence').textContent = `${(data.confidence * 100).toFixed(0)}%`;
    document.getElementById('activeAccidents').textContent = data.active_accidents.length;
    
    // Update status badge
    const statusBadge = document.getElementById('statusBadge');
    const statusText = document.getElementById('statusText');
    
    if (data.accident_detected) {
        statusBadge.classList.add('alert');
        statusText.textContent = '🚨 Accident Detected';
    } else {
        statusBadge.classList.remove('alert');
        statusText.textContent = '✅ All Clear';
    }
    
    // Update map
    if (data.accident_detected) {
        circle.setStyle({ color: '#ef4444', fillColor: '#ef4444' });
        marker.setIcon(L.icon({
            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
            shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
            shadowSize: [41, 41]
        }));
    } else {
        circle.setStyle({ color: '#10b981', fillColor: '#10b981' });
        marker.setIcon(L.icon({
            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
            shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
            shadowSize: [41, 41]
        }));
    }
    
    // Update chart
    updateChart(data);
}

/**
 * Update speed chart
 */
function updateChart(data) {
    const timestamp = new Date(data.timestamp).toLocaleTimeString();
    
    // Add new data
    chartData.labels.push(timestamp);
    chartData.speeds.push(data.speed);
    chartData.predicted.push(data.predicted_speed);
    chartData.cusum.push(data.cusum_stat);
    
    // Keep only last N points
    if (chartData.labels.length > maxDataPoints) {
        chartData.labels.shift();
        chartData.speeds.shift();
        chartData.predicted.shift();
        chartData.cusum.shift();
    }
    
    // Update chart
    speedChart.update('none');
}

/**
 * Handle accident alert
 */
function handleAccidentAlert(accident) {
    // Show notification
    showNotification(
        '⚠️ ACCIDENT DETECTED',
        `Location: Highway 101 | Confidence: ${(accident.confidence * 100).toFixed(0)}%`,
        'danger'
    );
    
    // Add to alerts panel
    addAlertToPanel(accident);
    
    // Play alert sound (optional)
    // new Audio('/static/sounds/alert.mp3').play();
}

/**
 * Handle accident cleared
 */
function handleAccidentCleared(data) {
    showNotification(
        '✅ ACCIDENT CLEARED',
        'Traffic has returned to normal',
        'success'
    );
    
    // Update alert in panel
    updateAlertInPanel(data.id, 'cleared');
}

/**
 * Add alert to alerts panel
 */
function addAlertToPanel(accident) {
    const container = document.getElementById('alertsContainer');
    
    // Remove empty state if exists
    const emptyState = container.querySelector('.empty-state');
    if (emptyState) {
        emptyState.remove();
    }
    
    // Create alert element
    const alertEl = document.createElement('div');
    alertEl.className = 'alert-item';
    alertEl.id = `alert-${accident.id}`;
    
    const methods = accident.detection_methods.map(m => 
        `<span class="method-tag">${m}</span>`
    ).join('');
    
    alertEl.innerHTML = `
        <div class="alert-header">
            <span class="alert-title">⚠️ Accident Detected</span>
            <span class="alert-badge active">ACTIVE</span>
        </div>
        <div class="alert-details">
            <div>Location: Highway 101, Mile 23.5</div>
            <div>Detected: ${new Date(accident.detected_at).toLocaleTimeString()}</div>
            <div>Confidence: ${(accident.confidence * 100).toFixed(0)}%</div>
            <div class="alert-methods">${methods}</div>
        </div>
    `;
    
    container.insertBefore(alertEl, container.firstChild);
}

/**
 * Update alert in panel
 */
function updateAlertInPanel(accidentId, status) {
    const alertEl = document.getElementById(`alert-${accidentId}`);
    if (alertEl) {
        alertEl.classList.add('cleared');
        const badge = alertEl.querySelector('.alert-badge');
        badge.textContent = 'CLEARED';
        badge.classList.remove('active');
        badge.classList.add('cleared');
    }
}

/**
 * Show notification toast
 */
function showNotification(title, message, type = 'info') {
    const container = document.getElementById('notificationContainer');
    
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    
    const icon = type === 'success' ? '✅' : type === 'danger' ? '⚠️' : 'ℹ️';
    
    notification.innerHTML = `
        <div class="notification-header">
            <span class="notification-icon">${icon}</span>
            <span class="notification-title">${title}</span>
        </div>
        <div class="notification-body">${message}</div>
    `;
    
    container.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        notification.style.animation = 'slideInRight 0.3s ease reverse';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}
