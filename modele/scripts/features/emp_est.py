"""
Script : emp_est.py
Objectif : Estimer le nombre d'emplois par maille de grille 200m en intersectant la grille
           avec la base SIRENE, en utilisant des pondérations par tranche d'effectifs.
Auteur : LEDERMANN Quentin
Date : June 2025
Utilisation : Étape de génération de feature dans le pipeline features.
"""

import os
import pandas as pd
import geopandas as gpd
from modele.utils.project_utils import print_status

# === PARAMÈTRES DU SCRIPT ===
SIRENE_PATH = "modele/data/raw/sirene.parquet"
GRID_PATH = "modele/output/grid/grid_mobiliscope_200m.parquet"
OUTPUT_PATH = "modele/output/features/emplois_estimes_pondere_200m.csv"


# Fonction principale
def compute_emplois_estimes_pondere(grid: gpd.GeoDataFrame) -> pd.DataFrame:
    try:
        if not os.path.exists(SIRENE_PATH):
            print_status("Fichier SIRENE introuvable", "err")
            return pd.DataFrame(columns=["idINSPIRE", "emplois_estimes_pondere"])

        gdf = gpd.read_parquet(SIRENE_PATH)
        print_status("SIRENE chargé", "ok", f"{len(gdf)} établissements")

        # Reconstruction de la géométrie si nécessaire
        if "geometry" not in gdf.columns or gdf.geometry.is_empty.all():
            print_status("Reconstruction de la géométrie depuis les coordonnées Lambert", "info")
            gdf["x"] = pd.to_numeric(gdf["coordonneeLambertAbscisseEtablissement"], errors="coerce")
            gdf["y"] = pd.to_numeric(gdf["coordonneeLambertOrdonneeEtablissement"], errors="coerce")
            gdf = gdf.dropna(subset=["x", "y"])
            gdf["geometry"] = gpd.points_from_xy(gdf["x"], gdf["y"])
            gdf = gpd.GeoDataFrame(gdf, geometry="geometry", crs="EPSG:2154")
        else:
            gdf = gdf.set_crs("EPSG:2154", allow_override=True)

        # Nettoyage
        for df in [grid, gdf]:
            if "index_right" in df.columns:
                df.drop(columns=["index_right"], inplace=True)

        # Jointure spatiale unique : assignation directe des établissements aux mailles de grille
        joined = gpd.sjoin(gdf, grid[["idINSPIRE", "geometry"]], how="inner", predicate="intersects")
        joined.drop(columns=["index_right"], errors="ignore", inplace=True)
        print_status("Établissements affectés aux mailles", "info", f"{len(joined)} correspondances")

        # Carte des tranches d'effectifs → estimation moyenne
        tranche_map = {
            "00": 0, "01": 1.5, "02": 4, "03": 8, "11": 15, "12": 35,
            "21": 75, "22": 150, "31": 225, "32": 350, "41": 500,
            "42": 750, "51": 1000, "52": 1500, "53": 2000
        }
        joined["tranche"] = joined["trancheEffectifsEtablissement"].map(tranche_map)
        joined["naf2"] = joined["activitePrincipaleEtablissement"].astype(str).str[:2]

        # Valeur de repli par code NAF
        naf_fallback = joined.dropna(subset=["tranche"]).groupby("naf2")["tranche"].mean()

        # Remplissage : tranche → repli NAF → 0
        joined["emplois_estimes"] = joined.apply(
            lambda row: row["tranche"] if pd.notnull(row["tranche"]) else naf_fallback.get(row["naf2"], 0),
            axis=1
        )

        # Agrégation par maille de grille
        emplois = joined.groupby("idINSPIRE")["emplois_estimes"].sum().reset_index()
        emplois.rename(columns={"emplois_estimes": "emplois_estimes_pondere"}, inplace=True)

        return emplois

    except Exception as e:
        print_status("Erreur lors du calcul de emplois_estimes_pondere", "err", str(e))
        return pd.DataFrame(columns=["idINSPIRE", "emplois_estimes_pondere"])


# Exécution directe
if __name__ == "__main__":
    print_status("Calcul de emplois_estimes_pondere", "info")

    grid = gpd.read_parquet(GRID_PATH)

    # Vérification du CRS
    if grid.crs is None:
        print_status("CRS de la grille manquant — forçage EPSG:2154", "info")
        grid.set_crs("EPSG:2154", inplace=True)
    elif grid.crs != "EPSG:2154":
        print_status("Reprojection de la grille", "info")
        grid = grid.to_crs("EPSG:2154")

    result = compute_emplois_estimes_pondere(grid)
    result.to_csv(OUTPUT_PATH, index=False)
    print_status("Estimation des emplois exportée", "ok", OUTPUT_PATH)
