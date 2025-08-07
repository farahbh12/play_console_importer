FROM python:3.11-slim

# Définir les variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=300 \
    PIP_INDEX_URL=https://pypi.org/simple/ \
    PIP_RETRIES=5

# Installer les dépendances système
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libpq-dev \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Définir le répertoire de travail
WORKDIR /app

# Copier et installer les dépendances Python
COPY requirements.txt .
RUN pip install --default-timeout=300 --retries 5 -r requirements.txt

# Copier le reste du code
COPY . .

# Rendre le script d'entrée exécutable
RUN chmod +x entrypoint.sh

# Créer un utilisateur non-root
RUN groupadd -r celery && \
    useradd -r -g celery celery && \
    chown -R celery:celery /app

# Passer à l'utilisateur non-root
USER celery

# Point d'entrée
ENTRYPOINT ["./entrypoint.sh"]

# Commande par défaut
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]