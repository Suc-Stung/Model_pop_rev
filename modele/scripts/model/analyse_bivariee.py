"""
Script : analyse_bivariee.py
Objectif : Analyse bivariée entre chaque variable explicative et les cibles population_jour / population_nuit.
           Calcul du R² et RMSE par régression linéaire simple, export CSV et graphiques.
Auteur : LEDERMANN Quentin
Date : June 2025
"""

import pandas as pd
import seaborn as sns
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
import numpy as np
import os

# Chargement du jeu de données
fichier_entree = "modele/output/fusion/features_modele.csv"
data = pd.read_csv(fichier_entree)

# Définition des variables cibles
variables_cibles = ["population_jour", "population_nuit"]

# Calcul du R² et RMSE par régression linéaire simple
resultats = []
for cible in variables_cibles:
    for colonne in data.columns:
        if colonne not in variables_cibles and colonne != "secteur_uid":
            x = data[[colonne]]
            y = data[cible]
            modele = LinearRegression().fit(x, y)
            y_pred = modele.predict(x)
            r2 = r2_score(y, y_pred)
            rmse = np.sqrt(mean_squared_error(y, y_pred))
            resultats.append({"Variable": colonne, "Cible": cible, "R²": r2, "RMSE": rmse})

# Sauvegarde des résultats en CSV
resultats_df = pd.DataFrame(resultats)
os.makedirs("modele/output/eval", exist_ok=True)
resultats_df.to_csv("modele/output/eval/metriques_bivariees.csv", index=False)

for cible in variables_cibles:
    df_cible = resultats_df[resultats_df["Cible"] == cible]

    # Graphique R²
    plt.figure(figsize=(12, 6))
    sns.barplot(data=df_cible, x="Variable", y="R²", palette="Blues_d")
    plt.title(f"R² par variable explicative ({cible})")
    plt.xticks(rotation=45, ha="right")
    plt.gca().yaxis.set_major_formatter(mtick.FormatStrFormatter('%.2f'))
    plt.tight_layout()
    plt.savefig(f"modele/output/eval/r2_{cible}.svg")
    plt.close()

    # Graphique RMSE
    plt.figure(figsize=(12, 6))
    sns.barplot(data=df_cible, x="Variable", y="RMSE", palette="Reds_d")
    plt.title(f"RMSE par variable explicative ({cible})")
    plt.xticks(rotation=45, ha="right")
    plt.gca().yaxis.set_major_formatter(mtick.FormatStrFormatter('%.2f'))
    plt.tight_layout()
    plt.savefig(f"modele/output/eval/rmse_{cible}.svg")
    plt.close()

# Graphiques combinés R² et RMSE
for cible in variables_cibles:
    df_cible = resultats_df[resultats_df["Cible"] == cible].sort_values("R²", ascending=False)

    fig, ax1 = plt.subplots(figsize=(14, 6))
    color_r2 = "tab:blue"
    color_rmse = "tab:red"

    ax1.set_title(f"R² et RMSE par variable explicative ({cible})")
    ax1.set_xlabel("Variable")
    ax1.set_ylabel("R²", color=color_r2)
    ax1.bar(df_cible["Variable"], df_cible["R²"], color=color_r2, alpha=0.6, label="R²")
    ax1.tick_params(axis="y", labelcolor=color_r2)
    ax1.set_ylim(0, 1)
    ax1.set_xticklabels(df_cible["Variable"], rotation=45, ha="right")

    ax2 = ax1.twinx()
    ax2.set_ylabel("RMSE", color=color_rmse)
    ax2.plot(df_cible["Variable"], df_cible["RMSE"], color=color_rmse, marker="o", label="RMSE")
    ax2.tick_params(axis="y", labelcolor=color_rmse)

    fig.tight_layout()
    plt.savefig(f"modele/output/eval/metriques_combinees_{cible}.svg")
    plt.close()
