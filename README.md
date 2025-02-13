# Arr Folder Renamer Docker

Ce projet permet d'exécuter un script Python pour gérer les chemins des médias dans Sonarr et Radarr à l'intérieur d'un container Docker, facilement déployable sur Unraid.

## Installation et Utilisation

### 1. Cloner le dépôt GitHub
```sh
git clone https://github.com/Nexius2/Arr-Folder-Renamer.git
cd Arr-Folder-Renamer
```

### 2. Construire l'image Docker
```sh
docker build -t arr-folder-renamer .
```

### 3. Lancer le container avec Docker Compose
```sh
docker-compose up -d
```

## Configuration
Les paramètres du script peuvent être modifiés via les variables d’environnement dans `docker-compose.yml` :

- `RUN_SONARR` : Active ou désactive le traitement de Sonarr (`True`/`False`)
- `RUN_RADARR` : Active ou désactive le traitement de Radarr (`True`/`False`)
- `WORK_LIMIT` : Nombre maximal de modifications par exécution
- `DRY_RUN` : Mode simulation (`True` = pas de modifications)
- `SONARR_URL` et `RADARR_URL` : URL de vos instances
- `SONARR_API_KEY` et `RADARR_API_KEY` : Clés API

## Logs
Les logs sont stockés dans `./logs`, accessible via le volume Docker.

## Mise à Jour
Pour mettre à jour le container :
```sh
docker-compose pull
docker-compose up -d --force-recreate
```

## Licence
Ce projet est sous licence MIT.

