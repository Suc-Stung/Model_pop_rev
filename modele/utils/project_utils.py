"""
Script : project_utils.py
Objectif : Fonctions utilitaires partagées entre les modules modele et appli.
Auteur : LEDERMANN Quentin
Date : June 2025
Utilisation : Importé par les scripts d'acquisition, prétraitement, features et modèles.
"""

import os
import yaml
import pandas as pd
import geopandas as gpd
from typing import Optional, Literal
from shapely.geometry import Polygon, MultiPolygon


def load_config(path: Optional[str] = None):
    """
    Charge la configuration YAML du projet.
    Détection automatique du chemin si non spécifié.
    """
    if path is None:
        if os.path.exists("appli/config/settings.yaml"):
            path = "appli/config/settings.yaml"
        else:
            path = "config/settings.yaml"
    with open(path, "r") as f:
        return yaml.safe_load(f)


def print_status(step: str, status: str = "ok", detail: str = ""):
    """Affiche un message de statut formaté avec un préfixe visuel."""
    prefix = {"ok": "[✓]", "err": "[✗]", "info": "[→]"}
    symbol = prefix.get(status, "[...]")
    message = f"{symbol} {step}"
    if detail:
        message += f" : {detail}"
    print(message)


def save_geoparquet(
    gdf: gpd.GeoDataFrame,
    path: str,
    compression: Optional[Literal['snappy', 'gzip', 'brotli']] = "brotli",
    append: bool = False
):
    """
    Sauvegarde un GeoDataFrame au format GeoParquet compressé.
    Si append=True et que le fichier existe déjà, concatène les données.
    """
    if append and os.path.exists(path):
        existing = gpd.read_parquet(path)
        gdf_concat = pd.concat([existing, gdf], ignore_index=True)
        gdf = gpd.GeoDataFrame(gdf_concat, geometry=existing.geometry.name, crs=existing.crs)
    gdf.to_parquet(path, compression=compression, index=False)


def get_chemin(cle: str, **kwargs) -> str:
    """
    Résout un chemin à partir de la configuration.
    Supporte les clés pointées et le formatage avec paramètres.

    Exemple :
        get_chemin("modele.donnees_brutes.sirene")
        get_chemin("appli.grille_fichier", departement="67", maillage=200)
    """
    config = load_config()
    clefs = cle.split(".")
    valeur = config
    for k in clefs:
        if isinstance(valeur, dict) and k in valeur:
            valeur = valeur[k]
        else:
            # Dernière clé non trouvée dans la configuration
            raise KeyError(f"Clé de chemin introuvable : {cle}")
    if isinstance(valeur, str) and kwargs:
        valeur = valeur.format(**kwargs)
    return valeur


def clean_nom(s):
    """Nettoie une colonne de chaînes : minuscules, suppression espaces, caractères spéciaux remplacés par '_'."""
    return s.str.lower().str.strip().str.replace(r"[^\w]+", "_", regex=True)


def remove_holes(geom):
    """Supprime les trous d'une géométrie polygonale (Polygon ou MultiPolygon)."""
    if geom is None or geom.is_empty:
        return geom
    if isinstance(geom, Polygon):
        return Polygon(geom.exterior)
    elif isinstance(geom, MultiPolygon):
        return MultiPolygon([Polygon(p.exterior) for p in geom.geoms])
    else:
        return geom
