"""
Script : train.py
Objectif : Entraîner plusieurs modèles (Régression Linéaire, Random Forest, XGBoost) sur les données
           de population (jour/nuit), prédire pour un département donné, et exporter les prédictions en GeoPackage.
Auteur : LEDERMANN Quentin
Date : June 2025
Utilisation : Script d'entraînement et de prédiction dans le pipeline de modélisation.
"""

import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler
import os
import geopandas as gpd
from modele.utils.project_utils import load_config, print_status, get_chemin

config = load_config()
DEPARTEMENT = config["departement"]
MAILLAGE = config["maillage"]

# === 1. Chargement des données d'entraînement ===
train_df = pd.read_csv(get_chemin("chemins_modele.fusion_modele"))
X_cols = [col for col in train_df.columns if col not in ["secteur_uid", "population_jour", "population_nuit"]]
X_train = train_df[X_cols]
y_train_jour = train_df["population_jour"]
y_train_nuit = train_df["population_nuit"]

# === 2. Chargement des features à prédire (département cible) ===
chemin_fusion = get_chemin("chemins_appli.fusion_fichier", maillage=MAILLAGE)
test_df = pd.read_csv(chemin_fusion)
test_df["idINSPIRE"] = test_df["idINSPIRE"].astype(str)

# Harmonisation des noms de colonnes
rename_mapping = {col.replace("_secteur", ""): col for col in train_df.columns if "_secteur" in col}
rename_mapping.update({
    "part_population_active": "part_actifs_secteur"
})
test_df.rename(columns=rename_mapping, inplace=True)

X_test = test_df.set_index("idINSPIRE")

# Vérification des colonnes manquantes
missing_cols = set(X_cols) - set(X_test.columns)

X_test = X_test.reindex(columns=X_cols).fillna(0)

# === 3. Normalisation ===
scaler = StandardScaler()
X_train = pd.DataFrame(scaler.fit_transform(X_train), columns=X_cols)
X_test = pd.DataFrame(scaler.transform(X_test), columns=X_cols, index=X_test.index)

# === 4. Entraînement des modèles ===
print("Entraînement des modèles...")

# Régression Linéaire
lr_jour = LinearRegression()
lr_nuit = LinearRegression()
lr_jour.fit(X_train, y_train_jour)
lr_nuit.fit(X_train, y_train_nuit)

# Random Forest
rf_jour = RandomForestRegressor()
rf_nuit = RandomForestRegressor()
rf_jour.fit(X_train, y_train_jour)
rf_nuit.fit(X_train, y_train_nuit)

# XGBoost
xgb_jour = XGBRegressor()
xgb_nuit = XGBRegressor()
xgb_jour.fit(X_train, y_train_jour)
xgb_nuit.fit(X_train, y_train_nuit)

# === 5. Prédiction ===
results = pd.DataFrame(index=X_test.index)

print("Colonnes utilisées pour les prédictions :")
print(X_test.columns)

results["prediction_lr_jour"] = lr_jour.predict(X_test)
results["prediction_lr_nuit"] = lr_nuit.predict(X_test)
results["prediction_rf_jour"] = rf_jour.predict(X_test)
results["prediction_rf_nuit"] = rf_nuit.predict(X_test)
results["prediction_xgb_jour"] = xgb_jour.predict(X_test)
results["prediction_xgb_nuit"] = xgb_nuit.predict(X_test)

print("Aperçu des prédictions :")
print(results.describe())

# === 6. Jointure spatiale avec la grille géographique ===
print("Jointure spatiale...")
grid = gpd.read_file(get_chemin("chemins_appli.grille_fichier", departement=DEPARTEMENT, maillage=MAILLAGE))
grid["idINSPIRE"] = grid["idINSPIRE"].astype(str)

gdf_result = grid.merge(results, on="idINSPIRE", how="left")

# === 7. Export GeoPackage ===
output_path = get_chemin("chemins_appli.prediction_fichier", departement=DEPARTEMENT)
gdf_result.to_file(output_path, layer="predictions_population", driver="GPKG")
print(f"Export GeoPackage terminé : {output_path}")
