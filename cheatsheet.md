# 🎯 Cheatsheet Complète - FIWARE sur Kubernetes + Istio

---

## 📦 GESTION DU CLUSTER

### Informations Cluster
```bash
# Voir les nœuds du cluster
kubectl get nodes

# Info sur le cluster
kubectl cluster-info

# Version de kubectl
kubectl version --client

# Contexte actuel
kubectl config current-context

# Lister tous les contextes
kubectl config get-contexts

# Changer de contexte
kubectl config use-context <nom-contexte>
```

---

## 🏗️ GESTION DES NAMESPACES

```bash
# Lister tous les namespaces
kubectl get namespaces
kubectl get ns

# Créer un namespace
kubectl create namespace <nom>

# Voir détails d'un namespace
kubectl describe namespace fiware-platform

# Supprimer un namespace (⚠️ supprime tout dedans)
kubectl delete namespace fiware-platform
```

---

## 🚀 GESTION DES PODS

### Voir les Pods
```bash
# Lister les pods
kubectl get pods -n fiware-platform

# Avec plus de détails (IP, nœud, etc.)
kubectl get pods -n fiware-platform -o wide

# Surveiller en temps réel
kubectl get pods -n fiware-platform -w
watch kubectl get pods -n fiware-platform

# Filtrer par label
kubectl get pods -n fiware-platform -l app=orion

# Tous les namespaces
kubectl get pods --all-namespaces
kubectl get pods -A
```

### Détails et Debugging
```bash
# Détails complets d'un pod
kubectl describe pod <nom-pod> -n fiware-platform

# Logs d'un pod (conteneur principal)
kubectl logs <nom-pod> -n fiware-platform

# Logs en temps réel (-f = follow)
kubectl logs <nom-pod> -n fiware-platform -f

# Logs d'un conteneur spécifique
kubectl logs <nom-pod> -n fiware-platform -c <nom-conteneur>

# Logs du conteneur précédent (après crash)
kubectl logs <nom-pod> -n fiware-platform --previous

# Logs de tous les pods d'une app
kubectl logs -n fiware-platform -l app=orion -c orion --tail=50

# Shell dans un pod
kubectl exec -it <nom-pod> -n fiware-platform -- /bin/bash
kubectl exec -it <nom-pod> -n fiware-platform -- sh

# Exécuter une commande dans un pod
kubectl exec <nom-pod> -n fiware-platform -- curl localhost:1026/version
```

### Gestion des Pods
```bash
# Supprimer un pod (sera recréé par le Deployment)
kubectl delete pod <nom-pod> -n fiware-platform

# Supprimer tous les pods d'une app
kubectl delete pods -n fiware-platform -l app=orion

# Forcer la suppression (--force --grace-period=0)
kubectl delete pod <nom-pod> -n fiware-platform --force --grace-period=0
```

---

## 📊 GESTION DES DEPLOYMENTS

### Voir les Deployments
```bash
# Lister les deployments
kubectl get deployments -n fiware-platform
kubectl get deploy -n fiware-platform

# Détails d'un deployment
kubectl describe deployment orion -n fiware-platform

# Voir l'historique des rollouts
kubectl rollout history deployment orion -n fiware-platform
```

### Scaling (Changer le Nombre de Replicas)
```bash
# Scaler un deployment
kubectl scale deployment orion --replicas=3 -n fiware-platform

# Scaler tous les deployments
kubectl scale deployment --all --replicas=0 -n fiware-platform

# Autoscaling (HPA)
kubectl autoscale deployment orion --min=2 --max=5 --cpu-percent=80 -n fiware-platform
```

### Rollouts et Mises à Jour
```bash
# Redémarrer un deployment (recréer tous les pods)
kubectl rollout restart deployment orion -n fiware-platform

# Redémarrer tous les deployments
kubectl rollout restart deployment --all -n fiware-platform

# Voir le statut d'un rollout
kubectl rollout status deployment orion -n fiware-platform

# Annuler un rollout (rollback)
kubectl rollout undo deployment orion -n fiware-platform

# Rollback vers une révision spécifique
kubectl rollout undo deployment orion --to-revision=2 -n fiware-platform

# Pause un rollout
kubectl rollout pause deployment orion -n fiware-platform

# Reprendre un rollout
kubectl rollout resume deployment orion -n fiware-platform
```

---

## 🌐 GESTION DES SERVICES

```bash
# Lister les services
kubectl get services -n fiware-platform
kubectl get svc -n fiware-platform

# Détails d'un service
kubectl describe service orion -n fiware-platform

# Voir les endpoints d'un service
kubectl get endpoints orion -n fiware-platform

# Supprimer un service
kubectl delete service orion -n fiware-platform
```

---

## 💾 GESTION DU STOCKAGE

### PersistentVolumeClaims (PVC)
```bash
# Lister les PVC
kubectl get pvc -n fiware-platform

# Détails d'un PVC
kubectl describe pvc mongodb-pvc -n fiware-platform

# Voir l'utilisation du stockage
kubectl get pvc -n fiware-platform -o custom-columns=NAME:.metadata.name,CAPACITY:.status.capacity.storage

# Supprimer un PVC (⚠️ supprime les données)
kubectl delete pvc mongodb-pvc -n fiware-platform
```

### PersistentVolumes (PV)
```bash
# Lister tous les PV
kubectl get pv

# Détails d'un PV
kubectl describe pv <nom-pv>

# Voir les PV orphelins (Released)
kubectl get pv | grep Released

# Supprimer les PV orphelins
kubectl get pv | grep Released | awk '{print $1}' | xargs kubectl delete pv
```

### StorageClasses
```bash
# Lister les classes de stockage disponibles
kubectl get storageclass
kubectl get sc

# Voir la classe par défaut
kubectl get sc -o jsonpath='{.items[?(@.metadata.annotations.storageclass\.kubernetes\.io/is-default-class=="true")].metadata.name}'
```

---

## 🔐 GESTION DES SECRETS

```bash
# Lister les secrets
kubectl get secrets -n fiware-platform

# Voir le contenu d'un secret (encodé base64)
kubectl get secret influxdb-secrets -n fiware-platform -o yaml

# Décoder un secret
kubectl get secret influxdb-secrets -n fiware-platform -o jsonpath='{.data.DOCKER_INFLUXDB_INIT_PASSWORD}' | base64 --decode

# Créer un secret depuis la ligne de commande
kubectl create secret generic my-secret --from-literal=password=secret123 -n fiware-platform

# Supprimer un secret
kubectl delete secret influxdb-secrets -n fiware-platform
```

---

## 🗺️ GESTION DES CONFIGMAPS

```bash
# Lister les ConfigMaps
kubectl get configmap -n fiware-platform
kubectl get cm -n fiware-platform

# Voir le contenu
kubectl describe configmap quantumleap-config -n fiware-platform

# Éditer un ConfigMap
kubectl edit configmap quantumleap-config -n fiware-platform

# Supprimer un ConfigMap
kubectl delete configmap quantumleap-config -n fiware-platform
```

---

## 📡 PORT FORWARDING (Accès Local)

```bash
# Forward un service
kubectl port-forward -n fiware-platform svc/orion 1026:1026

# Forward un pod
kubectl port-forward -n fiware-platform <nom-pod> 1026:1026

# En arrière-plan (&)
kubectl port-forward -n fiware-platform svc/orion 1026:1026 &

# Tuer tous les port-forwards
pkill -f "port-forward"
killall kubectl

# Plusieurs ports en même temps
kubectl port-forward -n fiware-platform svc/orion 1026:1026 &
kubectl port-forward -n fiware-platform svc/grafana 3000:3000 &
kubectl port-forward -n fiware-platform svc/influxdb 8086:8086 &
```

---

## 📋 APPLIQUER DES CONFIGURATIONS

```bash
# Appliquer un fichier
kubectl apply -f k8s/base/namespace.yaml

# Appliquer un dossier
kubectl apply -f k8s/base/mongodb/

# Appliquer récursivement
kubectl apply -f k8s/base/ -R

# Dry-run (voir ce qui serait appliqué sans l'appliquer)
kubectl apply -f k8s/base/orion/ --dry-run=client

# Supprimer selon un fichier
kubectl delete -f k8s/base/orion/deployment.yaml

# Forcer le remplacement
kubectl replace --force -f k8s/base/orion/deployment.yaml
```

---

## 🔍 ÉVÉNEMENTS ET DEBUGGING

```bash
# Voir les événements récents
kubectl get events -n fiware-platform

# Trier par timestamp
kubectl get events -n fiware-platform --sort-by='.lastTimestamp'

# Suivre les événements en temps réel
kubectl get events -n fiware-platform -w

# Événements pour un objet spécifique
kubectl describe pod <nom-pod> -n fiware-platform | grep Events: -A 20

# Tous les événements du cluster
kubectl get events --all-namespaces --sort-by='.lastTimestamp'
```

---

## 📊 MONITORING ET MÉTRIQUES

```bash
# CPU/RAM des nœuds (nécessite metrics-server)
kubectl top nodes

# CPU/RAM des pods
kubectl top pods -n fiware-platform

# Trier par CPU
kubectl top pods -n fiware-platform --sort-by=cpu

# Trier par RAM
kubectl top pods -n fiware-platform --sort-by=memory

# Métriques d'un pod spécifique
kubectl top pod <nom-pod> -n fiware-platform
```

---

## 🕸️ ISTIO

### Dashboards Istio
```bash
# Ouvrir Kiali (visualisation)
istioctl dashboard kiali

# Ouvrir Grafana (métriques)
istioctl dashboard grafana

# Ouvrir Prometheus
istioctl dashboard prometheus

# Ouvrir Jaeger (tracing)
istioctl dashboard jaeger

# Liste de tous les dashboards disponibles
istioctl dashboard --help
```

### Gestion Istio
```bash
# Version d'Istio
istioctl version

# Vérifier l'installation
istioctl verify-install

# Analyser la configuration
istioctl analyze -n fiware-platform

# Voir les proxies (sidecars)
istioctl proxy-status

# Configuration d'un proxy
istioctl proxy-config cluster <nom-pod> -n fiware-platform

# Logs du sidecar Envoy
kubectl logs <nom-pod> -n fiware-platform -c istio-proxy
```

### Objets Istio
```bash
# Lister les Gateways
kubectl get gateway -n fiware-platform

# Lister les VirtualServices
kubectl get virtualservice -n fiware-platform
kubectl get vs -n fiware-platform

# Lister les DestinationRules
kubectl get destinationrule -n fiware-platform
kubectl get dr -n fiware-platform

# Lister les PeerAuthentications (mTLS)
kubectl get peerauthentication -n fiware-platform
kubectl get pa -n fiware-platform

# Voir tous les objets Istio
kubectl get gateway,virtualservice,destinationrule,peerauthentication -n fiware-platform
```

---

## 🛠️ SCRIPTS PERSONNALISÉS (Vos Scripts)

```bash
# Voir le statut complet
./scripts/status.sh

# Arrêter la plateforme (scale à 0)
./scripts/stop.sh

# Redémarrer la plateforme
./scripts/start.sh

# Nettoyage complet (⚠️ supprime tout)
./scripts/cleanup.sh

# Redéploiement complet
./scripts/redeploy.sh

# Déploiement initial
./scripts/deploy.sh
```

---

## 🧪 TESTS ET VALIDATION

### Tester la Connectivité
```bash
# Lancer un pod temporaire pour tester
kubectl run curl-test --image=curlimages/curl --rm -it --restart=Never -n fiware-platform -- sh

# Depuis ce pod, tester les services :
# curl http://orion:1026/version
# curl http://mongodb:27017
# curl http://influxdb:8086/health

# Test direct (sans entrer dans le pod)
kubectl run curl-test --image=curlimages/curl --rm -it --restart=Never -n fiware-platform -- curl http://orion:1026/version
```

### Tester Orion
```bash
# Version
curl http://localhost:1026/version

# Créer une entité
curl -X POST http://localhost:1026/v2/entities \
  -H 'Content-Type: application/json' \
  -d '{"id":"Room1","type":"Room","temperature":{"value":23,"type":"Number"}}'

# Lister les entités
curl http://localhost:1026/v2/entities

# Récupérer une entité
curl http://localhost:1026/v2/entities/Room1

# Statistiques Orion
curl http://localhost:1026/statistics

# Mettre à jour un attribut
curl -X PUT http://localhost:1026/v2/entities/Room1/attrs/temperature/value \
  -H 'Content-Type: text/plain' \
  -d '25'

# Supprimer une entité
curl -X DELETE http://localhost:1026/v2/entities/Room1
```

---

## 🔄 ACTIONS RAPIDES COURANTES

### Redémarrer un Service qui Bug
```bash
# Redémarrer Orion
kubectl rollout restart deployment orion -n fiware-platform

# Ou supprimer le pod (il sera recréé)
kubectl delete pod -n fiware-platform -l app=orion
```

### Voir Pourquoi un Pod ne Démarre Pas
```bash
# 1. Voir le statut
kubectl get pod <nom-pod> -n fiware-platform

# 2. Voir les détails
kubectl describe pod <nom-pod> -n fiware-platform

# 3. Voir les logs
kubectl logs <nom-pod> -n fiware-platform

# 4. Logs du conteneur précédent si crashé
kubectl logs <nom-pod> -n fiware-platform --previous
```

### Libérer des Ressources
```bash
# Arrêter tout sans supprimer
kubectl scale deployment --all --replicas=0 -n fiware-platform

# Supprimer les pods Completed/Failed
kubectl delete pods -n fiware-platform --field-selector=status.phase=Failed
kubectl delete pods -n fiware-platform --field-selector=status.phase=Succeeded
```

### Accéder Rapidement aux Services
```bash
# Orion
kubectl port-forward -n fiware-platform svc/orion 1026:1026 &

# InfluxDB
kubectl port-forward -n fiware-platform svc/influxdb 8086:8086 &

# Grafana
kubectl port-forward -n fiware-platform svc/grafana 3000:3000 &

# Kiali
istioctl dashboard kiali
```

---

## 📝 ÉDITION RAPIDE

```bash
# Éditer un Deployment
kubectl edit deployment orion -n fiware-platform

# Éditer un Service
kubectl edit service orion -n fiware-platform

# Éditer un ConfigMap
kubectl edit configmap quantumleap-config -n fiware-platform

# Éditer un Secret
kubectl edit secret influxdb-secrets -n fiware-platform
```

---

## 🗑️ NETTOYAGE

```bash
# Supprimer un deployment
kubectl delete deployment orion -n fiware-platform

# Supprimer tous les deployments
kubectl delete deployment --all -n fiware-platform

# Supprimer le namespace complet
kubectl delete namespace fiware-platform

# Supprimer les ressources selon un fichier
kubectl delete -f k8s/base/orion/

# Supprimer en force
kubectl delete pod <nom-pod> -n fiware-platform --force --grace-period=0

# Nettoyer les PV orphelins
kubectl get pv | grep Released | awk '{print $1}' | xargs kubectl delete pv
```

---

## 🎯 LABELS ET SÉLECTEURS

```bash
# Lister avec labels
kubectl get pods -n fiware-platform --show-labels

# Filtrer par label
kubectl get pods -n fiware-platform -l app=orion
kubectl get pods -n fiware-platform -l app=orion,version=v4

# Plusieurs labels (OR)
kubectl get pods -n fiware-platform -l 'app in (orion,mongodb)'

# Ajouter un label
kubectl label pod <nom-pod> env=production -n fiware-platform

# Supprimer un label
kubectl label pod <nom-pod> env- -n fiware-platform

# Modifier un label
kubectl label pod <nom-pod> env=staging --overwrite -n fiware-platform
```

---

## 📤 EXPORT ET SAUVEGARDE

```bash
# Exporter un deployment en YAML
kubectl get deployment orion -n fiware-platform -o yaml > orion-backup.yaml

# Exporter tout le namespace
kubectl get all -n fiware-platform -o yaml > fiware-backup.yaml

# Exporter les secrets (⚠️ sensible)
kubectl get secrets -n fiware-platform -o yaml > secrets-backup.yaml

# Exporter les PVC
kubectl get pvc -n fiware-platform -o yaml > pvc-backup.yaml
```

---

## 🔍 RECHERCHE ET FILTRAGE

```bash
# Pods avec leur IP
kubectl get pods -n fiware-platform -o wide

# Pods avec colonnes personnalisées
kubectl get pods -n fiware-platform -o custom-columns=NAME:.metadata.name,STATUS:.status.phase,IP:.status.podIP

# JSON Path
kubectl get pods -n fiware-platform -o jsonpath='{.items[*].metadata.name}'

# Formater en JSON
kubectl get pod <nom-pod> -n fiware-platform -o json

# Formater en YAML
kubectl get pod <nom-pod> -n fiware-platform -o yaml

# Grep dans les ressources
kubectl get pods -n fiware-platform | grep orion
```