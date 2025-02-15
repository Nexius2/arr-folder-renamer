# -*- coding: utf-8 -*-

import logging
from logging.handlers import RotatingFileHandler
#from datetime import datetime
import requests

# Configuration des options
RUN_SONARR = True  # Activer/désactiver le traitement des séries Sonarr
RUN_RADARR = True  # Activer/désactiver le traitement des films Radarr
WORK_LIMIT = 10     # Limiter le nombre de modifications (0 pour illimité)
DRY_RUN = False    # Mode simulation (True = pas de modifications réelles)

# Paramètres Sonarr
SONARR_URL = "http://192.168.1.80:8989"    # URL de votre instance Sonarr
SONARR_API_KEY = "xxxxxxxxxxxxxxxxxxxx"        # Clé API de Sonarr

# Paramètres Radarr
RADARR_URL = "http://192.168.1.80:7878"    # URL de votre instance Radarr
RADARR_API_KEY = "yyyyyyyyyyyyyyyyyyyyyyy"        # Clé API de Radarr

def update_sonarr_path(original_path, imdb_id, tvdb_id):
    # Si aucun ID n'est disponible, ne pas modifier le path
    if imdb_id is None and tvdb_id is None:
        return original_path
    
    # Construire les segments
    segments = []
    
    if imdb_id is not None and str(imdb_id) not in str(original_path):
        segments.append(f"{{imdb-{imdb_id}}}")

    if tvdb_id is not None and str(tvdb_id) not in str(original_path):
        segments.append(f"{{tvdb-{tvdb_id}}}")
    
    # Si aucun segment n'est ajouté, retourner le path d'origine
    if not segments:
        return original_path
    
    # Nettoyer le path d'origine pour éviter les doublons de séparateurs
    original_path = original_path.rstrip('/')
    
    # Concaténer les segments avec " - "
    new_path = f"{original_path} - {' - '.join(segments)}"
    return new_path


def update_radarr_path(original_path, imdb_id, tmdb_id):
    # Si aucun ID n'est disponible, ne pas modifier le path
    if imdb_id is None and tmdb_id is None:
        return original_path
    
    # Construire les segments
    segments = []
    
    if imdb_id is not None and str(imdb_id) not in str(original_path):
        segments.append(f"{{imdb-{imdb_id}}}")
    if tmdb_id is not None and str(tmdb_id) not in str(original_path):
        segments.append(f"{{tmdb-{tmdb_id}}}")
    
    # Si aucun segment n'est ajouté, retourner le path d'origine
    if not segments:
        return original_path
    
    # Nettoyer le path d'origine pour éviter les doublons de séparateurs
    original_path = original_path.rstrip('/')
    
    # Concaténer les segments avec " - "
    new_path = f"{original_path} - {' - '.join(segments)}"
    return new_path

# Initialisation du main_logger
def process_sonarr(sonarr_url, api_key, main_logger, debug_logger, dry_run, work_limit):
    headers = {"Content-Type": "application/json", "X-Api-Key": api_key}
    
    # Récupérer toutes les séries
    response = requests.get(f"{sonarr_url}/api/v3/series", headers=headers)
    if response.status_code != 200:
        main_logger.error("Erreur lors de la récupération des séries Sonarr")
        return
    
    series_list = response.json()
    
    modified_count = 0
    for series in series_list:
        # Extraire les informations nécessaires
        title = series.get("title", "")
        sort_title = series.get("sortTitle", "")
        year = series.get("year", "")
        path = series.get("path", "")
        tvdb_id = series.get("tvdbId")
        imdb_id = series.get("imdbId")
        series_id = series.get("id")
        debug_logger.debug(f"Title: {title}: Year: {year}")
        
        # Vérifier si IMDB ou TVDB est manquant dans le path
        if (
            (str(imdb_id) not in path and str(tvdb_id) not in path)
            or "tvshows" in path.lower()
        ):
            new_path = update_sonarr_path(path, imdb_id, tvdb_id)
            
            if new_path != path:
                main_logger.info(f"Série {title} ({series_id}) : Chemin modifié de '{path}' à '{new_path}'")
                
                if not dry_run:
                    # Construction de l'URL
                    update_url = f"{sonarr_url}/api/v3/series/{series_id}?moveFiles=true"
                    
                    # Corps de la requête
                    payload = {
                        "title": title,
                        "sortTitle": sort_title,
                        "year": year,
                        "path": new_path,
                        "tvdbId": tvdb_id,
                        "imdbId": imdb_id,
                        "qualityProfileId": series.get("qualityProfileId"),
                        "seasonFolderEnabled": series.get("seasonFolderEnabled", True),
                        "metadataProfileId": series.get("metadataProfileId")
                        #"moveFiles": True  # Ajout de ce paramètre pour déplace les fichiers
                    }
                    
                    # Envoi de la requête
                    try:
                        response_update = requests.put(
                            update_url,
                            headers=headers,
                            json=payload
                        )
                        
                        if response_update.status_code == 200:
                            main_logger.info(f"Série {title} ({series_id}) : Chemin mis à jour avec succès.")
                        elif response_update.status_code == 202:
                            main_logger.info(f"Série {title} ({series_id}) : Le déplacement sera traité lors du prochain contrôle de tâches Sonarr.")
                        else:
                            # Log plus de détails pour le debug
                            error_details = {
                                "status": response_update.status_code,
                                "text": response_update.text,
                                "payload_sent": payload
                            }
                            main_logger.error(
                                f"Série {title} ({series_id}) : Échec de la mise à jour du chemin. Détails: {error_details}"
                            )
                            debug_logger.debug(f"Payload envoyé pour {title}: {payload}")
                            debug_logger.debug(f"Réponse complete: {response_update.text}")
                            
                    except Exception as e:
                        main_logger.error(
                            f"Série {title} ({series_id}) : Erreur lors de la requête PUT. Détails: {str(e)}"
                        )
                        debug_logger.debug(f"Erreur complete: {str(e)}")
                
                modified_count += 1
                
                if work_limit > 0 and modified_count >= work_limit:
                    main_logger.info(f"Limite de modifications atteinte ({work_limit}). Arrêt du script.")
                    return
            
            # Log détaillé pour debug.log
            debug_logger.debug(
                f"Série {title} ({series_id}) - Ancien path: '{path}', Nouveau path: '{new_path}'"
            )
    
    main_logger.info(f"Fin du traitement des séries Sonarr. Modifications effectuées: {modified_count}")




# Fonction pour traiter les films avec Radarr
def process_radarr(radarr_url, api_key, main_logger, debug_logger, dry_run, work_limit):
    headers = {"Content-Type": "application/json", "X-Api-Key": api_key}
    
    # Récupérer tous les films
    response = requests.get(f"{radarr_url}/api/v3/movie", headers=headers)
    if response.status_code != 200:
        main_logger.error("Erreur lors de la récupération des films Radarr")
        return
    
    movies_list = response.json()
    
    modified_count = 0
    for movie in movies_list:
        # Extraire les informations nécessaires
        title = movie.get("title", "")
        sort_title = movie.get("sortTitle", "")
        year = movie.get("year", "")
        path = movie.get("path", "")
        tmdb_id = movie.get("tmdbId")
        imdb_id = movie.get("imdbId")
        movie_id = movie.get("id")
        
        # Vérifier si IMDB ou TMDB est manquant dans le path
        if (
            (str(imdb_id) not in path and str(tmdb_id) not in path)
            or (tmdb_id is None)
            or (imdb_id is None)
        ):
            new_path = update_radarr_path(path, imdb_id, tmdb_id)
            
            if new_path != path:
                main_logger.info(f"Film {title} ({movie_id}) : Chemin modifié de '{path}' à '{new_path}'")
                
                if not dry_run:
                    # Inclure toutes les informations nécessaires dans le payload
                    payload = {
                        "id": movie_id,
                        "title": title,
                        "sortTitle": sort_title,
                        "year": year,
                        "tmdbId": tmdb_id,
                        "imdbId": imdb_id,
                        "path": new_path,
                        "monitored": movie.get("monitored", True),
                        "qualityProfileId": movie.get("qualityProfileId"),
                        "metadataProfileId": movie.get("metadataProfileId")
                    }
                    
                    response_update = requests.put(
                        f"{radarr_url}/api/v3/movie/{movie_id}?moveFiles=true",
                        headers=headers,
                        json=payload
                    )
                    
                    if response_update.status_code == 200:
                        main_logger.info(f"Film {title} ({movie_id}) : Chemin mis à jour avec succès.")
                    elif response_update.status_code == 202:
                        main_logger.info(f"Film {title} ({movie_id}) : Le déplacement sera traité lors du prochain contrôle de tâches Radarr.")
                    else:
                        main_logger.error(
                            f"Film {title} ({movie_id}) : Échec de la mise à jour du chemin. Code d'erreur: {response_update.status_code}"
                        )
                
                modified_count += 1
                if work_limit > 0 and modified_count >= work_limit:
                    main_logger.info(f"Limite de modifications atteinte ({work_limit}). Arrêt du script.")
                    return
            
            # Log détaillé pour debug.log
            debug_logger.debug(
                f"Film {title} ({movie_id}) - Ancien path: '{path}', Nouveau path: '{new_path}'"
            )
    
    main_logger.info(f"Fin du traitement des films Radarr. Modifications effectuées: {modified_count}")


def setup_logging():
    # Configuration du logger principal (main.log)
    main_logger = logging.getLogger("main")
    main_logger.setLevel(logging.INFO)
    main_handler = RotatingFileHandler(
        "main.log",
        maxBytes=1024*1024,
        backupCount=5
    )
    formatter_main = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    main_handler.setFormatter(formatter_main)
    main_logger.addHandler(main_handler)
    main_logger.propagate = False  # Empêche la propagation vers le logger par défaut

    # Configuration du logger détaillé (debug.log)
    debug_logger = logging.getLogger("debug")
    debug_logger.setLevel(logging.DEBUG)
    debug_handler = RotatingFileHandler(
        "debug.log",
        maxBytes=1024*1024,
        backupCount=5
    )
    formatter_debug = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    debug_handler.setFormatter(formatter_debug)
    debug_logger.addHandler(debug_handler)
    debug_logger.propagate = False  # Empêche la propagation vers le logger par défaut

    return main_logger, debug_logger


  

# Fonction principale
def main():
    # Initialisation des loggers
    main_logger, debug_logger = setup_logging()
    
    # Vérifier les paramètres de configuration
    if not SONARR_API_KEY or not RADARR_API_KEY:
        main_logger.error("Clés API manquantes. Veuillez configurer le script correctement.")
        return
    
    # Traitement des séries Sonarr si activé
    if RUN_SONARR:
        main_logger.info("Démarrage du traitement des séries Sonarr...")
        process_sonarr(SONARR_URL, SONARR_API_KEY, main_logger, debug_logger, DRY_RUN, WORK_LIMIT)
    
    # Traitement des films Radarr si activé
    if RUN_RADARR:
        main_logger.info("Démarrage du traitement des films Radarr...")
        process_radarr(RADARR_URL, RADARR_API_KEY, main_logger, debug_logger, DRY_RUN, WORK_LIMIT)
    
    main_logger.info("Fin du script.")

if __name__ == "__main__":
    main()

