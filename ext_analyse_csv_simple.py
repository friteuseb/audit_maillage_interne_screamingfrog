#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyse directe du CSV Screaming Frog existant
Version sans dépendances externes
"""

import csv
import re
import os
import json
from datetime import datetime
from collections import Counter
from urllib.parse import urlparse

def load_csv_file(csv_path):
    """Charge le CSV avec gestion d'encodage"""
    if not os.path.exists(csv_path):
        print(f"❌ Fichier non trouvé: {csv_path}")
        return None, None
        
    print(f"📁 Chargement du fichier: {csv_path}")
    
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            with open(csv_path, 'r', encoding=encoding, newline='') as f:
                # Détecter le délimiteur
                sample = f.read(1024)
                f.seek(0)
                
                delimiter = ','
                if sample.count('\t') > sample.count(','):
                    delimiter = '\t'
                
                reader = csv.DictReader(f, delimiter=delimiter)
                rows = list(reader)
                
            print(f"✅ Fichier chargé avec l'encodage: {encoding}")
            print(f"📊 Nombre de lignes: {len(rows)}")
            print(f"📋 Colonnes disponibles: {list(reader.fieldnames) if reader.fieldnames else []}")
            
            return rows, reader.fieldnames
            
        except Exception as e:
            continue
            
    print("❌ Impossible de charger le fichier CSV")
    return None, None

def is_internal_link(source_url, dest_url):
    """Vérifie si le lien est interne"""
    try:
        source_domain = urlparse(source_url).netloc
        dest_domain = urlparse(dest_url).netloc
        return source_domain == dest_domain
    except:
        return False

def is_mechanical_link(row):
    """Détermine si un lien est mécanique basé sur les données SF"""
    # Récupérer les valeurs
    anchor = str(row.get('Ancrage', '')).lower().strip()
    origin = str(row.get('Origine du lien', '')).lower()
    xpath = str(row.get('Chemin du lien', '')).lower()
    
    # Liens de navigation (détectés par SF)
    if origin in ['navigation', 'en-tête', 'pied de page']:
        return True
    
    # Patterns d'ancres mécaniques
    mechanical_anchors = [
        r'^(accueil|home|menu|navigation)$',
        r'^(suivant|précédent|next|previous|page \d+)$',
        r'^(lire la suite|en savoir plus|voir plus|read more)$',
        r'^(contact|à propos|mentions légales|cgv|politique)$',
        r'^\d+$',  # Seulement des chiffres
        r'^(cliquez ici|cliquer ici|ici|click here)$',
        r'^(retour|back|retour accueil)$',
        r'^(passer au contenu)$',
        r'^$'  # Ancres vides
    ]
    
    # Vérifier les ancres
    for pattern in mechanical_anchors:
        if re.search(pattern, anchor):
            return True
    
    # Patterns XPath mécaniques
    mechanical_xpath_patterns = [
        r'header|footer|nav|navigation|menu',
        r'breadcrumb|pagination',
        r'sidebar|widget'
    ]
    
    for pattern in mechanical_xpath_patterns:
        if re.search(pattern, xpath):
            return True
            
    return False

def analyze_internal_links(rows, website_domain):
    """Analyse les liens internes"""
    print(f"\n🔍 ANALYSE DES LIENS INTERNES")
    print("="*50)
    
    internal_links = []
    external_links = []
    mechanical_count = 0
    editorial_count = 0
    
    for row in rows:
        source = row.get('Source', '')
        destination = row.get('Destination', '')
        
        # Filtrer les liens internes
        if is_internal_link(source, destination):
            internal_links.append(row)
            
            # Classifier mécanique vs éditorial
            if is_mechanical_link(row):
                mechanical_count += 1
                row['is_mechanical'] = True
            else:
                editorial_count += 1
                row['is_mechanical'] = False
        else:
            external_links.append(row)
    
    print(f"📊 Statistiques:")
    print(f"  - Liens totaux: {len(rows)}")
    print(f"  - Liens internes: {len(internal_links)}")
    print(f"  - Liens externes: {len(external_links)}")
    print(f"  - Liens mécaniques: {mechanical_count}")
    print(f"  - Liens éditoriaux: {editorial_count}")
    
    if len(internal_links) > 0:
        print(f"  - Ratio éditorial: {(editorial_count/len(internal_links)*100):.1f}%")
    
    return internal_links

def analyze_linking_patterns(internal_links):
    """Analyse les patterns de maillage"""
    editorial_links = [link for link in internal_links if not link.get('is_mechanical', False)]
    
    # Pages sources (qui lient le plus)
    source_counter = Counter()
    for link in editorial_links:
        source_counter[link.get('Source', '')] += 1
    
    # Pages destinations (les plus liées)
    dest_counter = Counter()
    for link in editorial_links:
        dest_counter[link.get('Destination', '')] += 1
    
    # Ancres les plus utilisées
    anchor_counter = Counter()
    for link in editorial_links:
        anchor = link.get('Ancrage', '').strip()
        if anchor:
            anchor_counter[anchor] += 1
    
    # Pages orphelines (toutes les pages - pages liées)
    all_pages = set()
    linked_pages = set()
    
    for link in internal_links:
        all_pages.add(link.get('Source', ''))
        if not link.get('is_mechanical', False):
            linked_pages.add(link.get('Destination', ''))
    
    orphan_pages = all_pages - linked_pages
    
    return {
        'top_linking_pages': dict(source_counter.most_common(10)),
        'most_linked_pages': dict(dest_counter.most_common(10)),
        'top_anchors': dict(anchor_counter.most_common(20)),
        'over_optimized_anchors': {anchor: count for anchor, count in anchor_counter.items() if count > 5},
        'orphan_pages': list(orphan_pages),
        'stats': {
            'total_pages': len(all_pages),
            'total_internal_links': len(internal_links),
            'editorial_links': len(editorial_links),
            'mechanical_links': len(internal_links) - len(editorial_links),
            'avg_editorial_per_page': len(editorial_links) / len(all_pages) if len(all_pages) > 0 else 0
        }
    }

def generate_html_report(analysis, website_url):
    """Génère le rapport HTML"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"./exports/audit_report_{timestamp}.html"
    
    os.makedirs("./exports/", exist_ok=True)
    
    stats = analysis['stats']
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Audit de Maillage Interne - {website_url}</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 40px; line-height: 1.6; color: #333; background: #f8f9fa; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; text-align: center; }}
            .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }}
            .stat-card {{ background: white; padding: 20px; border-radius: 8px; border-left: 4px solid #007bff; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .stat-number {{ font-size: 2.5em; font-weight: bold; color: #007bff; }}
            .stat-label {{ color: #6c757d; font-size: 0.9em; }}
            .warning {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 15px 0; border-radius: 5px; }}
            .success {{ background: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin: 15px 0; border-radius: 5px; }}
            .section {{ background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #e1e5e9; }}
            th {{ background-color: #f8f9fa; font-weight: 600; }}
            tr:hover {{ background-color: #f8f9fa; }}
            .url {{ word-break: break-all; max-width: 500px; font-family: monospace; font-size: 0.85em; }}
            .recommendations {{ background: #e3f2fd; padding: 20px; border-radius: 8px; border-left: 4px solid #2196f3; }}
            ul.orphan-list {{ max-height: 300px; overflow-y: auto; background: #f8f9fa; padding: 15px; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔗 Audit de Maillage Interne</h1>
                <p><strong>Site:</strong> {website_url}</p>
                <p><strong>Date:</strong> {datetime.now().strftime("%d/%m/%Y à %H:%M")}</p>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">{stats['total_pages']}</div>
                    <div class="stat-label">Pages analysées</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{stats['editorial_links']}</div>
                    <div class="stat-label">Liens éditoriaux</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{stats['mechanical_links']}</div>
                    <div class="stat-label">Liens mécaniques</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{stats['avg_editorial_per_page']:.1f}</div>
                    <div class="stat-label">Liens éditoriaux/page</div>
                </div>
            </div>
    """
    
    # Pages les plus liées
    if analysis['most_linked_pages']:
        html_content += """
        <div class="section">
            <h2>📈 Pages les Plus Liées (liens entrants éditoriaux)</h2>
            <table>
                <tr><th>URL</th><th>Liens entrants</th></tr>
        """
        for url, count in list(analysis['most_linked_pages'].items())[:15]:
            html_content += f"<tr><td class='url'>{url}</td><td><strong>{count}</strong></td></tr>"
        html_content += "</table></div>"
    
    # Pages orphelines
    if analysis['orphan_pages']:
        html_content += f"""
        <div class="section">
            <h2>⚠️ Pages Orphelines</h2>
            <div class="warning">
                <p><strong>{len(analysis['orphan_pages'])} pages sans liens entrants éditoriaux:</strong></p>
                <ul class="orphan-list">
        """
        for orphan in analysis['orphan_pages'][:30]:
            html_content += f"<li class='url'>{orphan}</li>"
        if len(analysis['orphan_pages']) > 30:
            html_content += f"<li><em>... et {len(analysis['orphan_pages']) - 30} autres</em></li>"
        html_content += "</ul></div></div>"
    
    # Ancres sur-optimisées
    if analysis['over_optimized_anchors']:
        html_content += """
        <div class="section">
            <h2>⚠️ Ancres Potentiellement Sur-optimisées</h2>
            <div class="warning">
                <table>
                    <tr><th>Ancre</th><th>Occurrences</th></tr>
        """
        for anchor, count in list(analysis['over_optimized_anchors'].items())[:10]:
            html_content += f"<tr><td>{anchor}</td><td><strong>{count}</strong></td></tr>"
        html_content += "</table></div></div>"
    
    # Pages qui lient le plus
    if analysis['top_linking_pages']:
        html_content += """
        <div class="section">
            <h2>🔗 Pages avec le Plus de Liens Sortants</h2>
            <table>
                <tr><th>URL</th><th>Liens sortants</th></tr>
        """
        for url, count in list(analysis['top_linking_pages'].items())[:15]:
            html_content += f"<tr><td class='url'>{url}</td><td><strong>{count}</strong></td></tr>"
        html_content += "</table></div>"
    
    html_content += """
        <div class="recommendations">
            <h2>💡 Recommandations</h2>
            <ul>
                <li><strong>Pages orphelines:</strong> Créer des liens éditoriaux contextuels vers ces pages depuis des contenus pertinents</li>
                <li><strong>Ancres sur-optimisées:</strong> Diversifier avec des variantes sémantiques et des expressions naturelles</li>
                <li><strong>Maillage interne:</strong> Ajouter 2-3 liens internes pertinents dans chaque contenu</li>
                <li><strong>Liens éditoriaux:</strong> Privilégier les liens dans le corps du texte plutôt qu'en navigation</li>
                <li><strong>Ancres descriptives:</strong> Utiliser des ancres qui décrivent le contenu de la page de destination</li>
            </ul>
        </div>
    </div>
    </body>
    </html>
    """
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return report_file

def main():
    print("🕷️ AUDIT DE MAILLAGE INTERNE - Analyse CSV")
    print("="*50)
    
    # Utiliser le fichier existant
    csv_path = "./exports/tous_les_liens_sortants.csv"
    website_url = "https://www.reseau-travaux.fr/"
    
    # Charger le CSV
    rows, fieldnames = load_csv_file(csv_path)
    if not rows:
        return
    
    # Extraire le domaine du site
    website_domain = urlparse(website_url).netloc
    
    # Analyser les liens internes
    internal_links = analyze_internal_links(rows, website_domain)
    
    # Analyser les patterns
    analysis = analyze_linking_patterns(internal_links)
    
    # Générer le rapport
    report_file = generate_html_report(analysis, website_url)
    
    print(f"\n✅ AUDIT TERMINÉ")
    print("="*50)
    print(f"📄 Rapport HTML: {report_file}")
    print(f"🚫 Pages orphelines: {len(analysis['orphan_pages'])}")
    print(f"📈 Ratio liens éditoriaux: {(analysis['stats']['editorial_links']/analysis['stats']['total_internal_links']*100):.1f}%")
    print(f"\n🎉 Ouvrez le rapport: file://{os.path.abspath(report_file)}")

if __name__ == "__main__":
    main()
