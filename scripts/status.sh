#!/bin/bash

NAMESPACE="fiware-platform"
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}��� Statut de la plateforme FIWARE${NC}"
echo ""

# Pods
echo -e "${YELLOW}═══ PODS ═══${NC}"
kubectl get pods -n $NAMESPACE

echo ""
echo -e "${YELLOW}═══ SERVICES ═══${NC}"
kubectl get svc -n $NAMESPACE

echo ""
echo -e "${YELLOW}═══ PVC (Stockage) ═══${NC}"
kubectl get pvc -n $NAMESPACE

echo ""
echo -e "${YELLOW}═══ VIRTUALSERVICES (Istio) ═══${NC}"
kubectl get virtualservices -n $NAMESPACE 2>/dev/null || echo "Aucun VirtualService"

echo ""
echo -e "${YELLOW}═══ RESSOURCES UTILISÉES ═══${NC}"
kubectl top pods -n $NAMESPACE 2>/dev/null || echo "Metrics server non disponible"
