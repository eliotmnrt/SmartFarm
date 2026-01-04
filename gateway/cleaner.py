import pandas as pd
import numpy as np
import requests
import time
import math
from collections import deque, defaultdict
from dotenv import load_dotenv
import os

load_dotenv()  # charge le .env à la racine

API_KEY = os.getenv("API_KEY")


INPUT_DIRTY_FILE = 'sensor_data_raw_dirty.csv'
IOTA_HTTP_URL = "http://localhost:7896/iot/json"      # Pour envoyer les données
IOTA_ADMIN_URL = "http://localhost:4041/iot/devices"  # Pour créer les devices

FIWARE_HEADERS = {
    'fiware-service': 'openiot',
    'fiware-servicepath': '/',
    'Content-Type': 'application/json'
}

SEND_TO_ORION = True  

LAT_ORIGIN=46.194814
LON_ORIGIN=1.190861

KM_PER_DEG_LAT = 111.11
KM_PER_DEG_LON = 111.11 * math.cos(math.radians(LAT_ORIGIN))

# Positions des capteurs en dizaine de mètres (x, y)
sensors_positions = {  
    'cluster_01': (8, 32),
    'cluster_02': (33, 26),
    'cluster_03': (44, 19),
    'cluster_04': (63, 30),
    'cluster_05': (91, 28),
    'cluster_06': (2, 82),
    'cluster_07': (35, 70),
    'cluster_08': (45, 70),
    'cluster_09': (67, 75),
    'cluster_10': (89, 72),
}

def calculate_gps_coords(x_meters, y_meters):
    dx_km = x_meters / 1000.0 * 10
    dy_km = y_meters / 1000.0 * 10
    
    new_lon = LON_ORIGIN + (dx_km / KM_PER_DEG_LON)
    new_lat = LAT_ORIGIN + (dy_km / KM_PER_DEG_LAT)
    
    return new_lat, new_lon

# Seuils Physiques (Pour détecter les outliers x5 ou x-1)
THRESHOLDS = {
    'temperature': (-15, 60),       # °C
    'soilTemperature': (-10, 50),   # °C
    'humidity': (0, 100),           # %
    'soilMoisture': (0, 100),       # %
    'azote_mg_kg': (0, 400),        # N
    'phosphore_mg_kg': (0, 100),    # P
    'potassium_mg_kg': (0, 400),    # K
    'ph': (4, 9)                   # pH
}

class SensorGateway:
    def __init__(self):
        # Mémoire tampon : dictionnaire de deques (historique des 5 dernières valeurs valides)
        self.memory = defaultdict(lambda: defaultdict(lambda: deque(maxlen=5)))
        
        # Pour détecter les capteurs gelés (Freeze)
        self.freeze_counters = defaultdict(lambda: defaultdict(int))
        
        # Conserver la liste des devices déjà provisionnés
        self.known_devices = set()

    def ensure_device_exists(self, device_id):
        if device_id in self.known_devices:
            return True

        print(f"🆕 Nouveau device détecté : {device_id}. Tentative d'enregistrement...")

        x, y = sensors_positions.get(device_id, (0, 0))
        lat, lon = calculate_gps_coords(x, y)
        print(f"   📍 Position GPS calculée : lat={lat}, lon={lon}")
        # Payload de configuration du Device (Mapping)
        provisioning_payload = {
            "devices": [
                {
                    "device_id": device_id,
                    "apikey": API_KEY,
                    "entity_name": "urn:ngsi-ld:Cluster:" + device_id,
                    "entity_type": "Cluster",
                    "protocol": "IoTA-JSON",
                    "transport": "HTTP",
                    "endpoint": "http://iot-agent:7896/iot/json",
                    "attributes": [
                    {"object_id": "date", "name": "TimeInstant", "type": "DateTime"},
                    {"object_id": "ta", "name": "temperature", "type": "Number"},
                    {"object_id": "ts", "name": "soilTemperature", "type": "Number"},
                    {"object_id": "ha", "name": "humidity", "type": "Number"},
                    {"object_id": "hs", "name": "soilMoisture", "type": "Number"},
                    {"object_id": "n",  "name": "n", "type": "Number"},
                    {"object_id": "p",  "name": "p", "type": "Number"},
                    {"object_id": "k",  "name": "k", "type": "Number"},
                    {"object_id": "ph", "name": "ph", "type": "Number"}
                    ],
                    "static_attributes": [
                        {"name": "longitude", "type": "Number", "value": lon}, 
                        {"name": "latitude", "type": "Number", "value": lat},
                    ]
                }
            ]
        }

        try:
            response = requests.post(IOTA_ADMIN_URL, json=provisioning_payload, headers=FIWARE_HEADERS)
            
            # 201 = Créé, 409 = Existe déjà (C'est bon aussi)
            if response.status_code in [201, 200, 409]:
                print(f"✅ Device {device_id} enregistré (Code {response.status_code})")
                self.known_devices.add(device_id)
                return True
            else:
                print(f"❌ Échec provisioning {device_id}: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Erreur connexion Admin API: {e}")
            return False

    def clean_value(self, device_id, metric, value):
        # 1. Gestion des NaN (Donnée manquante)
        if pd.isna(value):
            if len(self.memory[device_id][metric]) > 0:
                # On remplace par la moyenne des dernières valeurs connues (Imputation)
                corrected = np.mean(self.memory[device_id][metric])
                return corrected, "FIXED_NAN"
            else:
                # Pas d'historique ? On retourne la moyenne du range théorique (Mieux que rien)
                t_min, t_max = THRESHOLDS.get(metric, (0, 0))
                return (t_min + t_max) / 2, "DEFAULT"

        # 2. Gestion des Outliers (Valeurs aberrantes physiquement)
        t_min, t_max = THRESHOLDS.get(metric, (-999, 999))
        if value < t_min or value > t_max:
            # C'est un outlier (ex: x5 ou négatif impossible)
            if len(self.memory[device_id][metric]) > 0:
                # On remplace par la moyenne mobile (lissage)
                corrected = np.mean(self.memory[device_id][metric])
                return corrected, "FIXED_OUTLIER"
            else:
                # Si c'est la première valeur et qu'elle est fausse, on clipe
                corrected = max(t_min, min(value, t_max))
                return corrected, "CLIPPED"
        
        #3. gestion des valeurs hors de portée statistique (3 écarts types)
    #    if len(self.memory[device_id][metric]) >= 2:
    #        mean_hist = np.mean(self.memory[device_id][metric])
    #        std_hist = np.std(self.memory[device_id][metric])
    #        if std_hist > 0:
    #            if abs(value - mean_hist) > 5 * std_hist:
    #                corrected = mean_hist
    #                return corrected, "FIXED_STAT_OUTLIER"

        # 4. Gestion du Freeze (Capteur bloqué)
        # Si la valeur est STRICTEMENT identique à la précédente
        if len(self.memory[device_id][metric]) > 0:
            last_val = self.memory[device_id][metric][-1]
            if value == last_val:
                self.freeze_counters[device_id][metric] += 1
            else:
                self.freeze_counters[device_id][metric] = 0
            
            # Si bloqué depuis plus de 5 cycles
            if self.freeze_counters[device_id][metric] > 5:
                value = -0.001
                print(f"   ❄️ Capteur {device_id} metric {metric} gelé. Forçage valeur à {value}.")
                return value, "FIXED_FREEZE"
                # TODO: envoyer alerte orion

        # 5. Lissage du Bruit (Noise Reduction)
        # Même si la valeur est bonne, on l'ajoute à l'historique et on lisse légèrement
        # Moyenne pondérée : 70% nouvelle valeur, 30% moyenne historique
        if len(self.memory[device_id][metric]) > 0:
            avg_history = np.mean(self.memory[device_id][metric])
            smoothed_value = (0.7 * value) + (0.3 * avg_history)
        else:
            smoothed_value = value

        # Mise à jour de la mémoire avec la valeur LISSÉE
        self.memory[device_id][metric].append(smoothed_value)
        
        return smoothed_value, "OK"

# --- MAIN LOOP (SIMULATION DU TEMPS) ---
def run_simulation():
    try:
        df_dirty = pd.read_csv(INPUT_DIRTY_FILE)
        df_dirty['timestamp'] = pd.to_datetime(df_dirty['timestamp'])
        
        # On trie par temps pour simuler l'arrivée des paquets
        df_dirty = df_dirty.sort_values(by=['timestamp', 'cluster_id'])
        
        gateway = SensorGateway()
        
        print(f"🚀 Démarrage de la Gateway de Nettoyage ({len(df_dirty)} mesures)...")
        
        # On groupe par timestamp (comme si on recevait un batch toutes les 30 min)
        for timestamp, group in df_dirty.groupby('timestamp'):
            iso_date = timestamp.isoformat()
            print(f"\n⏱️  Réception paquet : {iso_date}")
            
            for _, row in group.iterrows():
                device_id = row['cluster_id']
                payload_clean = {"date": iso_date}
                
                # Liste des colonnes capteurs à traiter
                sensor_cols = [c for c in THRESHOLDS.keys() if c in df_dirty.columns]
                
                debug_msg = []
                
                for metric in sensor_cols:
                    raw_val = row[metric]
                    
                    # --- LE CŒUR DU TRAITEMENT ---
                    clean_val, status = gateway.clean_value(device_id, metric, raw_val)
                    # -----------------------------
                    
                    payload_clean[metric] = round(clean_val, 2)
                    
                    # Juste pour l'affichage console si correction importante
                    if status != "OK" and status != "DEFAULT":
                        debug_msg.append(f"{metric}: {raw_val} -> {clean_val:.2f} ({status})")

                # Affichage des corrections pour ce device
                if debug_msg:
                    print(f"   🔧 {device_id} corrections : {', '.join(debug_msg)}")

                # Mapping des noms pour IoT Agent (si besoin de raccourcir)
                # Ici on garde les noms complets ou on mappe vers les codes courts ta, ts, etc.
                final_payload = {
                    "date": iso_date,
                    "ta": payload_clean.get('temperature'),
                    "ts": payload_clean.get('soilTemperature'),
                    "ha": payload_clean.get('humidity'),
                    "hs": payload_clean.get('soilMoisture'),
                    "n": payload_clean.get('azote_mg_kg'),
                    "p": payload_clean.get('phosphore_mg_kg'),
                    "k": payload_clean.get('potassium_mg_kg'),
                    "ph": payload_clean.get('ph'),
                }

                # ENVOI VERS ORION
                if SEND_TO_ORION:
                    try:
                        # Si on n'arrive pas à créer le device, on n'envoie pas la donnée
                        if not gateway.ensure_device_exists(device_id):
                            continue

                        url = f"{IOTA_HTTP_URL}?k={API_KEY}&i={device_id}"
                        requests.post(url, json=final_payload, timeout=1)
                    except Exception as e:
                        print(f"⚠️ Erreur lors de l'envoi à Orion pour le device {device_id}: {e}")
            
            # Petite pause pour voir défiler (optionnel)
            time.sleep(1)

        print("\n✅ Simulation terminée. Données nettoyées et envoyées.")

    except FileNotFoundError:
        print(f"❌ Erreur: Fichier {INPUT_DIRTY_FILE} introuvable.")

if __name__ == "__main__":
    run_simulation()