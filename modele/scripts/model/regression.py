"""
Script : regression.py
Objectif : Effectuer des régressions linéaires multiples + cartes de résidus,
           export des prédictions et cartes moyennes par ville.
Auteur : LEDERMANN Quentin
Date : June 2025
Utilisation : Analyse de performance spatiale par secteur.
"""

import os
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import geopandas as gpd
import statsmodels.api as sm
from sklearn.metrics import mean_squared_error, r2_score
from math import sqrt
from modele.utils.project_utils import print_status, get_chemin
from modele.utils.vis_utils import carte_residus_villes, carte_residus_region

# === CHEMINS ===
FUSION_PATH = get_chemin("chemins_modele.fusion_modele")
SECTEURS_PATH = get_chemin("chemins_modele.donnees_traitees.secteurs")
FIG_DIR = "modele/output/regression/figures"
STATS_DIR = "modele/output/regression"
PREDICTION_DIR = "modele/output/regression/predictions"
EXPORT_DIR = "modele/output/regression/export"
os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(STATS_DIR, exist_ok=True)
os.makedirs(PREDICTION_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True)

STATS_CSV = os.path.join(STATS_DIR, "statistiques_regression.csv")
SUMMARY_JOUR = os.path.join(STATS_DIR, "resume_regression_jour.txt")
SUMMARY_NUIT = os.path.join(STATS_DIR, "resume_regression_nuit.txt")
NOM_MODELE = "Régression Linéaire"


def analyser_regressions():
    """Effectue les régressions linéaires multiples et génère les cartes de résidus."""
    print_status("Chargement des données fusionnées", "info")
    df = pd.read_csv(FUSION_PATH)

    X_cols = [col for col in df.columns if col not in ["secteur_uid", "population_jour", "population_nuit"]]
    X = df[X_cols]
    y_jour = df["population_jour"]
    y_nuit = df["population_nuit"]

    print_status("Régression linéaire multiple", "info")
    X_const = sm.add_constant(X)
    model_jour = sm.OLS(y_jour, X_const).fit()
    model_nuit = sm.OLS(y_nuit, X_const).fit()

    y_pred_jour = model_jour.predict(X_const)
    y_pred_nuit = model_nuit.predict(X_const)

    rmse_jour = sqrt(mean_squared_error(y_jour, y_pred_jour))
    rmse_nuit = sqrt(mean_squared_error(y_nuit, y_pred_nuit))

    stats_df = pd.DataFrame([
        {"modele": "regression", "cible": "pop_jour", "r2": model_jour.rsquared, "rmse": rmse_jour},
        {"modele": "regression", "cible": "pop_nuit", "r2": model_nuit.rsquared, "rmse": rmse_nuit}
    ])
    stats_df.to_csv(STATS_CSV, index=False)

    # Export des résumés statsmodels
    with open(SUMMARY_JOUR, "w") as f:
        f.write(model_jour.summary().as_text())
    with open(SUMMARY_NUIT, "w") as f:
        f.write(model_nuit.summary().as_text())

    # Prédictions et cartes pour chaque cible
    for cible, y, y_pred in [("pop_jour", y_jour, y_pred_jour), ("pop_nuit", y_nuit, y_pred_nuit)]:
        df_pred = pd.DataFrame({
            "secteur_uid": df["secteur_uid"],
            "reel": y,
            "pred": y_pred,
            "residu": y - y_pred,
            "abs_residu": (y - y_pred).abs()
        })
        out_path = os.path.join(PREDICTION_DIR, f"predictions_{cible}.parquet")
        df_pred.to_parquet(out_path, index=False)

        carte_residus_villes(df_pred, cible, NOM_MODELE, EXPORT_DIR, SECTEURS_PATH, FIG_DIR)
        carte_residus_region(df_pred, cible, NOM_MODELE, "idf_", "Île-de-France", SECTEURS_PATH, FIG_DIR)
        carte_residus_region(df_pred, cible, NOM_MODELE, "lyon_", "Lyon", SECTEURS_PATH, FIG_DIR)

    print_status("Régression + cartes de résidus terminées", "ok")


if __name__ == "__main__":
    analyser_regressions()
