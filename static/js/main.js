/**
 * Traffic Accident Detection Dashboard - Main JavaScript
 * Handles WebSocket connections, real-time updates, and UI interactions
 */

// Global variables
let socket;
let map;
let speedChart;
let isMonitoring = false;
let selectedCarId = null;

// Map elements
const carMarkers = {}; // { carId: marker }
const carCircles = {}; // { carId: circle }

// Chart data
// distinct colors for cars
const CAR_COLORS = {
    'Car1': '#3b82f6', // Bright Blue
    'Car2': '#10b981', // Emerald Green
    'Car3': '#f59e0b', // Amber
    'Car4': '#ec4899', // Pink
    'Car5': '#8b5cf6'  // Violet
};
const DEFAULT_COLOR = '#64748b'; // Slate

function getCarColor(carId) {
    return CAR_COLORS[carId] || DEFAULT_COLOR;
}

/**
 * Initialize the application
 */
document.addEventListener('DOMContentLoaded', () => {

    try {
        initializeSocket();
    } catch (e) {
        console.error('Socket init failed:', e);
    }

    try {
        initializeMap();
    } catch (e) {
        console.error('Map init failed:', e);
    }

    try {
        initializeChart();
    } catch (e) {
        console.error('Chart init failed:', e);
    }

    try {
        initializeControls();
    } catch (e) {
        console.error('Controls init failed:', e);
    }
});

/**
 * Initialize Leaflet map
 */
function initializeMap() {
    // Create map centered on default location
    map = L.map('map', {
        zoomControl: false // Cleaner look
    }).setView([37.7749, -122.4194], 14);

    // Add zoom control to top-right
    L.control.zoom({
        position: 'topright'
    }).addTo(map);

    // Add tile layer (dark theme)
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
        maxZoom: 19
    }).addTo(map);
}

/**
 * Initialize Chart.js chart
 */
function initializeChart() {
    const ctx = document.getElementById('speedChart').getContext('2d');
    speedChart = new Chart(ctx, {
        type: 'line',
        data: {
            datasets: []
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Real-Time Vehicle Speeds',
                    color: '#e2e8f0'
                },
                legend: {
                    labels: { color: '#e2e8f0' }
                }
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'second',
                        displayFormats: { second: 'HH:mm:ss' }
                    },
                    grid: { color: '#334155' },
                    ticks: { color: '#94a3b8' },
                    title: { display: true, text: 'Time', color: '#94a3b8' }
                },
                y: {
                    beginAtZero: true,
                    max: 140,
                    grid: { color: '#334155' },
                    ticks: { color: '#94a3b8' },
                    title: { display: true, text: 'Speed (km/h)', color: '#94a3b8' }
                }
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
        showNotification('Connected', 'System ready', 'success');
    });

    socket.on('disconnect', () => {
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
    // Only bind if elements exist
    const startBtn = document.getElementById('startBtn');
    if (startBtn) {
        startBtn.addEventListener('click', () => {
            // Optimistic UI Update
            startBtn.disabled = true;
            startBtn.innerHTML = '<span class="spinner"></span> Starting...';
            document.getElementById('stopBtn').disabled = false;
            document.getElementById('injectBtn').disabled = false;
            document.getElementById('clearBtn').disabled = false;

            socket.emit('start_simulation');
        });
    }

    const stopBtn = document.getElementById('stopBtn');
    if (stopBtn) {
        stopBtn.addEventListener('click', () => {
            // Optimistic UI Update
            stopBtn.disabled = true;
            document.getElementById('startBtn').disabled = false;
            document.getElementById('startBtn').innerHTML = '<span class="btn-icon">▶️</span> <span>Start Simulation</span>';
            document.getElementById('injectBtn').disabled = true;
            document.getElementById('clearBtn').disabled = true;

            socket.emit('stop_simulation');
        });
    }

    const injectBtn = document.getElementById('injectBtn');
    if (injectBtn) {
        injectBtn.addEventListener('click', () => {
            // Visual feedback
            const originalText = injectBtn.innerHTML;
            injectBtn.innerHTML = '⚠️ Injecting...';
            setTimeout(() => { injectBtn.innerHTML = originalText; }, 1000);

            injectAccident();
        });
    }

    const clearBtn = document.getElementById('clearBtn');
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            // Visual feedback
            const originalText = clearBtn.innerHTML;
            clearBtn.innerHTML = '✅ Clearing...';
            setTimeout(() => { clearBtn.innerHTML = originalText; }, 1000);

            clearAccident();
        });
    }

    // Modal Logic
    const modal = document.getElementById('helpModal');
    const btn = document.getElementById('helpBtn');
    const closeBtns = document.getElementsByClassName('close-modal');

    if (modal && btn) {
        btn.onclick = (e) => {
            e.preventDefault();
            modal.style.display = 'block';
        }
    }

    if (closeBtns.length > 0) {
        for (let span of closeBtns) {
            span.onclick = () => {
                modal.style.display = 'none';
            }
        }
    }

    window.onclick = (event) => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    }
}


/**
 * Inject accident
 */
function injectAccident() {
    const payload = { duration: 120 };
    if (selectedCarId) payload.car_id = selectedCarId;

    fetch('/api/inject-accident', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
        .then(r => r.json())
        .then(d => showNotification('Accident Injected', `Target: ${d.car_id || 'Random'}`, 'warning'));
}

/**
 * Clear accidents (All cars)
 */
function clearAccident() {
    // Clear all by not sending a specific car_id
    const payload = {};

    fetch('/api/clear-accident', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
        .then(r => r.json())
        .then(d => showNotification('System Reset', 'All accident states cleared', 'success'));
}

function updateControlButtons() {
    // Only update if we want to sync with server state, but keep optimistic updates priority if needed.
    // Actually, server state confirmation is good to ensure we don't desync.
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    const injectBtn = document.getElementById('injectBtn');
    const clearBtn = document.getElementById('clearBtn');

    if (startBtn && stopBtn) {
        if (isMonitoring) {
            startBtn.disabled = true;
            startBtn.innerHTML = '<span class="spinner"></span> Running';
            stopBtn.disabled = false;
            if (injectBtn) injectBtn.disabled = false;
            if (clearBtn) clearBtn.disabled = false;
        } else {
            startBtn.disabled = false;
            startBtn.innerHTML = '<span class="btn-icon">▶️</span> <span>Start Simulation</span>';
            stopBtn.disabled = true;
            if (injectBtn) injectBtn.disabled = true;
            if (clearBtn) injectBtn.disabled = true;
        }
    }
}

/**
 * Update dashboard
 */
function updateDashboard(data) {
    const cars = data.cars;

    // Auto-select first car if none selected or if selected is gone
    if (cars.length > 0) {
        const stillExists = cars.find(c => c.car_id === selectedCarId);
        if (!selectedCarId || !stillExists) {
            selectedCarId = cars[0].car_id;
        }
    }

    const activeAccidentsElem = document.getElementById('activeAccidents');
    if (activeAccidentsElem) activeAccidentsElem.textContent = data.active_accidents.length;

    updateMap(cars);
    updateChart(cars); // Pass all cars to chart

    // Update Stats for SELECTED car only
    if (selectedCarId) {
        const carData = cars.find(c => c.car_id === selectedCarId);
        if (carData) {
            updateStats(carData);
        }
    }

    // Update Badge
    const activeCount = data.active_accidents.length;
    const badge = document.getElementById('statusBadge');
    if (badge) {
        if (activeCount > 0) {
            badge.classList.add('alert');
            badge.innerHTML = `<span class="status-dot"></span>🚨 ${activeCount} Alert(s)`;
            // Ensure dot is visible
            badge.querySelector('.status-dot').style.display = 'inline-block';
        } else {
            badge.classList.remove('alert');
            // Hide text when normal, just show dot or nothing if requested
            badge.innerHTML = `<span class="status-dot"></span>System Normal`;
        }
    }
}

/**
 * Update Map
 */
function updateMap(cars) {
    // Check for global accident state
    const anyAccident = cars.some(car => car.accident_active || car.accident_detected);

    cars.forEach(car => {
        const carId = car.car_id;
        const lat = car.location?.lat || 37.7749;
        const lon = car.location?.lon || -122.4194;
        // Individual accident state for markers (optional to keep, or sync with global?)
        // User asked for "color of location" to be red if anyone has accident.
        const isAccident = car.accident_active || car.accident_detected;

        // Custom Markers
        let iconUrl = 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png';
        if (isAccident) iconUrl = 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png';
        else if (carId === selectedCarId) iconUrl = 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png';

        if (carMarkers[carId]) {
            carMarkers[carId].setLatLng([lat, lon]);
            carMarkers[carId].setIcon(createIcon(iconUrl));
            // Update popup content dynamically
            const popupContent = `
                <div style="font-family: Inter, sans-serif;">
                    <b>${carId}</b><br>
                    <span style="color: ${isAccident ? '#ef4444' : '#10b981'}">
                        ${car.speed.toFixed(1)} mph
                    </span>
                </div>
            `;
            const popup = carMarkers[carId].getPopup();
            if (popup) popup.setContent(popupContent);
        } else {
            carMarkers[carId] = L.marker([lat, lon], { icon: createIcon(iconUrl) })
                .addTo(map)
                .bindPopup(`<b>${carId}</b>`);

            // Add click listener to select car
            carMarkers[carId].on('click', () => {
                selectedCarId = carId;
            });
        }

        if (carCircles[carId]) {
            carCircles[carId].setLatLng([lat, lon]);
            // Logic: Red if ANY accident, Green if ALL clear.
            carCircles[carId].setStyle({ color: anyAccident ? '#ef4444' : '#10b981' });
        } else {
            // Initial style
            carCircles[carId] = L.circle([lat, lon], {
                radius: 200,
                fillOpacity: 0.1,
                weight: 1,
                color: anyAccident ? '#ef4444' : '#10b981'
            }).addTo(map);
        }
    });
}

function createIcon(url) {
    return L.icon({
        iconUrl: url,
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
    });
}

/**
 * Update Stats
 */
function updateStats(data) {
    const setText = (id, txt) => {
        const el = document.getElementById(id);
        if (el) el.textContent = txt;
    };

    setText('currentSpeed', `${data.speed.toFixed(1)} mph`);
    setText('predictedSpeed', `${data.predicted_speed.toFixed(1)} mph`);

    const predEl = document.getElementById('predictedSpeed');
    if (predEl) predEl.style.fontSize = "1.75rem";

    setText('cusumStat', data.cusum_stat.toFixed(2));
    setText('sprtRatio', data.sprt_ratio.toFixed(2));
    setText('confidence', `${(data.confidence * 100).toFixed(0)}%`);
}

/**
 * Update Chart (Scatter)
 */
function updateChart(cars) {
    const now = new Date();

    cars.forEach(car => {
        let dataset = speedChart.data.datasets.find(ds => ds.label === car.car_id);
        if (!dataset) {
            const color = getCarColor(car.car_id);
            dataset = {
                label: car.car_id,
                data: [],
                borderColor: color,
                backgroundColor: color,
                pointRadius: 3,
                pointHoverRadius: 6,
                showLine: false // Pure scatter
            };
            speedChart.data.datasets.push(dataset);
        }

        dataset.data.push({
            x: now,
            y: car.speed
        });

        // Keep max 50 points per car
        if (dataset.data.length > 50) {
            dataset.data.shift();
        }
    });

    speedChart.update('none');
}

function handleAccidentAlert(accident) {
    showNotification('⚠️ ACCIDENT DETECTED', `Vehicle: ${accident.car_id}`, 'warning');
    addAlertToPanel(accident);
}

function handleAccidentCleared(data) {
    showNotification('✅ CLEARED', `Car: ${data.car_id}`, 'success');
    updateAlertInPanel(data.id, 'cleared');
}

function addAlertToPanel(accident) {
    const container = document.getElementById('alertsContainer');
    if (!container) return;

    const emptyState = container.querySelector('.empty-state');
    if (emptyState) emptyState.remove();

    const div = document.createElement('div');
    div.className = 'alert-item';
    div.id = `alert-${accident.id}`;
    div.innerHTML = `<div style="display:flex; justify-content:space-between; align-items:center;">
        <strong>⚠️ ${accident.car_id}</strong>
        <span style="font-size:0.75rem; background:#ef4444; color:white; padding:2px 6px; border-radius:4px;">ACTIVE</span>
    </div>`;
    container.insertBefore(div, container.firstChild);
}

function updateAlertInPanel(id, status) {
    const el = document.getElementById(`alert-${id}`);
    if (el) {
        const badge = el.querySelector('span');
        if (badge) {
            badge.textContent = 'CLEARED';
            badge.style.background = '#10b981';
        }
        el.classList.add('cleared');
    }
}

function showNotification(title, msg, type = 'info') {
    const c = document.getElementById('notificationContainer');
    if (!c) return;

    const n = document.createElement('div');
    n.className = `notification ${type}`;
    n.innerHTML = `<strong>${title}</strong><br>${msg}`;
    c.appendChild(n);
    setTimeout(() => { n.remove(); }, 4000);
}
