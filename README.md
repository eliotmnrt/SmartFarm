# 🌾 SmartFarm - Plateforme IoT FIWARE sur Kubernetes

**SmartFarm** est une plateforme IoT cloud-native dédiée à l'agriculture intelligente. Elle orchestre le cycle de vie complet des données agricoles : de la collecte simulée de capteurs géolocalisés à la prise de décision automatisée, en passant par l'analyse par Intelligence Artificielle.

L'infrastructure est bâtie sur l'écosystème **FIWARE** standardisé, déployée sur **Kubernetes** et sécurisée par **Istio**.

---

## 🏗️ Architecture

Le système repose sur une architecture micro-services avancée :

### 1. Couche Ingestion & Context (Core)
* **IoT Agent (JSON)** : Passerelle pour connecter les capteurs (HTTP) au format NGSI standard.
* **Orion Context Broker** : Cœur de la plateforme. Gère l'état actuel des entités (Digital Twins) et notifie les abonnés.
* **MongoDB** : Base de données persistante pour Orion et l'IoT Agent.

### 2. Couche Historisation (Time-Series)
* **QuantumLeap** : Convertit les données NGSI en séries temporelles.
* **CrateDB** : Base de données SQL distribuée pour le stockage long terme et les requêtes géospatiales.

### 3. Couche Intelligence & Décision (Smart Logic)
* **🤖 AI Service** : Service Python qui analyse l'historique (CrateDB) pour déterminer l'état de santé des champs (Sec, Humide, Standard) via des algorithmes de classification.
* **🧠 Decision Service** : Boucle de contrôle temps-réel qui interroge Orion, analyse la proportion d'états par zone et envoie des ordres d'irrigation (`irrigationrecommendation`) aux clusters.

### 4. Couche Visualisation
* **Grafana** : Tableaux de bord hybrides.
    * *Historique* via **CrateDB** (SQL).
    * *Temps Réel* via **Infinity** (Appel API direct vers Orion).

### 5. Infrastructure
* **Kubernetes** : Orchestration.
* **Istio** : Service Mesh (mTLS, Gateway, Observabilité).

---

## 📋 Prérequis

* **Kubernetes Cluster** : via [Docker Desktop](https://docs.docker.com/desktop/use-desktop/kubernetes/) (cluster Kubernetes activé) ou Minikube ou K3s. 
* **Kubectl** configuré, 
```bash
kubectl version
```
* **Istio** 1.28 installé sur le cluster (voir [Istio Docs](https://istio.io/latest/docs/setup/additional-setup/download-istio-release/)). Pour des raisons de simplicité, l'installation devra etre dans `~/istio/istio-1.28.0` (ou adaptez le script `redeploy.sh`). Puis lancez :
  ```bash
  istioctl install
  istioctl verify-install
  ```
  N'oubliez pas d'ajouter le `istioctl` à votre PATH: 
  ```bash
  export PATH=$PATH:~/istio/istio-1.28.0/bin
  ```
* **Python 3.9+** (pour la gateway de simulation).
* **Docker** (pour builder les images des services IA et Décision).
* **.env** : Contactez moi pour obtenir le fichier `.env`

---

## 🚀 Installation et Déploiement

### 1\. Démarrage du Cluster

Assurez-vous que votre cluster Kubernetes est actif.

```bash
kubectl cluster-info
```

### 2\. Déploiement des Services (Infrastructure)

Utilisez le script `redeploy.sh` pour déployer l'ensemble de la stack dans l'ordre correct (Namespace -\> Istio -\> DBs -\> Apps).

```bash
chmod +x scripts/*.sh
./scripts/redeploy.sh
```

Ce script va :

1.  Builder les images Docker des services IA et Décision.
2.  Créer le namespace `fiware-platform` avec l'injection Istio activée.
3.  Déployer les bases de données (MongoDB, CrateDB, InfluxDB).
4.  Déployer les composants FIWARE (Orion, IoT Agent, QuantumLeap).
5.  Déployer Grafana avec les sources de données pré-configurées.

### 3\. Vérification des Pods

Vérifiez que tous les pods sont en statut `Running` (1/1 ou 2/2 si Istio sidecar est actif).

```bash
./scripts/status.sh
```

-----

## ⚙️ Setup et Configuration (Provisioning)

Une fois les pods démarrés, il faut configurer la logique métier (créer les groupes de services et activer l'historisation).

Le script `setup.sh` automatise cette étape.

### Lancer le Setup

```bash
./scripts/setup.sh
```

**Ce que fait ce script :**

1.  **Port-Forwarding** : Ouvre des tunnels temporaires vers Orion (:1026), IoT Agent (:4041/:7896), CrateDB (:4200) et Grafana (:3000) pour permettre l'accès et la configuration depuis votre machine locale.
2.  **Subscription** : Crée une souscription dans Orion pour que tout changement sur un capteur soit envoyé à **QuantumLeap** pour archivage. Crée une une autre souscription pour notifier le service de classification AI à chaque mise à jour de capteur.

-----

## 🖥️ Utilisation

### 1\. Simulation de Données (Capteurs)

Pour tester le flux de données, utilisez le script de simulation de la gateway qui envoie des relevés à Fiware.
Assurez-vous d'avoir effectué le setup avant de lancer la simulation.

```bash
cd gateway
pip install -r requirements.txt
python cleaner.py
```

Ce que fait ce script python:
- **Provisioning Automatique** : Vérifie si les capteurs existent dans Orion. Sinon, il les crée avec leur géolocalisation GPS précise (attribut location).
- **Nettoyage de Données** : Lit des données brutes (sensor_data_raw_dirty.csv), détecte les erreurs, lisse les valeurs aberrantes.
- **Envoi IoT** : Envoie les données propres à l'IoT Agent pour simuler les relevés des capteurs


### 2\. Intelligence & Décision
Le système tourne en autonomie grâce à deux boucles de rétroaction :

**AI Service (Analyse)** :
- Écoute les notifications d'Orion.
- Calcule l'etat de chaque cluster (0: Sec, 1: Humide, 2: Standard).
- Met à jour l'attribut fieldState du capteur.

**Decision Service (Action)** :
- Scanne l'état des zones directement dans orion toutes les 10 secondes.
- Si un seuil de sécheresse defini (default : >20%) est dépassé, envoie l'ordre START_IRRIGATION via l'attribut irrigationrecommendation


### 3\. Visualisation (Grafana)

Accédez à Grafana pour voir les données en temps réel et l'historique.

  * **URL** : [http://localhost:3000](http://localhost:3000) (Assurez-vous que le port-forward est actif via `./scripts/portManager.sh status` ou manuellement).
  * **Login** : `admin`
  * **Mot de passe** : `admin`
  * **Dashboard** : Allez dans *Dashboards* \> *data*. Le dashboard est pré-chargé via le provisioning Kubernetes.

### 4\. Observabilité (Kiali)

Accedez à Kiali pour visualiser le maillage Istio et les métriques.

```bash
  istioctl dashboard kiali &
```
  * **URL** : [http://localhost:20001/kiali](http://localhost:20001/kiali) (Assurez-vous que le port-forward est actif via `./scripts/portManager.sh status` ou manuellement). Et selectionnez le namespace `fiware-platform` si nécessaire.


-----

## 🛠️ Maintenance et Scripts

Le dossier `scripts/` contient tous les utilitaires nécessaires :

| Script | Description |
| :--- | :--- |
| `./scripts/redeploy.sh` | **Installation complète.** Supprime et recrée les ressources Kubernetes. |
| `./scripts/setup.sh` | **Configuration logique.** Provisionne les devices et souscriptions via l'API. |
| `./scripts/start.sh` | Démarre la plateforme (Scale up) et active les port-forwards |
| `./scripts/stop.sh` | Arrête la plateforme (Scale down à 0 replicas) pour économiser les ressources |
| `./scripts/send-data.py` | Simule un capteur IoT envoyant des données |
| `./scripts/cleanup.sh` | Supprime toutes les ressources du cluster (Nettoyage total). |
| `./scripts/emptyDB.py` | Supprime toutes les données des DB Mongo(Orion) et CrateDB(Quantum Leap) (Nettoyage total). |
| `./scripts/portManager.sh` | Gère les port-forwards (start, stop, status). |


-----

## 📂 Structure du Projet

```text
eliotmnrt-smartfarm/
├── docker/
│   ├── serviceIA/              # Micro-service d'analyse (Modèle Sklearn)
│   └── serviceDecision/        # Micro-service de décision (Logique métier)
├── gateway/
│   ├── cleaner.py              # Gateway de simulation et nettoyage de données
│   └── trasher.py              # Générateur de chaos (données sales)
├── k8s/
│   ├── base/                   # Manifestes YAML (Deployment, Svc, PVC)
│   │   ├── ai-service/         # Deploiement du service IA dockerisé
│   │   ├── decision-service/   # Deploiement du service Decision dockerisé
│   │   ├── iot-agent/          # FIWARE IoT Agent (JSON)
│   │   ├── cratedb/            # CrateDB pour QuantumLeap
│   │   ├── mongodb/            # MongoDB pour Orion
│   │   ├── orion/              # FIWARE Orion Context Broker
│   │   ├── quantumleap/        # FIWARE QuantumLeap
│   │   └── grafana/            # ConfigMaps Datasources & Dashboards
│   └── istio/                  # Gateway & VirtualServices & Policies Istio
└── scripts/                    # Automatisation Bash
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


**Le script cleaner.py n'arrive pas à se connecter**

  * Vérifiez que les tunnels sont ouverts : lancez ./scripts/portManager.sh start.



**Les services IA/Décision ne semblent pas réagir**

  * Vérifiez les logs : kubectl logs -l app=ai-service -n fiware-platform.
  * Assurez-vous que les souscriptions dans Orion ont bien été créées via setup.sh.
  * Note : Le service décision est en mode "INFO" par défaut et ne loggue que les changements d'état majeurs pour éviter le bruit.

**Grafana affiche "No Data"**

  * Assurez-vous que le script cleaner.py tourne pour alimenter Orion et CrateDB.
  * Vérifiez que la souscription QuantumLeap a bien été créée via setup.sh.



## ❓ Utilisation de l'IA générative dans le projet

Des outils d'IA générative ont été employés pour :
- Générer la base de scripts d'automatisation en bash.
- Générer la base de fichiers python pour le traitement des données.
- Debuggage
- README.md

Toutefois, le code a été revu, corrigé et adapté manuellement pour s'assurer de son bon fonctionnement et de sa pertinence.


