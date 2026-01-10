#!/bin/bash

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

NAMESPACE="fiware-platform"

echo -e "${BLUE}🔍 Vérification des données dans Orion${NC}"
echo ""

# Port-forward vers Orion
kubectl port-forward -n $NAMESPACE svc/orion 1026:1026 > /dev/null 2>&1 &
PF_ORION=$!

cleanup() {
    kill $PF_ORION 2>/dev/null || true
}
trap cleanup EXIT

sleep 3

echo -e "${YELLOW}━━━ DONNÉES IoT (Sensors) ━━━${NC}"
curl -s "http://localhost:1026/v2/entities?type=Sensor" \
  -H 'fiware-service: openiot' \
  -H 'fiware-servicepath: /' > /tmp/iot_data.json 2>&1

python3 << 'PYTHON_EOF'
import json
import sys

try:
    with open('/tmp/iot_data.json') as f:
        data = json.load(f)
    
    if isinstance(data, list) and len(data) > 0:
        for entity in data:
            entity_id = entity.get('id', 'N/A')
            entity_type = entity.get('type', 'N/A')
            temp = entity.get('temperature', {}).get('value', 'N/A')
            humidity = entity.get('humidity', {}).get('value', 'N/A')
            pressure = entity.get('pressure', {}).get('value', 'N/A')
            print(f"  {entity_id} ({entity_type}): {temp}°C, {humidity}%, {pressure}hPa")
    else:
        print("Aucune donnée IoT trouvée")
except Exception as e:
    print(f"Aucune donnée IoT trouvée")
PYTHON_EOF

echo ""
echo -e "${YELLOW}━━━ DONNÉES MÉTÉO (Weather) ━━━${NC}"
curl -s "http://localhost:1026/v2/entities?type=WeatherObserved" \
  -H 'fiware-service: openiot' \
  -H 'fiware-servicepath: /' > /tmp/weather_data.json 2>&1

python3 << 'PYTHON_EOF'
import json
import sys

try:
    with open('/tmp/weather_data.json') as f:
        data = json.load(f)
    
    if isinstance(data, list) and len(data) > 0:
        for entity in data:
            entity_id = entity.get('id', 'N/A')
            entity_type = entity.get('type', 'N/A')
            temp = entity.get('temperature', {}).get('value', 'N/A')
            humidity = entity.get('humidity', {}).get('value', 'N/A')
            wind = entity.get('wind_speed', {}).get('value', 'N/A')
            provider = entity.get('data_provider', {}).get('value', 'N/A')
            print(f"  {entity_id} ({entity_type}): {temp}°C, {humidity}%, Wind {wind}m/s, Provider: {provider}")
    else:
        print("Aucune donnée météo trouvée")
except Exception as e:
    print(f"Aucune donnée météo trouvée")
PYTHON_EOF

echo ""
echo -e "${YELLOW}━━━ TOUTES LES ENTITÉS ━━━${NC}"
curl -s "http://localhost:1026/v2/entities" \
  -H 'fiware-service: openiot' \
  -H 'fiware-servicepath: /' > /tmp/all_entities.json 2>&1

python3 << 'PYTHON_EOF'
import json
import sys

try:
    with open('/tmp/all_entities.json') as f:
        data = json.load(f)
    
    if isinstance(data, list) and len(data) > 0:
        for entity in data:
            entity_id = entity.get('id', 'N/A')
            entity_type = entity.get('type', 'N/A')
            print(f"  {entity_id}: {entity_type}")
    else:
        print("Aucune entité trouvée")
except Exception as e:
    print(f"Aucune entité trouvée")
PYTHON_EOF

echo ""
echo -e "${GREEN}✅ Vérification terminée${NC}"
