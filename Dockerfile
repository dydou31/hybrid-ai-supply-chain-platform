FROM python:3.12-slim

# Évite les fichiers .pyc et force les logs Python immédiats
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Répertoire de travail
WORKDIR /app

# Installation des dépendances
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copie de l'application
COPY app ./app

# Copie Alembic pour les migrations
COPY alembic.ini .
COPY alembic ./alembic

# Utilisateur non-root pour la sécurité
RUN addgroup --system app && \
    adduser --system --ingroup app app && \
    chown -R app:app /app

USER app

# Port FastAPI
EXPOSE 8000

# Démarrage de l'API
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]