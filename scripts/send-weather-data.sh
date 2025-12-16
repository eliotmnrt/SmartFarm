#!/bin/bash

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

NAMESPACE="fiware-platform"

echo -e "${BLUE}🌤️  Test du Weather Agent avec fallback${NC}"
echo -e "${YELLOW}Config: Local Script → Open-Meteo${NC}"
echo ""

# Port-forward vers le Weather Agent
kubectl port-forward -n $NAMESPACE svc/weather-agent 8888:8888 > /dev/null 2>&1 &
PF_WEATHER=$!

cleanup() {
    kill $PF_WEATHER 2>/dev/null || true
}
trap cleanup EXIT

sleep 3

echo -e "${GREEN}✅ Prêt à envoyer les données météo${NC}"
echo -e "${YELLOW}Appuyez sur Ctrl+C pour arrêter${NC}"
echo ""

# Coordonnées GPS (modifiables)
LAT="48.8566"
LON="2.3522"
ENTITY_ID="Weather:Paris"

# Autres exemples :
# Londres: LAT="51.5074" LON="-0.1278" ENTITY_ID="Weather:London"
# New York: LAT="40.7128" LON="-74.0060" ENTITY_ID="Weather:NewYork"

COUNT=0
while true; do
    COUNT=$((COUNT + 1))
    
    echo -e "${BLUE}[$COUNT]${NC} Envoi données météo pour ${ENTITY_ID} (${LAT}, ${LON})..."
    
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "http://localhost:8888/weather" \
      -H 'Content-Type: application/json' \
      -d "{\"lat\": $LAT, \"lon\": $LON, \"entity_id\": \"$ENTITY_ID\"}")
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | head -n-1)
    
    if [ "$HTTP_CODE" -eq 200 ]; then
        # Use Python to parse JSON since jq may not be available
        echo "$BODY" > /tmp/weather_response.json 2>/dev/null
        
        PROVIDER=$(python3 -c "import json; data = json.load(open('/tmp/weather_response.json')); print(data.get('provider', 'Unknown'))" 2>/dev/null || echo "Unknown")
        TEMP=$(python3 -c "import json; data = json.load(open('/tmp/weather_response.json')); print(data.get('weather', {}).get('temp', 'N/A'))" 2>/dev/null || echo "N/A")
        HUM=$(python3 -c "import json; data = json.load(open('/tmp/weather_response.json')); print(data.get('weather', {}).get('humidity', 'N/A'))" 2>/dev/null || echo "N/A")
        WIND=$(python3 -c "import json; data = json.load(open('/tmp/weather_response.json')); print(data.get('weather', {}).get('wind_speed', 'N/A'))" 2>/dev/null || echo "N/A")
        DESC=$(python3 -c "import json; data = json.load(open('/tmp/weather_response.json')); print(data.get('weather', {}).get('description', 'N/A'))" 2>/dev/null || echo "N/A")
        ORION_STATUS=$(python3 -c "import json; data = json.load(open('/tmp/weather_response.json')); print(data.get('orion_status', 'N/A'))" 2>/dev/null || echo "N/A")
        
        echo -e "${GREEN}   ✓ Succès${NC}"
        echo -e "      📡 Provider utilisé: ${BLUE}${PROVIDER}${NC}"
        echo -e "      🌡️  Temp: ${BLUE}${TEMP}°C${NC} | 💧 Humidité: ${BLUE}${HUM}%${NC} | 💨 Vent: ${BLUE}${WIND}m/s${NC}"
        echo -e "      ☁️  ${DESC}"
        echo -e "      📊 Orion: HTTP ${ORION_STATUS}"
    else
        ERROR_MSG=$(echo "$BODY" | jq -r '.error' 2>/dev/null || echo "$BODY")
        echo -e "${RED}   ✗ Erreur HTTP $HTTP_CODE${NC}"
        echo -e "${RED}   Erreur: ${ERROR_MSG}${NC}"
    fi
    
    echo ""
    sleep 10
done
