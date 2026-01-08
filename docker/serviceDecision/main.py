import requests
import time
import datetime
import logging
from collections import defaultdict
import os



# --- CONFIGURATION LOGGING ---
# INFO : Affiche seulement les décisions (🚨) et les erreurs.
# DEBUG : Affiche aussi les stats (📊) et les détails HTTP.
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
ORION_URL = os.environ.get("ORION_HOST", "http://localhost:1026/v2/entities") # fallback localhost
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", 10))  # en secondes

ZONES = {
    "Champ_Nord": ["cluster_07", "cluster_08", "cluster_09", "cluster_10"],
    "Champ_Sud":  ["cluster_01", "cluster_02", "cluster_03", "cluster_04", "cluster_05"],
    "Champ_Lac":  ["cluster_06"]
}

THRESHOLD_DRY = float(os.environ.get("THRESHOLD_DRY", 0.20))      # > 20% Sec (0)
THRESHOLD_STANDARD = float(os.environ.get("THRESHOLD_STANDARD", 0.60)) # > 60% Standard (2)

HEADERS_GET = {'fiware-service': 'openiot'}
HEADERS_POST = {
    'fiware-service': 'openiot',
    'fiware-servicepath': '/',
    'Content-Type': 'application/json'
}

def get_realtime_states():
    """Récupère l'état actuel de tous les Devices via Orion"""    
    url = f"{ORION_URL}?type=Cluster&options=keyValues&limit=1000"
    
    try:
        resp = requests.get(url, headers=HEADERS_GET)
        if resp.status_code == 200:
            return resp.json()
        else:
            logger.error(f"❌ Erreur Orion ({resp.status_code}): {resp.text}")
            return []
    except Exception as e:
        logger.error(f"❌ Erreur connexion Orion: {e}")
        return []

def send_alert(zone_name, action, clusters):
    """Envoie l'ordre à Orion"""
    logger.info(f"🚨 DÉCISION {zone_name} : {action}")
    
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    for device_id in clusters:
        entity_id = f"urn:ngsi-ld:Cluster:{device_id}"
        url = f"{ORION_URL}/{entity_id}/attrs"
        
        payload = {
            "irrigationRecommendation": {
                "value": action,
                "type": "Text"
            },
            "lastDecisionDate": {
                "value": timestamp,
                "type": "DateTime"
            }
        }
        try:
            resp = requests.post(url, json=payload, headers=HEADERS_POST)
            if resp.status_code >= 400:
                logger.error(
                    f"   Erreur update {device_id} (HTTP {resp.status_code}): {resp.text}"
                )
            else:
                logger.debug(
                    f"   Update envoyé pour {device_id} (HTTP {resp.status_code})"
                )
        except Exception as e:
            logger.error(f"   Erreur update {device_id}: {e}")

def run_decision_cycle():
    devices = get_realtime_states()
    
    if not devices:
        return

    device_map = {}
    for d in devices:
        d_id = d.get('id', '')
        simple_id = d_id.split(':')[-1] 
        device_map[simple_id] = d.get('fieldState', -1)
        timestamp = d.get('TimeInstant', 'Inconnu')

    # Analyse par Zone a un instant T
    logger.info("--- Nouvelle Analyse ---")
    logger.info(f"⏱️ Timestamp des données : {timestamp}") 
    for zone_name, cluster_list in ZONES.items():
        states_in_zone = []
        
        for cluster_id in cluster_list:
            state = device_map.get(cluster_id, "Inconnu")
            states_in_zone.append(state)
        
        total_sensors = len(states_in_zone)
        count_sec = states_in_zone.count(0)
        count_standard = states_in_zone.count(2)
        
        if total_sensors > 0:
            ratio_sec = count_sec / total_sensors
            ratio_standard = count_standard / total_sensors
            
            logger.debug(f"📊 {zone_name}: {count_sec}/{total_sensors} 'Sec' ({ratio_sec*100:.0f}%)")
            logger.debug(f"📊 {zone_name}: {count_standard}/{total_sensors} 'Standard' ({ratio_standard*100:.0f}%)")
            
            if ratio_sec >= THRESHOLD_DRY or ratio_standard >= THRESHOLD_STANDARD:
                send_alert(zone_name, "START_IRRIGATION", cluster_list)
            else:
                send_alert(zone_name, "NO_IRRIGATION", cluster_list)
        else:
            logger.warning(f"⚠️ {zone_name}: Aucun capteur détecté.")

if __name__ == "__main__":
    logger.info("🚀 Service de Décision Démarré (Logs filtrés)")
    while True:
        run_decision_cycle()
        time.sleep(CHECK_INTERVAL)