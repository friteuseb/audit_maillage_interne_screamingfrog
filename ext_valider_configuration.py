#!/usr/bin/env python3
"""
Script de validation de la configuration du projet d'audit de maillage interne
Vérifie la cohérence des fichiers, dépendances et configuration
"""

import os
import json
import sys
from pathlib import Path

def check_files():
    """Vérifie la présence des fichiers essentiels"""
    required_files = [
        '01_workflow_audit_ia_complet.py',
        'ext_audit_maillage_classique.py',
        'ext_analyse_csv_simple.py',
        'ext_detecteur_contenu_ia.py',
        'ext_analyseur_anthropic.py',
        'ext_analyseur_semantique.py',
        'ext_configuration_audit.json',
        'ext_config_screaming_frog.xml',
        '.env.example',
        'README.md'
    ]

    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)

    return missing_files

def check_config():
    """Vérifie la validité du fichier de configuration"""
    config_file = 'ext_configuration_audit.json'
    if not os.path.exists(config_file):
        return False, "Fichier ext_configuration_audit.json manquant"

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)

        required_keys = ['screaming_frog_path', 'export_path', 'analysis_thresholds']
        for key in required_keys:
            if key not in config:
                return False, f"Clé manquante dans la configuration: {key}"

        return True, "Configuration valide"
    except json.JSONDecodeError as e:
        return False, f"Erreur JSON dans ext_configuration_audit.json: {e}"
    except Exception as e:
        return False, f"Erreur lors de la lecture de la configuration: {e}"

def check_dependencies():
    """Vérifie les dépendances Python"""
    dependencies_status = {}

    # Dépendances de base
    try:
        import requests
        dependencies_status['requests'] = "✅ Installé"
    except ImportError:
        dependencies_status['requests'] = "❌ Manquant"

    try:
        from bs4 import BeautifulSoup
        dependencies_status['beautifulsoup4'] = "✅ Installé"
    except ImportError:
        dependencies_status['beautifulsoup4'] = "❌ Manquant"

    try:
        import anthropic
        dependencies_status['anthropic'] = "✅ Installé"
    except ImportError:
        dependencies_status['anthropic'] = "❌ Manquant (optionnel pour IA)"

    # Dépendances ML
    try:
        from sentence_transformers import SentenceTransformer
        dependencies_status['sentence-transformers'] = "✅ Installé"
    except ImportError:
        dependencies_status['sentence-transformers'] = "❌ Manquant (optionnel pour analyse sémantique)"

    try:
        import sklearn
        dependencies_status['scikit-learn'] = "✅ Installé"
    except ImportError:
        dependencies_status['scikit-learn'] = "❌ Manquant (optionnel pour analyse sémantique)"

    return dependencies_status

def check_env_file():
    """Vérifie la présence et le contenu du fichier .env"""
    if not os.path.exists('.env'):
        return "⚠️ Fichier .env manquant (copiez .env.example)"

    # Vérifier si ANTHROPIC_API_KEY est défini
    try:
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if api_key and len(api_key.strip()) > 10:
            return "✅ .env configuré avec clé API Anthropic"
        else:
            return "⚠️ Clé API Anthropic manquante ou invalide dans .env"
    except ImportError:
        return "⚠️ python-dotenv non installé, impossible de vérifier .env"

def main():
    """Fonction principale de validation"""
    print("🔍 VALIDATION DE LA CONFIGURATION DU PROJET")
    print("=" * 50)

    # Vérification des fichiers
    print("\n📁 Vérification des fichiers...")
    missing_files = check_files()
    if missing_files:
        print("❌ Fichiers manquants:")
        for file in missing_files:
            print(f"   - {file}")
    else:
        print("✅ Tous les fichiers requis sont présents")

    # Vérification de la configuration
    print("\n⚙️ Vérification de la configuration...")
    config_ok, config_msg = check_config()
    print(f"   {config_msg}")

    # Vérification des dépendances
    print("\n📦 Vérification des dépendances...")
    deps = check_dependencies()
    for dep, status in deps.items():
        print(f"   {dep}: {status}")

    # Vérification du fichier .env
    print("\n🔑 Vérification de l'environnement...")
    env_status = check_env_file()
    print(f"   {env_status}")

    # Résumé
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ:")

    all_good = len(missing_files) == 0 and config_ok
    if all_good:
        print("✅ Configuration valide - Prêt pour l'audit!")
        print("\n🚀 Commandes disponibles:")
        print("   python 01_workflow_audit_ia_complet.py     # Audit IA complet")
        print("   python ext_audit_maillage_classique.py      # Audit classique")
        print("   python ext_analyse_csv_simple.py           # Analyse CSV rapide")
    else:
        print("⚠️ Configuration incomplète - Corrigez les problèmes ci-dessus")
        if missing_files:
            print(f"   • {len(missing_files)} fichier(s) manquant(s)")
        if not config_ok:
            print("   • Problème de configuration")

    return 0 if all_good else 1

if __name__ == "__main__":
    sys.exit(main())