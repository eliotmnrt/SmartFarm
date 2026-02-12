import requests
import time
import datetime
import logging
from collections import defaultdict
import os
from dotenv import load_dotenv

# --- CONFIGURATION DES CHEMINS & ENV ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(BASE_DIR, '.env')

# 1. On cherche dans le dossier du script
if os.path.exists(env_path):
    load_dotenv(env_path)
    env_location = "Dossier courant"
# 2. Sinon, on cherche 1 niveau au-dessus (docker/)
elif os.path.exists(os.path.join(BASE_DIR, '../.env')):
    load_dotenv(os.path.join(BASE_DIR, '../.env'))
    env_location = "Dossier parent (../)"
# 3. Sinon, on cherche 2 niveaux au-dessus (smartfarm2.0/ -> LA RACINE)
elif os.path.exists(os.path.join(BASE_DIR, '../../.env')):
    load_dotenv(os.path.join(BASE_DIR, '../../.env'))
    env_location = "Racine du projet (../../)"
else:
    env_location = "❌ NON TROUVÉ"

# --- RÉCUPÉRATION DES VARIABLES ---
ORION_URL = os.environ.get("ORION_HOST", "http://localhost:1026/v2/entities")
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", 10))
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# --- DIAGNOSTIC AU DÉMARRAGE ---
print("\n" + "="*40)
print(" 🔍 DIAGNOSTIC DE DÉMARRAGE")
print("="*40)
print(f"📂 Dossier script : {BASE_DIR}")
print(f"🌍 Fichier .env   : {env_location}")

if DISCORD_WEBHOOK_URL:
    print(f"💬 Discord Webhook: ✅ CHARGÉ (OK)")
else:
    print(f"💬 Discord Webhook: ❌ NON TROUVÉ (Variable vide)")
    print("   👉 Solution rapide : Copie ton fichier .env dans le dossier 'serviceDecision'")
print("="*40 + "\n")

# --- CONFIGURATION LOGGING ---
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# --- PARAMÈTRES MÉTIER ---
ZONES = {
    "Champ_Nord": ["cluster_07", "cluster_08", "cluster_09", "cluster_10"],
    "Champ_Sud":  ["cluster_01", "cluster_02", "cluster_03", "cluster_04", "cluster_05"],
    "Serre_Lac":  ["cluster_06"]
}

THRESHOLD_DRY = float(os.environ.get("THRESHOLD_DRY", 0.20))
THRESHOLD_STANDARD = float(os.environ.get("THRESHOLD_STANDARD", 0.60))

HEADERS_GET = {'fiware-service': 'openiot'}
HEADERS_POST = {
    'fiware-service': 'openiot',
    'fiware-servicepath': '/',
    'Content-Type': 'application/json'
}

zone_memory = {}

# --- FONCTIONS ---

def send_discord_alert(title, message, color):
    """ Envoie une notification Discord """
    if not DISCORD_WEBHOOK_URL:
        logger.warning("⚠️ Alerte ignorée : Pas d'URL Discord configurée.")
        return

    payload = {
        "embeds": [{
            "title": title,
            "description": message,
            "color": color,
            "footer": {"text": "SmartFarm Decision Service"}
        }]
    }
    try:
        resp = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=2)
        if resp.status_code not in [200, 204]:
            logger.error(f"⚠️ Erreur Discord HTTP {resp.status_code}: {resp.text}")
    except Exception as e:
        logger.error(f"⚠️ Erreur connexion Discord: {e}")

def get_realtime_states():
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

def send_order_to_orion(zone_name, action, clusters):
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    for device_id in clusters:
        entity_id = f"urn:ngsi-ld:Cluster:{device_id}"
        url = f"{ORION_URL}/{entity_id}/attrs"
        payload = {
            "irrigationRecommendation": { "value": action, "type": "Text" },
            "lastDecisionDate": { "value": timestamp, "type": "DateTime" }
        }
        try:
            requests.post(url, json=payload, headers=HEADERS_POST)
        except Exception:
            pass 

def process_zone_decision(zone_name, action, clusters, stats_msg):
    last_action = zone_memory.get(zone_name)
    if action != last_action:
        logger.info(f"🚨 CHANGEMENT D'ÉTAT {zone_name} : {last_action} -> {action}")
        
        send_order_to_orion(zone_name, action, clusters)
        
        if action == "START_IRRIGATION":
            emoji = "💧"
            color = 3447003 
            title = f"{emoji} Activation Arrosage : {zone_name}"
        else:
            emoji = "🛑"
            color = 15158332 
            title = f"{emoji} Arrêt Arrosage : {zone_name}"
            
        desc = f"**Raison :** {stats_msg}\n**Nouvel Ordre :** `{action}`"
        send_discord_alert(title, desc, color)
        
        zone_memory[zone_name] = action
    else:
        logger.debug(f"💤 {zone_name}: Stable ({action})")

def run_decision_cycle():
    devices = get_realtime_states()
    if not devices: return

    device_map = {}
    for d in devices:
        d_id = d.get('id', '')
        simple_id = d_id.split(':')[-1] 
        device_map[simple_id] = d.get('fieldState', -1) 

    logger.info("--- Analyse Cycle ---")
    
    for zone_name, cluster_list in ZONES.items():
        states_in_zone = []
        for cluster_id in cluster_list:
            state = device_map.get(cluster_id, -1) 
            states_in_zone.append(state)
        
        total_sensors = len(states_in_zone)
        count_sec = states_in_zone.count(0)     
        count_standard = states_in_zone.count(2) 
        
        if total_sensors > 0:
            ratio_sec = count_sec / total_sensors
            ratio_standard = count_standard / total_sensors
            
            stats_readable = f"{count_sec} Secs, {count_standard} Standards (sur {total_sensors})"
            
            if ratio_sec >= THRESHOLD_DRY or ratio_standard >= THRESHOLD_STANDARD:
                new_action = "START_IRRIGATION"
            else:
                new_action = "NO_IRRIGATION"
            
            process_zone_decision(zone_name, new_action, cluster_list, stats_readable)
        else:
            logger.warning(f"⚠️ {zone_name}: Aucun capteur détecté.")

if __name__ == "__main__":
    if DISCORD_WEBHOOK_URL:
        send_discord_alert("🧠 Service IA Démarré", "Prêt à analyser...", 9807270)
    
    while True:
        run_decision_cycle()
        time.sleep(CHECK_INTERVAL)