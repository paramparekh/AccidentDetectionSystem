# 🚀 Quick Start Guide

## Installation (5 minutes)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run the Application
```bash
python app.py
```

### Step 3: Open in Browser
Navigate to: **http://localhost:5000**

---

## First-Time Demo (2 minutes)

1. **Click "Start Monitoring"** button
   - Dashboard will come alive with real-time updates
   - Speed chart starts updating every 2 seconds
   - Map shows green status (normal traffic)

2. **Click "Inject Accident (Demo)"** button
   - Watch the system detect the accident within 3-6 seconds
   - Map marker turns red
   - Alert notification appears
   - Speed chart shows sharp drop
   - CUSUM statistic crosses threshold

3. **Observe Accident Tracking**
   - System monitors accident persistence
   - Alert panel shows detection methods used
   - Statistics update in real-time

4. **Watch Automatic Clearance**
   - After ~2 minutes, traffic normalizes
   - System automatically detects clearance
   - Green notification appears
   - Map returns to green

---

## For Interviews/Demos

### 30-Second Pitch
*"This is a real-time traffic accident detection system I built. It uses statistical algorithms like CUSUM and SPRT to analyze GPS speed data and detect accidents within seconds. Let me show you..."*

### 2-Minute Demo Script

1. **"Here's the live dashboard monitoring traffic"** *(point to 4 panels)*

2. **"I'll inject an accident scenario"** *(click button)*
   - "Watch how quickly it detects the speed drop"
   - "The CUSUM statistic crosses the threshold here"
   - "Multiple algorithms agree - CUSUM, SPRT, and Page-Hinkley"

3. **"The system tracks the accident in real-time"** *(show chart)*
   - "Blue line is actual speed, purple is ARIMA prediction"
   - "You can see the confidence level is 94%"

4. **"And it automatically detects when traffic clears"** *(wait for clearance)*
   - "Green notification, map turns green, all back to normal"

5. **"Behind the scenes"** *(optional technical deep-dive)*
   - "Flask backend with WebSocket for real-time streaming"
   - "ARIMA for time-series prediction"
   - "Voting mechanism requires 2 out of 3 tests to agree"
   - "Sub-second latency from detection to alert"

---

## Troubleshooting

### Port 5000 already in use
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# macOS/Linux
lsof -ti:5000 | xargs kill -9
```

### Dependencies fail to install
```bash
# Try upgrading pip first
python -m pip install --upgrade pip

# Then retry
pip install -r requirements.txt
```

### Chart not showing
- Hard refresh browser: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
- Check browser console for errors (F12)

---

## Next Steps

### For Your Resume
1. Take screenshots of the dashboard
2. Record a short demo video (30-60 seconds)
3. Use the resume bullet points from README.md
4. Add GitHub repo link

### To Deploy Online
1. Create GitHub repository
2. Push code: `git remote add origin <url>` then `git push -u origin master`
3. Deploy to Heroku (free tier):
   ```bash
   # Install Heroku CLI, then:
   heroku create your-app-name
   git push heroku master
   heroku open
   ```

### To Extend to Production Mode
1. Add REST API endpoints in `app.py`:
   ```python
   @app.route('/api/ingest/gps', methods=['POST'])
   def ingest_gps_data():
       # Handle real GPS data
   ```
2. Update README to mention production capability
3. Add API documentation

---

## Project Structure

```
Lab 5/
├── app.py                          # Flask application & WebSocket server
├── config.py                       # Configuration parameters
├── requirements.txt                # Python dependencies
├── README.md                       # Full documentation
│
├── models/
│   ├── __init__.py
│   └── sequential_estimators.py    # ARIMA, CUSUM, SPRT, Page-Hinkley
│
├── utils/
│   ├── __init__.py
│   └── data_simulator.py           # Traffic data generator
│
├── templates/
│   └── index.html                  # Dashboard HTML
│
└── static/
    ├── css/
    │   └── index.css               # Styles & design system
    └── js/
        └── main.js                 # WebSocket client & UI logic
```

---

## Key Files to Show Recruiters

1. **`models/sequential_estimators.py`** - Your algorithm implementations
2. **`app.py`** - Backend architecture with WebSocket
3. **`static/js/main.js`** - Real-time frontend updates
4. **`README.md`** - Professional documentation

---

**🎯 You're ready to impress recruiters! Good luck with your SDE applications!**
