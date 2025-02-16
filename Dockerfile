# Utiliser une image Python légère
FROM python:3.10-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier le script et les fichiers nécessaires
COPY main.py /app/
COPY config.ini /config/

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Définir le volume pour la configuration
VOLUME ["/config"]

# Lancer le script
CMD ["python", "main.py"]
