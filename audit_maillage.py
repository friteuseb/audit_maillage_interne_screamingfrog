#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audit de Maillage Interne - Version Complète
Propose soit un nouveau crawl soit l'analyse de CSV existants
"""

import subprocess
import csv
import re
import os
import json
from datetime import datetime
from collections import Counter
from urllib.parse import urlparse
import glob

class CompleteLinkAuditor:
    def __init__(self, config_file='audit_config.json'):
        self.config = self.load_config(config_file)
        
    def load_config(self, config_file):
        """Charge la configuration"""
        default_config = {
            "screaming_frog_path": "/mnt/c/Program Files (x86)/Screaming Frog SEO Spider/ScreamingFrogSEOSpiderCli.exe",
            "export_path": "./exports/",
            "ignore_extensions": [".pdf", ".jpg", ".png", ".gif", ".css", ".js", ".ico", ".svg"],
            "min_anchor_length": 3
        }
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        except FileNotFoundError:
            print(f"⚠️  Config file {config_file} not found, using defaults")
            
        return default_config

    def show_menu(self):
        """Affiche le menu principal"""
        print("🔗 AUDIT DE MAILLAGE INTERNE")
        print("="*50)
        print("Choisissez une option :")
        print()
        print("1. 🕷️  Nouveau crawl Screaming Frog + Analyse")
        print("2. 📊 Analyser un CSV existant")
        print("3. 📁 Lister les CSV disponibles")
        print("4. ⚙️  Configuration")
        print("5. ❌ Quitter")
        print()
        
        while True:
            choice = input("Votre choix (1-5): ").strip()
            if choice in ['1', '2', '3', '4', '5']:
                return choice
            print("❌ Choix invalide, veuillez choisir entre 1 et 5")

    def list_existing_csvs(self):
        """Liste les CSV disponibles"""
        csv_files = []
        
        # Chercher dans le dossier exports
        if os.path.exists(self.config['export_path']):
            csv_files.extend(glob.glob(f"{self.config['export_path']}*.csv"))
        
        # Chercher dans le répertoire courant
        csv_files.extend(glob.glob("*.csv"))
        
        # Supprimer les doublons et trier par date de modification
        csv_files = list(set(csv_files))
        csv_files.sort(key=os.path.getmtime, reverse=True)
        
        if not csv_files:
            print("📭 Aucun fichier CSV trouvé")
            return []
        
        print(f"\n📁 Fichiers CSV disponibles ({len(csv_files)}):")
        print("-" * 60)
        
        for i, file_path in enumerate(csv_files, 1):
            file_size = os.path.getsize(file_path)
            file_date = datetime.fromtimestamp(os.path.getmtime(file_path))
            print(f"{i:2d}. {os.path.basename(file_path)}")
            print(f"    📍 {file_path}")
            print(f"    📊 {file_size:,} octets | 📅 {file_date.strftime('%d/%m/%Y %H:%M')}")
            print()
        
        return csv_files

    def run_new_crawl(self, website_url):
        """Lance un nouveau crawl Screaming Frog"""
        print(f"\n🚀 NOUVEAU CRAWL")
        print("="*50)
        print(f"Site: {website_url}")
        
        # Créer le dossier d'export
        os.makedirs(self.config['export_path'], exist_ok=True)
        
        # Commande Screaming Frog
        crawl_command = [
            self.config["screaming_frog_path"],
            "-headless",
            "-crawl", website_url,
            "--output-folder", self.config['export_path'],
            "--export-format", "csv",
            "--bulk-export", "Links:All Outlinks",
            "--save-crawl"
        ]
        
        try:
            print("⏳ Crawl en cours (cela peut prendre plusieurs minutes)...")
            result = subprocess.run(crawl_command, capture_output=True, text=True, timeout=3600)
            
            if result.returncode == 0:
                print("✅ Crawl terminé avec succès")
                
                # Chercher le fichier CSV créé
                csv_files = []
                if os.path.exists(self.config['export_path']):
                    csv_files = [f for f in os.listdir(self.config['export_path']) if f.endswith('.csv')]
                
                if csv_files:
                    latest_file = max([f"{self.config['export_path']}{f}" for f in csv_files], key=os.path.getctime)
                    print(f"📄 Fichier créé: {latest_file}")
                    return latest_file
                else:
                    print("⚠️  Fichier CSV non trouvé")
                    return None
            else:
                print(f"❌ Erreur lors du crawl:")
                print(result.stderr)
                return None
                
        except subprocess.TimeoutExpired:
            print("⏰ Crawl interrompu (timeout)")
            return None
        except FileNotFoundError:
            print("❌ Screaming Frog non trouvé. Vérifiez le chemin dans la configuration.")
            return None
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return None

    def load_csv_file(self, csv_path):
        """Charge un fichier CSV"""
        if not os.path.exists(csv_path):
            print(f"❌ Fichier non trouvé: {csv_path}")
            return None, None
            
        print(f"📁 Chargement de: {os.path.basename(csv_path)}")
        
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
                    
                print(f"✅ Fichier chargé ({len(rows)} lignes)")
                return rows, reader.fieldnames
                
            except Exception as e:
                continue
                
        print("❌ Impossible de charger le fichier CSV")
        return None, None

    def is_internal_link(self, source_url, dest_url):
        """Vérifie si le lien est interne"""
        try:
            source_domain = urlparse(source_url).netloc
            dest_domain = urlparse(dest_url).netloc
            return source_domain == dest_domain
        except:
            return False

    def is_mechanical_link(self, row):
        """Détermine si un lien est mécanique"""
        # Gérer les différents noms de colonnes possibles
        anchor_col = None
        origin_col = None
        xpath_col = None
        
        for col in row.keys():
            col_lower = col.lower().strip('\ufeff"')
            if 'anchor' in col_lower or 'ancrage' in col_lower:
                anchor_col = col
            elif 'origin' in col_lower or 'origine' in col_lower:
                origin_col = col
            elif 'xpath' in col_lower or 'chemin' in col_lower:
                xpath_col = col
        
        anchor = str(row.get(anchor_col, '')).lower().strip() if anchor_col else ''
        origin = str(row.get(origin_col, '')).lower() if origin_col else ''
        xpath = str(row.get(xpath_col, '')).lower() if xpath_col else ''
        
        # Liens de navigation (détectés par SF)
        if any(x in origin for x in ['navigation', 'en-tête', 'pied de page', 'header', 'footer', 'nav']):
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
        
        for pattern in mechanical_anchors:
            if re.search(pattern, anchor):
                return True
        
        # Patterns XPath mécaniques
        if any(x in xpath for x in ['header', 'footer', 'nav', 'navigation', 'menu', 'breadcrumb', 'pagination']):
            return True
            
        return False

    def analyze_csv(self, csv_path, website_url=None):
        """Analyse un fichier CSV"""
        print(f"\n📊 ANALYSE DU FICHIER CSV")
        print("="*50)
        
        # Charger le CSV
        rows, fieldnames = self.load_csv_file(csv_path)
        if not rows:
            return None
        
        # Détecter l'URL du site si pas fournie
        if not website_url and rows:
            first_source = rows[0].get('Source', '')
            if first_source:
                website_url = f"{urlparse(first_source).scheme}://{urlparse(first_source).netloc}/"
        
        print(f"🌐 Site analysé: {website_url}")
        
        # Analyser les liens
        internal_links = []
        external_links = []
        mechanical_count = 0
        editorial_count = 0
        
        for row in rows:
            # Trouver les colonnes source/destination
            source_col = dest_col = None
            for col in row.keys():
                col_clean = col.lower().strip('\ufeff"')
                if 'source' in col_clean:
                    source_col = col
                elif 'destination' in col_clean or 'target' in col_clean:
                    dest_col = col
            
            if not source_col or not dest_col:
                continue
                
            source = row.get(source_col, '')
            destination = row.get(dest_col, '')
            
            # Filtrer les liens internes
            if self.is_internal_link(source, destination):
                internal_links.append(row)
                
                # Classifier mécanique vs éditorial
                if self.is_mechanical_link(row):
                    mechanical_count += 1
                    row['is_mechanical'] = True
                else:
                    editorial_count += 1
                    row['is_mechanical'] = False
            else:
                external_links.append(row)
        
        print(f"\n📊 Résultats:")
        print(f"  📈 Liens totaux: {len(rows):,}")
        print(f"  🏠 Liens internes: {len(internal_links):,}")
        print(f"  🌍 Liens externes: {len(external_links):,}")
        print(f"  🔧 Liens mécaniques: {mechanical_count:,}")
        print(f"  ✍️  Liens éditoriaux: {editorial_count:,}")
        
        if len(internal_links) > 0:
            ratio = (editorial_count/len(internal_links)*100)
            print(f"  📊 Ratio éditorial: {ratio:.1f}%")
        
        # Analyser les patterns
        analysis = self.analyze_linking_patterns(internal_links, website_url)
        
        # Générer le rapport
        report_file = self.generate_html_report(analysis, website_url, csv_path)
        
        print(f"\n✅ ANALYSE TERMINÉE")
        print("="*50)
        print(f"📄 Rapport HTML: {report_file}")
        print(f"🚫 Pages orphelines: {len(analysis['orphan_pages'])}")
        
        return report_file

    def analyze_linking_patterns(self, internal_links, website_url):
        """Analyse les patterns de maillage"""
        editorial_links = [link for link in internal_links if not link.get('is_mechanical', False)]
        
        # Trouver les colonnes
        source_col = dest_col = anchor_col = None
        if internal_links:
            for col in internal_links[0].keys():
                col_clean = col.lower().strip('\ufeff"')
                if 'source' in col_clean:
                    source_col = col
                elif 'destination' in col_clean:
                    dest_col = col
                elif 'anchor' in col_clean or 'ancrage' in col_clean:
                    anchor_col = col
        
        # Compteurs
        source_counter = Counter()
        dest_counter = Counter()
        anchor_counter = Counter()
        
        for link in editorial_links:
            if source_col:
                source_counter[link.get(source_col, '')] += 1
            if dest_col:
                dest_counter[link.get(dest_col, '')] += 1
            if anchor_col:
                anchor = link.get(anchor_col, '').strip()
                if anchor:
                    anchor_counter[anchor] += 1
        
        # Pages orphelines
        all_pages = set()
        linked_pages = set()
        
        for link in internal_links:
            if source_col:
                all_pages.add(link.get(source_col, ''))
            if dest_col and not link.get('is_mechanical', False):
                linked_pages.add(link.get(dest_col, ''))
        
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

    def generate_html_report(self, analysis, website_url, source_file):
        """Génère le rapport HTML"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"{self.config['export_path']}audit_report_{timestamp}.html"
        
        os.makedirs(self.config['export_path'], exist_ok=True)
        
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
                .meta {{ background: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #6c757d; }}
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
                
                <div class="meta">
                    <strong>📄 Fichier source:</strong> {os.path.basename(source_file)}<br>
                    <strong>⚙️  Script:</strong> Audit automatisé de maillage interne
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number">{stats['total_pages']:,}</div>
                        <div class="stat-label">Pages analysées</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{stats['editorial_links']:,}</div>
                        <div class="stat-label">Liens éditoriaux</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{stats['mechanical_links']:,}</div>
                        <div class="stat-label">Liens mécaniques</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{stats['avg_editorial_per_page']:.1f}</div>
                        <div class="stat-label">Liens éditoriaux/page</div>
                    </div>
                </div>
        """
        
        # Ajouter les sections d'analyse...
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
        
        html_content += """
            <div class="recommendations">
                <h2>💡 Recommandations</h2>
                <ul>
                    <li><strong>Pages orphelines:</strong> Créer des liens éditoriaux contextuels vers ces pages</li>
                    <li><strong>Maillage interne:</strong> Ajouter 2-3 liens internes pertinents par page</li>
                    <li><strong>Ancres descriptives:</strong> Utiliser des ancres qui décrivent le contenu cible</li>
                    <li><strong>Liens contextuels:</strong> Privilégier les liens dans le corps du texte</li>
                </ul>
            </div>
        </div>
        </body>
        </html>
        """
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return report_file

    def show_config(self):
        """Affiche et permet de modifier la configuration"""
        print(f"\n⚙️  CONFIGURATION ACTUELLE")
        print("="*50)
        print(f"📍 Screaming Frog: {self.config['screaming_frog_path']}")
        print(f"📁 Dossier export: {self.config['export_path']}")
        print(f"📏 Longueur min ancre: {self.config['min_anchor_length']}")
        print(f"🚫 Extensions ignorées: {', '.join(self.config['ignore_extensions'])}")
        
        modify = input("\nModifier la configuration ? (o/N): ").lower()
        if modify == 'o':
            # Ici on pourrait ajouter la modification de config
            print("Modification de config pas encore implémentée")

    def run(self):
        """Lance l'application principale"""
        while True:
            choice = self.show_menu()
            
            if choice == '1':
                # Nouveau crawl
                website_url = input("\n🌐 URL du site à crawler: ").strip()
                if not website_url:
                    print("❌ URL requise")
                    continue
                
                csv_file = self.run_new_crawl(website_url)
                if csv_file:
                    input("\n⏸️  Appuyez sur Entrée pour lancer l'analyse...")
                    self.analyze_csv(csv_file, website_url)
                
            elif choice == '2':
                # Analyser CSV existant
                csv_files = self.list_existing_csvs()
                if not csv_files:
                    input("\n⏸️  Appuyez sur Entrée pour continuer...")
                    continue
                
                while True:
                    try:
                        file_choice = input(f"\nChoisir un fichier (1-{len(csv_files)}) ou 'r' pour retour: ").strip()
                        if file_choice.lower() == 'r':
                            break
                        
                        file_index = int(file_choice) - 1
                        if 0 <= file_index < len(csv_files):
                            selected_file = csv_files[file_index]
                            website_url = input("🌐 URL du site (optionnel): ").strip() or None
                            self.analyze_csv(selected_file, website_url)
                            break
                        else:
                            print("❌ Numéro invalide")
                    except ValueError:
                        print("❌ Veuillez entrer un numéro")
                
            elif choice == '3':
                # Lister CSV
                self.list_existing_csvs()
                input("\n⏸️  Appuyez sur Entrée pour continuer...")
                
            elif choice == '4':
                # Configuration
                self.show_config()
                
            elif choice == '5':
                # Quitter
                print("\n👋 Au revoir !")
                break
            
            print("\n" + "="*50)

if __name__ == "__main__":
    auditor = CompleteLinkAuditor()
    auditor.run()