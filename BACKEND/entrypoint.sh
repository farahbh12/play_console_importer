#!/bin/sh

set -e

# This script is the single entrypoint for the container.
# It waits for the database, runs migrations, and starts the application.

# Wait for the database to be ready.
# The `db` hostname is from the docker-compose service name.
echo "Waiting for PostgreSQL..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "PostgreSQL started"

# Change ownership of the app directory to the non-root user.
# This is necessary because the volume is mounted as root.
chown -R celery:celery /app

# Run all subsequent commands as the non-root 'celery' user.
# The 'gosu' command is a lightweight 'sudo' alternative.
# The 'exec' command replaces the shell process, making Gunicorn the main process (PID 1).

# Apply database migrations
gosu celery python manage.py migrate

# Start Gunicorn server
# The --chdir flag tells Gunicorn to run from the /app directory.
echo "Starting Gunicorn server..."
exec gosu celery gunicorn --chdir /app config.wsgi:application --bind 0.0.0.0:8000
