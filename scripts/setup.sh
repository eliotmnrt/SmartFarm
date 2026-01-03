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
  "throttling": 0
}'

sleep 2

echo -e "${BLUE}[4/4] Création de la souscription Orion -> Service IA...${NC}"
curl -X POST "http://localhost:1026/v2/subscriptions" \
  -H 'Content-Type: application/json' \
  -H 'fiware-service: openiot' \
  -H 'fiware-servicepath: /' \
  -d '{
  "description": "IA Feedback Loop: Detect Field State",
  "subject": {
    "entities": [
      {
        "idPattern": ".*",
        "type": "'${ENTITY_TYPE}'"      
      }
    ],
    "condition": {
      "attrs": [ 
        "temperature", "humidity", "soilMoisture", "soilTemperature"
        ] 
      }
  },
  "notification": {
    "http": {
      "url": "http://ai-service:8000/v2/notify"
    },
    "attrs": [
      "temperature", "soilTemperature", 
      "humidity", "soilMoisture"
    ]
  },
  "throttling": 0
}'

echo -e "${GREEN}✅ Setup terminé !${NC}"