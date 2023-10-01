
# [![CryptoBot](./logo.png)](http://51.158.67.16/) ![Deployment status](https://img.shields.io/github/actions/workflow/status/JohannGump/CryptoBot-Binance/kubernetes_cicd.yaml?label=Deployment&style=flat-square&labelColor=63748e) ![Rolling update status](https://img.shields.io/github/actions/workflow/status/JohannGump/CryptoBot-Binance/model_rolling_update.yaml?label=Rolling%20update&style=flat-square&labelColor=63748e)

Bot de support au trading de crypto-monnaies basé sur un modèle de Machine Learning. Projet réalisé dans le cadre de la formation MLOPs DataScientest, promotion Mai 2023.

_Auteurs - Johann Ambrugeat, Julien Le Bot, Christopher Corbin_

## Architecture de la solution

TODO: diagramme

## 🚀 Installation et lancement

**Pré-requis :**  Docker >= 24.0.5, Python >= 3.9.18

Depuis un terminal, cloner le dépôt et se positionner dans le projet: 

```sh
git clone https://github.com/JohannGump/CryptoBot-Binance.git
cd CryptoBot-Binance
```

_Optionnel (ie. auto-completion VSCode, execution des scripts sur hôte)_

Créer un environnement virtuel Python dans le projet et installer les dépendances des modules:

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r binance_bridge/requirements.txt
pip install -r data/requirements.txt
pip install -r model/requirements.txt
pip install -r web_api/requirements.txt
```

Créez un network docker nommé _cryptobot-network_
```sh
docker network create cryptobot-network
```

Executez docker compose pour démarrer l'ensemble des services

```sh
docker compose up
```

Patientez quelques minutes (cela peu être long au premier démarrage), jusqu'a observer une sortie ressemblant à celle-ci

    c-requester | [2023-10-01 17:20:22] [INFO] predict - WEEKLY predictions up to date, latest 2023-10-23 02:00:00

Vous pouvez maintenant naviguer à l'adresse suivante pour accéder à la vitrine de l'application: [http://localhost:8000](http://localhost:8000)

L'accès à l'interface Airflow est disponible ici (login: airflow, mdp: airflow): [http://localhost:8080](http://localhost:8080)

## 🗂️ Organisation du code

- _airflow_ : dags airflows
- _airflow-setup_ : manifests de déploiement d'Airflow sur le cluster Kubernetes
- _binance_bridge_ : utilitaires de communication avec l'API Binance, définitions des constantes
- _data_ : scripts _etl_ des données d'entrainement, build file Docker
- _kubernetes_ : manifests de déploiment de la solution sur cluster Kubernetes
- _model_ : scripts d'entrainement (preprocessing, fit, save) des modèles, build files Docker (entraineur de modèles, serveur de modèles)
- _requester_ : etl données de prédictions, requêteur de prédcitions
- _web_api_ : vitrine publique de l'application