import pandas as pd
import requests
import time

# Configuration
IOT_AGENT_URL = "http://localhost:7896/iot/json"
API_KEY = "4jggokgpepnvsb2uv4s40d59ov"
CSV_FILE = "docker/serviceIA/donnees_spatiales_cluster.csv"

# Chargement
df = pd.read_csv(CSV_FILE)
df['timestamp'] = pd.to_datetime(df['timestamp'])

print(f"🚀 Simulation avec horodatage réel...")

for timestamp, group in df.groupby('timestamp'):
    # On convertit le timestamp en string ISO 8601
    # Ex: "2024-01-15T14:30:00.000Z"
    iso_date = timestamp.isoformat()
    
    print(f"⏱️ Envoi du paquet : {iso_date}")
    
    for _, row in group.iterrows():
        device_id = row['cluster_id']
        
        payload = {
            "date": iso_date,
            "ta": row['temperature'],
            "ts": row['soilTemperature'],
            "ha": row['humidity'],
            "hs": row['soilMoisture'],
            "n":  row['azote_mg_kg'],
            "p":  row['phosphore_mg_kg'],
            "k":  row['potassium_mg_kg'],
            "ph": row['ph']
        }
        
        try:
            url = f"{IOT_AGENT_URL}?k={API_KEY}&i={device_id}"
            requests.post(url, json=payload)
        except Exception:
            pass

    time.sleep(5)

print("✅ Terminé.")