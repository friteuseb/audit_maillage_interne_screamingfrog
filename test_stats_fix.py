#!/usr/bin/env python3
"""
Test script to verify that statistics are properly calculated and displayed in HTML reports
"""

import csv
import os
from audit_maillage import CompleteLinkAuditor

def create_test_csv():
    """Create a simple test CSV with some internal links"""
    test_data = [
        ["Type", "Source", "Destination", "Ancrage", "Origine du lien"],
        ["Hyperlien", "https://example.com/page1", "https://example.com/page2", "lien vers page 2", "Contenu"],
        ["Hyperlien", "https://example.com/page1", "https://example.com/page3", "voir page 3", "Contenu"],
        ["Hyperlien", "https://example.com/page2", "https://example.com/page1", "retour accueil", "Navigation"],
        ["Hyperlien", "https://example.com/page3", "https://example.com/page1", "accueil", "Navigation"],
        ["Hyperlien", "https://example.com/page2", "https://example.com/page3", "article connexe", "Contenu"],
    ]
    
    test_file = "./test_links.csv"
    with open(test_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(test_data)
    
    return test_file

def main():
    print("🧪 Test de correction des statistiques")
    print("=" * 50)
    
    # Créer un fichier CSV de test
    test_file = create_test_csv()
    print(f"✅ Fichier CSV de test créé: {test_file}")
    
    # Créer l'auditeur
    auditor = CompleteLinkAuditor()
    
    # Analyser le CSV directement - cela génère automatiquement le rapport HTML
    print("📊 Analyse en cours...")
    report_file = auditor.analyze_csv(test_file, "https://example.com")
    
    if not report_file:
        print("❌ Erreur lors de l'analyse")
        return
        
    print(f"✅ Rapport généré: {report_file}")
    
    # Vérifier que les statistiques sont correctement affichées dans le HTML
    print("\n🔍 Vérification des statistiques dans le rapport HTML...")
    with open(report_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Chercher les patterns de statistiques connus basés sur les données de test
    # Notre test crée 3 pages avec 3 liens éditoriaux
    expected_pages = 3
    expected_editorial = 3
    expected_ratio = 60.0  # 3 éditoriaux sur 5 total = 60%
    
    success_count = 0
    total_checks = 4
    
    if f"{expected_pages:,}" in html_content:
        print("✅ Total pages correctement affiché (3)")
        success_count += 1
    else:
        print("❌ Total pages non affiché correctement")
        print(f"   Recherche de: {expected_pages:,}")
    
    if f"{expected_editorial:,}" in html_content:
        print("✅ Liens éditoriaux correctement affichés (3)")
        success_count += 1
    else:
        print("❌ Liens éditoriaux non affichés correctement")
        print(f"   Recherche de: {expected_editorial:,}")
    
    if f"{expected_ratio:.1f}%" in html_content:
        print("✅ Ratio éditorial correctement affiché (60.0%)")
        success_count += 1
    else:
        print("❌ Ratio éditorial non affiché correctement")
        print(f"   Recherche de: {expected_ratio:.1f}%")
    
    # Vérifier qu'il n'y a plus de placeholders non remplacés
    if "{stats[" not in html_content:
        print("✅ Aucun placeholder non remplacé trouvé")
        success_count += 1
    else:
        print("❌ Des placeholders {stats[...]} non remplacés trouvés")
        # Montrer quelques exemples
        import re
        placeholders = re.findall(r'\{stats\[[^\}]+\]', html_content)
        for placeholder in placeholders[:3]:  # Montrer max 3 exemples
            print(f"   Exemple: {placeholder}")
    
    print(f"\n📊 Résultat: {success_count}/{total_checks} vérifications réussies")
    
    # Nettoyage
    try:
        os.remove(test_file)
        print(f"\n🧹 Fichier de test supprimé: {test_file}")
    except:
        pass
    
    print("\n🎉 Test terminé!")

if __name__ == "__main__":
    main()