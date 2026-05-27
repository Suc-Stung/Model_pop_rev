"""
Script : model_pipeline.py
Objectif : Orchestrer l'exécution complète du module de modélisation :
           fusion des données, régressions linéaires, Random Forest, XGBoost, ACP.
Auteur : LEDERMANN Quentin
Date : June 2025
Utilisation : Pipeline final du module modèle.
"""

from modele.scripts.model.fusion_modele import fusionner_features_par_secteur, ajouter_cibles_populations
from modele.scripts.model.regression import analyser_regressions
from modele.scripts.model.random_forest import analyse_random_forest
from modele.scripts.model.xg_boost import analyse_xgboost

import pandas as pd
import os
from modele.scripts.features.features_utils import print_status


def run_model_pipeline():
    print_status("=== DÉBUT DU PIPELINE DE MODÉLISATION ===", "info")

    # === 1. Fusion des données ===
    print_status("Fusion des features + cibles", "info")
    df = fusionner_features_par_secteur()
    df = ajouter_cibles_populations(df)
    os.makedirs("modele/output/fusion", exist_ok=True)
    df.to_csv("modele/output/fusion/features_population.csv", index=False)

    # === 2. Modèles ===
    analyser_regressions()
    analyse_random_forest()
    analyse_xgboost()

    print_status("=== PIPELINE DE MODÉLISATION TERMINÉ ===", "ok")


if __name__ == "__main__":
    run_model_pipeline()
