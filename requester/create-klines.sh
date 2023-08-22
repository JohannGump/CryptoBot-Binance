#!/bin/bash
log() {
    echo [$(date +'%Y-%m-%d %H:%M:%S')] [$1] $(basename $0) - $2
}

PYTHON_PATH=/usr/local/bin/python

$PYTHON_PATH /app/main.py

# Vérification du code de sortie du script main.py
if [ $? -eq 0 ]; then
    # Si main.py s'est terminé avec succès, exécute preprocessing.py à l'intérieur du conteneur
    $PYTHON_PATH /app/preprocessing.py

    if [ $? -eq 0 ]; then
        # if preprocessing.py stop successfully then do prediction
        $PYTHON_PATH /app/predict.py

    else
        # if preprocessing.py have encountered an error
        log INFO 'preprocessing.py has encountered an error. predict.py wont be executed'

    fi

else
    # Si main.py a rencontré une erreur, affiche un message
    log INFO 'main.py has encountered an error. preprocessing.py wont be executed'
fi
