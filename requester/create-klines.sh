#!/bin/bash

echo 'coucou'
python main.py

echo 'caca'

# Vérification du code de sortie du script main.py
if [ $? -eq 0 ]; then
    # Si main.py s'est terminé avec succès, exécute preprocessing.py à l'intérieur du conteneur
    python preprocessing.py
else
    # Si main.py a rencontré une erreur, affiche un message
    echo "Le script main.py a rencontré une erreur. preprocessing.py ne sera pas exécuté."
fi