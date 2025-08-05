#!/usr/bin/env python3
"""
Test script pour vérifier les améliorations apportées :
1. Graphiques pour la Distribution Thématique
2. Suppression des icônes
3. Correction de la capitalisation
"""

import csv
import os
import re
from audit_maillage import CompleteLinkAuditor

def create_rich_test_csv():
    """Créer un CSV de test avec plus de données pour tester les graphiques"""
    test_data = [
        ["Type", "Source", "Destination", "Ancrage", "Origine du lien"],
        # Liens éditoriaux avec mots-clés variés
        ["Hyperlien", "https://example.com/page1", "https://example.com/seo", "guide seo complet", "Contenu"],
        ["Hyperlien", "https://example.com/page1", "https://example.com/marketing", "stratégies marketing", "Contenu"],
        ["Hyperlien", "https://example.com/page2", "https://example.com/seo", "optimisation seo", "Contenu"],
        ["Hyperlien", "https://example.com/page2", "https://example.com/blog", "article de blog", "Contenu"],
        ["Hyperlien", "https://example.com/page3", "https://example.com/marketing", "marketing digital", "Contenu"],
        ["Hyperlien", "https://example.com/page3", "https://example.com/contact", "nous contacter", "Contenu"],
        ["Hyperlien", "https://example.com/seo", "https://example.com/page1", "page principale", "Contenu"],
        ["Hyperlien", "https://example.com/marketing", "https://example.com/blog", "nos articles", "Contenu"],
        # Liens mécaniques
        ["Hyperlien", "https://example.com/page1", "https://example.com/page2", "suivant", "Navigation"],
        ["Hyperlien", "https://example.com/page2", "https://example.com/page1", "précédent", "Navigation"],
        ["Hyperlien", "https://example.com/page3", "https://example.com/page1", "accueil", "Navigation"],
    ]
    
    test_file = "./test_improvements.csv"
    with open(test_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(test_data)
    
    return test_file

def check_html_improvements(html_content):
    """Vérifier que les améliorations sont présentes dans le HTML"""
    checks = {
        'graphiques_thematiques': False,
        'icones_supprimees': True,  # Par défaut True, on cherche les icônes restantes
        'capitalisation_correcte': True  # Par défaut True, on cherche les erreurs
    }
    
    # 1. Vérifier la présence des graphiques thématiques
    if 'bar-chart' in html_content and 'pie-chart' in html_content:
        checks['graphiques_thematiques'] = True
    
    # 2. Vérifier l'absence d'icônes dans les titres
    emoji_pattern = r'[🔗📊📈📄🕸️📝🏷️💰🧠🎯⚡🔧✅⚠️🚫🔴🟢🔵💡]'
    if re.search(emoji_pattern, html_content):
        checks['icones_supprimees'] = False
        # Montrer quelques exemples avec contexte
        matches = re.findall(r'.{0,30}[🔗📊📈📄🕸️📝🏷️💰🧠🎯⚡🔧✅⚠️🚫🔴🟢🔵💡].{0,30}', html_content)
        print(f"   ❌ Icônes trouvées ({len(matches)}) :")
        for i, match in enumerate(matches[:3]):  # Montrer max 3 exemples
            print(f"      {i+1}. {match.strip()}")
    
    # 3. Vérifier la capitalisation (chercher des titres avec plusieurs majuscules)
    title_pattern = r'<h[1-6][^>]*>([^<]+)</h[1-6]>'
    titles = re.findall(title_pattern, html_content)
    
    problematic_titles = []
    for title in titles:
        # Nettoyer le titre des balises HTML
        clean_title = re.sub(r'<[^>]+>', '', title).strip()
        
        # Vérifier si le titre a plus d'une majuscule inappropriée
        # (on ignore les acronymes comme HTML, CSS, SEO, etc.)
        words = clean_title.split()
        if len(words) > 1:
            # Le premier mot doit commencer par une majuscule
            # Les autres mots ne devraient pas sauf exceptions (H1, Title, etc.)
            for i, word in enumerate(words[1:], 1):
                if word[0].isupper() and word.lower() not in ['h1', 'title', 'html', 'css', 'seo']:
                    problematic_titles.append(clean_title)
                    break
    
    if problematic_titles:
        checks['capitalisation_correcte'] = False
        print(f"   ❌ Titres avec capitalisation incorrecte : {problematic_titles[:3]}")
    
    return checks

def main():
    print("🧪 Test des améliorations apportées")
    print("=" * 50)
    
    # Créer un fichier CSV de test avec plus de contenu
    test_file = create_rich_test_csv()
    print(f"✅ Fichier CSV de test créé : {test_file}")
    
    # Créer l'auditeur
    auditor = CompleteLinkAuditor()
    
    # Analyser le CSV
    print("📊 Analyse en cours...")
    report_file = auditor.analyze_csv(test_file, "https://example.com")
    
    if not report_file:
        print("❌ Erreur lors de l'analyse")
        return
    
    print(f"✅ Rapport généré : {report_file}")
    
    # Lire le contenu HTML généré
    print("\n🔍 Vérification des améliorations...")
    with open(report_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Vérifier les améliorations
    checks = check_html_improvements(html_content)
    
    print("\n📊 Résultats des vérifications :")
    if checks['graphiques_thematiques']:
        print("✅ Graphiques thématiques : Présents (bar-chart et pie-chart)")
    else:
        print("❌ Graphiques thématiques : Absents")
    
    if checks['icones_supprimees']:
        print("✅ Icônes supprimées : Aucune icône trouvée dans le HTML")
    else:
        print("❌ Icônes supprimées : Des icônes sont encore présentes")
    
    if checks['capitalisation_correcte']:
        print("✅ Capitalisation : Correcte (une seule majuscule au début)")
    else:
        print("❌ Capitalisation : Des erreurs détectées")
    
    # Compter les succès
    success_count = sum(checks.values())
    total_checks = len(checks)
    
    print(f"\n🎯 Score global : {success_count}/{total_checks} améliorations validées")
    
    if success_count == total_checks:
        print("🎉 Toutes les améliorations sont correctement implémentées !")
    else:
        print("⚠️ Certaines améliorations nécessitent encore des ajustements")
    
    # Nettoyage
    try:
        os.remove(test_file)
        print(f"\n🧹 Fichier de test supprimé : {test_file}")
    except:
        pass
    
    print("\n✅ Test terminé !")

if __name__ == "__main__":
    main()