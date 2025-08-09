#!/bin/sh

# Créer le fichier de credentials à partir de la variable d'environnement si elle existe
if [ -n "$GOOGLE_APPLICATION_CREDENTIALS_JSON" ]; then
  echo "Création du fichier credentials.json à partir de la variable d'environnement..."
  echo "$GOOGLE_APPLICATION_CREDENTIALS_JSON" > /app/credentials.json
  export GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json
fi

# Afficher toutes les variables d'environnement
echo "Variables d'environnement :"
env

# Vérifier le fichier de credentials si la variable est définie
if [ -n "$GOOGLE_APPLICATION_CREDENTIALS_JSON" ]; then
  echo "Contenu du fichier de credentials :"
  cat $GOOGLE_APPLICATION_CREDENTIALS || echo "Fichier de credentials introuvable"
fi





# The main command (from docker-compose) will handle migrations.



# Execute the main command (passed from CMD or docker-compose)
exec "$@"
