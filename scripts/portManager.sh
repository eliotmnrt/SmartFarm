#!/bin/bash

# ==========================================
# GESTION DES FICHIERS ET COULEURS
# ==========================================
PID_FILE="/tmp/fiware_pids.txt"

# Couleurs pour le terminal
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# ==========================================
# FONCTION : OUVRIR LES TUNNELS (start_port_forwards)
# ==========================================
start_port_forwards() {
    local NAMESPACE=$1
    echo -e "${YELLOW}🔌 Mise en place des tunnels (Port-Forwarding)...${NC}"

    if [ -f "$PID_FILE" ]; then
        echo -e "${RED}Attention:${NC} Le fichier PID ($PID_FILE) existe déjà. Les anciens tunnels sont peut-être actifs."
        status_port_forwards
        echo "Si des tunnels sont actifs, veuillez les fermer avec './portManager.sh stop' avant de continuer."
        return 1
    fi

    # Récupération dynamique des noms de pods
    POD_ORION=$(kubectl get pod -n $NAMESPACE -l app=orion -o jsonpath="{.items[0].metadata.name}" 2>/dev/null)
    POD_IOTA=$(kubectl get pod -n $NAMESPACE -l app=iot-agent -o jsonpath="{.items[0].metadata.name}" 2>/dev/null)
    POD_QL=$(kubectl get pod -n $NAMESPACE -l app=quantumleap -o jsonpath="{.items[0].metadata.name}" 2>/dev/null)
    POD_GRAFANA=$(kubectl get pod -n $NAMESPACE -l app=grafana -o jsonpath="{.items[0].metadata.name}" 2>/dev/null)
    POD_CRATE=$(kubectl get pod -n $NAMESPACE -l app=cratedb -o jsonpath="{.items[0].metadata.name}" 2>/dev/null)

    if [ -z "$POD_ORION" ] || [ -z "$POD_IOTA" ]; then
        echo -e "${RED}ERREUR:${NC} Impossible de trouver les pods Orion ou IoT Agent dans le namespace $NAMESPACE."
        return 1
    fi

    # Lancement des tunnels en arrière-plan et stockage des PIDs
    ALL_PIDS=()
    
    # Orion
    kubectl port-forward -n $NAMESPACE $POD_ORION 1026:1026 > /dev/null 2>&1 &
    ALL_PIDS+=($!)
    echo "  - Orion: 1026 (PID: $!)"
    
    # IoT Agent (North & South)
    kubectl port-forward -n $NAMESPACE $POD_IOTA 4041:4041 > /dev/null 2>&1 &
    ALL_PIDS+=($!)
    echo "  - IoT Agent (Config): 4041 (PID: $!)"
    
    kubectl port-forward -n $NAMESPACE $POD_IOTA 7896:7896 > /dev/null 2>&1 &
    ALL_PIDS+=($!)
    echo "  - IoT Agent (Data): 7896 (PID: $!)"
    
    # Grafana
    kubectl port-forward -n $NAMESPACE $POD_GRAFANA 3000:3000 > /dev/null 2>&1 &
    ALL_PIDS+=($!)
    echo "  - Grafana: 3000 (PID: $!)"
    
    # QuantumLeap
    kubectl port-forward -n $NAMESPACE $POD_QL 8668:8668 > /dev/null 2>&1 &
    ALL_PIDS+=($!)
    echo "  - QuantumLeap: 8668 (PID: $!)"

    # CrateDB
    kubectl port-forward -n $NAMESPACE $POD_CRATE 4200:4200 > /dev/null 2>&1 &
    ALL_PIDS+=($!)
    echo "  - CrateDB: 4200 (PID: $!)"

    # Stocker tous les PIDs dans un fichier temporaire
    echo "${ALL_PIDS[@]}" > "$PID_FILE"
    
    echo -e "${GREEN}✅ Tunnels lancés. Attente de 5s pour la stabilisation...${NC}"
    sleep 5
    return 0
}

# ==========================================
# FONCTION : STATUT DES TUNNELS (status_port_forwards)
# ==========================================
status_port_forwards() {
    echo -e "${YELLOW}🔍 Vérification du statut des Port-Forwards...${NC}"
    if [ ! -f "$PID_FILE" ]; then
        echo "   Aucun fichier PID trouvé. Les tunnels sont supposés fermés."
        return
    fi
    
    PIDS=$(cat "$PID_FILE")
    for PID in $PIDS; do
        # kill -0 $PID vérifie si le processus existe et peut recevoir des signaux
        if kill -0 $PID 2>/dev/null; then
            echo -e "   [${GREEN}ACTIF${NC}] PID $PID est en cours d'exécution."
        else
            echo -e "   [${RED}INACTIF${NC}] PID $PID ne répond plus (tunnel fermé)."
        fi
    done
}

# ==========================================
# FONCTION : FERMER LES TUNNELS (close_port_forwards)
# ==========================================
close_port_forwards() {
    echo -e "${YELLOW}🛑 Fermeture de tous les Port-Forwards...${NC}"
    if [ ! -f "$PID_FILE" ]; then
        echo "   Aucun fichier PID trouvé. Rien à fermer."
        return 0
    fi

    PIDS=$(cat "$PID_FILE")
    SUCCESS_COUNT=0
    for PID in $PIDS; do
        if kill $PID 2>/dev/null; then
            echo "   [TERMINÉ] Processus $PID tué."
            SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        fi
    done

    if [ $SUCCESS_COUNT -gt 0 ]; then
        rm "$PID_FILE"
        echo -e "${GREEN}✅ $SUCCESS_COUNT tunnels fermés et nettoyage effectué.${NC}"
        return 0
    else
        echo "   Aucun processus actif à fermer. Nettoyage du fichier PID."
        rm "$PID_FILE"
        return 0
    fi
}

# ==========================================
# EXÉCUTION SELON L'ARGUMENT
# ==========================================
ACTION=$1

case "$ACTION" in
    start)
        # Nécessite le namespace en argument 2
        start_port_forwards $2
        ;;
    stop)
        close_port_forwards
        ;;
    status)
        status_port_forwards
        ;;
    *)
        echo "Usage: $0 {start <namespace> | stop | status}"
        exit 1
        ;;
esac