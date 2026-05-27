"""
Script : features_pipeline.py
Objectif : Exécuter séquentiellement la génération de toutes les features spatiales
           pour chaque maille de grille (score POI, emplois, densités, morphologie, socio-démographie, etc.).
Auteur : LEDERMANN Quentin
Date : June 2025
Utilisation : Pipeline principal du module 'features', à exécuter après le prétraitement.
"""

import geopandas as gpd
from modele.utils.project_utils import load_config, print_status

# === IMPORT DES FONCTIONS DE FEATURES ===
from modele.scripts.features.score_poi import compute_score_poi_pondere
from modele.scripts.features.emp_est import compute_emplois_estimes_pondere
from modele.scripts.features.dens_eta import compute_densite_etablissements
from modele.scripts.features.dens_com import compute_densite_commerces
from modele.scripts.features.in_mix_fonc import compute_indice_mixite_fonctionnelle
from modele.scripts.features.part_pop_act import compute_part_population_active
from modele.scripts.features.part_jeune import compute_part_jeunes
from modele.scripts.features.shape_index import compute_shape_index_moyen
from modele.scripts.features.h_pond import compute_hauteur_ponderee_surface
from modele.scripts.features.sd_h import compute_ecart_type_hauteur
from modele.scripts.features.sd_area import compute_ecart_type_surface_batiment
from modele.scripts.features.dis_moy_bati import compute_distance_moyenne_batiments
from modele.scripts.features.larg_moy_voirie import compute_largeur_moyenne_voirie
from modele.scripts.features.dens_voirie import compute_densite_voirie_optimisee
from modele.scripts.features.vol_moy import compute_volume_moyen_par_maille


# Exécute une fonction de feature et sauvegarde son résultat en CSV
def safe_run(name, func, *args):
    try:
        print_status(f"Début : {name}", "info")
        df = func(*args)
        df.to_csv(f"output/features/{name}_{MAILLAGE}m.csv", index=False)
        print_status(f"{name} terminé", "ok")
    except Exception as e:
        print_status(f"{name} échoué", "err", str(e))


# Pipeline principal
def main():
    global config, MAILLAGE
    config = load_config()
    departement = config["departement"]
    MAILLAGE = config["maillage"]

    print_status("=== DÉBUT DU PIPELINE FEATURES ===", "info")

    # Chargement de la grille
    grid = gpd.read_file(f"output/grid/grid_{departement}_{MAILLAGE}m.geojson").to_crs("EPSG:2154")

    # Chargement unique des données partagées (évite les lectures redondantes)
    recens_data = gpd.read_parquet("modele/data/raw/recens.parquet")
    bati_data = gpd.read_parquet("modele/data/processed/BATIMENT.parquet")

    # === Exécution des features ===
    safe_run("score_poi_pondere", compute_score_poi_pondere, grid)
    safe_run("emplois_estimes_pondere", compute_emplois_estimes_pondere, grid)
    safe_run("densite_etablissements", compute_densite_etablissements, grid)
    safe_run("densite_commerces", compute_densite_commerces)
    safe_run("indice_mixite_fonctionnelle", compute_indice_mixite_fonctionnelle, grid)
    safe_run("part_population_active", compute_part_population_active, grid, recens_data)
    safe_run("part_jeunes", compute_part_jeunes, grid, recens_data)
    safe_run("shape_index_moyen", compute_shape_index_moyen, grid)
    safe_run("hauteur_ponderee_surface", compute_hauteur_ponderee_surface, grid)
    safe_run("ecart_type_hauteur", compute_ecart_type_hauteur, grid)
    safe_run("ecart_type_surface_batiment", compute_ecart_type_surface_batiment, grid)
    safe_run("distance_moyenne_batiments", compute_distance_moyenne_batiments, grid, bati_data)
    safe_run("largeur_moyenne_voirie", compute_largeur_moyenne_voirie, grid)
    safe_run("densite_voirie", compute_densite_voirie_optimisee)
    safe_run("volume_moyen_bati", compute_volume_moyen_par_maille, grid)

    print_status("=== PIPELINE FEATURES TERMINÉ ===", "ok")


if __name__ == "__main__":
    main()
