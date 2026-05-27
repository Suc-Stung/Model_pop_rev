"""
Script : comparaison_modele.py
Objectif : Visualiser les performances comparées des modèles (R² et RMSE)
Auteur : LEDERMANN Quentin
Date : June 2025
Utilisation : Comparaison et export des graphiques récapitulatifs.
"""

import matplotlib
matplotlib.use('Agg')
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.container as container
import seaborn as sns
import os

# === CHEMINS ===
REGRESSION_PATH = "modele/output/regression/statistiques_regression.csv"
RF_PATH = "modele/output/random_forest/scores_random_forest.csv"
XGB_PATH = "modele/output/xgboost/scores_xgboost.csv"
FIG_DIR = "modele/output/eval"
os.makedirs(FIG_DIR, exist_ok=True)

# === CHARGEMENT DES DONNÉES ===
regression_df = pd.read_csv(REGRESSION_PATH)
rf_df = pd.read_csv(RF_PATH)
xgb_df = pd.read_csv(XGB_PATH)

# Ajout du nom du modèle si absent
rf_df["modele"] = "random_forest"
xgb_df["modele"] = "xgboost"

# Harmonisation des noms de colonnes cibles
renommage_cible = {"population_jour": "pop_jour", "population_nuit": "pop_nuit"}
rf_df["cible"] = rf_df["cible"].replace(renommage_cible)
xgb_df["cible"] = xgb_df["cible"].replace(renommage_cible)

# Fusion
df = pd.concat([regression_df, rf_df, xgb_df], ignore_index=True)

# Tri
df = df.sort_values(by=["cible", "modele"])

# === ÉTIQUETTES ET PALETTE ===
etiquettes_modele = {
    "regression": "Régression Linéaire",
    "random_forest": "Random Forest",
    "xgboost": "XGBoost"
}
palette = {
    "Régression Linéaire": "#56c2fc",
    "Random Forest": "#2f7625",
    "XGBoost": "#fabd53"
}
df["modele"] = df["modele"].replace(etiquettes_modele)

# === VISUALISATION ===
sns.set_theme(style="whitegrid")
fig, axes = plt.subplots(1, 2, figsize=(16, 8))

# R²
r2_plot = sns.barplot(data=df, x="cible", y="r2", hue="modele", ax=axes[0], palette=palette)
axes[0].set_title("Score R² par modèle et variable cible", fontsize=16)
axes[0].set_ylabel("Coefficient de détermination R²", fontsize=12)
axes[0].set_xlabel("Variable cible", fontsize=12)
axes[0].tick_params(labelsize=11)
axes[0].legend(loc="lower right", title="Modèle", fontsize=11, title_fontsize=12)

for cont in r2_plot.containers:
    if isinstance(cont, container.BarContainer):
        r2_plot.bar_label(cont, fmt="%.3f", label_type="edge", fontsize=11, padding=3)

# RMSE
rmse_plot = sns.barplot(data=df, x="cible", y="rmse", hue="modele", ax=axes[1], palette=palette)
axes[1].set_title("Erreur Quadratique Moyenne (RMSE)", fontsize=16)
axes[1].set_ylabel("RMSE", fontsize=12)
axes[1].set_xlabel("Variable cible", fontsize=12)
for cont in rmse_plot.containers:
    if isinstance(cont, container.BarContainer):
        rmse_plot.bar_label(cont, fmt="%.0f", label_type="edge", fontsize=11, padding=3)

plt.tight_layout(pad=3.0)
plt.savefig(os.path.join(FIG_DIR, "comparaison_modeles_r2_rmse.svg"), dpi=600)
print("Graphique enregistré dans :", FIG_DIR)

# === CRÉATION DU TABLEAU RÉCAPITULATIF ===

# Préparation des données pour le tableau
table_data = df.groupby("modele")[["r2", "rmse"]].mean().reset_index()
table_data.columns = ["Modèle", "R² moyen", "RMSE moyen"]

# Arrondi : 3 décimales pour R², 0 pour RMSE
table_data["R² moyen"] = table_data["R² moyen"].round(3)
table_data["RMSE moyen"] = table_data["RMSE moyen"].round(0)

# Création de la figure pour le tableau
fig_table, ax_table = plt.subplots(figsize=(8, 4))
ax_table.axis("tight")
ax_table.axis("off")

# Ajout du tableau avec couleurs pour les lignes
table = ax_table.table(
    cellText=table_data.values.tolist(),
    colLabels=table_data.columns.tolist(),
    cellLoc="center",
    loc="center"
)
table.auto_set_font_size(False)
table.set_fontsize(12)
table.scale(1.2, 1.2)

# Couleurs des modèles pour la première colonne
couleurs_lignes = {
    "Régression Linéaire": "#56c2fc",
    "Random Forest": "#2f7625",
    "XGBoost": "#fabd53"
}

# Application des couleurs aux lignes
for (row, col), cell in table.get_celld().items():
    if col == 0 and row > 0:
        nom_modele = table_data.values[row - 1][0]
        cell.set_facecolor(couleurs_lignes.get(nom_modele, "#ffffff"))
        cell.set_text_props(color="white", weight="bold")

# En-tête du tableau en gris clair
for (row, col), cell in table.get_celld().items():
    if row == 0:
        cell.set_facecolor("#d5d5d5")
        cell.set_text_props(color="black", weight="bold")

# Sauvegarde du tableau
plt.savefig(os.path.join(FIG_DIR, "tableau_recapitulatif.svg"), dpi=600)
print("Tableau récapitulatif enregistré dans :", FIG_DIR)
