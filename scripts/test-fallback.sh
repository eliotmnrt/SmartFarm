#!/bin/bash

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

NAMESPACE="fiware-platform"

echo -e "${BLUE}🧪 Test du mécanisme de fallback Weather Agent${NC}"
echo -e "${YELLOW}════════════════════════════════════════════════${NC}"
echo ""

# Configuration actuelle
CURRENT_CONFIG='[{"type": "script", "name": "LocalScript-Primary", "path": "/opt/scripts/weather-data.sh"}, {"type": "openmeteo", "name": "Open-Meteo-Fallback"}]'

# Configuration avec script cassé pour forcer le fallback
BROKEN_CONFIG='[{"type": "script", "name": "LocalScript-Primary", "path": "/opt/scripts/INVALID-PATH.sh"}, {"type": "openmeteo", "name": "Open-Meteo-Fallback"}]'

echo -e "${BLUE}📝 Étape 1: Test avec configuration normale${NC}"
echo -e "   Provider attendu: ${GREEN}LocalScript-Primary${NC}"
echo ""

kubectl port-forward -n $NAMESPACE svc/weather-agent 8888:8888 > /dev/null 2>&1 &
PF_PID=$!

cleanup() {
    kill $PF_PID 2>/dev/null || true
}
trap cleanup EXIT

sleep 3

RESPONSE=$(curl -s -X POST "http://localhost:8888/weather" \
  -H 'Content-Type: application/json' \
  -d '{"lat": 48.8566, "lon": 2.3522, "entity_id": "Weather:TestNormal"}')

PROVIDER=$(echo "$RESPONSE" | python3 -c "import json, sys; data = json.load(sys.stdin); print(data.get('provider', 'Unknown'))" 2>/dev/null || echo "Unknown")

if [ "$PROVIDER" = "LocalScript-Primary" ]; then
    echo -e "   ${GREEN}✅ Test 1 réussi: LocalScript fonctionne${NC}"
    echo -e "      Provider utilisé: ${BLUE}$PROVIDER${NC}"
else
    echo -e "   ${RED}❌ Test 1 échoué: Provider = $PROVIDER (attendu: LocalScript-Primary)${NC}"
fi

echo ""
echo -e "${BLUE}📝 Étape 2: Modification de la config pour casser le script local${NC}"
echo -e "   Changement du chemin vers un fichier invalide..."

kubectl set env deployment/weather-agent -n $NAMESPACE \
  WEATHER_APIS_CONFIG="$BROKEN_CONFIG" > /dev/null 2>&1

echo -e "   ${YELLOW}⏳ Attente du redémarrage du pod...${NC}"
kubectl rollout status deployment/weather-agent -n $NAMESPACE --timeout=60s

# Redémarrer le port-forward
kill $PF_PID 2>/dev/null || true
sleep 2
kubectl port-forward -n $NAMESPACE svc/weather-agent 8888:8888 > /dev/null 2>&1 &
PF_PID=$!
sleep 3

echo ""
echo -e "${BLUE}📝 Étape 3: Test avec script cassé (fallback attendu)${NC}"
echo -e "   Provider attendu: ${GREEN}Open-Meteo-Fallback${NC}"
echo ""

RESPONSE=$(curl -s -X POST "http://localhost:8888/weather" \
  -H 'Content-Type: application/json' \
  -d '{"lat": 48.8566, "lon": 2.3522, "entity_id": "Weather:TestFallback"}')

PROVIDER=$(echo "$RESPONSE" | python3 -c "import json, sys; data = json.load(sys.stdin); print(data.get('provider', 'Unknown'))" 2>/dev/null || echo "Unknown")
TEMP=$(echo "$RESPONSE" | python3 -c "import json, sys; data = json.load(sys.stdin); print(data.get('weather', {}).get('temp', 'N/A'))" 2>/dev/null || echo "N/A")

if [ "$PROVIDER" = "Open-Meteo-Fallback" ]; then
    echo -e "   ${GREEN}✅ Test 2 réussi: Fallback vers Open-Meteo${NC}"
    echo -e "      Provider utilisé: ${BLUE}$PROVIDER${NC}"
    echo -e "      Température: ${BLUE}${TEMP}°C${NC}"
else
    echo -e "   ${RED}❌ Test 2 échoué: Provider = $PROVIDER (attendu: Open-Meteo-Fallback)${NC}"
fi

echo ""
echo -e "${BLUE}📝 Étape 4: Restauration de la configuration normale${NC}"

kubectl set env deployment/weather-agent -n $NAMESPACE \
  WEATHER_APIS_CONFIG="$CURRENT_CONFIG" > /dev/null 2>&1

echo -e "   ${YELLOW}⏳ Attente du redémarrage du pod...${NC}"
kubectl rollout status deployment/weather-agent -n $NAMESPACE --timeout=60s

# Redémarrer le port-forward
kill $PF_PID 2>/dev/null || true
sleep 2
kubectl port-forward -n $NAMESPACE svc/weather-agent 8888:8888 > /dev/null 2>&1 &
PF_PID=$!
sleep 3

echo ""
echo -e "${BLUE}📝 Étape 5: Vérification que le script local refonctionne${NC}"

RESPONSE=$(curl -s -X POST "http://localhost:8888/weather" \
  -H 'Content-Type: application/json' \
  -d '{"lat": 48.8566, "lon": 2.3522, "entity_id": "Weather:TestRestore"}')

PROVIDER=$(echo "$RESPONSE" | python3 -c "import json, sys; data = json.load(sys.stdin); print(data.get('provider', 'Unknown'))" 2>/dev/null || echo "Unknown")

if [ "$PROVIDER" = "LocalScript-Primary" ]; then
    echo -e "   ${GREEN}✅ Test 3 réussi: Configuration restaurée${NC}"
    echo -e "      Provider utilisé: ${BLUE}$PROVIDER${NC}"
else
    echo -e "   ${RED}❌ Test 3 échoué: Provider = $PROVIDER (attendu: LocalScript-Primary)${NC}"
fi

echo ""
echo -e "${YELLOW}════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Tests de fallback terminés${NC}"
echo ""
