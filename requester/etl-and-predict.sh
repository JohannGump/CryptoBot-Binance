#!/bin/bash

log() {
    >&2 echo [$(date +'%Y-%m-%d %H:%M:%S')] [$1] $(basename $0) - $2
}

python /app/update_klines.py

if [ $? -eq 0 ]; then
    # Si update_klines.py s'est terminé avec succès, exécute predict.py à l'intérieur du conteneur
    python /app/predict.py
else
    # Si update_klines.py a rencontré une erreur, affiche un message
    log INFO 'update_klines.py has encountered an error. predict.py wont be executed'
fi
