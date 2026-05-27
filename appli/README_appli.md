# Application du Modèle

## Avant-propos

Ce dossier est dédié à l'application du modèle de répartition dynamique de la population. Il est conçu pour un département choisi par l'utilisateur et une taille de grille ajustable (de 100 à 1 000 mètres).

## Structure du dossier

```
Model_pop/appli
├── cache/                   # Fichiers temporaires
├── config/                  # Fichier de configuration
│   └── settings.yaml        # Configuration principale (département, maillage, chemins)
├── data/                    # Dossier global des données utilisées
│   ├── bpe/                 # Données BPE (Base Permanente des Équipements)
│   ├── features/            # Données de features intermédiaires
│   ├── osm/                 # Données OpenStreetMap
│   ├── recens/              # Données INSEE du recensement
│   ├── sirene/              # Données SIRENE
│   └── topo/                # Données BD TOPO (IGN)
├── output/                  # Résultats des traitements
│   ├── features/            # Variables spatiales générées par maille
│   ├── fusion/              # Features fusionnées prêtes pour la prédiction
│   ├── grid/                # Grilles spatiales générées
│   └── results/             # Prédictions finales (GeoPackage)
├── scripts/                 # Scripts organisés par module
│   ├── acquisition/         # Téléchargement des données
│   ├── features/            # Création des variables spatiales
│   └── preprocess/          # Prétraitements intermédiaires
├── utils/                   # Utilitaires
│   └── score_POI.csv        # Catalogue de pondération des POI
└── README_appli.md          # Guide d'information et d'utilisation
```

## Configuration minimale

- Python 3.12.X ou ultérieur
- Microsoft Visual C++ 14.X ou ultérieur
- Espace disque : ~75 Go
- Connexion Internet

## Configuration du projet

Toute la configuration est centralisée dans le fichier **`appli/config/settings.yaml`**. Avant toute exécution, vérifiez les paramètres suivants :

```yaml
departement: "67"     # Code du département cible
maillage: 200         # Taille de la grille en mètres (100 à 1000)
```

Le fichier contient également les chemins de données (`chemins_modele.*`, `chemins_appli.*`), les scores de pondération des POI, et les modèles de noms de fichiers avec les variables `{departement}`, `{maillage}` et `{nom}`.

<br>

# Acquisition des Données

## Lancement du téléchargement automatisé

1. Vérifiez le code **département** et la **taille de grille** dans `appli/config/settings.yaml`.

2. Exécutez le pipeline d'acquisition :

```bash
python -m appli.scripts.acquisition.acquisition_pipeline
```

⚠️ Peut prendre plusieurs dizaines de minutes. En cas d'erreur, le script affiche l'erreur et la fonction associée.

## Sources téléchargées

| Source | Format | Contenu |
|---|---|---|
| SIRENE (INSEE) | GeoJSON | Établissements actifs du département |
| BPE (INSEE) | GeoJSON | Équipements publics du département |
| OpenStreetMap | GeoJSON | Bâtiments, commerces, bureaux, services, loisirs |
| Recensement (INSEE) | GeoJSON | Grille 200m avec indicateurs socio-démographiques |
| BD TOPO (IGN) | Shapefile | Bâtiments et tronçons de route |

## Résultats

Les données téléchargées sont sauvegardées au format GeoJSON dans le dossier `appli/data` et ses sous-dossiers respectifs.

<br>

# Construction des Variables

## Exécution du prétraitement et de la création des variables

1. Exécutez le script de prétraitement :

```bash
python -m appli.scripts.preprocess.preprocess_pipeline
```

2. Exécutez le script de création des variables spatiales :

```bash
python -m appli.scripts.features.features_pipeline
```

3. Exécutez le script de fusion des variables :

```bash
python -m appli.scripts.features.features_fusion
```

⚠️ Peut prendre plusieurs minutes. La présence de **FutureWarning** n'affecte pas les résultats.

## Variables générées

| Variable | Description |
|---|---|
| `score_poi_pondere` | Score pondéré d'attractivité des points d'intérêt |
| `emplois_estimes_pondere` | Estimation du nombre d'emplois par maille |
| `densite_etablissements` | Densité d'établissements par surface bâtie |
| `densite_commerces` | Densité commerciale par surface bâtie |
| `indice_mixite_fonctionnelle` | Indice de diversité fonctionnelle (entropie de Shannon) |
| `part_population_active` | Part de la population active (18-64 ans) |
| `part_jeunes` | Part des jeunes (moins de 25 ans) |
| `shape_index_moyen` | Indice de compacité moyen des bâtiments |
| `hauteur_ponderee_surface` | Hauteur pondérée par la surface bâtie |
| `ecart_type_hauteur` | Écart-type des hauteurs des bâtiments |
| `ecart_type_surface_batiment` | Écart-type des surfaces des bâtiments |
| `distance_moyenne_batiments` | Distance moyenne entre bâtiments |
| `volume_moyen_batiments` | Volume moyen des bâtiments |
| `largeur_moyenne_rue` | Largeur moyenne des rues |

## Résultats

Les variables sont créées et sauvegardées dans le dossier `appli/output/features`. Le fichier fusionné est exporté dans `appli/output/fusion/features_fusionnees_{maillage}m.csv`.

<br>

# Application du Modèle

## Prédiction et cartographie

Le script d'entraînement applique trois modèles (Régression Linéaire, Random Forest, XGBoost) au département cible et exporte les résultats.

1. Exécutez le script d'entraînement :

```bash
python -m modele.scripts.train.train
```

⚠️ Peut prendre plusieurs minutes.

## Résultats

Le fichier de sortie `predictions_{departement}.gpkg` est sauvegardé dans le dossier `appli/output/results`. Il contient les couches suivantes :

| Couche | Contenu |
|---|---|
| `predictions_population` | Prédictions de population par maille (LR jour/nuit, RF jour/nuit, XGB jour/nuit) |

<br>

# Utilitaires Partagés

Le projet s'appuie sur des modules utilitaires centralisés dans `modele/utils/` :

| Module | Fonctions |
|---|---|
| `project_utils.py` | `load_config()`, `print_status()`, `save_geoparquet()`, `clean_nom()`, `remove_holes()`, `get_chemin()` |
| `vis_utils.py` | `carte_residus_villes()`, `carte_residus_region()` — partagées entre les 3 modèles |

Ces modules sont réexportés par des wrappers légers dans `appli/scripts/features/features_utils.py`, `appli/scripts/acquisition/download_utils.py` et `appli/scripts/preprocess/preprocess_utils.py`.

---

**© 2024-2025 — Projet TER — Université de Strasbourg**
