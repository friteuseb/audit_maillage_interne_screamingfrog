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
        """Lance un nouveau crawl Screaming Frog avec diagnostic"""
        print(f"\n🚀 NOUVEAU CRAWL")
        print("="*50)
        print(f"Site: {website_url}")
        
        # Vérifier que Screaming Frog existe
        sf_path = self.config["screaming_frog_path"]
        if not os.path.exists(sf_path):
            print(f"❌ Screaming Frog non trouvé à: {sf_path}")
            print("\n💡 Solutions possibles:")
            print("1. Installer Screaming Frog SEO Spider")
            print("2. Mettre à jour le chemin dans audit_config.json")
            print("3. Utiliser l'option 2 pour analyser un CSV existant")
            
            # Chemins alternatifs courants
            alt_paths = [
                "/mnt/c/Program Files/Screaming Frog SEO Spider/ScreamingFrogSEOSpiderCli.exe",
                "/mnt/c/Program Files (x86)/Screaming Frog SEO Spider/ScreamingFrogSEOSpiderCli.exe",
                "C:\\Program Files\\Screaming Frog SEO Spider\\ScreamingFrogSEOSpiderCli.exe",
                "C:\\Program Files (x86)\\Screaming Frog SEO Spider\\ScreamingFrogSEOSpiderCli.exe"
            ]
            
            print("\n🔍 Chemins alternatifs à essayer:")
            for path in alt_paths:
                if os.path.exists(path):
                    print(f"  ✅ Trouvé: {path}")
                else:
                    print(f"  ❌ Absent: {path}")
            
            return None
        
        # Créer le dossier d'export
        os.makedirs(self.config['export_path'], exist_ok=True)
        
        # Tester la connectivité réseau
        print("🌐 Test de connectivité...")
        try:
            from urllib.request import urlopen
            from urllib.parse import urlparse
            
            # Test simple de connectivité
            parsed = urlparse(website_url)
            test_url = f"{parsed.scheme}://{parsed.netloc}"
            
            response = urlopen(test_url, timeout=10)
            if response.status == 200:
                print("✅ Site accessible")
            else:
                print(f"⚠️  Réponse HTTP {response.status}")
        except Exception as e:
            print(f"⚠️  Problème de connectivité: {e}")
            print("💡 Vérifiez votre connexion internet et l'URL du site")
        
        # Commande Screaming Frog - retour à la version qui fonctionnait
        # Créer le dossier d'export local et nettoyer les anciens fichiers
        os.makedirs(self.config['export_path'], exist_ok=True)
        
        # Nettoyer les anciens fichiers CSV pour éviter les conflits
        import glob
        old_csvs = glob.glob(f"{self.config['export_path']}*.csv")
        for old_csv in old_csvs:
            try:
                os.remove(old_csv)
                print(f"🗑️  Supprimé: {os.path.basename(old_csv)}")
            except Exception as e:
                print(f"⚠️  Impossible de supprimer {old_csv}: {e}")
        
        # Convertir le chemin Linux en chemin Windows pour Screaming Frog
        linux_path = os.path.abspath(self.config['export_path'])
        
        # Convertir le chemin WSL en chemin Windows
        try:
            # Utiliser wslpath pour convertir le chemin Linux en chemin Windows
            result = subprocess.run(['wslpath', '-w', linux_path], 
                                  capture_output=True, text=True, check=True)
            windows_path = result.stdout.strip()
            output_folder = windows_path
            print(f"🔍 Chemin converti Linux → Windows: '{linux_path}' → '{windows_path}'")
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Si wslpath n'est pas disponible, essayer une conversion manuelle
            if linux_path.startswith('/home/'):
                # Convertir /home/user/... vers C:\Users\user\...
                parts = linux_path.split('/')
                if len(parts) >= 3:
                    windows_path = f"C:\\Users\\{parts[2]}" + "\\".join([''] + parts[3:])
                    output_folder = windows_path
                    print(f"🔍 Conversion manuelle: '{linux_path}' → '{windows_path}'")
                else:
                    output_folder = linux_path
                    print(f"⚠️  Impossible de convertir le chemin, utilisation du chemin Linux")
            else:
                output_folder = linux_path
                print(f"⚠️  Chemin non standard, utilisation du chemin Linux")
        
        print(f"🔍 Chemin final utilisé: '{output_folder}'")
        
        crawl_command = [
            sf_path,
            "-headless",
            "-crawl", website_url,
            "--output-folder", output_folder,
            "--export-format", "csv",
            "--bulk-export", "Links:All Outlinks"
        ]
        
        print(f"🔧 Commande: {' '.join(crawl_command[:3])} [...]")
        
        try:
            print("⏳ Crawl en cours (cela peut prendre plusieurs minutes)...")
            result = subprocess.run(
                crawl_command, 
                capture_output=True, 
                text=True, 
                timeout=3600,
                cwd=os.path.dirname(sf_path)
            )
            
            # Diagnostic détaillé
            if result.returncode == 0:
                print("✅ Crawl terminé avec succès")
                
                # Chercher le fichier CSV créé dans le dossier d'export
                csv_files = []
                if os.path.exists(self.config['export_path']):
                    all_files = os.listdir(self.config['export_path'])
                    csv_files = [f for f in all_files if f.endswith('.csv') and ('outlink' in f.lower() or 'liens_sortants' in f.lower())]
                    
                    print(f"📁 Fichiers créés dans {self.config['export_path']}:")
                    for f in all_files:
                        print(f"  - {f}")
                
                if csv_files:
                    latest_file = max([f"{self.config['export_path']}{f}" for f in csv_files], key=lambda x: os.path.getctime(x))
                    print(f"📄 Fichier CSV des liens: {latest_file}")
                    return latest_file
                else:
                    print("⚠️  Fichier CSV des liens non trouvé")
                    print("💡 Le crawl a peut-être échoué ou aucun lien trouvé")
                    return None
            else:
                print(f"❌ Erreur lors du crawl (code: {result.returncode})")
                if result.stdout:
                    print(f"📤 Sortie: {result.stdout[:500]}")
                if result.stderr:
                    print(f"📥 Erreur: {result.stderr[:500]}")
                
                # Suggestions d'erreurs courantes
                if "access" in result.stderr.lower() or "permission" in result.stderr.lower():
                    print("💡 Problème de permissions - essayez de lancer en administrateur")
                elif "network" in result.stderr.lower() or "timeout" in result.stderr.lower():
                    print("💡 Problème réseau - vérifiez la connectivité et les proxies")
                elif "license" in result.stderr.lower():
                    print("💡 Problème de licence - vérifiez votre licence Screaming Frog")
                
                return None
                
        except subprocess.TimeoutExpired:
            print("⏰ Crawl interrompu (timeout après 1h)")
            print("💡 Le site est peut-être trop volumineux, essayez avec une limite de pages")
            return None
        except FileNotFoundError:
            print(f"❌ Exécutable non trouvé: {sf_path}")
            print("💡 Vérifiez l'installation et le chemin de Screaming Frog")
            return None
        except Exception as e:
            print(f"❌ Erreur inattendue: {e}")
            return None

    def load_csv_file(self, csv_path):
        """Charge un fichier CSV avec gestion d'erreur robuste"""
        if not os.path.exists(csv_path):
            print(f"❌ Fichier non trouvé: {csv_path}")
            return None, None
            
        print(f"📁 Chargement de: {os.path.basename(csv_path)}")
        
        # Vérifier la taille du fichier
        try:
            file_size = os.path.getsize(csv_path)
            if file_size == 0:
                print("❌ Le fichier CSV est vide")
                return None, None
            elif file_size > 100 * 1024 * 1024:  # 100MB
                print(f"⚠️  Fichier volumineux ({file_size // 1024 // 1024}MB), le traitement peut être lent")
        except OSError as e:
            print(f"❌ Erreur lors de la lecture du fichier: {e}")
            return None, None
        
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        last_error = None
        
        for encoding in encodings:
            try:
                with open(csv_path, 'r', encoding=encoding, newline='') as f:
                    # Détecter le délimiteur avec une analyse plus robuste
                    sample = f.read(2048)
                    f.seek(0)
                    
                    if not sample.strip():
                        print("❌ Le fichier CSV est vide ou ne contient que des espaces")
                        return None, None
                    
                    # Détection intelligente du délimiteur
                    delimiter = ','
                    tab_count = sample.count('\t')
                    comma_count = sample.count(',')
                    semicolon_count = sample.count(';')
                    
                    if tab_count > comma_count and tab_count > semicolon_count:
                        delimiter = '\t'
                    elif semicolon_count > comma_count:
                        delimiter = ';'
                    
                    reader = csv.DictReader(f, delimiter=delimiter)
                    
                    # Vérifier que nous avons des colonnes
                    if not reader.fieldnames:
                        continue
                    
                    # Nettoyer les noms de colonnes (BOM, espaces)
                    clean_fieldnames = []
                    for field in reader.fieldnames:
                        if field:
                            clean_field = field.strip().strip('\ufeff"\'')
                            clean_fieldnames.append(clean_field)
                    
                    if not clean_fieldnames:
                        continue
                    
                    # Charger les données avec validation
                    rows = []
                    for i, row in enumerate(reader):
                        if i > 500000:  # Limite de sécurité
                            print(f"⚠️  Limitation à 500,000 lignes pour éviter les problèmes de mémoire")
                            break
                        
                        # Créer un dictionnaire avec les noms nettoyés
                        clean_row = {}
                        for old_key, new_key in zip(reader.fieldnames, clean_fieldnames):
                            clean_row[new_key] = row.get(old_key, '')
                        rows.append(clean_row)
                    
                    if not rows:
                        print("❌ Aucune donnée trouvée dans le fichier CSV")
                        return None, None
                    
                print(f"✅ Fichier chargé avec l'encodage {encoding} ({len(rows):,} lignes)")
                print(f"📋 Colonnes: {', '.join(clean_fieldnames[:5])}{'...' if len(clean_fieldnames) > 5 else ''}")
                return rows, clean_fieldnames
                
            except UnicodeDecodeError as e:
                last_error = f"Erreur d'encodage {encoding}: {e}"
                continue
            except csv.Error as e:
                last_error = f"Erreur CSV avec {encoding}: {e}"
                continue
            except Exception as e:
                last_error = f"Erreur inattendue avec {encoding}: {e}"
                continue
                
        print(f"❌ Impossible de charger le fichier CSV. Dernière erreur: {last_error}")
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
        """Détermine si un lien est mécanique avec détection avancée"""
        # Gérer les différents noms de colonnes possibles
        anchor_col = None
        origin_col = None
        xpath_col = None
        link_type_col = None
        
        for col in row.keys():
            col_lower = col.lower().strip('\ufeff"')
            if 'anchor' in col_lower or 'ancrage' in col_lower:
                anchor_col = col
            elif 'origin' in col_lower or 'origine' in col_lower:
                origin_col = col
            elif 'xpath' in col_lower or 'chemin' in col_lower:
                xpath_col = col
            elif 'type' in col_lower and 'link' in col_lower:
                link_type_col = col
        
        anchor = str(row.get(anchor_col, '')).lower().strip() if anchor_col else ''
        origin = str(row.get(origin_col, '')).lower() if origin_col else ''
        xpath = str(row.get(xpath_col, '')).lower() if xpath_col else ''
        link_type = str(row.get(link_type_col, '')).lower() if link_type_col else ''
        
        # Utiliser la configuration pour les patterns
        mechanical_patterns = self.config.get('mechanical_anchor_patterns', [])
        mechanical_selectors = self.config.get('mechanical_selectors', [])
        
        # 1. Liens de navigation détectés par Screaming Frog
        navigation_origins = ['navigation', 'en-tête', 'pied de page', 'header', 'footer', 'nav', 'menu']
        if any(x in origin for x in navigation_origins):
            return True
        
        # 2. Type de lien explicite (si disponible)
        if link_type in ['navigation', 'menu', 'footer', 'header', 'breadcrumb']:
            return True
        
        # 3. Patterns d'ancres mécaniques (utilise la config)
        default_mechanical_anchors = [
            r'^(accueil|home|menu|navigation)$',
            r'^(suivant|précédent|next|previous|page \d+)$',
            r'^(lire la suite|en savoir plus|voir plus|read more|more)$',
            r'^(contact|à propos|mentions légales|cgv|politique|privacy)$',
            r'^\d+$',  # Seulement des chiffres
            r'^(cliquez ici|cliquer ici|ici|click here|here)$',
            r'^(retour|back|retour accueil)$',
            r'^(passer au contenu|skip to content)$',
            r'^(voir tout|see all|view all)$',
            r'^(\+|\-|\>|\<|\»|\«)$',  # Symboles seuls
            r'^$'  # Ancres vides
        ]
        
        patterns_to_use = mechanical_patterns if mechanical_patterns else default_mechanical_anchors
        
        for pattern in patterns_to_use:
            if re.search(pattern, anchor, re.IGNORECASE):
                return True
        
        # 4. Détection avancée par position/contexte XPath
        mechanical_xpath_patterns = [
            r'(header|footer|nav|navigation|menu)',
            r'(breadcrumb|pagination|pager)',
            r'(sidebar|widget|aside)',
            r'(social|share|partage)',
            r'(tag|category|categorie)',
            r'(related|connexe|similaire)',
            r'role=["\']?(navigation|menu|banner|contentinfo)["\']?'
        ]
        
        for pattern in mechanical_xpath_patterns:
            if re.search(pattern, xpath, re.IGNORECASE):
                return True
        
        # 5. Détection par sélecteurs CSS (si disponible dans xpath)
        default_selectors = ['.menu', '.nav', '.header', '.footer', '.breadcrumb', '.pagination', '.sidebar']
        selectors_to_use = mechanical_selectors if mechanical_selectors else default_selectors
        
        for selector in selectors_to_use:
            if selector.replace('.', '') in xpath or selector in xpath:
                return True
        
        # 6. Ancres très courtes ou non descriptives
        if len(anchor.strip()) <= 2 and anchor.strip() not in ['tv', 'pc', 'seo', 'api', 'faq']:
            return True
        
        # 7. Détection d'URL complètes comme ancres (souvent mécaniques)
        if anchor.startswith(('http://', 'https://', 'www.')):
            return True
            
        return False

    def analyze_csv(self, csv_path, website_url=None):
        """Analyse un fichier CSV avec gestion d'erreur complète"""
        print(f"\n📊 ANALYSE DU FICHIER CSV")
        print("="*50)
        
        try:
            # Charger le CSV
            rows, fieldnames = self.load_csv_file(csv_path)
            if not rows:
                print("❌ Impossible de continuer sans données")
                return None
            
            # Détecter l'URL du site si pas fournie
            if not website_url and rows:
                try:
                    first_source = rows[0].get('Source', '') or rows[0].get('source', '') or rows[0].get('URL', '')
                    if first_source:
                        parsed = urlparse(first_source)
                        if parsed.scheme and parsed.netloc:
                            website_url = f"{parsed.scheme}://{parsed.netloc}/"
                        else:
                            print("⚠️  URL du site non détectée automatiquement")
                except Exception as e:
                    print(f"⚠️  Erreur lors de la détection de l'URL: {e}")
            
            if not website_url:
                print("⚠️  URL du site manquante - certaines analyses peuvent être limitées")
            else:
                print(f"🌐 Site analysé: {website_url}")
            
            # Identifier les colonnes importantes
            column_mapping = self.identify_columns(fieldnames)
            if not column_mapping['source'] or not column_mapping['dest']:
                print("❌ Colonnes Source/Destination non trouvées")
                print(f"📋 Colonnes disponibles: {', '.join(fieldnames)}")
                return None
            
            print(f"📋 Colonnes utilisées:")
            print(f"  - Source: {column_mapping['source']}")
            print(f"  - Destination: {column_mapping['dest']}")
            print(f"  - Ancre: {column_mapping['anchor'] or 'Non trouvée'}")
            
            # Analyser les liens
            internal_links = []
            external_links = []
            mechanical_count = 0
            editorial_count = 0
            error_count = 0
            
            for i, row in enumerate(rows):
                try:
                    source = row.get(column_mapping['source'], '').strip()
                    destination = row.get(column_mapping['dest'], '').strip()
                    
                    # Valider les URLs
                    if not source or not destination:
                        error_count += 1
                        continue
                    
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
                        
                except Exception as e:
                    error_count += 1
                    if error_count <= 5:  # Afficher seulement les 5 premières erreurs
                        print(f"⚠️  Erreur ligne {i+2}: {e}")
            
            if error_count > 5:
                print(f"⚠️  ... et {error_count - 5} autres erreurs ignorées")
            
            print(f"\n📊 Résultats:")
            print(f"  📈 Liens totaux: {len(rows):,}")
            print(f"  🏠 Liens internes: {len(internal_links):,}")
            print(f"  🌍 Liens externes: {len(external_links):,}")
            print(f"  🔧 Liens mécaniques: {mechanical_count:,}")
            print(f"  ✍️  Liens éditoriaux: {editorial_count:,}")
            
            if error_count > 0:
                print(f"  ⚠️  Erreurs ignorées: {error_count:,}")
            
            if len(internal_links) > 0:
                ratio = (editorial_count/len(internal_links)*100)
                print(f"  📊 Ratio éditorial: {ratio:.1f}%")
            
            # Analyser les patterns
            analysis = self.analyze_linking_patterns(internal_links, website_url)
            
            # Ajouter analyse de qualité des liens éditoriaux
            quality_analysis = self.analyze_editorial_quality(internal_links, analysis['stats'])
            analysis.update(quality_analysis)
            
            # Générer le rapport
            report_file = self.generate_html_report(analysis, website_url, csv_path)
            
            print(f"\n✅ ANALYSE TERMINÉE")
            print("="*50)
            print(f"📄 Rapport HTML: {report_file}")
            print(f"🚫 Pages orphelines: {len(analysis['orphan_pages'])}")
            
            return report_file
            
        except Exception as e:
            print(f"❌ Erreur critique lors de l'analyse: {e}")
            print("💡 Vérifiez que le fichier CSV est valide et accessible")
            return None

    def identify_columns(self, fieldnames):
        """Identifie les colonnes importantes dans le CSV"""
        mapping = {
            'source': None,
            'dest': None,
            'anchor': None,
            'origin': None,
            'xpath': None
        }
        
        for field in fieldnames:
            field_lower = field.lower().strip()
            
            # Source
            if 'source' in field_lower and not mapping['source']:
                mapping['source'] = field
            
            # Destination
            elif any(term in field_lower for term in ['destination', 'target', 'dest']) and not mapping['dest']:
                mapping['dest'] = field
            
            # Ancre
            elif any(term in field_lower for term in ['anchor', 'ancrage', 'link text', 'text']) and not mapping['anchor']:
                mapping['anchor'] = field
            
            # Origine
            elif any(term in field_lower for term in ['origin', 'origine', 'type']) and not mapping['origin']:
                mapping['origin'] = field
            
            # XPath
            elif any(term in field_lower for term in ['xpath', 'chemin', 'path']) and not mapping['xpath']:
                mapping['xpath'] = field
        
        return mapping

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
            'over_optimized_anchors': {anchor: count for anchor, count in anchor_counter.items() if count > self.config.get('analysis_thresholds', {}).get('max_anchor_repetition', 5)},
            'orphan_pages': list(orphan_pages),
            'stats': {
                'total_pages': len(all_pages),
                'total_internal_links': len(internal_links),
                'editorial_links': len(editorial_links),
                'mechanical_links': len(internal_links) - len(editorial_links),
                'avg_editorial_per_page': len(editorial_links) / len(all_pages) if len(all_pages) > 0 else 0,
                'editorial_ratio': (len(editorial_links) / len(internal_links) * 100) if len(internal_links) > 0 else 0
            }
        }

    def analyze_editorial_quality(self, internal_links, stats):
        """Analyse la qualité des liens éditoriaux"""
        editorial_links = [link for link in internal_links if not link.get('is_mechanical', False)]
        
        # Trouver les colonnes
        anchor_col = dest_col = None
        if editorial_links:
            for col in editorial_links[0].keys():
                col_clean = col.lower().strip('\ufeff"')
                if 'anchor' in col_clean or 'ancrage' in col_clean:
                    anchor_col = col
                elif 'destination' in col_clean:
                    dest_col = col
        
        # Analyser la qualité des ancres
        anchor_quality = {
            'too_short': [],
            'too_long': [],
            'good_quality': [],
            'keyword_stuffed': [],
            'url_anchors': []
        }
        
        semantic_variations = {}  # Grouper les variations sémantiques
        
        for link in editorial_links:
            anchor = link.get(anchor_col, '').strip() if anchor_col else ''
            dest = link.get(dest_col, '') if dest_col else ''
            
            if not anchor:
                continue
                
            # Analyser la longueur
            word_count = len(anchor.split())
            if word_count == 1 and len(anchor) < 4:
                anchor_quality['too_short'].append({'anchor': anchor, 'dest': dest})
            elif word_count > 8:
                anchor_quality['too_long'].append({'anchor': anchor, 'dest': dest})
            elif 2 <= word_count <= 6:
                anchor_quality['good_quality'].append({'anchor': anchor, 'dest': dest})
            
            # Détecter le keyword stuffing (répétition excessive de mots-clés)
            words = anchor.lower().split()
            word_freq = {}
            for word in words:
                if len(word) > 3:  # Ignorer les mots courts
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            if any(freq > 2 for freq in word_freq.values()):
                anchor_quality['keyword_stuffed'].append({'anchor': anchor, 'dest': dest})
            
            # Détecter les ancres URL
            if any(anchor.startswith(prefix) for prefix in ['http://', 'https://', 'www.']):
                anchor_quality['url_anchors'].append({'anchor': anchor, 'dest': dest})
        
        # Analyse de la distribution thématique
        thematic_distribution = self.analyze_thematic_distribution(editorial_links, anchor_col, dest_col)
        
        return {
            'anchor_quality': anchor_quality,
            'thematic_distribution': thematic_distribution,
            'editorial_quality_score': self.calculate_editorial_score(
                anchor_quality, 
                len(editorial_links),
                stats['editorial_ratio'],
                stats['total_internal_links']
            )
        }
    
    def analyze_thematic_distribution(self, editorial_links, anchor_col, dest_col):
        """Analyse la distribution thématique des liens"""
        # Extraire les mots-clés des ancres et URLs
        anchor_keywords = Counter()
        dest_categories = Counter()
        
        for link in editorial_links:
            anchor = link.get(anchor_col, '').strip().lower() if anchor_col else ''
            dest = link.get(dest_col, '') if dest_col else ''
            
            # Analyser les mots-clés des ancres
            words = re.findall(r'\b\w{4,}\b', anchor)  # Mots de 4 lettres+
            for word in words:
                anchor_keywords[word] += 1
            
            # Catégoriser les destinations par type de page
            if dest:
                if any(term in dest.lower() for term in ['blog', 'article', 'actualit']):
                    dest_categories['Blog/Articles'] += 1
                elif any(term in dest.lower() for term in ['produit', 'product', 'service']):
                    dest_categories['Produits/Services'] += 1
                elif any(term in dest.lower() for term in ['contact', 'about', 'propos']):
                    dest_categories['Pages institutionnelles'] += 1
                else:
                    dest_categories['Autres'] += 1
        
        return {
            'top_anchor_keywords': dict(anchor_keywords.most_common(15)),
            'destination_categories': dict(dest_categories)
        }
    
    def calculate_editorial_score(self, anchor_quality, total_editorial, editorial_ratio, total_internal_links):
        """Calcule un score de qualité éditorial (0-100)"""
        if total_editorial == 0:
            return 0
        
        # Score de base en fonction du ratio éditorial (poids le plus important)
        # Ratio idéal : 70-80%, acceptable : 50-70%, faible < 50%
        if editorial_ratio >= 70:
            base_score = 90
        elif editorial_ratio >= 50:
            base_score = 70
        elif editorial_ratio >= 30:
            base_score = 50
        elif editorial_ratio >= 15:
            base_score = 30
        else:
            base_score = 10  # Très faible ratio éditorial
        
        # Pénalités sur la qualité des ancres (proportionnelles au score de base)
        penalty_factor = base_score / 100  # Réduire les pénalités si le score de base est déjà bas
        
        too_short_penalty = (len(anchor_quality['too_short']) / total_editorial) * 15 * penalty_factor
        too_long_penalty = (len(anchor_quality['too_long']) / total_editorial) * 10 * penalty_factor
        keyword_stuffed_penalty = (len(anchor_quality['keyword_stuffed']) / total_editorial) * 20 * penalty_factor
        url_anchors_penalty = (len(anchor_quality['url_anchors']) / total_editorial) * 25 * penalty_factor
        
        # Bonus limité pour les bonnes ancres (max +5 points)
        good_quality_ratio = len(anchor_quality['good_quality']) / total_editorial
        good_quality_bonus = min(5, good_quality_ratio * 10)
        
        # Pénalité supplémentaire si très peu de liens éditoriaux au total
        if total_editorial < 50:
            volume_penalty = 10
        elif total_editorial < 20:
            volume_penalty = 20
        else:
            volume_penalty = 0
        
        final_score = base_score - too_short_penalty - too_long_penalty - keyword_stuffed_penalty - url_anchors_penalty + good_quality_bonus - volume_penalty
        
        # S'assurer que le score reste entre 0 et 100
        final_score = max(0, min(100, final_score))
        
        return round(final_score, 1)

    def generate_html_report(self, analysis, website_url, source_file):
        """Génère le rapport HTML"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"{self.config['export_path']}audit_report_{timestamp}.html"
        
        os.makedirs(self.config['export_path'], exist_ok=True)
        
        stats = analysis['stats']
        
        # Score de qualité
        quality_score = analysis.get('editorial_quality_score', 0)
        score_color = '#28a745' if quality_score >= 80 else '#ffc107' if quality_score >= 60 else '#dc3545'
        
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
                .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
                .stat-card {{ background: white; padding: 20px; border-radius: 8px; border-left: 4px solid #007bff; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .stat-card.quality {{ border-left-color: {score_color}; }}
                .stat-number {{ font-size: 2.5em; font-weight: bold; color: #007bff; }}
                .stat-number.quality {{ color: {score_color}; }}
                .stat-label {{ color: #6c757d; font-size: 0.9em; }}
                .warning {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .success {{ background: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .danger {{ background: #f8d7da; border-left: 4px solid #dc3545; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .section {{ background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #e1e5e9; }}
                th {{ background-color: #f8f9fa; font-weight: 600; }}
                tr:hover {{ background-color: #f8f9fa; }}
                .url {{ word-break: break-all; max-width: 500px; font-family: monospace; font-size: 0.85em; }}
                .recommendations {{ background: #e3f2fd; padding: 20px; border-radius: 8px; border-left: 4px solid #2196f3; }}
                ul.orphan-list {{ max-height: 300px; overflow-y: auto; background: #f8f9fa; padding: 15px; border-radius: 5px; }}
                .progress-bar {{ width: 100%; height: 20px; background: #e9ecef; border-radius: 10px; overflow: hidden; margin: 10px 0; }}
                .progress-fill {{ height: 100%; background: linear-gradient(90deg, #dc3545 0%, #ffc107 50%, #28a745 100%); transition: width 0.3s; }}
                .keyword-cloud {{ display: flex; flex-wrap: wrap; gap: 10px; margin: 15px 0; }}
                .keyword-tag {{ background: #e9ecef; padding: 5px 10px; border-radius: 15px; font-size: 0.85em; }}
                .chart-container {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0; }}
                .chart {{ background: white; padding: 15px; border-radius: 8px; text-align: center; }}
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
                    <strong>⚙️  Script:</strong> Audit automatisé de maillage interne v2.0
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
                        <div class="stat-number">{stats['editorial_ratio']:.1f}%</div>
                        <div class="stat-label">Ratio éditorial</div>
                    </div>
                    <div class="stat-card quality">
                        <div class="stat-number quality">{quality_score}/100</div>
                        <div class="stat-label">Score qualité</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{stats['avg_editorial_per_page']:.1f}</div>
                        <div class="stat-label">Liens éditoriaux/page</div>
                    </div>
                </div>
                
                <div class="section">
                    <h2>📊 Score de Qualité Éditorial</h2>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {quality_score}%"></div>
                    </div>
                    <p><strong>{quality_score}/100</strong> - """
        
        if quality_score >= 80:
            html_content += """<span style="color: #28a745;">Excellente qualité</span></p>"""
        elif quality_score >= 60:
            html_content += """<span style="color: #ffc107;">Qualité moyenne</span></p>"""
        else:
            html_content += """<span style="color: #dc3545;">Qualité à améliorer</span></p>"""
        
        html_content += "</div>"
        
        # Qualité des ancres
        if 'anchor_quality' in analysis:
            anchor_quality = analysis['anchor_quality']
            html_content += f"""
            <div class="section">
                <h2>🏷️ Qualité des Ancres Éditoriales</h2>
                <div class="chart-container">
                    <div class="chart">
                        <h4>Répartition</h4>
                        <p>✅ Bonne qualité: <strong>{len(anchor_quality.get('good_quality', []))}</strong></p>
                        <p>⚠️ Trop courtes: <strong>{len(anchor_quality.get('too_short', []))}</strong></p>
                        <p>⚠️ Trop longues: <strong>{len(anchor_quality.get('too_long', []))}</strong></p>
                        <p>🚫 Sur-optimisées: <strong>{len(anchor_quality.get('keyword_stuffed', []))}</strong></p>
                    </div>
                </div>
            """
            
            if anchor_quality.get('too_short'):
                html_content += """
                <div class="warning">
                    <h4>Ancres trop courtes (exemples)</h4>
                    <ul>
                """
                for item in anchor_quality['too_short'][:5]:
                    html_content += f"<li><strong>'{item['anchor']}'</strong> → {item['dest']}</li>"
                html_content += "</ul></div>"
            
            if anchor_quality.get('keyword_stuffed'):
                html_content += """
                <div class="danger">
                    <h4>Ancres potentiellement sur-optimisées</h4>
                    <ul>
                """
                for item in anchor_quality['keyword_stuffed'][:5]:
                    html_content += f"<li><strong>'{item['anchor']}'</strong> → {item['dest']}</li>"
                html_content += "</ul></div>"
            
            html_content += "</div>"
        
        # Distribution thématique
        if 'thematic_distribution' in analysis:
            thematic = analysis['thematic_distribution']
            html_content += """
            <div class="section">
                <h2>🎯 Distribution Thématique</h2>
            """
            
            if thematic.get('top_anchor_keywords'):
                html_content += """
                <h4>Mots-clés principaux dans les ancres</h4>
                <div class="keyword-cloud">
                """
                for keyword, count in list(thematic['top_anchor_keywords'].items())[:15]:
                    html_content += f"""<span class="keyword-tag">{keyword} ({count})</span>"""
                html_content += "</div>"
            
            if thematic.get('destination_categories'):
                html_content += """
                <h4>Types de pages liées</h4>
                <table>
                    <tr><th>Catégorie</th><th>Nombre de liens</th></tr>
                """
                for category, count in thematic['destination_categories'].items():
                    html_content += f"<tr><td>{category}</td><td><strong>{count}</strong></td></tr>"
                html_content += "</table>"
            
            html_content += "</div>"
        
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
        
        # Recommandations personnalisées
        html_content += f"""
            <div class="recommendations">
                <h2>💡 Recommandations Prioritaires</h2>
                <ul>
        """
        
        # Recommandations dynamiques basées sur l'analyse
        if len(analysis['orphan_pages']) > 0:
            html_content += f"<li><strong>Pages orphelines ({len(analysis['orphan_pages'])}):</strong> Créer des liens éditoriaux contextuels depuis vos contenus les plus populaires</li>"
        
        if stats['editorial_ratio'] < 50:
            html_content += f"<li><strong>Ratio éditorial faible ({stats['editorial_ratio']:.1f}%):</strong> Augmenter les liens éditoriaux dans vos contenus</li>"
        
        if analysis.get('anchor_quality', {}).get('too_short'):
            html_content += f"<li><strong>Ancres trop courtes:</strong> Améliorer {len(analysis['anchor_quality']['too_short'])} ancres avec des descriptions plus précises</li>"
        
        if stats['avg_editorial_per_page'] < 2:
            html_content += f"<li><strong>Maillage insuffisant:</strong> Viser 2-3 liens éditoriaux minimum par page (actuellement {stats['avg_editorial_per_page']:.1f})</li>"
        
        html_content += """
                    <li><strong>Ancres naturelles:</strong> Utiliser des ancres descriptives qui décrivent le contenu de destination</li>
                    <li><strong>Contexte éditorial:</strong> Intégrer les liens dans le corps du texte plutôt qu'en navigation</li>
                    <li><strong>Diversité thématique:</strong> Varier les ancres pour éviter la sur-optimisation</li>
                </ul>
            </div>
        </div>
        </body>
        </html>
        """
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Générer aussi un export CSV des recommandations
        csv_export_file = self.generate_csv_export(analysis, website_url, source_file)
        
        return report_file

    def generate_csv_export(self, analysis, website_url, source_file):
        """Génère un export CSV des recommandations"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_file = f"{self.config['export_path']}recommendations_{timestamp}.csv"
        
        try:
            with open(csv_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                
                # En-têtes
                writer.writerow([
                    'Type', 'Priorité', 'URL', 'Problème', 'Recommandation', 'Détails'
                ])
                
                # Pages orphelines
                for orphan in analysis.get('orphan_pages', []):
                    writer.writerow([
                        'Page orpheline',
                        'Haute',
                        orphan,
                        'Aucun lien entrant éditorial',
                        'Créer des liens éditoriaux contextuels',
                        'Page sans maillage interne éditorial'
                    ])
                
                # Ancres problématiques
                if 'anchor_quality' in analysis:
                    anchor_quality = analysis['anchor_quality']
                    
                    # Ancres trop courtes
                    for item in anchor_quality.get('too_short', []):
                        writer.writerow([
                            'Ancre défaillante',
                            'Moyenne',
                            item['dest'],
                            f"Ancre trop courte: '{item['anchor']}'",
                            'Utiliser une ancre plus descriptive',
                            f"Ancre actuelle: '{item['anchor']}'"
                        ])
                    
                    # Ancres sur-optimisées
                    for item in anchor_quality.get('keyword_stuffed', []):
                        writer.writerow([
                            'Ancre sur-optimisée',
                            'Haute',
                            item['dest'],
                            f"Ancre potentiellement sur-optimisée: '{item['anchor']}'",
                            'Diversifier avec des expressions naturelles',
                            'Risque de pénalité SEO'
                        ])
                    
                    # Ancres URL
                    for item in anchor_quality.get('url_anchors', []):
                        writer.writerow([
                            'Ancre non-optimisée',
                            'Moyenne',
                            item['dest'],
                            f"URL utilisée comme ancre: '{item['anchor']}'",
                            'Remplacer par une ancre descriptive',
                            'Les URLs ne sont pas des ancres optimales'
                        ])
                
                # Ancres répétitives
                for anchor, count in analysis.get('over_optimized_anchors', {}).items():
                    writer.writerow([
                        'Ancre répétitive',
                        'Moyenne',
                        'Multiple',
                        f"Ancre utilisée {count} fois: '{anchor}'",
                        'Diversifier les variantes sémantiques',
                        f'Répétition excessive ({count} occurrences)'
                    ])
                
                # Recommandations générales basées sur les stats
                stats = analysis.get('stats', {})
                
                if stats.get('editorial_ratio', 0) < 50:
                    writer.writerow([
                        'Stratégie globale',
                        'Haute',
                        website_url or 'Site entier',
                        f"Ratio éditorial faible ({stats['editorial_ratio']:.1f}%)",
                        'Augmenter les liens éditoriaux dans les contenus',
                        'Moins de 50% de liens éditoriaux'
                    ])
                
                if stats.get('avg_editorial_per_page', 0) < 2:
                    writer.writerow([
                        'Densité de maillage',
                        'Moyenne',
                        website_url or 'Site entier',
                        f"Maillage insuffisant ({stats['avg_editorial_per_page']:.1f} liens/page)",
                        'Viser 2-3 liens éditoriaux minimum par page',
                        'Maillage interne sous-optimal'
                    ])
            
            print(f"📊 Export CSV généré: {csv_file}")
            return csv_file
            
        except Exception as e:
            print(f"⚠️  Erreur lors de la génération du CSV: {e}")
            return None

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