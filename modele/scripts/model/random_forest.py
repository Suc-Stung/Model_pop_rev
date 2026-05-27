"""
Script : random_forest.py
Objectif : Modéliser la population (jour et nuit) avec Random Forest + export des prédictions,
           cartes de résidus et importance des variables.
Auteur : LEDERMANN Quentin
Date : June 2025
Utilisation : Modélisation non-linéaire complémentaire.
"""

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import os
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, root_mean_squared_error
from modele.utils.project_utils import print_status, get_chemin
from modele.utils.vis_utils import carte_residus_villes, carte_residus_region

# === CHEMINS ===
FUSION_PATH = get_chemin("chemins_modele.fusion_modele")
SECTEURS_PATH = get_chemin("chemins_modele.donnees_traitees.secteurs")
FIG_DIR = "modele/output/random_forest_test/figures"
PREDICTION_DIR = "modele/output/random_forest_test/predictions"
STATS_DIR = "modele/output/random_forest_test"
EXPORT_DIR = "modele/output/random_forest_test/export"
os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(PREDICTION_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True)

IMPORTANCES_CSV = lambda cible: os.path.join(STATS_DIR, f"importance_variables_rf_{cible}.csv")
IMPORTANCES_PNG = lambda cible: os.path.join(FIG_DIR, f"importance_variables_rf_{cible}.svg")
SCORES_CSV = os.path.join(STATS_DIR, "scores_random_forest.csv")
NOM_MODELE = "Random Forest"

plt.rcParams["font.family"] = "Arial"


def modele_rf(X, y, y_label, secteurs_uid):
    """Entraîne un Random Forest, évalue, exporte l'importance et les cartes de résidus."""
    print_status(f"Random Forest pour {y_label}", "info")

    rf = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    rf.fit(X, y)
    y_pred = rf.predict(X)

    r2 = r2_score(y, y_pred)
    rmse = root_mean_squared_error(y, y_pred)

    print_status(f"{y_label.upper()} : R² = {r2:.3f}, RMSE = {rmse:.2f}", "ok")

    # Importance des variables
    importances = pd.Series(rf.feature_importances_, index=X.columns).sort_values(ascending=False)
    importances_df = importances.reset_index()
    importances_df.columns = ["variables", "importance"]
    importances_df.to_csv(IMPORTANCES_CSV(y_label), index=False)

    plt.figure(figsize=(12, max(6, 0.4 * len(importances))))
    sns.barplot(x=importances.values, y=importances.index, hue=importances.index, dodge=False, palette="viridis", legend=False)
    for i, (val, label) in enumerate(zip(importances.values, importances.index)):
        plt.text(val + 0.001, i, f"{val:.3f}", va='center')
    plt.title(f"Importance des variables - {NOM_MODELE} - ({y_label})", fontsize=16)
    plt.xlabel("Importance", fontsize=14)
    plt.ylabel("Variables", fontsize=14)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.tight_layout()
    plt.savefig(IMPORTANCES_PNG(y_label), dpi=600)
    plt.close()

    # Export des prédictions
    df_pred = pd.DataFrame({
        "secteur_uid": secteurs_uid,
        "reel": y,
        "pred": y_pred,
        "residu": y - y_pred,
        "abs_residu": (y - y_pred).abs()
    })
    out_csv = os.path.join(PREDICTION_DIR, f"predictions_{y_label}.csv")
    df_pred.to_csv(out_csv, index=False)

    # Cartes des résidus
    carte_residus_villes(df_pred, y_label, NOM_MODELE, EXPORT_DIR, SECTEURS_PATH, FIG_DIR)
    carte_residus_region(df_pred, y_label, NOM_MODELE, "idf_", "Île-de-France", SECTEURS_PATH, FIG_DIR)
    carte_residus_region(df_pred, y_label, NOM_MODELE, "lyon_", "Lyon", SECTEURS_PATH, FIG_DIR)

    return {"modele": "random_forest", "cible": y_label, "r2": r2, "rmse": rmse}


def analyse_random_forest():
    """Charge les données et exécute l'analyse Random Forest pour jour et nuit."""
    print_status("Chargement des données", "info")
    df = pd.read_csv(FUSION_PATH)

    X_cols = [col for col in df.columns if col not in ["secteur_uid", "population_jour", "population_nuit"]]
    X = df[X_cols]
    secteurs_uid = df["secteur_uid"]

    stats = []
    stats.append(modele_rf(X, df["population_jour"], "population_jour", secteurs_uid))
    stats.append(modele_rf(X, df["population_nuit"], "population_nuit", secteurs_uid))

    pd.DataFrame(stats).to_csv(SCORES_CSV, index=False)
    print_status("Random Forest terminé", "ok", SCORES_CSV)


if __name__ == "__main__":
    analyse_random_forest()
