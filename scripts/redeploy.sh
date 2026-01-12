#!/bin/bash

set -e

NAMESPACE="fiware-platform"
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN} Building docker images ${NC}"
echo ""
# Construire les images Docker
docker build -t smartfarm/decision-service:local ./docker/serviceDecision/
docker build -t smartfarm/ai-service:local ./docker/serviceIA/
docker build -t smartfarm/notification-service:local ./docker/serviceNotif/

echo -e "${GREEN} Redéploiement complet de la plateforme FIWARE...${NC}"
echo ""

# Fonction pour attendre les pods
wait_for_pods() {
    local app=$1
    echo -e "${YELLOW}   ⏳ Attente de $app...${NC}"
    kubectl wait --for=condition=ready pod -l app=$app -n $NAMESPACE --timeout=300s 2>/dev/null
    echo -e "${GREEN}   ✅ $app prêt${NC}"
}

# 1. Namespace
echo -e "${BLUE}[0/9]${NC} Création du namespace..."
kubectl apply -f k8s/base/namespace.yaml
sleep 2

# 7. Istio Services
echo -e "${BLUE}[1/9]${NC} Déploiement des Services Istio..."
kubectl apply -f k8s/istio/
sleep 10

# 2. MongoDB
echo -e "${BLUE}[2/9]${NC} Déploiement de MongoDB..."
kubectl apply -f k8s/base/mongodb/
wait_for_pods "mongodb"

# 3. Cratedb
echo -e "${BLUE}[3/9]${NC} Déploiement de Cratedb..."
kubectl apply -f k8s/base/cratedb/
wait_for_pods "cratedb"

# 4. Orion
echo -e "${BLUE}[4/9]${NC} Déploiement d'Orion..."
kubectl apply -f k8s/base/orion/
wait_for_pods "orion"

# 5. QuantumLeap
echo -e "${BLUE}[5/9]${NC} Déploiement de QuantumLeap..."
kubectl apply -f k8s/base/quantumleap/
wait_for_pods "quantumleap"

# 6. IoT Agent
echo -e "${BLUE}[6/9]${NC} Déploiement de l'IoT Agent..."
kubectl apply -f k8s/base/iot-agent/
wait_for_pods "iot-agent"

#7. Grafana pod
echo -e "${BLUE}[7/9]${NC} Création de l'utilisateur Grafana..."
kubectl apply -f k8s/base/grafana/
wait_for_pods "grafana"

#8. AI-service
echo -e "${BLUE}[8/9]${NC} Déploiement de l'AI-Service..."
kubectl apply -f k8s/base/ai-service/
wait_for_pods "ai-service"

#9. Decision-service
echo -e "${BLUE}[9/9]${NC} Déploiement de la Decision-Service..."
kubectl apply -f k8s/base/decision-service/
wait_for_pods "decision-service"


if [ -f .env ]; then
    # "export" automatiquement les variables lues
    set -a
    source .env
    set +a
else
    echo "⚠️  Erreur : Fichier .env introuvable !"
    exit 1
fi

# 2. Vérifier que la variable existe bien
if [ -z "$DISCORD_WEBHOOK_URL" ]; then
    echo "⚠️  Erreur : La variable DISCORD_WEBHOOK_URL est vide ou absente du .env"
    exit 1
fi

echo "🚀 Création/Mise à jour du secret Discord..."

kubectl create secret generic discord-secret \
  --namespace=fiware-platform \
  --from-literal=webhook_url_discord="$DISCORD_WEBHOOK_URL" \
  --dry-run=client -o yaml | kubectl apply -f -

echo "✅ Secret 'discord-secret' configuré."

sleep 2 

#10. Notification-service
echo -e "${BLUE}[10/9]${NC} Déploiement de la Notification-Service..."
kubectl apply -f k8s/base/notification-service/
wait_for_pods "notification-service"




# Installer Prometheus
kubectl apply -f ~/istio/istio-1.28.0/samples/addons/prometheus.yaml

# Installer Grafana
kubectl apply -f ~/istio/istio-1.28.0/samples/addons/grafana.yaml

# Installer Kiali
kubectl apply -f ~/istio/istio-1.28.0/samples/addons/kiali.yaml

echo ""
echo -e "${GREEN}✅ Redéploiement terminé !${NC}"
echo ""
echo -e "Statut final :"
kubectl get pods -n fiware-platform
