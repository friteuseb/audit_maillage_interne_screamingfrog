#!/usr/bin/env python3
"""
Script d'installation des dépendances pour l'analyse sémantique avancée
"""

import subprocess
import sys

def install_dependencies():
    """Installer les dépendances ML pour l'analyse sémantique"""
    print("🔧 Installation des dépendances pour l'analyse sémantique avancée...")
    print("=" * 60)
    
    # Liste des packages requis
    packages = [
        "sentence-transformers>=2.2.0",
        "scikit-learn>=1.0.0",
        "torch>=1.9.0",  # PyTorch (CPU only)
        "numpy>=1.21.0"
    ]
    
    print(f"📦 Packages à installer : {', '.join(packages)}")
    print("⏳ Cette opération peut prendre plusieurs minutes...")
    
    try:
        # Installer les packages
        for package in packages:
            print(f"\n🔄 Installation de {package}...")
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", package
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ {package} installé avec succès")
            else:
                print(f"❌ Erreur lors de l'installation de {package}:")
                print(result.stderr)
                return False
        
        print("\n🎉 Toutes les dépendances ont été installées avec succès !")
        print("\nℹ️  L'analyse sémantique CamemBERT sera maintenant disponible automatiquement.")
        print("💾 Le cache des embeddings sera créé dans ./semantic_cache/")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur critique lors de l'installation : {e}")
        return False

def test_installation():
    """Tester l'installation des dépendances"""
    print("\n🧪 Test de l'installation...")
    
    try:
        from sentence_transformers import SentenceTransformer
        from sklearn.metrics.pairwise import cosine_similarity
        from sklearn.cluster import DBSCAN
        import numpy as np
        
        print("✅ Toutes les dépendances sont correctement installées")
        
        # Test rapide du modèle
        print("🔄 Test de chargement d'un modèle léger...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Test d'encodage
        test_texts = ["intelligence artificielle", "machine learning"]
        embeddings = model.encode(test_texts)
        
        print(f"✅ Test réussi ! Dimension des embeddings : {embeddings.shape[1]}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Dépendance manquante : {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur lors du test : {e}")
        return False

def main():
    print("🚀 INSTALLATION ANALYSE SÉMANTIQUE AVANCÉE")
    print("=" * 50)
    print("Cette installation va ajouter :")
    print("• CamemBERT pour l'analyse française")
    print("• Clustering sémantique intelligent")
    print("• Analyse de cohérence ancres ↔ contenus")
    print("• Détection d'opportunités de maillage")
    print("• Cache intelligent des embeddings")
    
    response = input("\n❓ Continuer l'installation ? (o/N) : ").lower().strip()
    
    if response in ['o', 'oui', 'y', 'yes']:
        success = install_dependencies()
        
        if success:
            test_success = test_installation()
            
            if test_success:
                print("\n🎯 INSTALLATION TERMINÉE AVEC SUCCÈS !")
                print("\n📋 Prochaines étapes :")
                print("1. Relancez votre analyse avec : python audit_maillage.py")
                print("2. L'analyse sémantique sera automatiquement activée")
                print("3. Le premier run sera plus lent (téléchargement du modèle)")
                print("4. Les runs suivants utiliseront le cache pour plus de rapidité")
            else:
                print("\n⚠️  Installation terminée mais des erreurs de test sont survenues")
        else:
            print("\n❌ L'installation a échoué")
            print("💡 Essayez : pip install --upgrade pip setuptools wheel")
    else:
        print("❌ Installation annulée")

if __name__ == "__main__":
    main()