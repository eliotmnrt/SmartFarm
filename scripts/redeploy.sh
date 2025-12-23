#!/bin/bash

set -e

NAMESPACE="fiware-platform"
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}��� Redéploiement complet de la plateforme FIWARE...${NC}"
echo ""

# Fonction pour attendre les pods
wait_for_pods() {
    local app=$1
    echo -e "${YELLOW}   ⏳ Attente de $app...${NC}"
    kubectl wait --for=condition=ready pod -l app=$app -n $NAMESPACE --timeout=300s 2>/dev/null
    echo -e "${GREEN}   ✅ $app prêt${NC}"
}

# 1. Namespace
echo -e "${BLUE}[1/6]${NC} Création du namespace..."
kubectl apply -f k8s/base/namespace.yaml
sleep 2

# 7. Istio
echo -e "${BLUE}[1.5/6]${NC} Déploiement des Services Istio..."
kubectl apply -f k8s/istio/
sleep 10

# 2. MongoDB
echo -e "${BLUE}[2/6]${NC} Déploiement de MongoDB..."
kubectl apply -f k8s/base/mongodb/
wait_for_pods "mongodb"

# 3. Cratedb
echo -e "${BLUE}[3/6]${NC} Déploiement de Cratedb..."
kubectl apply -f k8s/base/cratedb/
wait_for_pods "cratedb"

# 4. Orion
echo -e "${BLUE}[4/6]${NC} Déploiement d'Orion..."
kubectl apply -f k8s/base/orion/
wait_for_pods "orion"

# 5. QuantumLeap
echo -e "${BLUE}[5/6]${NC} Déploiement de QuantumLeap..."
kubectl apply -f k8s/base/quantumleap/
wait_for_pods "quantumleap"

# 6. IoT Agent
echo -e "${BLUE}[6/6]${NC} Déploiement de l'IoT Agent..."
kubectl apply -f k8s/base/iot-agent/
wait_for_pods "iot-agent"

#7. Grafana pod
echo -e "${BLUE}[7/6]${NC} Création de l'utilisateur Grafana..."
kubectl apply -f k8s/base/grafana/
wait_for_pods "grafana"

#8. AI-service
echo -e "${BLUE}[8/6]${NC} Déploiement de l'AI-Service..."
kubectl apply -f k8s/base/ai-service/
wait_for_pods "ai-service"




# Installer Prometheus
kubectl apply -f ~/istio/istio-1.28.0/samples/addons/prometheus.yaml

# Installer Grafana
kubectl apply -f ~/istio/istio-1.28.0/samples/addons/grafana.yaml

# Installer Kiali
kubectl apply -f ~/istio/istio-1.28.0/samples/addons/kiali.yaml
wait_for_pods "kiali"

echo ""
echo -e "${GREEN}✅ Redéploiement terminé !${NC}"
echo ""
echo -e "Statut final :"
kubectl get pods -n fiware-platform
