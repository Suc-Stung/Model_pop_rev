"""
Script : setup_env.py
Objectif : Créer l'environnement virtuel Python et installer les dépendances
           du projet Model_pop avec gestion des erreurs.
Auteur : LEDERMANN Quentin
Date : June 2025
"""

import os
import sys
import platform
import subprocess
import shutil


def verifier_version_python():
    """Vérifie que la version de Python est ≥ 3.10."""
    version_min = (3, 10)
    version_actuelle = sys.version_info[:2]
    if version_actuelle < version_min:
        print(
            f"[✗] Python {version_actuelle[0]}.{version_actuelle[1]} détecté. "
            f"Version minimale requise : Python {version_min[0]}.{version_min[1]}+."
        )
        return False
    print(f"[✓] Python {version_actuelle[0]}.{version_actuelle[1]} détecté.")
    return True


def verifier_module_venv():
    """Vérifie si le module venv est disponible."""
    try:
        import venv  # noqa: F401
        return True
    except ImportError:
        return False


def creer_venv():
    """Crée l'environnement virtuel .venv. Retourne True si succès."""
    venv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv")

    # Supprimer un ancien .venv partiel ou corrompu
    if os.path.exists(venv_path) and not os.path.exists(os.path.join(venv_path, "Scripts", "python.exe")):
        print("[→] Suppression d'un .venv incomplet...")
        shutil.rmtree(venv_path, ignore_errors=True)

    print("[→] Création de l'environnement virtuel (.venv)...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "venv", venv_path],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"[✗] Erreur création venv : {result.stderr}")
            return False
    except Exception as e:
        print(f"[✗] Exception création venv : {e}")
        return False

    # Vérifier que le venv a bien été créé
    pip_path = (
        os.path.join(venv_path, "Scripts", "pip.exe")
        if platform.system() == "Windows"
        else os.path.join(venv_path, "bin", "pip")
    )
    python_path = (
        os.path.join(venv_path, "Scripts", "python.exe")
        if platform.system() == "Windows"
        else os.path.join(venv_path, "bin", "python")
    )
    if not os.path.exists(python_path):
        print("[✗] L'environnement virtuel n'a pas été créé correctement.")
        return False

    print(f"[✓] Environnement virtuel créé dans {venv_path}")
    return True, pip_path, python_path


def installer_dependances(pip_executable):
    """Installe les dépendances depuis requirements.txt."""
    print("[→] Installation des dépendances...")
    req_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
    try:
        result = subprocess.run(
            [pip_executable, "install", "--upgrade", "pip"],
            capture_output=True, text=True
        )
        result = subprocess.run(
            [pip_executable, "install", "-r", req_path],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"[✗] Erreur installation dépendances : {result.stderr}")
            return False
        print("[✓] Dépendances installées avec succès.")
        return True
    except Exception as e:
        print(f"[✗] Exception installation dépendances : {e}")
        return False


def afficher_instructions_activation():
    """Affiche la commande d'activation du venv."""
    if platform.system() == "Windows":
        cmd_activation = ".venv\\Scripts\\activate"
    else:
        cmd_activation = "source .venv/bin/activate"
    print(f"\n[→] Pour activer l'environnement virtuel, exécutez :\n    {cmd_activation}\n")


def main():
    print("=== CONFIGURATION DU PROJET MODEL_POP ===\n")

    if not verifier_version_python():
        sys.exit(1)

    if not verifier_module_venv():
        print("[✗] Le module 'venv' n'est pas disponible dans cette installation Python.")
        print("    Solutions :")
        print("      - Utilisez une distribution Python complète (python.org)")
        print("      - Réinstallez Python avec les composants optionnels 'pip' et 'venv'")
        print(f"    Python actuel : {sys.executable}")
        sys.exit(1)

    result = creer_venv()
    if not result:
        print("[✗] Échec de la création de l'environnement virtuel. Abandon.")
        sys.exit(1)

    _, pip_exe, _ = result

    if not installer_dependances(pip_exe):
        print("[✗] Échec de l'installation des dépendances. Abandon.")
        sys.exit(1)

    afficher_instructions_activation()
    print("=== CONFIGURATION TERMINÉE ===")
    print("Consultez le fichier README.md pour les instructions suivantes.")


if __name__ == "__main__":
    main()
