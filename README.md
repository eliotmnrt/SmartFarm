
-----

# 🌾 SmartFarm - Plateforme IoT FIWARE sur Kubernetes

**SmartFarm** est une plateforme IoT cloud-native dédiée à l'agriculture intelligente ("Smart Agriculture"). Elle permet la collecte, le traitement, l'historisation et la visualisation de données de capteurs (Température, Humidité, Pression, Sol, etc.) en utilisant l'écosystème **FIWARE** standardisé.

L'infrastructure est déployée sur **Kubernetes** et sécurisée/gérée par **Istio** (Service Mesh).

-----

## 🏗️ Architecture

Le système repose sur une architecture micro-services :

  * **Ingestion IoT** :
      * [cite\_start]**IoT Agent (JSON)** : Bridge pour connecter les appareils HTTP/MQTT au format NGSI[cite: 188].
  * **Gestion de Contexte** :
      * [cite\_start]**Orion Context Broker** : Cœur de la plateforme, gère l'état actuel des entités (Digital Twins)[cite: 221].
      * [cite\_start]**MongoDB** : Base de données pour Orion et l'IoT Agent[cite: 201].
  * **Historisation (Time-Series)** :
      * [cite\_start]**QuantumLeap** : Persiste les données historiques géospatiales et temporelles[cite: 235].
      * [cite\_start]**CrateDB** : Base de données SQL orientée Time-Series pour le stockage long terme[cite: 138].
  * **Visualisation** :
      * [cite\_start]**Grafana** : Tableaux de bord pour visualiser les données agronomiques via CrateDB[cite: 173].
  * **Infrastructure** :
      * **Kubernetes** : Orchestration des conteneurs.
      * [cite\_start]**Istio** : Gestion du trafic, Ingress Gateway et sécurité mTLS[cite: 247, 248].

-----

## 📋 Prérequis

Avant de commencer, assurez-vous d'avoir installé :

1.  **Kubernetes Cluster** (Docker Desktop, Minikube, ou K3s).
2.  **kubectl** (CLI Kubernetes configurée).
3.  **Istio** (installé sur le cluster ou via `istioctl` dans le même repertoire que le script redeploy.sh).
4.  **Outils CLI** : `curl`, `jq` (pour les scripts).

-----

## 🚀 Installation et Déploiement

### 1\. Démarrage du Cluster

Assurez-vous que votre cluster Kubernetes est actif.

```bash
kubectl cluster-info
```

### 2\. Déploiement des Services (Infrastructure)

[cite\_start]Utilisez le script `redeploy.sh` pour déployer l'ensemble de la stack dans l'ordre correct (Namespace -\> Istio -\> DBs -\> Apps)[cite: 268].

```bash
cd eliotmnrt-smartfarm
chmod +x scripts/*.sh
./scripts/redeploy.sh
```

*Ce script va :*

1.  [cite\_start]Créer le namespace `fiware-platform` avec l'injection Istio activée[cite: 137].
2.  Déployer les bases de données (MongoDB, CrateDB, InfluxDB).
3.  Déployer les composants FIWARE (Orion, IoT Agent, QuantumLeap).
4.  Déployer Grafana avec les sources de données pré-configurées.

### 3\. Vérification des Pods

Vérifiez que tous les pods sont en statut `Running` (1/1 ou 2/2 si Istio sidecar est actif).

```bash
kubectl get pods -n fiware-platform
```

-----

## ⚙️ Setup et Configuration (Provisioning)

Une fois les pods démarrés, il faut configurer la logique métier (créer les groupes de services, déclarer les capteurs et activer l'historisation).

Le script `setup.sh` automatise cette étape critique.

### Lancer le Setup

```bash
./scripts/setup.sh
```

[cite\_start]**Ce que fait ce script [cite: 275-285] :**

1.  **Port-Forwarding** : Ouvre des tunnels temporaires vers Orion (:1026), IoT Agent (:4041/:7896) et Grafana (:3000) pour permettre la configuration depuis votre machine locale.
2.  **Service Group** : Configure l'IoT Agent pour accepter les données avec l'API Key.
3.  **Device Provisioning** : Crée le capteur `sensor001` et le lie explicitement à l'entité `urn:ngsi-ld:Sensor:001` pour éviter les doublons.
4.  [cite\_start]**Subscription** : Crée une souscription dans Orion pour que tout changement sur un capteur soit envoyé à **QuantumLeap** pour archivage[cite: 281].

-----

## 🖥️ Utilisation

### 1\. Simulation de Données (Capteurs)

Pour tester le flux de données, utilisez le script de simulation qui envoie des relevés de température/humidité aléatoires.

```bash
./scripts/send-data.sh
```

[cite\_start]*Le script envoie une requête POST HTTP au port Sud de l'IoT Agent (:7896) toutes les 5 secondes[cite: 273].*

### 2\. Visualisation (Grafana)

Accédez à Grafana pour voir les données en temps réel et l'historique.

  * **URL** : [http://localhost:3000](https://www.google.com/search?q=http://localhost:3000) (Assurez-vous que le port-forward est actif via `./scripts/start.sh` ou manuellement).
  * **Login** : `admin`
  * [cite\_start]**Mot de passe** : `admin` [cite: 173]
  * **Dashboard** : Allez dans *Dashboards* \> *Smart Farm Monitor*. [cite\_start]Le dashboard est pré-chargé via le provisioning Kubernetes[cite: 174].

-----

## 🛠️ Maintenance et Scripts

Le dossier `scripts/` contient tous les utilitaires nécessaires :

| Script | Description |
| :--- | :--- |
| `./scripts/redeploy.sh` | [cite\_start]**Installation complète.** Supprime et recrée les ressources Kubernetes[cite: 268]. |
| `./scripts/setup.sh` | [cite\_start]**Configuration logique.** Provisionne les devices et souscriptions via l'API[cite: 275]. |
| `./scripts/start.sh` | [cite\_start]Démarre la plateforme (Scale up) et active les port-forwards[cite: 286]. |
| `./scripts/stop.sh` | [cite\_start]Arrête la plateforme (Scale down à 0 replicas) pour économiser les ressources[cite: 287]. |
| `./scripts/send-data.sh` | [cite\_start]Simule un capteur IoT envoyant des données[cite: 272]. |
| `./scripts/cleanup.sh` | Supprime toutes les ressources du cluster (Nettoyage total). |

-----

## 📂 Structure du Projet

```text
eliotmnrt-smartfarm/
├── k8s/
│   ├── base/               # Manifestes Kubernetes de base
│   │   ├── namespace.yaml
│   │   ├── orion/          # Context Broker
│   │   ├── iot-agent/      # Bridge IoT (HTTP/JSON)
│   │   ├── quantumleap/    # Time-Series Persister
│   │   ├── cratedb/        # DB Historique
│   │   ├── mongodb/        # DB Entités
│   │   └── grafana/        # Visualisation & Dashboards
│   └── istio/              # Configuration Service Mesh (Gateway, mTLS)
└── scripts/                # Scripts d'automatisation (Bash)
```

-----

## ❓ Troubleshooting

**Les pods restent en "Pending"**

  * Vérifiez les ressources de votre cluster (Docker Desktop \> Settings \> Resources). FIWARE demande au moins 4GB à 6GB de RAM.

**Erreur "Connection refused" lors du setup**

  * Les port-forwards ont peut-être échoué. Relancez `./scripts/setup.sh` ou ouvrez manuellement les ports :
    ```bash
    kubectl port-forward -n fiware-platform svc/iot-agent 4041:4041 &
    kubectl port-forward -n fiware-platform svc/orion 1026:1026 &
    ```

**Grafana n'affiche pas de données**

  * Vérifiez que le script `send-data.sh` tourne.
  * Vérifiez que la datasource CrateDB est bien configurée (Testez la connexion dans Grafana).
