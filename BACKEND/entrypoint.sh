#!/bin/sh

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

# Vérifier les URLs enregistrées
echo "URLs enregistrées :"
python manage.py show_urls

# Execute the main command (passed from CMD or docker-compose)
exec "$@"
