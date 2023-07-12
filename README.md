# CryptoBot-Binance
Création d'un bot de trading basé sur un modèle de Machine Learning et qui investit sur des marchés crypto

Le dépôt contient : 
- un dossier api-call: un script de récupération des data via l'API Biance (fichier json unqiue - méthode pull)  et un script de preprocessing qui devront être activés par un cron 
- un dossier websocket-stream: un script de récupération des data via websockets (multi json - méthode push) et un script de preprocessing qui devra être activé par un cron
