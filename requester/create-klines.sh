#!/bin/bash

PYTHON_PATH=/usr/local/bin/python

echo $PYTHON_PATH
$PYTHON_PATH /app/main.py

echo 'Adding data klines and delete duplicate - OK'

# Vérification du code de sortie du script main.py
if [ $? -eq 0 ]; then
    # Si main.py s'est terminé avec succès, exécute preprocessing.py à l'intérieur du conteneur
   $PYTHON_PATH /app/preprocessing.py

   echo 'Datafile for choosen interval prediction - OK'

   if [ $? -eq 0 ]; then
   # if preprocessing.py stop successfully then do prediction
   $PYTHON_PATH /app/predict.py

    echo 'Predictions for each symbol - OK'

    else
    #if preprocessing.py have encountered an error
    echo 'preprocessing.py has encountered an error. predict.py won t be executed.'

    fi

else
    # Si main.py a rencontré une erreur, affiche un message
    echo 'main.py has encountered an error. preprocessing.py won t be executed'
fi
