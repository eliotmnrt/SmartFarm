from flask import Flask, request, render_template_string
import datetime
import json

app = Flask(__name__)
measurements = {}

# --- SEUILS ---
IDEAL_TEMP_MIN, IDEAL_TEMP_MAX = 18.0, 28.0
IDEAL_HUM_MIN, IDEAL_HUM_MAX = 40.0, 70.0

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>SmartFarm Live</title>
    <meta http-equiv="refresh" content="3">
    <meta charset="UTF-8">
    <style>
        body { font-family: 'Segoe UI', sans-serif; padding: 20px; background: #eef2f3; color: #333; }
        h1 { text-align: center; color: #2c3e50; font-weight: 300; margin-bottom: 40px; }
        
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 25px; }
        
        .card { 
            background: white; 
            padding: 20px; 
            border-radius: 15px; 
            box-shadow: 0 10px 25px rgba(0,0,0,0.05); 
            position: relative; 
            overflow: hidden; /* Important pour contenir la notif */
            transition: transform 0.3s ease;
        }
        .card:hover { transform: translateY(-5px); }

        .id { font-weight: bold; font-size: 1.2em; color: #34495e; margin-bottom: 15px; }
        .measure { display: flex; justify-content: space-between; margin: 10px 0; font-size: 1.1em; }
        .val { font-weight: bold; color: #555; }
        .time { font-size: 0.8em; color: #bdc3c7; text-align: right; margin-top: 20px; }

        /* --- STYLE DES NOTIFICATIONS (TOASTS) --- */
        .toast {
            position: absolute;
            top: 15px;
            right: 15px;
            padding: 8px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: bold;
            display: flex;
            align-items: center;
            gap: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            
            /* L'animation magique */
            animation: slideInRight 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards;
            transform: translateX(120%); /* Caché par défaut */
        }

        /* Types de notifications */
        .toast-ideal { 
            background: linear-gradient(135deg, #d4fc79 0%, #96e6a1 100%); 
            color: #1e6b28; 
        }
        .toast-warning { 
            background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 99%, #fecfef 100%); 
            color: #c0392b; 
        }

        /* L'animation Keyframes */
        @keyframes slideInRight {
            0% { transform: translateX(100%); opacity: 0; }
            100% { transform: translateX(0); opacity: 1; }
        }

        /* Icône animée */
        .icon-pulse { animation: pulse 2s infinite; }
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.2); }
            100% { transform: scale(1); }
        }

        .waiting { text-align: center; color: #999; margin-top: 50px; }
    </style>
</head>
<body>
    <h1>🌱 Monitoring Temps Réel</h1>
    <div class="grid">
        {% for id, data in sensors.items() %}
        <div class="card">
            
            {% if data.status == 'IDEAL' %}
            <div class="toast toast-ideal">
                <span class="icon-pulse">✨</span> Conditions idéales
            </div>
            {% elif data.status == 'WARNING' %}
            <div class="toast toast-warning">
                <span class="icon-pulse">⚠️</span> Attention !
            </div>
            {% endif %}

            <div class="id">{{ id }}</div>
            <div class="measure"><span>Température</span> <span class="val">{{ data.temp_str }}</span></div>
            <div class="measure"><span>Humidité</span> <span class="val">{{ data.hum_str }}</span></div>
            <div class="time">{{ data.time }}</div>
        </div>
        {% else %}
        <div class="waiting">En attente de connexion...</div>
        {% endfor %}
    </div>
</body>
</html>
"""

def extract_value(item, keys):
    for key in keys:
        val = item.get(key)
        if val is not None:
            if isinstance(val, dict): return val.get('value', None)
            return val
    return None

@app.route('/notify', methods=['POST'])
def notify():
    try:
        content = request.json
        if 'data' in content:
            for item in content['data']:
                device_id = item.get('id')
                
                # Extraction
                raw_t = extract_value(item, ['t', 'temp', 'temperature', 'temperature_air', 'Temperature'])
                raw_h = extract_value(item, ['h', 'hum', 'humidity', 'humidity_air', 'Humidity'])
                
                # Logique Notification
                status = None
                if isinstance(raw_t, (int, float)) and isinstance(raw_h, (int, float)):
                    if (IDEAL_TEMP_MIN <= raw_t <= IDEAL_TEMP_MAX) and (IDEAL_HUM_MIN <= raw_h <= IDEAL_HUM_MAX):
                        status = "IDEAL"
                    elif (raw_t < 5 or raw_t > 35):
                        status = "WARNING"
                
                measurements[device_id] = {
                    'temp_str': f"{raw_t} °C" if raw_t is not None else "--",
                    'hum_str': f"{raw_h} %" if raw_h is not None else "--",
                    'status': status,
                    'time': datetime.datetime.now().strftime("%H:%M:%S")
                }
        return "OK", 200
    except:
        return "Error", 500

@app.route('/')
def index():
    return render_template_string(HTML, sensors=measurements)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)