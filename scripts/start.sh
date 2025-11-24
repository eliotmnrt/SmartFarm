#!/bin/bash

set -e

NAMESPACE="fiware-platform"
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}🚀 Démarrage de la plateforme FIWARE...${NC}"

# Fonction pour attendre les pods
wait_for_pods() {
    local app=$1
    local replicas=$2
    echo -e "${YELLOW}   ⏳ Attente de $app...${NC}"
    kubectl wait --for=condition=ready pod -l app=$app -n $NAMESPACE --timeout=300s
    echo -e "${GREEN}   ✅ $app démarré ($replicas replicas)${NC}"
}

# Deploiement des Services Istio
echo -e "${BLUE}[0/5]${NC} Déploiement des Services Istio..."
kubectl scale deployment istio-ingressgateway --replicas=1 -n istio-system

# Démarrer MongoDB
echo -e "${BLUE}[1/5]${NC} Démarrage de MongoDB..."
kubectl scale deployment mongodb --replicas=1 -n $NAMESPACE
wait_for_pods "mongodb" 1

# Démarrer InfluxDcratedbB
echo -e "${BLUE}[2/5]${NC} Démarrage de Cratedb..."
kubectl scale deployment cratedb --replicas=1 -n $NAMESPACE
wait_for_pods "cratedb" 1

# Démarrer Orion
echo -e "${BLUE}[3/5]${NC} Démarrage d'Orion..."
kubectl scale deployment orion --replicas=1 -n $NAMESPACE
wait_for_pods "orion" 1

# demarrer QuantumLeap
echo -e "${BLUE}[4/5]${NC} Démarrage de QuantumLeap..."
kubectl scale deployment quantumleap --replicas=1 -n $NAMESPACE
wait_for_pods "quantumleap" 1

# Démarrer IoT Agent
echo -e "${BLUE}[5/5]${NC} Démarrage de l'IoT Agent..."
kubectl scale deployment iot-agent --replicas=1 -n $NAMESPACE
wait_for_pods "iot-agent" 1


echo ""
echo -e "${GREEN}✅ Plateforme démarrée avec succès !${NC}"
echo ""
echo -e "Statut des pods :"
kubectl get pods -n $NAMESPACE