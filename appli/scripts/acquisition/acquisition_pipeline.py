"""
Script : acquisition_pipeline.py
Objectif : Orchestrer l'exécution séquentielle de tous les scripts d'acquisition de données
           (SIRENE, BPE, OSM, Recensement, BD TOPO) et nettoyer le cache à la fin.
Auteur : LEDERMANN Quentin
Date : June 2025
Utilisation : Script maître du module acquisition, à exécuter pour récupérer toutes les données.
"""

import sys
import traceback
import os
import shutil

from appli.scripts.acquisition.sirene import download_sirene
from appli.scripts.acquisition.bpe import download_bpe
from appli.scripts.acquisition.osm import download_osm
from appli.scripts.acquisition.recens import download_recens
from appli.scripts.acquisition.topo import download_topo
from appli.scripts.acquisition.download_utils import print_status


# === PARAMÈTRES GÉNÉRAUX ===
CACHE_DIR = "appli/cache"


def safe_run(name, func):
    """Exécute une fonction en capturant les erreurs éventuelles."""
    try:
        func()
    except Exception as e:
        print_status(name, "err", str(e))
        traceback.print_exc()


def clean_cache():
    """Supprime le contenu du dossier cache à la fin du processus."""
    if os.path.exists(CACHE_DIR):
        for filename in os.listdir(CACHE_DIR):
            file_path = os.path.join(CACHE_DIR, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print_status("Erreur suppression cache", "err", f"{file_path} : {e}")
        print_status("Dossier cache nettoyé", "ok")
    else:
        print_status("Dossier cache introuvable", "info")


def main():
    """Fonction principale exécutant tous les modules d'acquisition."""
    print("=== DÉBUT DE L'ACQUISITION DES DONNÉES ===\n")
    safe_run("Téléchargement SIRENE", download_sirene)
    safe_run("Téléchargement BPE", download_bpe)
    safe_run("Téléchargement OSM", download_osm)
    safe_run("Téléchargement Recensement", download_recens)
    safe_run("Téléchargement BD TOPO", download_topo)
    clean_cache()
    print("\n=== ACQUISITION DES DONNÉES TERMINÉE ===")


if __name__ == "__main__":
    main()
