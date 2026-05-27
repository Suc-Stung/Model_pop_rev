"""
Script : topo.py
Objectif : Télécharger le jeu de données BD TOPO depuis l'URL spécifiée dans topo_url.yaml,
           extraire les fichiers BATIMENT et TRONCON_DE_ROUTE (avec leurs fichiers compagnons
           .shp, .shx, .dbf, .prj, .cpg), et les sauvegarder dans le répertoire de sortie.
Auteur : LEDERMANN Quentin
Date : June 2025
Utilisation : Script d'acquisition et de prétraitement des données BD TOPO pour un département.
"""

import os
import requests
import yaml
import py7zr
from io import BytesIO
import shutil
from appli.scripts.acquisition.download_utils import load_config, print_status

# Extensions des fichiers compagnons d'un shapefile
EXTENSIONS_SHAPEFILE = (".shp", ".shx", ".dbf", ".prj", ".cpg")

# Noms des couches à extraire
COUCHES_A_EXTRAIRE = ("BATIMENT", "TRONCON_DE_ROUTE")


def get_topo_url():
    """Récupère l'URL BD TOPO depuis le fichier de configuration."""
    with open("appli/config/topo_url.yaml", "r") as f:
        topo_config = yaml.safe_load(f)
    departement = load_config()["departement"]
    return topo_config["topo_url"].get(f"{departement}_url")


def _copier_shapefile_avec_compagnons(extract_root, nom_couche, output_dir):
    """Recherche et copie un shapefile et tous ses fichiers compagnons."""
    found_any = False
    for root, _, files in os.walk(extract_root):
        for file in files:
            name, ext = os.path.splitext(file)
            if name.upper() == nom_couche and ext.lower() == ".shp":
                # Copie du .shp et de tous les fichiers compagnons
                for ext_comp in EXTENSIONS_SHAPEFILE:
                    src = os.path.join(root, f"{name}{ext_comp}")
                    if os.path.exists(src):
                        dst = os.path.join(output_dir, f"{name}{ext_comp}")
                        shutil.copy2(src, dst)
                found_any = True
    return found_any


def download_topo():
    """Télécharge et extrait les données BD TOPO pour le département configuré."""
    url = get_topo_url()
    if not url:
        print_status("BD TOPO", "err", "URL manquante dans topo_url.yaml")
        return

    extract_root = "appli/cache"
    output_dir = "appli/data/topo"
    os.makedirs(extract_root, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    try:
        # Téléchargement de l'archive BD TOPO
        print_status("Téléchargement BD TOPO", "info")
        r = requests.get(url)
        if r.status_code != 200:
            raise Exception(f"Code HTTP {r.status_code}")
        with py7zr.SevenZipFile(BytesIO(r.content)) as archive:
            archive.extractall(path=extract_root)
        print_status("Extraction BD TOPO réussie", "ok")

        # Recherche et copie des couches BATIMENT et TRONCON_DE_ROUTE
        total_trouve = 0
        for couche in COUCHES_A_EXTRAIRE:
            if _copier_shapefile_avec_compagnons(extract_root, couche, output_dir):
                print_status(f"Couche {couche} extraite", "ok")
                total_trouve += 1
            else:
                print_status(f"Couche {couche} introuvable", "info")

        if total_trouve > 0:
            print_status(f"{total_trouve} couche(s) extraite(s) avec fichiers compagnons", "ok")
        else:
            print_status("Aucune couche BATIMENT ou TRONCON_DE_ROUTE trouvée", "err")

    except Exception as e:
        print_status("Échec du téléchargement BD TOPO", "err", str(e))
    finally:
        # Nettoyage du répertoire d'extraction
        if os.path.exists(extract_root):
            shutil.rmtree(extract_root)


if __name__ == "__main__":
    download_topo()
