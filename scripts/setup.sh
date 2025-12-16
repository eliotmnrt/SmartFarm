#!/bin/bash

# ==========================================
# CONFIGURATION
# ==========================================
NAMESPACE="fiware-platform"
API_KEY="4jggokgpepnvsb2uv4s40d59ov"
DEVICE_ID="sensor001"
ENTITY_ID="urn:ngsi-ld:Cluster:cluster_1"
ENTITY_TYPE="Cluster"

# Couleurs pour le terminal
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Initialisation de la configuration FIWARE (Fresh Setup)...${NC}"

# ==========================================
# 1. PORT FORWARDING
# ==========================================
echo -e "${YELLOW}🔌 Mise en place des tunnels (Port-Forwarding)...${NC}"

./scripts/portManager.sh stop

./scripts/portManager.sh start $NAMESPACE


echo -e "⏳ Attente de 5s pour la stabilisation...${NC}"
sleep 5

# ==========================================
# 2. PROVISIONNEMENT IOT AGENT
# ==========================================

echo -e "${BLUE}[1/4] Création du Service Group...${NC}"
# Définit les règles générales pour cette API Key
curl -s -X POST "http://localhost:4041/iot/services" \
  -H 'Content-Type: application/json' \
  -H 'fiware-service: openiot' \
  -H 'fiware-servicepath: /' \
  -d '{
 "services": [
   {
     "apikey": "'$API_KEY'",
     "cbroker": "http://orion:1026",
     "entity_type": "Thing",
     "resource": "/iot/json"
   }
 ]
}' && echo " OK"

echo -e "${BLUE}[2/4] Création des Devices (Mapping Explicite)...${NC}"

# ... (Partie 2 avant la boucle)

echo -e "${BLUE}[2/4] Création des Devices (Mapping Explicite)...${NC}"


KM_PER_DEG_LAT=110.574 # ~ 1 degré de latitude en km
KM_PER_DEG_LON=77.200  # ~ 1 degré de longitude en km à 46.19° de latitude (Approximation)

# Coordonnées de référence pour le calcul GPS (Origine)
LAT_ORIGIN=46.194814
LON_ORIGIN=1.190861

calculate_gps_long() {
    local DX=$1 # Déplacement en X (Longitude)
    local NEW_LON=$(awk "BEGIN {print $LON_ORIGIN + ($DX / $KM_PER_DEG_LON)}")
    echo "$NEW_LON"
}

calculate_gps_lat() {
    local DY=$1 # Déplacement en Y (Latitude)
    local NEW_LAT=$(awk "BEGIN {print $LAT_ORIGIN + ($DY / $KM_PER_DEG_LAT)}")
    echo "$NEW_LAT"
}

for i in $(seq -f "%02g" 1 10); do
  DEVICE_ID="cluster_$i"
  echo "Enregistrement de $DEVICE_ID..."

  case $i in
    01) X=8; Y=32 ;;
    02) X=33; Y=26 ;;
    03) X=44; Y=19 ;;
    04) X=63; Y=30 ;;
    05) X=91; Y=28 ;;
    06) X=2; Y=82 ;;
    07) X=35; Y=70 ;;
    08) X=45; Y=70 ;;
    09) X=67; Y=75 ;;
    10) X=89; Y=72 ;;
    *) X=0; Y=0 ;;
  esac

  LON=$(calculate_gps_long $X)
  LAT=$(calculate_gps_lat $Y)

  echo -n "  -> Localisation (X: $LON, Y: $LAT  )..."


  curl -s -X POST "http://localhost:4041/iot/devices" \
    -H 'Content-Type: application/json' \
    -H 'fiware-service: openiot' \
    -H 'fiware-servicepath: /' \
    -d '{
    "devices": [
      {
        "device_id": "'"$DEVICE_ID"'",
        "apikey": "'"$API_KEY"'",
        "entity_name": "urn:ngsi-ld:Cluster:'"$DEVICE_ID"'",
        "entity_type": "'"$ENTITY_TYPE"'",
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
          {"name": "longitude", "type": "Number", "value": "'"$LON"'"}, 
          {"name": "latitude", "type": "Number", "value": "'"$LAT"'"}
        ]
      }
    ]
  }'
  
  echo " OK" 
done 


# ==========================================
# 3. SUBSCRIPTION QUANTUMLEAP
# ==========================================

echo -e "${BLUE}[3/4] Création de la souscription Orion -> QuantumLeap...${NC}"
# Orion notifiera QuantumLeap (nom DNS interne k8s: quantumleap)
curl -s -X POST "http://localhost:1026/v2/subscriptions" \
  -H 'Content-Type: application/json' \
  -H 'fiware-service: openiot' \
  -H 'fiware-servicepath: /' \
  -d '{
  "description": "Notify QuantumLeap of all Sensor changes",
  "subject": {
    "entities": [
      {
        "idPattern": ".*",
        "type": "'$ENTITY_TYPE'"
      }
    ],
    "condition": {
      "attrs": []
    }
  },
  "notification": {
    "http": {
      "url": "http://quantumleap:8668/v2/notify"
    },
    "attrs": [],
    "metadata": ["dateCreated", "dateModified"]
  },
  "throttling": 1
}'

sleep 2

echo -e "${YELLOW}🔍 Vérification dans Orion (Entité: urn:ngsi-ld:Cluster:'$DEVICE_ID')...${NC}"
RESPONSE=$(curl -s "http://localhost:1026/v2/entities/urn:ngsi-ld:Cluster:'$DEVICE_ID'" \
  -H 'fiware-service: openiot' \
  -H 'fiware-servicepath: /')

# Affichage du résultat
echo $RESPONSE

echo -e "${GREEN}✅ Setup terminé !${NC}"