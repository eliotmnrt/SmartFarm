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
echo -e "${BLUE}[1/11]${NC} Création du namespace..."
kubectl apply -f ../k8s/base/namespace.yaml
sleep 2

# 2. Istio
echo -e "${BLUE}[2/11]${NC} Déploiement des Services Istio..."
kubectl apply -f ../k8s/istio/
sleep 10

# 3. MongoDB
echo -e "${BLUE}[3/11]${NC} Déploiement de MongoDB..."
kubectl apply -f ../k8s/base/mongodb/
wait_for_pods "mongodb"

# 4. Cratedb
echo -e "${BLUE}[4/11]${NC} Déploiement de Cratedb..."
kubectl apply -f ../k8s/base/cratedb/
wait_for_pods "cratedb"

# 5. Orion
echo -e "${BLUE}[5/11]${NC} Déploiement d'Orion..."
kubectl apply -f ../k8s/base/orion/
wait_for_pods "orion"

# 6. QuantumLeap
echo -e "${BLUE}[6/11]${NC} Déploiement de QuantumLeap..."
kubectl apply -f ../k8s/base/quantumleap/
wait_for_pods "quantumleap"

# 7. IoT Agent
echo -e "${BLUE}[7/11]${NC} Déploiement de l'IoT Agent..."
kubectl apply -f ../k8s/base/iot-agent/
wait_for_pods "iot-agent"

# 9. Grafana pod
echo -e "${BLUE}[9/11]${NC} Création de l'utilisateur Grafana..."
kubectl apply -f ../k8s/base/grafana/
wait_for_pods "grafana"

# 9. AI-service
echo -e "${BLUE}[9/11]${NC} Déploiement de l'AI-Service..."
kubectl apply -f k8s/base/ai-service/
wait_for_pods "ai-service"

# 10. Decision-service
echo -e "${BLUE}[10/11]${NC} Déploiement de la Decision-Service..."
kubectl apply -f k8s/base/decision-service/
wait_for_pods "decision-service"

#11. Weather Agent
echo -e "${BLUE}[11/11]${NC} Déploiement du Weather Agent..."
kubectl apply -f k8s/base/weather-agent/
wait_for_pods "weather-agent"





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
