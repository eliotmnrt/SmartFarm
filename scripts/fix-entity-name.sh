#!/bin/bash

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${RED}╔════════════════════════════════════════════╗${NC}"
echo -e "${RED}║  ��� Correction Entity Name (Definitif)   ║${NC}"
echo -e "${RED}╚════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${YELLOW}[1/10] Suppression COMPLÈTE dans MongoDB...${NC}"
kubectl exec -n fiware-platform \
  $(kubectl get pod -n fiware-platform -l app=mongodb -o name | head -1) \
  -c mongodb -- mongo iotagent --eval "
    db.devices.deleteMany({});
    db.groups.deleteMany({});
    print('✓ MongoDB nettoyé');
  "
echo -e "${GREEN}✅ MongoDB nettoyé${NC}"

echo -e "${YELLOW}[2/10] Redémarrage IoT Agent (vider cache)...${NC}"
kubectl rollout restart deployment iot-agent -n fiware-platform > /dev/null
sleep 5
kubectl wait --for=condition=ready pod -l app=iot-agent -n fiware-platform --timeout=180s > /dev/null 2>&1
echo -e "${GREEN}✅ IoT Agent redémarré${NC}"

# Port-forwards
kubectl port-forward -n fiware-platform svc/iot-agent 4041:4041 7896:7896 > /dev/null 2>&1 &
PF1=$!
kubectl port-forward -n fiware-platform svc/orion 1026:1026 > /dev/null 2>&1 &
PF2=$!

cleanup() {
    kill $PF1 $PF2 2>/dev/null || true
}
trap cleanup EXIT

sleep 10

echo -e "${YELLOW}[3/10] Test IoT Agent...${NC}"
ABOUT=$(curl -s http://localhost:4041/iot/about 2>/dev/null)
if [ -z "$ABOUT" ]; then
    echo -e "${RED}❌ IoT Agent inaccessible${NC}"
    exit 1
fi
echo -e "${GREEN}✅ IoT Agent OK${NC}"

echo -e "${YELLOW}[4/10] Nettoyage Orion...${NC}"
curl -s http://localhost:1026/v2/entities \
  -H 'fiware-service: openiot' \
  -H 'fiware-servicepath: /' 2>/dev/null | jq -r '.[].id' 2>/dev/null | while read ENTITY_ID; do
    curl -s -X DELETE "http://localhost:1026/v2/entities/$ENTITY_ID" \
      -H 'fiware-service: openiot' \
      -H 'fiware-servicepath: /' > /dev/null 2>&1
done
echo -e "${GREEN}✅ Orion nettoyé${NC}"

echo -e "${YELLOW}[5/10] Création du service...${NC}"
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST http://localhost:4041/iot/services \
  -H 'Content-Type: application/json' \
  -H 'fiware-service: openiot' \
  -H 'fiware-servicepath: /' \
  -d '{
  "services": [{
    "apikey": "4jggokgpepnvsb2uv4s40d59ov",
    "cbroker": "http://orion:1026",
    "entity_type": "Thing",
    "resource": "/iot/json"
  }]
}')

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
if [ "$HTTP_CODE" != "201" ] && [ "$HTTP_CODE" != "409" ]; then
    echo -e "${RED}❌ Erreur service (HTTP $HTTP_CODE)${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Service créé${NC}"

echo -e "${YELLOW}[6/10] Provisioning device CORRECT...${NC}"
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST http://localhost:4041/iot/devices \
  -H 'Content-Type: application/json' \
  -H 'fiware-service: openiot' \
  -H 'fiware-servicepath: /' \
  -d '{
  "devices": [{
    "device_id": "sensor001",
    "entity_name": "urn:ngsi-ld:Sensor:001",
    "entity_type": "Sensor",
    "protocol": "IoTA-JSON",
    "transport": "HTTP",
    "attributes": [
      {"object_id": "t", "name": "temperature", "type": "Number"},
      {"object_id": "h", "name": "humidity", "type": "Number"},
      {"object_id": "p", "name": "pressure", "type": "Number"}
    ]
  }]
}')

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
if [ "$HTTP_CODE" != "201" ]; then
    echo -e "${RED}❌ Erreur device (HTTP $HTTP_CODE)${NC}"
    BODY=$(echo "$RESPONSE" | head -n-1)
    echo -e "${RED}$BODY${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Device provisionné${NC}"

sleep 2

echo -e "${YELLOW}[7/10] Vérification API...${NC}"
DEVICE_INFO=$(curl -s http://localhost:4041/iot/devices \
  -H 'fiware-service: openiot' \
  -H 'fiware-servicepath: /' 2>/dev/null)

ENTITY_NAME=$(echo "$DEVICE_INFO" | jq -r '.devices[0].entity_name' 2>/dev/null)
ENTITY_TYPE=$(echo "$DEVICE_INFO" | jq -r '.devices[0].entity_type' 2>/dev/null)

echo -e "${BLUE}   Entity Name API: $ENTITY_NAME${NC}"
echo -e "${BLUE}   Entity Type API: $ENTITY_TYPE${NC}"

if [ "$ENTITY_NAME" != "urn:ngsi-ld:Sensor:001" ]; then
    echo -e "${RED}❌ entity_name INCORRECT dans l'API !${NC}"
    echo -e "${YELLOW}Vérification directe dans MongoDB...${NC}"
fi

echo -e "${YELLOW}[8/10] Vérification MongoDB directe...${NC}"
MONGO_CHECK=$(kubectl exec -n fiware-platform \
  $(kubectl get pod -n fiware-platform -l app=mongodb -o name | head -1) \
  -c mongodb -- mongo iotagent --quiet --eval "
    var device = db.devices.findOne({id: 'sensor001'});
    if (device) {
        print('name=' + device.name);
        print('type=' + device.type);
    } else {
        print('NOT_FOUND');
    }
  " 2>/dev/null)

echo -e "${BLUE}$MONGO_CHECK${NC}"

if echo "$MONGO_CHECK" | grep -q "name=urn:ngsi-ld:Sensor:001"; then
    echo -e "${GREEN}✅ MongoDB : entity_name CORRECT${NC}"
elif echo "$MONGO_CHECK" | grep -q "NOT_FOUND"; then
    echo -e "${RED}❌ Device NON TROUVÉ dans MongoDB !${NC}"
    exit 1
else
    echo -e "${RED}❌ MongoDB : entity_name INCORRECT${NC}"
    echo -e "${YELLOW}Correction manuelle dans MongoDB...${NC}"
    kubectl exec -n fiware-platform \
      $(kubectl get pod -n fiware-platform -l app=mongodb -o name | head -1) \
      -c mongodb -- mongo iotagent --eval "
        db.devices.updateOne(
          {id: 'sensor001'},
          {\$set: {
            name: 'urn:ngsi-ld:Sensor:001',
            type: 'Sensor'
          }}
        );
      " > /dev/null
    echo -e "${GREEN}✅ Correction appliquée${NC}"
    
    # Redémarrer IoT Agent
    kubectl rollout restart deployment iot-agent -n fiware-platform > /dev/null
    sleep 5
    kubectl wait --for=condition=ready pod -l app=iot-agent -n fiware-platform --timeout=180s > /dev/null 2>&1
    kubectl port-forward -n fiware-platform svc/iot-agent 7896:7896 > /dev/null 2>&1 &
    sleep 5
fi

echo -e "${YELLOW}[9/10] Test mesure...${NC}"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST "http://localhost:7896/iot/json?k=4jggokgpepnvsb2uv4s40d59ov&i=sensor001" \
  -H 'Content-Type: application/json' \
  -d '{"t": 23.5, "h": 65, "p": 1013}')

if [ "$HTTP_CODE" != "200" ]; then
    echo -e "${RED}❌ Erreur envoi mesure (HTTP $HTTP_CODE)${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Mesure envoyée${NC}"

sleep 4

echo -e "${YELLOW}[10/10] Vérification Orion...${NC}"
ENTITY=$(curl -s http://localhost:1026/v2/entities/urn:ngsi-ld:Sensor:001 \
  -H 'fiware-service: openiot' \
  -H 'fiware-servicepath: /' 2>/dev/null)

ENTITY_ID=$(echo "$ENTITY" | jq -r '.id' 2>/dev/null)

if [ "$ENTITY_ID" == "urn:ngsi-ld:Sensor:001" ]; then
    TEMP=$(echo "$ENTITY" | jq -r '.temperature.value' 2>/dev/null)
    TYPE=$(echo "$ENTITY" | jq -r '.type' 2>/dev/null)
    echo -e "${GREEN}✅✅✅ SUCCÈS TOTAL !${NC}"
    echo -e "${BLUE}   Entity ID   : $ENTITY_ID${NC}"
    echo -e "${BLUE}   Entity Type : $TYPE${NC}"
    echo -e "${BLUE}   Température : ${TEMP}°C${NC}"
else
    echo -e "${RED}❌ Entité TOUJOURS introuvable${NC}"
    echo -e "${YELLOW}Vérification de ce qui existe :${NC}"
    curl -s http://localhost:1026/v2/entities \
      -H 'fiware-service: openiot' \
      -H 'fiware-servicepath: /' | jq '.[] | {id, type}'
    exit 1
fi

# Subscription
curl -s -X POST http://localhost:1026/v2/subscriptions \
  -H 'Content-Type: application/json' \
  -H 'fiware-service: openiot' \
  -H 'fiware-servicepath: /' \
  -d '{
  "description": "Notify QuantumLeap",
  "subject": {"entities": [{"idPattern": ".*", "type": "Sensor"}]},
  "notification": {"http": {"url": "http://quantumleap:8668/v2/notify"}},
  "throttling": 1
}' > /dev/null 2>&1

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ��� PROBLÈME RÉSOLU DÉFINITIVEMENT !     ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Test :${NC}"
echo -e "  ${GREEN}curl http://localhost:1026/v2/entities/urn:ngsi-ld:Sensor:001 -H 'fiware-service: openiot' -H 'fiware-servicepath: /' | jq${NC}"
echo ""
