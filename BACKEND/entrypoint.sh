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

# Vérifier le fichier de credentials
echo "Contenu du fichier de credentials :"
cat $GOOGLE_APPLICATION_CREDENTIALS || echo "Fichier de credentials introuvable"

# Vérifier les fichiers de templates
echo "Liste des fichiers de templates :"
find /app/play_reports/templates -type f



# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate



# Execute the main command (passed from CMD or docker-compose)
exec "$@"
