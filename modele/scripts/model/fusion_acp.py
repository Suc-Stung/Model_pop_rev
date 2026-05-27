"""
Script : fusion_acp.py
Objectif : Fusionner tous les fichiers CSV de features présents dans output/features/
           sur la clé commune 'idINSPIRE' pour l'analyse ACP.
Auteur : LEDERMANN Quentin
Date : June 2025
Utilisation : Étape de préparation des données pour l'analyse factorielle (ACP).
"""

import glob
import os
import pandas as pd
from modele.scripts.features.features_utils import print_status

# === PARAMÈTRES ===
FEATURES_DIR = "modele/output/features"
OUTPUT_PATH = "modele/output/fusion/variables_merged.csv"
EXTENSION = "*.csv"

# Liste des fichiers de features
liste_fichiers = glob.glob(os.path.join(FEATURES_DIR, EXTENSION))

# Initialisation du tableau fusionné
df_merged = None

if not liste_fichiers:
    print_status("Aucun fichier de feature trouvé", "err")
    exit()

for fichier in liste_fichiers:
    df = pd.read_csv(fichier)

    if 'idINSPIRE' not in df.columns:
        raise ValueError(f"Le fichier {fichier} ne contient pas la colonne 'idINSPIRE'")

    # Agrégation des doublons éventuels (ex. fusion POI + bâtiments)
    if df['idINSPIRE'].duplicated().any():
        df = df.groupby('idINSPIRE').mean(numeric_only=True).reset_index()

    # Fusion progressive
    df_merged = df if df_merged is None else pd.merge(df_merged, df, on="idINSPIRE", how="outer")

# Remplacement des valeurs manquantes
if df_merged is not None:
    df_merged = df_merged.fillna(0)
else:
    raise ValueError("Aucune donnée fusionnée trouvée pour appliquer fillna.")

# Export final
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
df_merged.to_csv(OUTPUT_PATH, index=False)
print_status("Fusion ACP terminée", "ok", f"Fichier exporté : {OUTPUT_PATH}")
