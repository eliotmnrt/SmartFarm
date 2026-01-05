#!/bin/bash

set -e

NAMESPACE="fiware-platform"
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${RED}⚠️  ATTENTION : Cela va supprimer TOUTES les données !${NC}"
echo -e "${YELLOW}Appuyez sur Entrée pour continuer ou Ctrl+C pour annuler...${NC}"
read

echo -e "${YELLOW}���️  Suppression du namespace...${NC}"
kubectl delete namespace $NAMESPACE

echo -e "${YELLOW}Attente de la suppression complète...${NC}"
while kubectl get namespace $NAMESPACE 2>/dev/null; do
    echo -n "."
    sleep 2
done
echo ""

echo -e "${GREEN}✅ Namespace supprimé${NC}"

# Optionnel : Nettoyer les PersistentVolumes orphelins
echo ""

./scripts/portManager.sh stop

echo -e "${GREEN}✅ Nettoyage complet terminé${NC}"
