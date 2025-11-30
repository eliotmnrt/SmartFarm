#!/bin/bash

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

NAMESPACE="fiware-platform"

echo -e "${BLUE}��� Simulation de Capteur IoT${NC}"

kubectl port-forward -n $NAMESPACE svc/iot-agent 7896:7896 > /dev/null 2>&1 &
PF=$!

cleanup() {
    kill $PF 2>/dev/null || true
}
trap cleanup EXIT

sleep 3

echo -e "${GREEN}✅ Prêt à envoyer des données${NC}"
echo -e "${YELLOW}Appuyez sur Ctrl+C pour arrêter${NC}"
echo ""

COUNT=0
while true; do
    TEMP=$(awk -v min=18 -v max=28 'BEGIN{srand(); printf "%.1f", min+rand()*(max-min)}')
    HUM=$(awk -v min=50 -v max=80 'BEGIN{srand(); printf "%.0f", min+rand()*(max-min)}')
    PRESS=$(awk -v min=990 -v max=1020 'BEGIN{srand(); printf "%.0f", min+rand()*(max-min)}')
    
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
      -X POST "http://localhost:7896/iot/json?k=4jggokgpepnvsb2uv4s40d59ov&i=sensor001" \
      -H 'Content-Type: application/json' \
      -d "{\"t\": $TEMP, \"h\": $HUM, \"p\": $PRESS}")
    
    COUNT=$((COUNT + 1))
    
    if [ "$RESPONSE" -eq 200 ]; then
        echo -e "${GREEN}[$COUNT] ✓${NC} Temp: ${BLUE}${TEMP}°C${NC} | Hum: ${BLUE}${HUM}%${NC} | Press: ${BLUE}${PRESS}hPa${NC}"
    else
        echo -e "${RED}[$COUNT] ✗ Erreur HTTP $RESPONSE${NC}"
    fi
    
    sleep 5
done
