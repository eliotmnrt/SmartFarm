#!/bin/bash

# ==========================================
# CONFIGURATION
# ==========================================
NAMESPACE="fiware-platform"
API_KEY="4jggokgpepnvsb2uv4s40d59ov"
DEVICE_ID="sensor001"
ENTITY_ID="urn:ngsi-ld:Sensor:001"
ENTITY_TYPE="Sensor"

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

# Récupération dynamique des noms de pods
POD_ORION=$(kubectl get pod -n $NAMESPACE -l app=orion -o jsonpath="{.items[0].metadata.name}")
POD_IOTA=$(kubectl get pod -n $NAMESPACE -l app=iot-agent -o jsonpath="{.items[0].metadata.name}")
POD_QL=$(kubectl get pod -n $NAMESPACE -l app=quantumleap -o jsonpath="{.items[0].metadata.name}")
POD_GRAFANA=$(kubectl get pod -n $NAMESPACE -l app=grafana -o jsonpath="{.items[0].metadata.name}")

# Lancement des tunnels en arrière-plan
kubectl port-forward -n $NAMESPACE $POD_ORION 1026:1026 > /dev/null 2>&1 &
PID_ORION=$!
kubectl port-forward -n $NAMESPACE $POD_IOTA 4041:4041 > /dev/null 2>&1 &
PID_IOTA_NORTH=$!
kubectl port-forward -n $NAMESPACE $POD_IOTA 7896:7896 > /dev/null 2>&1 &
PID_IOTA_SOUTH=$!
#grafana port
kubectl port-forward -n $NAMESPACE $POD_GRAFANA 3000:3000 > /dev/null 2>&1 &

# Weather agent port-forward (if present)
POD_WEATHER=$(kubectl get pod -n $NAMESPACE -l app=weather-agent -o jsonpath="{.items[0].metadata.name}" 2>/dev/null || true)
if [ -n "$POD_WEATHER" ]; then
  kubectl port-forward -n $NAMESPACE $POD_WEATHER 8888:8888 > /dev/null 2>&1 &
  PID_WEATHER=$!
fi


# Optionnel : Tunnel vers QL pour vérifier l'API directement si besoin
kubectl port-forward -n $NAMESPACE $POD_QL 8668:8668 > /dev/null 2>&1 &
PID_QL=$!

echo "   - Orion: 1026 ($PID_ORION)"
echo "   - IoT Agent (Config): 4041 ($PID_IOTA_NORTH)"
echo "   - IoT Agent (Data): 7896 ($PID_IOTA_SOUTH)"
echo "   - QuantumLeap: 8668 ($PID_QL)"
if [ -n "$PID_WEATHER" ]; then
  echo "   - Weather Agent: 8888 ($PID_WEATHER)"
fi

echo -e "${YELLOW}⏳ Attente de 5s pour la stabilisation...${NC}"
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

echo -e "${BLUE}[2/4] Création du Device (Mapping Explicite)...${NC}"
# ⚠️ CRITIQUE : On inclut "apikey" ICI pour lier fermement ce device au groupe
# et éviter la création d'un doublon par défaut.
curl -s -X POST "http://localhost:4041/iot/devices" \
  -H 'Content-Type: application/json' \
  -H 'fiware-service: openiot' \
  -H 'fiware-servicepath: /' \
  -d '{
 "devices": [
   {
     "device_id": "'$DEVICE_ID'",
     "apikey": "'$API_KEY'",
     "entity_name": "'$ENTITY_ID'",
     "entity_type": "'$ENTITY_TYPE'",
     "protocol": "IoTA-JSON",
     "transport": "HTTP",
     "endpoint": "http://iot-agent:7896/iot/json",
     "attributes": [
       {"object_id": "t", "name": "temperature", "type": "Number"},
       {"object_id": "h", "name": "humidity", "type": "Number"},
       {"object_id": "p", "name": "pressure", "type": "Number"}
     ]
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
  "throttling": 1
}' && echo " OK"

# ==========================================
# 4. TEST ET VÉRIFICATION
# ==========================================

echo -e "${BLUE}[4/4] Envoi de données de test...${NC}"
curl -s -X POST "http://localhost:7896/iot/json?k=$API_KEY&i=$DEVICE_ID" \
  -H 'Content-Type: application/json' \
  -d '{"t": 24.5, "h": 55, "p": 1012}' && echo " Données envoyées."

sleep 2

echo -e "${YELLOW}🔍 Vérification dans Orion (Entité: $ENTITY_ID)...${NC}"
RESPONSE=$(curl -s "http://localhost:1026/v2/entities/$ENTITY_ID" \
  -H 'fiware-service: openiot' \
  -H 'fiware-servicepath: /')

# Affichage du résultat
echo $RESPONSE | jq . 2>/dev/null || echo $RESPONSE

echo -e "${GREEN}✅ Setup terminé !${NC}"