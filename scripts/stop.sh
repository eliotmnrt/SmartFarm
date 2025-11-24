#!/bin/bash

set -e

NAMESPACE="fiware-platform"
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🛑 Arrêt de la plateforme FIWARE...${NC}"

# Scale tous les deployments à 0
echo -e "${YELLOW}Mise à l'échelle des deployments à 0...${NC}"
kubectl scale deployment --all --replicas=0 -n $NAMESPACE

# Attendre que tous les pods soient terminés
echo -e "${YELLOW}Attente de l'arrêt des pods...${NC}"
kubectl wait --for=delete pod --all -n $NAMESPACE --timeout=120s 2>/dev/null || true

echo -e "${GREEN}✅ Plateforme arrêtée${NC}"
echo -e "Les données sont préservées dans les PVC"