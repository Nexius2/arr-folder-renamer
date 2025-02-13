# Utiliser une image Python légère
FROM python:3.10-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier le script et les fichiers nécessaires
COPY main.py requirements.txt /app/

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Définir les variables d'environnement pour la configuration
ENV RUN_SONARR=True \
    RUN_RADARR=True \
    WORK_LIMIT=10 \
    DRY_RUN=False \
    SONARR_URL=http://192.168.1.80:8989 \
    SONARR_API_KEY=xxxxxxx \
    RADARR_URL=http://192.168.1.80:7878 \
    RADARR_API_KEY=yyyyyyy

# Lancer le script
CMD ["python", "main.py"]
