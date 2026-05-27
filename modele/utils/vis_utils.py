"""
Script : vis_utils.py
Objectif : Fonctions de visualisation cartographique partagées entre les modèles (Random Forest, XGBoost, Régression).
Auteur : LEDERMANN Quentin
Date : June 2025
Utilisation : Importé par les scripts de modèle pour générer les cartes de résidus.
"""

import os
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import geopandas as gpd
from shapely.ops import unary_union
from modele.utils.project_utils import clean_nom, remove_holes


def _preparer_donnees_residus_par_ville(df_pred, secteurs_path):
    """
    Agrège les résidus par secteur Mobiliscope et fusionne avec les géométries.
    Retourne un GeoDataFrame des résidus moyens par ville.
    """
    df_pred = df_pred.copy()
    df_pred["secteur_uid"] = df_pred["secteur_uid"].str.lower()
    moyennes = df_pred.groupby("secteur_uid", as_index=False)[["residu", "abs_residu"]].mean()

    gdf = gpd.read_parquet(secteurs_path).to_crs("EPSG:2154")
    gdf["ENQUETE"] = clean_nom(gdf["ENQUETE"])
    gdf["CODE_SEC"] = clean_nom(gdf["CODE_SEC"].astype(str))
    gdf["secteur_uid"] = gdf["ENQUETE"] + "_" + gdf["CODE_SEC"]
    gdf = gdf.merge(moyennes, on="secteur_uid", how="inner")

    gdf["geometry"] = gdf["geometry"].buffer(0)
    geometries = gdf.groupby("ENQUETE")["geometry"].apply(lambda x: unary_union(x.tolist()))
    moyennes_ville = gdf.groupby("ENQUETE")[["residu", "abs_residu"]].mean()

    gdf_villes = gpd.GeoDataFrame(moyennes_ville, geometry=geometries, crs=gdf.crs).reset_index()
    gdf_villes = gdf_villes[~gdf_villes["geometry"].is_empty & gdf_villes["geometry"].is_valid]
    gdf_villes["geometry"] = gdf_villes["geometry"].apply(lambda g: remove_holes(g.buffer(0)))
    return gdf_villes


def _preparer_residus_region(df_pred, secteurs_path, region_prefix):
    """Filtre les résidus pour une région spécifique (idf_, lyon_)."""
    df_pred = df_pred.copy()
    df_pred["secteur_uid"] = df_pred["secteur_uid"].str.lower()

    gdf = gpd.read_parquet(secteurs_path).to_crs("EPSG:2154")
    gdf["ENQUETE"] = gdf["ENQUETE"].str.lower()
    gdf["CODE_SEC"] = gdf["CODE_SEC"].astype(str)
    gdf["secteur_uid"] = gdf["ENQUETE"] + "_" + gdf["CODE_SEC"]
    merged = gdf.merge(df_pred, on="secteur_uid", how="left")
    return merged[merged["secteur_uid"].str.startswith(region_prefix)]


def carte_residus_villes(df_pred, cible, modele_nom, export_dir, secteurs_path, fig_dir):
    """
    Génère une carte des résidus moyens par ville (résidu et résidu absolu).

    Paramètres :
        df_pred : DataFrame contenant secteur_uid, reel, pred, residu, abs_residu
        cible : nom de la variable cible (ex: 'population_jour')
        modele_nom : nom du modèle pour les titres (ex: 'Random Forest')
        export_dir : dossier d'export des fichiers Parquet
        secteurs_path : chemin vers le fichier des secteurs Mobiliscope
        fig_dir : dossier d'export des figures SVG
    """
    gdf_villes = _preparer_donnees_residus_par_ville(df_pred, secteurs_path)
    gdf_villes.to_parquet(
        os.path.join(export_dir, f"residus_par_ville_{modele_nom.lower().replace(' ', '_')}_{cible}.parquet"),
        index=False
    )

    vmax = gdf_villes["residu"].abs().max()
    vmin = -vmax

    # Carte des résidus (positifs/négatifs)
    fig, ax = plt.subplots(figsize=(12, 10))
    gdf_villes.plot(
        column="residu", cmap="coolwarm", legend=True,
        edgecolor="grey", linewidth=0.3, ax=ax,
        legend_kwds={"label": "Résidu moyen par ville", "shrink": 0.7},
        vmin=vmin, vmax=vmax
    )
    ax.set_title(f"Erreur moyenne par ville - {modele_nom} - ({cible})", fontsize=16)
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, f"residus_moyens_par_ville_{cible}.svg"), dpi=600)
    plt.close()

    # Carte des résidus absolus
    fig, ax = plt.subplots(figsize=(12, 10))
    gdf_villes.plot(
        column="abs_residu", cmap="OrRd", legend=True,
        edgecolor="grey", linewidth=0.3, ax=ax,
        legend_kwds={"label": "Résidu absolu moyen par ville", "shrink": 0.7}
    )
    ax.set_title(f"Erreur absolue moyenne par ville - {modele_nom} - ({cible})", fontsize=16)
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, f"residus_absolus_moyens_par_ville_{cible}.svg"), dpi=600)
    plt.close()


def carte_residus_region(df_pred, cible, modele_nom, region_prefix, region_label, secteurs_path, fig_dir):
    """
    Génère une carte détaillée des résidus pour une région spécifique.

    Paramètres :
        region_prefix : préfixe du secteur pour filtrer (ex: 'idf_', 'lyon_')
        region_label : nom lisible de la région pour les titres (ex: 'Île-de-France', 'Lyon')
    """
    gdf_region = _preparer_residus_region(df_pred, secteurs_path, region_prefix)
    if gdf_region.empty:
        return

    vmax = gdf_region["residu"].abs().max()
    vmin = -vmax

    # Carte des résidus
    fig, ax = plt.subplots(figsize=(12, 10))
    gdf_region.plot(
        column="residu", cmap="coolwarm", legend=True,
        edgecolor="black", linewidth=0.2, ax=ax,
        legend_kwds={"label": "Résidu (réel - prédit)", "shrink": 0.7},
        vmin=vmin, vmax=vmax
    )
    ax.set_title(f"Carte détaillée des résidus - {region_label} - {modele_nom} - ({cible})", fontsize=16)
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, f"residus_{region_prefix}_{cible}.svg"), dpi=600)
    plt.close()

    # Carte des résidus absolus
    fig, ax = plt.subplots(figsize=(12, 10))
    gdf_region.plot(
        column="abs_residu", cmap="OrRd", legend=True,
        edgecolor="black", linewidth=0.2, ax=ax,
        legend_kwds={"label": "Résidu absolu |réel - prédit|", "shrink": 0.7}
    )
    ax.set_title(f"Carte détaillée des résidus absolus - {region_label} - {modele_nom} - ({cible})", fontsize=16)
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, f"residus_absolus_{region_prefix}_{cible}.svg"), dpi=600)
    plt.close()
