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
import time
from datetime import datetime
from collections import Counter

# Import de l'analyseur sémantique
try:
    from ext_analyseur_semantique import get_semantic_analyzer
    SEMANTIC_ANALYSIS_AVAILABLE = True
except ImportError:
    SEMANTIC_ANALYSIS_AVAILABLE = False
from urllib.parse import urlparse
import glob

class CompleteLinkAuditor:
    def __init__(self, config_file='ext_configuration_audit.json'):
        self.config = self.load_config(config_file)
        
    def load_config(self, config_file):
        """Charge la configuration"""
        import platform
        import os

        # Détecter le système d'exploitation pour le chemin par défaut
        system = platform.system()
        if system == "Windows":
            possible_paths = [
                "C:\\Program Files\\Screaming Frog SEO Spider\\ScreamingFrogSEOSpiderCli.exe",
                "C:\\Program Files (x86)\\Screaming Frog SEO Spider\\ScreamingFrogSEOSpiderCli.exe",
                "C:\\Screaming Frog\\ScreamingFrogSEOSpiderCli.exe"
            ]
            default_sf_path = next((path for path in possible_paths if os.path.exists(path)), possible_paths[0])
        elif system == "Darwin":  # macOS
            possible_paths = [
                "/Applications/Screaming Frog SEO Spider.app/Contents/MacOS/ScreamingFrogSEOSpiderCli",
                "/usr/local/bin/screamingfrogseospider",
                "/opt/homebrew/bin/screamingfrogseospider"
            ]
            default_sf_path = next((path for path in possible_paths if os.path.exists(path)), possible_paths[0])
        else:  # Linux et autres
            possible_paths = [
                "/usr/bin/screamingfrogseospider",
                "/usr/local/bin/screamingfrogseospider",
                "/opt/screamingfrog/screamingfrogseospider"
            ]
            default_sf_path = next((path for path in possible_paths if os.path.exists(path)), possible_paths[0])

        default_config = {
            "screaming_frog_path": default_sf_path,
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

    def create_screaming_frog_config(self, user_agent=None, attempt_number=1):
        """Crée un fichier de configuration temporaire pour Screaming Frog"""
        import tempfile
        import json as json_module

        # Liste de user-agents pour différentes tentatives
        fallback_user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
            "Screaming Frog SEO Spider/18.0"  # Dernier recours avec l'agent par défaut
        ]

        if user_agent is None:
            # Utiliser l'agent de la config ou un agent de fallback
            if attempt_number == 1:
                user_agent = self.config.get('crawl_settings', {}).get('user_agent', fallback_user_agents[0])
            else:
                # Essayer différents agents selon le nombre de tentatives
                agent_index = min(attempt_number - 1, len(fallback_user_agents) - 1)
                user_agent = fallback_user_agents[agent_index]

        print(f"🔧 Tentative {attempt_number}: User-Agent = {user_agent}")

        # Configuration Screaming Frog en format JSON
        config_data = {
            "spider": {
                "general": {
                    "userAgent": {
                        "userAgent": user_agent,
                        "robotsUserAgent": "Googlebot"  # Pour suivre les directives robots.txt de Googlebot
                    },
                    "crawlDelay": self.config.get('crawl_settings', {}).get('crawl_delay', 0.5),
                    "respectRobots": self.config.get('crawl_settings', {}).get('respect_robots', True),
                    "maxCrawlDepth": self.config.get('crawl_settings', {}).get('crawl_depth', 10)
                },
                "limits": {
                    "maxPages": 10000  # Limite par défaut pour éviter des crawls trop longs
                }
            }
        }

        # Créer un fichier temporaire pour la configuration
        temp_config = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', prefix='sf_config_')
        try:
            json_module.dump(config_data, temp_config, indent=2)
            temp_config.flush()
            print(f"📁 Config temporaire créée: {temp_config.name}")
            return temp_config.name
        except Exception as e:
            print(f"⚠️  Erreur lors de la création de la config: {e}")
            return None
        finally:
            temp_config.close()

    def run_new_crawl(self, website_url, url_filter=None, max_attempts=3):
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
            print("2. Mettre à jour le chemin dans ext_configuration_audit.json")
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
        
        # Utiliser le chemin absolu pour le dossier d'export
        output_folder = os.path.abspath(self.config['export_path'])
        print(f"🔍 Chemin d'export utilisé: '{output_folder}'")
        
        # Vérifier si les fonctionnalités sémantiques sont disponibles
        semantic_exports = ""
        if self.config.get('enable_semantic_analysis', False):
            semantic_exports = ",Embeddings:All,Content Clusters:Similar Pages"
            print("🧠 Analyse sémantique activée (nécessite SF v22+ et API AI configurée)")

        # Essayer différentes configurations en cas d'échec
        for attempt in range(1, max_attempts + 1):
            print(f"\n🔄 Tentative {attempt}/{max_attempts}")

            # Créer une configuration temporaire avec user-agent personnalisé
            config_file = self.create_screaming_frog_config(attempt_number=attempt)
            if not config_file:
                continue

            crawl_command = [
                sf_path,
                "--headless",
                "--crawl", website_url,
                "--config", config_file,
                "--output-folder", output_folder,
                "--export-format", "csv",
                "--bulk-export", f"All Outlinks,All Inlinks{semantic_exports}"
            ]

            print(f"🔧 Commande complète: {' '.join(crawl_command[:6])} [...]")
            print(f"🔧 Config utilisée: {config_file}")

            try:
                print("⏳ Crawl en cours...")
                print("💡 Monitoring en temps réel :")

                # Lancer le processus sans capturer la sortie pour voir le feedback
                process = subprocess.Popen(
                    crawl_command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=False,  # Mode binaire pour gérer l'encodage manuellement
                    bufsize=1
                )

                # Afficher la sortie en temps réel
                output_lines = []
                start_time = time.time()
                last_update = start_time
                initial_files = set(os.listdir(output_folder)) if os.path.exists(output_folder) else set()

                print("📝 Logs Screaming Frog:")
                print("-" * 50)

                while True:
                    raw_line = process.stdout.readline()
                    if not raw_line and process.poll() is not None:
                        break

                    # Gérer l'encodage avec plusieurs tentatives
                    line = ""
                    for encoding in ['utf-8', 'latin-1', 'cp1252', 'ascii']:
                        try:
                            line = raw_line.decode(encoding).strip()
                            break
                        except UnicodeDecodeError:
                            continue

                    if line:
                        output_lines.append(line)
                        # Afficher seulement les lignes importantes
                        if any(keyword in line.lower() for keyword in [
                            'crawling', 'found', 'discovered', 'completed', 'error',
                            'finished', 'exported', 'links', 'pages', 'progress', 'update'
                        ]):
                            print(f"📋 {line}")

                    # Afficher un indicateur de progression toutes les 30 secondes
                    current_time = time.time()
                    if current_time - last_update > 30:
                        elapsed = int(current_time - start_time)

                        # Vérifier les nouveaux fichiers créés
                        if os.path.exists(output_folder):
                            current_files = set(os.listdir(output_folder))
                            new_files = current_files - initial_files
                            if new_files:
                                print(f"📁 Nouveaux fichiers: {', '.join(new_files)}")

                        print(f"⏱️  Temps écoulé: {elapsed//60}m {elapsed%60}s - Crawl en cours...")
                        last_update = current_time

                # Attendre la fin du processus
                return_code = process.wait()
                total_time = int(time.time() - start_time)

                print("-" * 50)
                print(f"⏱️  Durée totale: {total_time//60}m {total_time%60}s")

                # Créer un objet result compatible
                class MockResult:
                    def __init__(self, returncode, stdout_lines):
                        self.returncode = returncode
                        self.stdout = '\n'.join(stdout_lines)
                        self.stderr = ''

                result = MockResult(return_code, output_lines)

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
                        # Nettoyer le fichier de config temporaire
                        if config_file and os.path.exists(config_file):
                            os.unlink(config_file)
                        return latest_file
                    else:
                        print("⚠️  Fichier CSV des liens non trouvé")
                        print("💡 Le crawl a peut-être échoué ou aucun lien trouvé")
                        # Nettoyer le fichier de config temporaire
                        if config_file and os.path.exists(config_file):
                            os.unlink(config_file)
                        return None
                else:
                    print(f"❌ Erreur lors du crawl (code: {result.returncode})")

                    # Analyser les logs pour identifier les problèmes
                    output_text = result.stdout.lower()

                    print(f"\n🔍 DEBUG - Code de retour: {result.returncode}")
                    print(f"🔍 DEBUG - Taille de sortie: {len(result.stdout)} caractères")
                
                # Rechercher des indices dans les logs
                if "403" in output_text or "forbidden" in output_text:
                    print("🚫 Erreur 403 Forbidden détectée")
                    if attempt < max_attempts:
                        print(f"🔄 Tentative avec un autre User-Agent ({attempt + 1}/{max_attempts})")
                        # Nettoyer le fichier de config temporaire
                        if config_file and os.path.exists(config_file):
                            os.unlink(config_file)
                        continue  # Passer à la tentative suivante
                    else:
                        print("❌ Toutes les tentatives ont échoué")
                        print("💡 Solutions possibles :")
                        print("   - Le site bloque tous les types de crawlers/bots")
                        print("   - Vérifier si le site nécessite une authentification")
                        print("   - Essayer avec une limite de vitesse plus lente")
                        print("   - Contacter l'administrateur du site")
                elif "404" in output_text or "not found" in output_text:
                    print("🔍 Erreur 404 - URL non trouvée")
                    print("💡 Vérifiez que l'URL de départ existe bien")
                    # Cette erreur ne justifie pas une nouvelle tentative
                    break
                    
                    # Test rapide de connectivité depuis WSL
                    try:
                        test_result = subprocess.run(['curl', '-I', '-s', '--max-time', '10', website_url], 
                                                   capture_output=True, text=True, timeout=15)
                        if test_result.returncode == 0 and '200' in test_result.stdout:
                            print("✅ L'URL est accessible depuis WSL - problème avec Screaming Frog")
                            print("💡 Essayez de redémarrer Screaming Frog ou vérifiez les paramètres réseau")
                        else:
                            print("❌ L'URL n'est pas accessible depuis WSL non plus")
                    except Exception as e:
                        print(f"⚠️  Impossible de tester la connectivité: {e}")
                elif "timeout" in output_text or "connection" in output_text:
                    print("⏰ Problème de connexion/timeout")
                    if attempt < max_attempts:
                        print(f"🔄 Nouvelle tentative avec délai plus long ({attempt + 1}/{max_attempts})")
                        if config_file and os.path.exists(config_file):
                            os.unlink(config_file)
                        time.sleep(5)  # Attendre un peu avant la nouvelle tentative
                        continue
                    else:
                        print("💡 Le site met trop de temps à répondre de façon répétée")
                elif "license" in output_text:
                    print("📄 Problème de licence Screaming Frog")
                    print("💡 Vérifiez votre licence ou utilisez la version gratuite")
                    break  # Pas de tentative supplémentaire pour un problème de licence
                elif "memory" in output_text or "heap" in output_text:
                    print("💾 Problème de mémoire")
                    print("💡 Augmentez la mémoire allouée à Screaming Frog")
                    break  # Pas de tentative supplémentaire pour un problème de mémoire
                elif "rate limit" in output_text or "too many requests" in output_text:
                    print("🚦 Limite de taux détectée")
                    if attempt < max_attempts:
                        wait_time = attempt * 10  # Attendre de plus en plus longtemps
                        print(f"🔄 Attente de {wait_time}s avant la tentative {attempt + 1}/{max_attempts}")
                        if config_file and os.path.exists(config_file):
                            os.unlink(config_file)
                        time.sleep(wait_time)
                        continue
                    else:
                        print("💡 Le site applique une limite de taux très stricte")
                elif "blocked" in output_text or "banned" in output_text:
                    print("🚫 Site bloquant activement les requêtes")
                    if attempt < max_attempts:
                        print(f"🔄 Tentative avec un User-Agent différent ({attempt + 1}/{max_attempts})")
                        if config_file and os.path.exists(config_file):
                            os.unlink(config_file)
                        continue
                    else:
                        print("💡 Le site bloque systématiquement les tentatives d'accès")
                
                # Afficher une partie des logs pour diagnostic
                if result.stdout:
                    print(f"\n📤 Derniers logs (500 caractères):")
                    print(result.stdout[-500:])
                
                # Vérifier si des fichiers ont quand même été créés
                if os.path.exists(output_folder):
                    current_files = set(os.listdir(output_folder))
                    new_files = current_files - initial_files
                    if new_files:
                        print(f"\n📁 Fichiers créés malgré l'erreur: {', '.join(new_files)}")
                        # Essayer de continuer avec les fichiers partiels
                        csv_files = [f for f in new_files if f.endswith('.csv') and ('outlink' in f.lower() or 'liens_sortants' in f.lower())]
                        if csv_files:
                            latest_file = f"{output_folder}/{csv_files[0]}"
                            print(f"⚠️  Tentative d'analyse du fichier partiel: {latest_file}")
                            return latest_file
                
                # Nettoyer le fichier de config temporaire
                if config_file and os.path.exists(config_file):
                    os.unlink(config_file)

            except subprocess.TimeoutExpired:
                print("⏰ Crawl interrompu (timeout après 1h)")
                print("💡 Le site est peut-être trop volumineux, essayez avec une limite de pages")
                # Nettoyer le fichier de config temporaire
                if config_file and os.path.exists(config_file):
                    os.unlink(config_file)
                if attempt < max_attempts:
                    print(f"🔄 Nouvelle tentative avec timeout ({attempt + 1}/{max_attempts})")
                    continue
                return None

            except FileNotFoundError:
                print(f"❌ Exécutable non trouvé: {sf_path}")
                print("💡 Vérifiez l'installation et le chemin de Screaming Frog")
                # Nettoyer le fichier de config temporaire
                if config_file and os.path.exists(config_file):
                    os.unlink(config_file)
                return None

            except Exception as e:
                print(f"❌ Erreur inattendue lors de la tentative {attempt}: {e}")
                # Nettoyer le fichier de config temporaire
                if config_file and os.path.exists(config_file):
                    os.unlink(config_file)
                if attempt < max_attempts:
                    print(f"🔄 Nouvelle tentative ({attempt + 1}/{max_attempts})")
                    continue
                return None

            # Si on arrive ici avec succès, nettoyer le fichier de config et retourner
            if config_file and os.path.exists(config_file):
                os.unlink(config_file)
            break  # Sortir de la boucle de retry en cas de succès

        # Si toutes les tentatives ont échoué
        print("❌ Toutes les tentatives de crawl ont échoué")
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

    def matches_url_filter(self, row, url_filter, column_mapping):
        """Vérifie si un lien correspond au filtre d'URL spécifié"""
        source_col = column_mapping.get('source')
        dest_col = column_mapping.get('dest')
        
        if not source_col or not dest_col:
            return True  # Si pas de colonnes, garder tout
        
        source = row.get(source_col, '').strip()
        dest = row.get(dest_col, '').strip()
        
        # Garder le lien si la source OU la destination correspondent au filtre
        source_matches = source.startswith(url_filter) if source else False
        dest_matches = dest.startswith(url_filter) if dest else False
        
        return source_matches or dest_matches

    def analyze_csv(self, csv_path, website_url=None, url_filter=None):
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
                
            # Identifier les colonnes importantes AVANT le filtrage
            column_mapping = self.identify_columns(fieldnames)
            if not column_mapping['source'] or not column_mapping['dest']:
                print("❌ Colonnes Source/Destination non trouvées")
                print(f"📋 Colonnes disponibles: {', '.join(fieldnames)}")
                return None
            
            if url_filter:
                print(f"🎯 Filtrage activé: {url_filter}")
                # Filtrer les lignes selon le préfixe d'URL
                original_count = len(rows)
                rows = [row for row in rows if self.matches_url_filter(row, url_filter, column_mapping)]
                filtered_count = len(rows)
                print(f"📊 Filtrage: {original_count:,} → {filtered_count:,} liens ({original_count-filtered_count:,} supprimés)")
                
                if filtered_count == 0:
                    print("❌ Aucun lien ne correspond au filtre spécifié")
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
            
            # Analyser la qualité du contenu si les fichiers sont disponibles
            content_analysis = self.analyze_content_quality(csv_path, website_url, url_filter)
            if content_analysis:
                analysis['content_quality'] = content_analysis
            
            # Analyser les clusters sémantiques si disponibles
            if self.config.get('semantic_analysis', {}).get('enable_semantic_analysis', False):
                semantic_analysis = self.analyze_semantic_clusters(csv_path, website_url, url_filter)
                if semantic_analysis:
                    analysis['semantic_clusters'] = semantic_analysis
            
            # Analyse sémantique avancée avec CamemBERT (automatique)
            if SEMANTIC_ANALYSIS_AVAILABLE:
                # Collecter les données de pages si disponibles
                page_data = {}
                if content_analysis and isinstance(content_analysis, dict):
                    # Essayer de collecter Title, H1, Meta descriptions depuis les analyses
                    page_data = self.collect_page_data_for_semantic(csv_path)
                
                # Filtrer pour ne garder que les liens éditoriaux
                editorial_links = [link for link in internal_links if not link.get('is_mechanical', False)]
                
                advanced_semantic = self.analyze_semantic_advanced(
                    editorial_links, 
                    column_mapping.get('anchor'), 
                    column_mapping.get('dest'),
                    page_data
                )
                if advanced_semantic:
                    analysis['advanced_semantic'] = advanced_semantic
            
            # Générer les données pour le graphique de réseau
            network_data = self.generate_network_data(internal_links, column_mapping)
            analysis['network_data'] = network_data
            
            # Générer le rapport
            report_file = self.generate_html_report(analysis, website_url, csv_path, url_filter)
            
            print(f"\n✅ ANALYSE TERMINÉE")
            print("="*50)
            print(f"📄 Rapport HTML: {report_file}")
            
            # Créer un lien cliquable pour le terminal
            import os
            absolute_path = os.path.abspath(report_file)
            clickable_link = f"file://{absolute_path}"
            print(f"🔗 Lien cliquable: {clickable_link}")
            
            print(f"🚫 Pages orphelines: {len(analysis['orphan_pages'])}")
            
            # Option pour ouvrir automatiquement
            try:
                import webbrowser
                print(f"\n💡 Ouverture automatique du rapport...")
                webbrowser.open(clickable_link)
                print(f"✅ Rapport ouvert dans votre navigateur par défaut")
            except Exception as e:
                print(f"⚠️  Impossible d'ouvrir automatiquement: {e}")
                print(f"💡 Ctrl+Click sur le lien ci-dessus pour l'ouvrir")
            
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
        """Analyse la distribution thématique des liens avec NLP avancé"""
        
        # Stop words français étendus
        french_stop_words = {
            'le', 'de', 'et', 'à', 'un', 'il', 'être', 'et', 'en', 'avoir', 'que', 'pour',
            'dans', 'ce', 'son', 'une', 'sur', 'avec', 'ne', 'se', 'pas', 'tout', 'plus',
            'par', 'grand', 'en', 'une', 'être', 'et', 'à', 'il', 'avoir', 'ne', 'je', 'son',
            'que', 'se', 'qui', 'ce', 'dans', 'en', 'du', 'elle', 'au', 'de', 'le', 'un',
            'nous', 'vous', 'ils', 'elles', 'leur', 'leurs', 'cette', 'ces', 'ses', 'nos',
            'vos', 'très', 'bien', 'encore', 'toujours', 'déjà', 'aussi', 'puis', 'donc',
            'ainsi', 'alors', 'après', 'avant', 'depuis', 'pendant', 'comme', 'quand',
            'comment', 'pourquoi', 'où', 'dont', 'laquelle', 'lequel', 'lesquels', 'desquels',
            'auquel', 'auxquels', 'duquel', 'desquelles', 'auxquelles', 'celle', 'celui',
            'ceux', 'celles', 'tout', 'tous', 'toute', 'toutes', 'autre', 'autres', 'même',
            'mêmes', 'tel', 'telle', 'tels', 'telles', 'quel', 'quelle', 'quels', 'quelles',
            'voir', 'savoir', 'faire', 'dire', 'aller', 'venir', 'pouvoir', 'vouloir',
            'devoir', 'falloir', 'prendre', 'donner', 'mettre', 'porter', 'tenir', 'venir',
            'partir', 'sortir', 'entrer', 'monter', 'descendre', 'passer', 'rester', 'devenir',
            'sembler', 'paraître', 'apparaître', 'disparaître', 'arriver', 'partir', 'naître',
            'mourir', 'vivre', 'exister', 'ici', 'là', 'ailleurs', 'partout', 'nulle', 'part',
            'quelque', 'part', 'jamais', 'toujours', 'souvent', 'parfois', 'quelquefois',
            'rarement', 'peu', 'beaucoup', 'trop', 'assez', 'tant', 'autant', 'si', 'aussi',
            'moins', 'davantage', 'plutôt', 'surtout', 'notamment', 'seulement', 'uniquement',
            'vraiment', 'certainement', 'probablement', 'peut', 'être', 'sans', 'doute',
            'évidemment', 'naturellement', 'heureusement', 'malheureusement', 'découvrir',
            'découvrez', 'voir', 'lire', 'consulter', 'cliquer', 'accéder', 'suivre', 'plus',
            'notre', 'votre', 'leur', 'cette', 'cette', 'ces', 'tous', 'toutes'
        }
        
        # Mots génériques supplémentaires à filtrer
        generic_words = {
            'page', 'site', 'web', 'internet', 'online', 'cliquez', 'ici', 'là', 'suivant',
            'précédent', 'retour', 'accueil', 'home', 'menu', 'navigation', 'lien', 'liens',
            'article', 'articles', 'actualité', 'actualités', 'news', 'blog', 'post',
            'plus', 'moins', 'tout', 'tous', 'toute', 'toutes', 'autre', 'autres'
        }
        
        # Combine stop words
        all_stop_words = french_stop_words.union(generic_words)
        
        # Extraire et analyser les ancres
        anchor_texts = []
        dest_categories = Counter()
        
        for link in editorial_links:
            anchor = link.get(anchor_col, '').strip().lower() if anchor_col else ''
            dest = link.get(dest_col, '') if dest_col else ''
            
            if anchor and len(anchor) > 2:
                anchor_texts.append(anchor)
            
            # Catégoriser les destinations par type de page
            if dest:
                if any(term in dest.lower() for term in ['blog', 'article', 'actualit', 'news']):
                    dest_categories['Blog/Articles'] += 1
                elif any(term in dest.lower() for term in ['produit', 'product', 'service', 'solution']):
                    dest_categories['Produits/Services'] += 1
                elif any(term in dest.lower() for term in ['contact', 'about', 'propos', 'equipe', 'team']):
                    dest_categories['Pages institutionnelles'] += 1
                elif any(term in dest.lower() for term in ['expertise', 'competence', 'metier', 'domaine']):
                    dest_categories['Expertises'] += 1
                elif any(term in dest.lower() for term in ['carriere', 'emploi', 'job', 'recrutement']):
                    dest_categories['Carrières/Emploi'] += 1
                else:
                    dest_categories['Autres'] += 1
        
        # Analyse NLP avancée des ancres
        semantic_keywords = self.extract_semantic_keywords(anchor_texts, all_stop_words)
        
        return {
            'top_anchor_keywords': semantic_keywords,
            'destination_categories': dict(dest_categories)
        }
    
    def extract_semantic_keywords(self, anchor_texts, stop_words):
        """Extraction de mots-clés sémantiques avec techniques NLP"""
        
        # 1. Extraction des mots simples filtrés
        word_freq = Counter()
        bigram_freq = Counter()
        trigram_freq = Counter()
        
        for anchor in anchor_texts:
            # Nettoyer le texte
            clean_anchor = re.sub(r'[^\w\s]', ' ', anchor.lower())
            words = [w.strip() for w in clean_anchor.split() if len(w.strip()) >= 3]
            
            # Filtrer les stop words et mots génériques
            meaningful_words = [w for w in words if w not in stop_words and len(w) >= 3]
            
            # Compter les mots simples
            for word in meaningful_words:
                if len(word) >= 4:  # Mots de 4 lettres minimum
                    word_freq[word] += 1
            
            # Compter les bigrammes (expressions de 2 mots)
            if len(meaningful_words) >= 2:
                for i in range(len(meaningful_words) - 1):
                    bigram = f"{meaningful_words[i]} {meaningful_words[i+1]}"
                    if len(bigram) >= 8:  # Éviter les bigrammes trop courts
                        bigram_freq[bigram] += 1
            
            # Compter les trigrammes (expressions de 3 mots)
            if len(meaningful_words) >= 3:
                for i in range(len(meaningful_words) - 2):
                    trigram = f"{meaningful_words[i]} {meaningful_words[i+1]} {meaningful_words[i+2]}"
                    if len(trigram) >= 12:  # Éviter les trigrammes trop courts
                        trigram_freq[trigram] += 1
        
        # 2. Calculer des scores de pertinence (simple TF-IDF-like)
        total_anchors = len(anchor_texts)
        scored_keywords = {}
        
        # Scorer les mots simples
        for word, freq in word_freq.items():
            if freq >= 2:  # Minimum 2 occurrences
                # Score basé sur fréquence et longueur du mot
                score = freq * (1 + len(word) / 10)
                scored_keywords[word] = {
                    'count': freq,
                    'score': score,
                    'type': 'mot'
                }
        
        # Scorer les bigrammes (bonus car plus informatifs)
        for bigram, freq in bigram_freq.items():
            if freq >= 2:  # Minimum 2 occurrences
                score = freq * 2.5  # Bonus pour les expressions
                scored_keywords[bigram] = {
                    'count': freq,
                    'score': score,
                    'type': 'expression'
                }
        
        # Scorer les trigrammes (bonus encore plus élevé)
        for trigram, freq in trigram_freq.items():
            if freq >= 2:  # Minimum 2 occurrences
                score = freq * 4  # Gros bonus pour les expressions longues
                scored_keywords[trigram] = {
                    'count': freq,
                    'score': score,
                    'type': 'expression longue'
                }
        
        # 3. Trier par score et retourner le top 15
        sorted_keywords = sorted(scored_keywords.items(), key=lambda x: x[1]['score'], reverse=True)
        
        # Formater pour compatibilité avec l'ancien format
        result = {}
        for keyword, data in sorted_keywords[:15]:
            result[keyword] = data['count']
        
        return result
    
    def analyze_semantic_advanced(self, editorial_links, anchor_col, dest_col, page_data=None):
        """Analyse sémantique avancée avec CamemBERT"""
        if not SEMANTIC_ANALYSIS_AVAILABLE:
            print("⚠️  Analyse sémantique avancée non disponible (dépendances manquantes)")
            return None
        
        print("\n🧠 ANALYSE SÉMANTIQUE AVANCÉE (CamemBERT)")
        print("=" * 50)
        
        # Obtenir l'analyseur sémantique
        analyzer = get_semantic_analyzer()
        
        # Afficher les stats du cache
        cache_stats = analyzer.get_cache_stats()
        print(f"📦 Cache: {cache_stats['files']} entrées ({cache_stats['size_mb']} MB)")
        
        results = {}
        
        # 1. Clustering sémantique des ancres
        anchors = []
        for link in editorial_links:
            anchor = link.get(anchor_col, '').strip() if anchor_col else ''
            if anchor and len(anchor) > 3:
                anchors.append(anchor)
        
        if anchors:
            semantic_clusters = analyzer.cluster_semantic_themes(anchors, min_cluster_size=2)
            results['semantic_clusters'] = semantic_clusters
            
            if semantic_clusters:
                print(f"🎯 {len(semantic_clusters)} thèmes sémantiques identifiés:")
                for theme, anchor_list in semantic_clusters.items():
                    print(f"   • {theme} ({len(anchor_list)} ancres)")
            else:
                print("⚠️  Aucun cluster sémantique significatif trouvé")
        
        # 2. Analyse de cohérence ancre ↔ contenu (si données disponibles)
        if page_data:
            print("🔍 Analyse de cohérence ancres ↔ contenus de pages...")
            
            anchor_texts = []
            page_contents = []
            
            for link in editorial_links[:50]:  # Limiter pour les performances
                anchor = link.get(anchor_col, '').strip() if anchor_col else ''
                dest_url = link.get(dest_col, '') if dest_col else ''
                
                if anchor and dest_url and dest_url in page_data:
                    anchor_texts.append(anchor)
                    # Combiner toutes les données textuelles disponibles
                    content_parts = []
                    page_info = page_data[dest_url]
                    
                    # Priorité aux éléments les plus importants
                    priority_order = ['titles', 'h1', 'h2', 'h3', 'meta_desc', 'meta_keywords']
                    for data_type in priority_order:
                        if data_type in page_info and page_info[data_type]:
                            content_parts.append(page_info[data_type])
                    
                    # Ajouter images alt text si disponible (moins prioritaire)
                    if 'images_alt' in page_info and page_info['images_alt']:
                        # Limiter le alt text pour éviter la pollution
                        alt_text = page_info['images_alt'][:200]  # Max 200 chars
                        content_parts.append(alt_text)
                    
                    combined_content = ' '.join(content_parts)
                    page_contents.append(combined_content)
            
            if anchor_texts and page_contents:
                coherence_scores = analyzer.analyze_semantic_coherence(anchor_texts, page_contents)
                avg_coherence = sum(coherence_scores) / len(coherence_scores) if coherence_scores else 0
                
                results['coherence_analysis'] = {
                    'average_score': avg_coherence,
                    'total_analyzed': len(coherence_scores),
                    'high_coherence': len([s for s in coherence_scores if s > 0.7]),
                    'low_coherence': len([s for s in coherence_scores if s < 0.4])
                }
                
                print(f"   📊 Score moyen de cohérence: {avg_coherence:.2f}")
                print(f"   ✅ Liens très cohérents (>0.7): {results['coherence_analysis']['high_coherence']}")
                print(f"   ⚠️  Liens peu cohérents (<0.4): {results['coherence_analysis']['low_coherence']}")
        
        # 3. Recherche d'opportunités de maillage
        if page_data and len(page_data) > 1:
            print("🔍 Recherche d'opportunités de maillage...")
            
            # Préparer les contenus enrichis des pages
            page_contents_for_gaps = {}
            for url, data in list(page_data.items())[:100]:  # Limiter pour les performances
                content_parts = []
                
                # Utiliser toutes les données disponibles pour une meilleure similarité
                priority_order = ['titles', 'h1', 'h2', 'h3', 'meta_desc']
                for data_type in priority_order:
                    if data_type in data and data[data_type]:
                        content_parts.append(data[data_type])
                
                # Ajouter meta keywords si disponibles (utiles pour la similarité)
                if 'meta_keywords' in data and data['meta_keywords']:
                    content_parts.append(data['meta_keywords'])
                
                if content_parts:
                    combined_content = ' '.join(content_parts)
                    page_contents_for_gaps[url] = combined_content
            
            if len(page_contents_for_gaps) > 1:
                opportunities = analyzer.find_semantic_gaps(page_contents_for_gaps, threshold=0.6)
                results['link_opportunities'] = opportunities
                
                if opportunities:
                    print(f"   🚀 {len(opportunities)} opportunités de maillage trouvées")
                    for i, (url1, url2, similarity) in enumerate(opportunities[:5]):
                        print(f"   {i+1}. Similarité {similarity:.2f}: {url1} ↔ {url2}")
                else:
                    print("   ℹ️  Aucune opportunité significative trouvée")
        
        return results
    
    def collect_page_data_for_semantic(self, csv_base_path):
        """Collecter les données textuelles des pages pour l'analyse sémantique"""
        page_data = {}
        
        # Obtenir le dossier de base des fichiers CSV
        base_dir = os.path.dirname(csv_base_path)
        base_name = os.path.splitext(os.path.basename(csv_base_path))[0]
        
        # Patterns de fichiers à chercher (enrichis)
        file_patterns = {
            'titles': ['page_titles', 'titles', 'titres'],
            'h1': ['h1', 'h1_1'],
            'h2': ['h2', 'h2_1'],
            'h3': ['h3', 'h3_1'],
            'meta_desc': ['meta_description', 'description', 'meta_descriptions'],
            'meta_keywords': ['meta_keywords', 'keywords', 'mots_cles'],
            'images_alt': ['images', 'image_alt', 'alt_text'],
            'schema_org': ['schema', 'structured_data', 'schema_org']
        }
        
        # Chercher et charger chaque type de fichier
        for data_type, patterns in file_patterns.items():
            found_file = None
            
            for pattern in patterns:
                # Essayer différents formats de noms
                for filename in [
                    f"{pattern}.csv",
                    f"{base_name}_{pattern}.csv",
                    f"all_{pattern}.csv",
                    f"tous_les_{pattern}.csv"
                ]:
                    filepath = os.path.join(base_dir, filename)
                    if os.path.exists(filepath):
                        found_file = filepath
                        break
                
                if found_file:
                    break
            
            # Charger le fichier trouvé
            if found_file:
                try:
                    rows, fieldnames = self.load_csv_file(found_file)
                    if rows:
                        print(f"✅ Trouvé pour analyse sémantique: {data_type} -> {os.path.basename(found_file)}")
                        
                        # Identifier les colonnes URL et contenu
                        url_col = None
                        content_col = None
                        
                        for col in fieldnames:
                            col_lower = col.lower()
                            if 'address' in col_lower or 'url' in col_lower:
                                url_col = col
                            elif self._matches_content_column(data_type, col_lower):
                                content_col = col
                        
                        # Extraire les données
                        if url_col and content_col:
                            for row in rows:
                                url = row.get(url_col, '').strip()
                                content = row.get(content_col, '').strip()
                                
                                if url and content:
                                    if url not in page_data:
                                        page_data[url] = {}
                                    page_data[url][data_type] = content
                
                except Exception as e:
                    print(f"⚠️  Erreur lors du chargement de {found_file}: {e}")
        
        if page_data:
            print(f"📊 Données collectées pour {len(page_data)} pages pour l'analyse sémantique")
        
        return page_data
    
    def _matches_content_column(self, data_type, col_lower):
        """Déterminer si une colonne correspond au type de contenu recherché"""
        column_patterns = {
            'titles': ['title', 'titre', 'page title'],
            'h1': ['h1', 'heading 1', 'titre 1'],
            'h2': ['h2', 'heading 2', 'titre 2'],
            'h3': ['h3', 'heading 3', 'titre 3'],
            'meta_desc': ['description', 'meta description', 'meta_description'],
            'meta_keywords': ['keywords', 'meta keywords', 'meta_keywords', 'mots', 'cles'],
            'images_alt': ['alt', 'alt text', 'alternative', 'image alt'],
            'schema_org': ['schema', 'structured', 'microdata', 'json-ld']
        }
        
        if data_type in column_patterns:
            return any(pattern in col_lower for pattern in column_patterns[data_type])
        
        return False
    
    def generate_semantic_analysis_section(self, semantic_data):
        """Générer la section d'analyse sémantique avec graphiques"""
        
        html_content = """
        <div class="section">
            <h2>Analyse sémantique avancée (CamemBERT)</h2>
        """
        
        # 1. Clustering sémantique avec graphiques
        if 'semantic_clusters' in semantic_data and semantic_data['semantic_clusters']:
            clusters = semantic_data['semantic_clusters']
            total_anchors = sum(len(anchors) for anchors in clusters.values())
            
            # Vérifier si l'analyse est pertinente (plus d'un cluster ou diversité suffisante)
            if len(clusters) == 1:
                cluster_name = list(clusters.keys())[0]
                cluster_anchors = list(clusters.values())[0]
                unique_anchors = set(anchor.lower().strip() for anchor in cluster_anchors)
                diversity_ratio = len(unique_anchors) / len(cluster_anchors)
                
                if diversity_ratio < 0.3:  # Faible diversité
                    html_content += f"""
                    <div class="warning">
                        <h3>⚠️ Analyse sémantique non pertinente</h3>
                        <p><strong>Problème détecté :</strong> Faible diversité des ancres de liens</p>
                        <ul>
                            <li>📊 Ancres analysées : {total_anchors}</li>
                            <li>🔄 Ancres uniques : {len(unique_anchors)} ({diversity_ratio:.1%})</li>
                            <li>🎯 Cluster unique : "{cluster_name}"</li>
                        </ul>
                        
                        <h4>💡 Recommandations pour améliorer l'analyse sémantique :</h4>
                        <ol>
                            <li><strong>Diversifier les ancres :</strong> Utiliser des termes variés et descriptifs</li>
                            <li><strong>Éviter la répétition :</strong> "{cluster_anchors[0] if cluster_anchors else 'N/A'}" apparaît {cluster_anchors.count(cluster_anchors[0]) if cluster_anchors else 0} fois</li>
                            <li><strong>Ancres contextuelles :</strong> Décrire le contenu de destination plutôt que le nom du site</li>
                            <li><strong>Synonymes et variations :</strong> "services", "expertise", "solutions", "conseil"...</li>
                            <li><strong>Ancres longue traîne :</strong> "extension bois Amiens", "terrasse composite", "permis de construire"</li>
                        </ol>
                        
                        <div class="success">
                            <p><strong>✅ Objectif :</strong> Atteindre au moins 30% de diversité pour une analyse sémantique utile</p>
                        </div>
                    </div>
                    """
                    html_content += "</div>"  # Fermer la section
                    return html_content
            
            # Si on arrive ici, l'analyse est pertinente (diversité suffisante ou plusieurs clusters)
            html_content += f"""
            <div class="semantic-analysis">
                <h3>Thèmes sémantiques identifiés ({len(clusters)} clusters, {total_anchors} ancres)</h3>
                
                <div class="chart-container">
                    <div class="chart">
                        <h4>Répartition des thèmes</h4>
                        <div class="pie-chart-semantic">
            """
            
            # Graphique en secteurs des thèmes
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FF8A80', '#FFD93D', '#6C5CE7', '#FD79A8']
            for i, (theme, anchors) in enumerate(clusters.items()):
                percentage = (len(anchors) / total_anchors) * 100
                color = colors[i % len(colors)]
                html_content += f"""
                            <div class="pie-item-semantic">
                                <span class="pie-color" style="background-color: {color}"></span>
                                <span class="pie-label-semantic">{theme}: {len(anchors)} ancres ({percentage:.1f}%)</span>
                            </div>
                """
            
            html_content += """
                        </div>
                    </div>
                    
                    <div class="chart">
                        <h4>Détail par thème</h4>
                        <div class="themes-detail">
            """
            
            # Graphique en barres horizontales avec détails
            max_anchors = max(len(anchors) for anchors in clusters.values())
            for i, (theme, anchors) in enumerate(clusters.items()):
                percentage = (len(anchors) / max_anchors) * 100
                color = colors[i % len(colors)]
                
                html_content += f"""
                            <div class="theme-item">
                                <div class="theme-header">
                                    <span class="theme-name">{theme}</span>
                                    <span class="theme-count">{len(anchors)} ancres</span>
                                </div>
                                <div class="theme-bar-container">
                                    <div class="theme-bar" style="width: {percentage}%; background-color: {color}"></div>
                                </div>
                                <div class="theme-examples">
                """
                
                # Afficher quelques exemples d'ancres
                example_anchors = anchors[:5]  # Top 5 exemples
                for anchor in example_anchors:
                    html_content += f'<span class="anchor-example">"{anchor}"</span>'
                
                if len(anchors) > 5:
                    html_content += f'<span class="anchor-more">... et {len(anchors) - 5} autres</span>'
                
                html_content += """
                                </div>
                            </div>
                """
            
            html_content += """
                        </div>
                    </div>
                </div>
            """
            
            # 3. Nuage de mots par thème
            html_content += """
                <h4>Nuages de mots par thème</h4>
                <div class="word-clouds-container">
            """
            
            for i, (theme, anchors) in enumerate(clusters.items()):
                color = colors[i % len(colors)]
                
                # Extraire les mots les plus fréquents du thème
                all_words = []
                for anchor in anchors:
                    words = anchor.lower().split()
                    all_words.extend([w for w in words if len(w) > 3])
                
                from collections import Counter
                word_freq = Counter(all_words)
                top_words = word_freq.most_common(10)
                
                html_content += f"""
                    <div class="word-cloud-theme" style="border-left: 4px solid {color}">
                        <h5>{theme}</h5>
                        <div class="word-cloud-mini">
                """
                
                for word, freq in top_words:
                    # Taille basée sur la fréquence (min 0.8em, max 1.6em)
                    size = 0.8 + (freq / max(1, max(f for _, f in top_words))) * 0.8
                    html_content += f'<span class="word-mini" style="font-size: {size}em; color: {color}">{word}</span>'
                
                html_content += """
                        </div>
                    </div>
                """
            
            html_content += "</div>"
        
        # 2. Analyse de cohérence si disponible
        if 'coherence_analysis' in semantic_data:
            coherence = semantic_data['coherence_analysis']
            html_content += f"""
            <div class="coherence-analysis">
                <h3>Cohérence sémantique ancres ↔ contenus</h3>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number">{coherence['average_score']:.2f}</div>
                        <div class="stat-label">Score moyen</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{coherence['high_coherence']}</div>
                        <div class="stat-label">Liens très cohérents (>0.7)</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{coherence['low_coherence']}</div>
                        <div class="stat-label">Liens peu cohérents (<0.4)</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{coherence['total_analyzed']}</div>
                        <div class="stat-label">Liens analysés</div>
                    </div>
                </div>
            </div>
            """
        
        # 3. Opportunités de maillage si disponibles
        if 'link_opportunities' in semantic_data and semantic_data['link_opportunities']:
            opportunities = semantic_data['link_opportunities'][:10]  # Top 10
            html_content += f"""
            <div class="opportunities-analysis">
                <h3>Opportunités de maillage détectées</h3>
                <p>Pages sémantiquement similaires qui pourraient être liées :</p>
                <table>
                    <tr><th>Similarité</th><th>Page 1</th><th>Page 2</th></tr>
            """
            
            for url1, url2, similarity in opportunities:
                similarity_percent = similarity * 100
                color = '#28a745' if similarity > 0.8 else '#ffc107' if similarity > 0.6 else '#dc3545'
                html_content += f"""
                    <tr>
                        <td><span style="color: {color}; font-weight: bold">{similarity_percent:.1f}%</span></td>
                        <td class="url">{url1}</td>
                        <td class="url">{url2}</td>
                    </tr>
                """
            
            html_content += "</table></div>"
        
        # Si aucun clustering n'est disponible
        else:
            html_content += """
            <div class="warning">
                <h3>ℹ️ Analyse sémantique non disponible</h3>
                <p><strong>Raisons possibles :</strong></p>
                <ul>
                    <li>🔢 Trop peu d'ancres de liens (minimum 3 requis)</li>
                    <li>🔄 Diversité insuffisante des ancres (&lt; 30%)</li>
                    <li>⚙️ Erreur lors du traitement NLP</li>
                </ul>
                
                <h4>💡 Pour activer l'analyse sémantique :</h4>
                <ol>
                    <li><strong>Augmenter le nombre de liens éditoriaux</strong> (minimum 10 recommandé)</li>
                    <li><strong>Diversifier les ancres de liens :</strong>
                        <ul>
                            <li>"nos services de construction"</li>
                            <li>"expertise en extension bois"</li>
                            <li>"solutions d'aménagement"</li>
                            <li>"conseil en rénovation"</li>
                        </ul>
                    </li>
                    <li><strong>Éviter les ancres génériques :</strong> "cliquez ici", "en savoir plus"</li>
                    <li><strong>Utiliser des termes métiers spécifiques</strong> à votre domaine</li>
                </ol>
            </div>
            """
        
        html_content += "</div>"  # Fermer la section
        
        return html_content
    
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

    def analyze_content_quality(self, csv_path, website_url, url_filter=None):
        """Analyse la qualité du contenu en cherchant les fichiers CSV supplémentaires"""
        base_path = os.path.dirname(csv_path)
        content_data = {}
        
        # Fichiers CSV à analyser
        csv_files = {
            'word_count': ['word_count', 'nombre_mots', 'wordcount'],
            'page_titles': ['page_titles', 'titles', 'titres'],
            'h1': ['h1', 'h1_1'],
            'internal': ['internal', 'pages_internes', 'all_pages']
        }
        
        print(f"\n🔍 ANALYSE DE QUALITÉ DU CONTENU")
        print("="*50)
        
        # Chercher les fichiers dans le dossier
        available_files = {}
        if os.path.exists(base_path):
            for file in os.listdir(base_path):
                if file.endswith('.csv'):
                    file_lower = file.lower()
                    for data_type, patterns in csv_files.items():
                        if any(pattern in file_lower for pattern in patterns):
                            available_files[data_type] = os.path.join(base_path, file)
                            print(f"✅ Trouvé: {data_type} -> {file}")
        
        if not available_files:
            print("⚠️  Aucun fichier de contenu trouvé - utilisez l'export complet de Screaming Frog")
            return None
        
        # Charger et analyser les données
        analysis_results = {}
        
        # 1. Analyse du nombre de mots
        if 'word_count' in available_files:
            word_analysis = self.analyze_word_count(available_files['word_count'], url_filter)
            if word_analysis:
                analysis_results['word_analysis'] = word_analysis
        
        # 2. Analyse des titres et H1
        if 'page_titles' in available_files and 'h1' in available_files:
            title_h1_analysis = self.analyze_title_h1_coherence(
                available_files['page_titles'], 
                available_files['h1'], 
                url_filter
            )
            if title_h1_analysis:
                analysis_results['title_h1_coherence'] = title_h1_analysis
        
        # 3. Identification des pages de conversion
        if 'internal' in available_files:
            conversion_analysis = self.identify_conversion_pages(available_files['internal'], url_filter)
            if conversion_analysis:
                analysis_results['conversion_pages'] = conversion_analysis
        
        return analysis_results if analysis_results else None

    def analyze_word_count(self, csv_path, url_filter=None):
        """Analyse le nombre de mots par page"""
        try:
            rows, fieldnames = self.load_csv_file(csv_path)
            if not rows:
                return None
            
            print(f"📊 Analyse du nombre de mots ({len(rows):,} pages)")
            
            # Filtrer si nécessaire
            if url_filter:
                original_count = len(rows)
                rows = [row for row in rows if any(
                    str(row.get(col, '')).startswith(url_filter) 
                    for col in row.keys() if 'url' in col.lower() or 'address' in col.lower()
                )]
                print(f"🎯 Après filtrage: {len(rows):,} pages ({original_count - len(rows):,} supprimées)")
            
            # Identifier la colonne de mots
            word_col = None
            url_col = None
            for col in fieldnames:
                col_lower = col.lower()
                if any(term in col_lower for term in ['word', 'mots', 'count']):
                    word_col = col
                elif any(term in col_lower for term in ['address', 'url', 'source']):
                    url_col = col
            
            if not word_col or not url_col:
                print("❌ Colonnes 'word count' ou 'URL' non trouvées")
                return None
            
            # Analyser les données
            word_counts = []
            for row in rows:
                try:
                    word_count = int(row.get(word_col, 0))
                    url = row.get(url_col, '')
                    if word_count >= 0 and url:  # Exclure les valeurs négatives
                        word_counts.append({'url': url, 'word_count': word_count})
                except (ValueError, TypeError):
                    continue
            
            if not word_counts:
                return None
            
            # Statistiques
            counts = [item['word_count'] for item in word_counts]
            
            analysis = {
                'total_pages': len(word_counts),
                'avg_words': sum(counts) / len(counts),
                'median_words': sorted(counts)[len(counts)//2],
                'min_words': min(counts),
                'max_words': max(counts),
                'thin_content': [item for item in word_counts if item['word_count'] < 300],
                'rich_content': [item for item in word_counts if item['word_count'] > 1500],
                'quality_content': [item for item in word_counts if 300 <= item['word_count'] <= 1500]
            }
            
            print(f"📈 Statistiques:")
            print(f"  - Moyenne: {analysis['avg_words']:.0f} mots")
            print(f"  - Contenu thin (< 300): {len(analysis['thin_content'])} pages")
            print(f"  - Contenu riche (> 1500): {len(analysis['rich_content'])} pages")
            print(f"  - Contenu qualité (300-1500): {len(analysis['quality_content'])} pages")
            
            return analysis
            
        except Exception as e:
            print(f"❌ Erreur lors de l'analyse des mots: {e}")
            return None

    def analyze_title_h1_coherence(self, titles_csv, h1_csv, url_filter=None):
        """Analyse la cohérence entre les titres et H1"""
        try:
            # Charger les deux fichiers
            titles_data, _ = self.load_csv_file(titles_csv)
            h1_data, _ = self.load_csv_file(h1_csv)
            
            if not titles_data or not h1_data:
                return None
            
            print(f"🏷️  Analyse cohérence Title/H1")
            
            # Créer des dictionnaires par URL
            titles_dict = {}
            h1_dict = {}
            
            # Parser les titres
            for row in titles_data:
                url = None
                title = None
                for col, value in row.items():
                    col_lower = col.lower()
                    if any(term in col_lower for term in ['address', 'url', 'source']):
                        url = value
                    elif any(term in col_lower for term in ['title', 'titre']):
                        title = value
                
                if url and title and (not url_filter or url.startswith(url_filter)):
                    titles_dict[url] = title
            
            # Parser les H1
            for row in h1_data:
                url = None
                h1 = None
                for col, value in row.items():
                    col_lower = col.lower()
                    if any(term in col_lower for term in ['address', 'url', 'source']):
                        url = value
                    elif 'h1' in col_lower:
                        h1 = value
                
                if url and h1 and (not url_filter or url.startswith(url_filter)):
                    h1_dict[url] = h1
            
            # Analyser la cohérence
            coherence_analysis = {
                'total_pages_with_both': 0,
                'identical': [],
                'similar': [],
                'different': [],
                'missing_h1': [],
                'missing_title': []
            }
            
            all_urls = set(titles_dict.keys()) | set(h1_dict.keys())
            
            for url in all_urls:
                title = titles_dict.get(url, '')
                h1 = h1_dict.get(url, '')
                
                if not title:
                    coherence_analysis['missing_title'].append(url)
                elif not h1:
                    coherence_analysis['missing_h1'].append(url)
                else:
                    coherence_analysis['total_pages_with_both'] += 1
                    
                    # Comparaison
                    if title.strip().lower() == h1.strip().lower():
                        coherence_analysis['identical'].append({'url': url, 'text': title})
                    elif self.similarity_score(title, h1) > 0.7:
                        coherence_analysis['similar'].append({
                            'url': url, 'title': title, 'h1': h1
                        })
                    else:
                        coherence_analysis['different'].append({
                            'url': url, 'title': title, 'h1': h1
                        })
            
            print(f"📊 Résultats cohérence:")
            print(f"  - Pages avec Title et H1: {coherence_analysis['total_pages_with_both']}")
            print(f"  - Identiques: {len(coherence_analysis['identical'])}")
            print(f"  - Similaires: {len(coherence_analysis['similar'])}")
            print(f"  - Différents: {len(coherence_analysis['different'])}")
            
            return coherence_analysis
            
        except Exception as e:
            print(f"❌ Erreur lors de l'analyse Title/H1: {e}")
            return None

    def identify_conversion_pages(self, csv_path, url_filter=None):
        """Identifie les pages de conversion potentielles"""
        try:
            rows, fieldnames = self.load_csv_file(csv_path)
            if not rows:
                return None
            
            print(f"💰 Identification des pages de conversion")
            
            # Patterns de conversion
            conversion_patterns = {
                'contact': ['contact', 'nous-contacter', 'contactez', 'get-in-touch'],
                'achat': ['achat', 'acheter', 'buy', 'purchase', 'commande', 'commander', 'order'],
                'inscription': ['inscription', 'register', 'signup', 'sign-up', 's-inscrire'],
                'devis': ['devis', 'quote', 'estimation', 'demande', 'request'],
                'panier': ['panier', 'cart', 'basket', 'checkout'],
                'pricing': ['prix', 'pricing', 'tarifs', 'rates', 'cost'],
                'demo': ['demo', 'demonstration', 'essai', 'trial', 'test']
            }
            
            conversion_pages = {category: [] for category in conversion_patterns.keys()}
            
            # Identifier la colonne URL
            url_col = None
            title_col = None
            for col in fieldnames:
                col_lower = col.lower()
                if any(term in col_lower for term in ['address', 'url', 'source']):
                    url_col = col
                elif any(term in col_lower for term in ['title', 'titre']):
                    title_col = col
            
            if not url_col:
                print("❌ Colonne URL non trouvée")
                return None
            
            for row in rows:
                url = row.get(url_col, '').lower()
                title = row.get(title_col, '').lower() if title_col else ''
                
                # Appliquer le filtre
                if url_filter and not row.get(url_col, '').startswith(url_filter):
                    continue
                
                # Vérifier les patterns
                full_text = f"{url} {title}"
                for category, patterns in conversion_patterns.items():
                    if any(pattern in full_text for pattern in patterns):
                        conversion_pages[category].append({
                            'url': row.get(url_col, ''),
                            'title': row.get(title_col, '') if title_col else '',
                            'category': category
                        })
                        break  # Une page ne peut être que dans une catégorie
            
            # Statistiques
            total_conversion_pages = sum(len(pages) for pages in conversion_pages.values())
            print(f"📊 Pages de conversion trouvées: {total_conversion_pages}")
            
            for category, pages in conversion_pages.items():
                if pages:
                    print(f"  - {category.title()}: {len(pages)} pages")
            
            return {
                'by_category': conversion_pages,
                'total_conversion_pages': total_conversion_pages,
                'conversion_rate_potential': total_conversion_pages / len(rows) * 100 if rows else 0
            }
            
        except Exception as e:
            print(f"❌ Erreur lors de l'identification des pages de conversion: {e}")
            return None

    def similarity_score(self, text1, text2):
        """Calcule un score de similarité simple entre deux textes"""
        if not text1 or not text2:
            return 0
        
        # Normaliser
        t1 = set(text1.lower().split())
        t2 = set(text2.lower().split())
        
        # Jaccard similarity
        intersection = len(t1 & t2)
        union = len(t1 | t2)
        
        return intersection / union if union > 0 else 0

    def analyze_semantic_clusters(self, csv_path, website_url, url_filter=None):
        """Analyse les clusters sémantiques générés par Screaming Frog v22+"""
        base_path = os.path.dirname(csv_path)
        
        # Fichiers sémantiques à rechercher
        semantic_files = {
            'embeddings': ['embeddings', 'embedding'],
            'similar_pages': ['similar', 'cluster', 'semantic'],
            'content_clusters': ['content_cluster', 'clusters']
        }
        
        print(f"\n🧠 ANALYSE SÉMANTIQUE (Screaming Frog v22+)")
        print("="*50)
        
        # Chercher les fichiers sémantiques
        available_files = {}
        if os.path.exists(base_path):
            for file in os.listdir(base_path):
                if file.endswith('.csv'):
                    file_lower = file.lower()
                    for data_type, patterns in semantic_files.items():
                        if any(pattern in file_lower for pattern in patterns):
                            available_files[data_type] = os.path.join(base_path, file)
                            print(f"✅ Trouvé: {data_type} -> {file}")
        
        if not available_files:
            print("⚠️  Aucun fichier sémantique trouvé")
            print("💡 Activez l'analyse sémantique dans Screaming Frog (Config > API Access > AI)")
            return None
        
        analysis_results = {}
        
        # 1. Analyse des pages similaires
        if 'similar_pages' in available_files:
            similarity_analysis = self.analyze_similar_pages(available_files['similar_pages'], url_filter)
            if similarity_analysis:
                analysis_results['similar_pages'] = similarity_analysis
        
        # 2. Analyse des clusters de contenu
        if 'content_clusters' in available_files:
            cluster_analysis = self.analyze_content_clusters(available_files['content_clusters'], url_filter)
            if cluster_analysis:
                analysis_results['content_clusters'] = cluster_analysis
        
        # 3. Recommandations de maillage sémantique
        if analysis_results:
            linking_recommendations = self.generate_semantic_linking_recommendations(analysis_results)
            analysis_results['linking_recommendations'] = linking_recommendations
        
        return analysis_results if analysis_results else None

    def analyze_similar_pages(self, csv_path, url_filter=None):
        """Analyse les pages sémantiquement similaires"""
        try:
            rows, fieldnames = self.load_csv_file(csv_path)
            if not rows:
                return None
                
            print(f"🔍 Analyse de similarité sémantique ({len(rows):,} relations)")
            
            # Filtrer si nécessaire
            if url_filter:
                original_count = len(rows)
                rows = [row for row in rows if any(
                    str(row.get(col, '')).startswith(url_filter) 
                    for col in row.keys() if 'url' in col.lower() or 'source' in col.lower()
                )]
                print(f"🎯 Après filtrage: {len(rows):,} relations ({original_count - len(rows):,} supprimées)")
            
            # Identifier les colonnes
            source_col = target_col = similarity_col = None
            for col in fieldnames:
                col_lower = col.lower()
                if any(term in col_lower for term in ['source', 'page', 'url']) and not target_col:
                    source_col = col
                elif any(term in col_lower for term in ['target', 'similar', 'related']) and source_col:
                    target_col = col
                elif any(term in col_lower for term in ['similarity', 'score', 'distance']):
                    similarity_col = col
            
            if not source_col or not target_col:
                print("❌ Colonnes source/target non trouvées")
                return None
            
            # Analyser les relations
            similarity_threshold = self.config.get('semantic_analysis', {}).get('similarity_threshold', 0.85)
            high_similarity_pairs = []
            similarity_scores = []
            
            for row in rows:
                try:
                    source = row.get(source_col, '')
                    target = row.get(target_col, '')
                    score = float(row.get(similarity_col, 0)) if similarity_col else 1.0
                    
                    if source and target and score >= similarity_threshold:
                        high_similarity_pairs.append({
                            'source': source,
                            'target': target,
                            'similarity': score
                        })
                        similarity_scores.append(score)
                        
                except (ValueError, TypeError):
                    continue
            
            if not high_similarity_pairs:
                return None
            
            analysis = {
                'total_similar_pairs': len(high_similarity_pairs),
                'avg_similarity': sum(similarity_scores) / len(similarity_scores),
                'high_similarity_threshold': similarity_threshold,
                'similar_page_pairs': high_similarity_pairs[:50],  # Limiter pour la performance
                'top_similarity_scores': sorted(similarity_scores, reverse=True)[:10]
            }
            
            print(f"📊 Résultats similarité:")
            print(f"  - Paires très similaires (>{similarity_threshold}): {len(high_similarity_pairs)}")
            print(f"  - Score moyen: {analysis['avg_similarity']:.3f}")
            
            return analysis
            
        except Exception as e:
            print(f"❌ Erreur lors de l'analyse de similarité: {e}")
            return None

    def analyze_content_clusters(self, csv_path, url_filter=None):
        """Analyse les clusters de contenu"""
        try:
            rows, fieldnames = self.load_csv_file(csv_path)
            if not rows:
                return None
                
            print(f"🗂️  Analyse des clusters de contenu ({len(rows):,} pages)")
            
            # Identifier les colonnes
            url_col = cluster_col = None
            for col in fieldnames:
                col_lower = col.lower()
                if any(term in col_lower for term in ['url', 'address', 'page']):
                    url_col = col
                elif any(term in col_lower for term in ['cluster', 'group', 'category']):
                    cluster_col = col
            
            if not url_col:
                print("❌ Colonne URL non trouvée")
                return None
            
            # Grouper par clusters
            clusters = {}
            for row in rows:
                url = row.get(url_col, '')
                cluster_id = row.get(cluster_col, 'unclustered') if cluster_col else 'all_pages'
                
                # Appliquer le filtre
                if url_filter and not url.startswith(url_filter):
                    continue
                
                if cluster_id not in clusters:
                    clusters[cluster_id] = []
                clusters[cluster_id].append(url)
            
            # Analyser la distribution des clusters
            min_cluster_size = self.config.get('semantic_analysis', {}).get('min_cluster_size', 3)
            meaningful_clusters = {k: v for k, v in clusters.items() if len(v) >= min_cluster_size}
            
            analysis = {
                'total_clusters': len(clusters),
                'meaningful_clusters': len(meaningful_clusters),
                'total_clustered_pages': sum(len(pages) for pages in clusters.values()),
                'avg_cluster_size': sum(len(pages) for pages in clusters.values()) / len(clusters) if clusters else 0,
                'cluster_distribution': {k: len(v) for k, v in meaningful_clusters.items()},
                'largest_clusters': dict(sorted(meaningful_clusters.items(), key=lambda x: len(x[1]), reverse=True)[:10])
            }
            
            print(f"📊 Résultats clustering:")
            print(f"  - Clusters totaux: {analysis['total_clusters']}")
            print(f"  - Clusters significatifs (≥{min_cluster_size}): {analysis['meaningful_clusters']}")
            print(f"  - Taille moyenne: {analysis['avg_cluster_size']:.1f} pages/cluster")
            
            return analysis
            
        except Exception as e:
            print(f"❌ Erreur lors de l'analyse des clusters: {e}")
            return None

    def generate_semantic_linking_recommendations(self, semantic_data):
        """Génère des recommandations de maillage basées sur l'analyse sémantique"""
        recommendations = {
            'missing_internal_links': [],
            'cluster_orphans': [],
            'cross_cluster_opportunities': [],
            'content_gap_analysis': []
        }
        
        # Analyser les pages similaires sans liens
        if 'similar_pages' in semantic_data:
            similar_pairs = semantic_data['similar_pages'].get('similar_page_pairs', [])
            
            for i, pair in enumerate(similar_pairs[:20]):  # Limiter à 20 recommandations
                recommendations['missing_internal_links'].append({
                    'source_page': pair['source'],
                    'target_page': pair['target'],
                    'similarity_score': pair['similarity'],
                    'recommendation': f"Lien éditorial recommandé (similarité: {pair['similarity']:.3f})",
                    'priority': 'high' if pair['similarity'] > 0.9 else 'medium'
                })
        
        # Analyser les clusters pour identifier les opportunités
        if 'content_clusters' in semantic_data:
            cluster_dist = semantic_data['content_clusters'].get('cluster_distribution', {})
            
            for cluster_id, size in cluster_dist.items():
                if size >= 5:  # Clusters avec au moins 5 pages
                    recommendations['cross_cluster_opportunities'].append({
                        'cluster': cluster_id,
                        'pages_count': size,
                        'recommendation': f"Créer une page pilier pour le cluster '{cluster_id}' ({size} pages)",
                        'priority': 'high' if size > 10 else 'medium'
                    })
        
        print(f"💡 Recommandations sémantiques générées:")
        print(f"  - Liens manquants: {len(recommendations['missing_internal_links'])}")
        print(f"  - Opportunités inter-clusters: {len(recommendations['cross_cluster_opportunities'])}")
        
        return recommendations

    def generate_network_data(self, internal_links, column_mapping):
        """Génère les données pour le graphique de réseau du maillage interne"""
        nodes = {}
        edges = []
        
        # Ne prendre que les liens éditoriaux pour le graphique
        editorial_links = [link for link in internal_links if not link.get('is_mechanical', False)]
        
        source_col = column_mapping.get('source')
        dest_col = column_mapping.get('dest')
        anchor_col = column_mapping.get('anchor')
        
        if not source_col or not dest_col:
            return {'nodes': [], 'edges': []}
        
        # Compter les liens entrants pour chaque page
        inbound_count = {}
        outbound_count = {}
        
        for link in editorial_links:
            source = link.get(source_col, '').strip()
            dest = link.get(dest_col, '').strip()
            
            if source and dest and source != dest:  # Éviter les auto-liens
                # Compter les liens entrants
                inbound_count[dest] = inbound_count.get(dest, 0) + 1
                outbound_count[source] = outbound_count.get(source, 0) + 1
                
                # Ajouter les nœuds
                nodes[source] = nodes.get(source, {'id': source, 'inbound': 0, 'outbound': 0})
                nodes[dest] = nodes.get(dest, {'id': dest, 'inbound': 0, 'outbound': 0})
        
        # Mettre à jour les compteurs des nœuds
        for url, count in inbound_count.items():
            if url in nodes:
                nodes[url]['inbound'] = count
        
        for url, count in outbound_count.items():
            if url in nodes:
                nodes[url]['outbound'] = count
        
        # Créer les arêtes avec ancres
        for link in editorial_links:
            source = link.get(source_col, '').strip()
            dest = link.get(dest_col, '').strip()
            anchor = link.get(anchor_col, '').strip() if anchor_col else ''
            
            if source and dest and source != dest:
                edges.append({
                    'source': source,
                    'target': dest,
                    'anchor': anchor[:50] + '...' if len(anchor) > 50 else anchor  # Limiter la longueur
                })
        
        # Limiter le nombre de nœuds pour la performance (garder les plus connectés)
        if len(nodes) > 100:
            # Trier par nombre total de connexions (entrants + sortants)
            sorted_nodes = sorted(nodes.values(), 
                                key=lambda x: x['inbound'] + x['outbound'], 
                                reverse=True)[:100]
            
            # Filtrer les nœuds et edges
            kept_urls = {node['id'] for node in sorted_nodes}
            nodes = {url: data for url, data in nodes.items() if url in kept_urls}
            edges = [edge for edge in edges if edge['source'] in kept_urls and edge['target'] in kept_urls]
        
        # Simplifier les URLs pour l'affichage
        for node in nodes.values():
            try:
                parsed = urlparse(node['id'])
                # Garder seulement le chemin, sans le domaine
                display_path = parsed.path.rstrip('/')
                if not display_path:
                    display_path = '/'
                elif len(display_path) > 30:
                    display_path = display_path[:27] + '...'
                node['label'] = display_path
            except:
                node['label'] = node['id'][:30] + '...' if len(node['id']) > 30 else node['id']
        
        return {
            'nodes': list(nodes.values()),
            'edges': edges[:500]  # Limiter les arêtes pour la performance
        }

    def generate_html_report(self, analysis, website_url, source_file, url_filter=None):
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
                .bar-chart {{ margin: 15px 0; }}
                .bar-item {{ margin: 8px 0; display: flex; align-items: center; }}
                .bar-label {{ min-width: 120px; font-size: 0.9em; margin-right: 10px; }}
                .bar-container {{ flex: 1; display: flex; align-items: center; }}
                .bar-fill {{ height: 20px; background: linear-gradient(90deg, #36A2EB, #4BC0C0); border-radius: 10px; margin-right: 8px; min-width: 2px; }}
                .bar-value {{ font-weight: bold; color: #333; min-width: 30px; }}
                .pie-chart {{ margin: 15px 0; }}
                .pie-item {{ margin: 8px 0; display: flex; align-items: center; }}
                .pie-color {{ width: 16px; height: 16px; border-radius: 50%; margin-right: 8px; }}
                .pie-label {{ font-size: 0.9em; }}
                
                /* Styles pour l'analyse sémantique */
                .semantic-analysis {{ margin: 20px 0; }}
                .pie-chart-semantic {{ margin: 15px 0; }}
                .pie-item-semantic {{ margin: 8px 0; display: flex; align-items: center; }}
                .pie-label-semantic {{ font-size: 0.9em; font-weight: 500; }}
                .themes-detail {{ margin: 15px 0; }}
                .theme-item {{ margin: 15px 0; padding: 10px; border-radius: 8px; background: #f8f9fa; }}
                .theme-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }}
                .theme-name {{ font-weight: bold; color: #333; }}
                .theme-count {{ font-size: 0.9em; color: #666; }}
                .theme-bar-container {{ width: 100%; height: 20px; background: #e9ecef; border-radius: 10px; margin-bottom: 8px; }}
                .theme-bar {{ height: 100%; border-radius: 10px; }}
                .theme-examples {{ display: flex; flex-wrap: wrap; gap: 5px; }}
                .anchor-example {{ background: #e3f2fd; padding: 2px 6px; border-radius: 12px; font-size: 0.8em; color: #1976d2; }}
                .anchor-more {{ font-style: italic; color: #666; font-size: 0.8em; }}
                
                /* Nuages de mots par thème */
                .word-clouds-container {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0; }}
                .word-cloud-theme {{ background: white; padding: 15px; border-radius: 8px; }}
                .word-cloud-mini {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }}
                .word-mini {{ padding: 3px 8px; background: rgba(0,0,0,0.05); border-radius: 12px; font-weight: 500; }}
                
                /* Analyses de cohérence et opportunités */
                .coherence-analysis, .opportunities-analysis {{ margin: 25px 0; padding: 20px; background: #f8f9fa; border-radius: 8px; }}
                #network-graph {{ width: 100%; height: 600px; border: 1px solid #e1e5e9; border-radius: 8px; background: white; }}
                .network-controls {{ margin: 15px 0; text-align: center; }}
                .network-controls button {{ margin: 0 5px; padding: 8px 16px; border: 1px solid #007bff; background: white; color: #007bff; border-radius: 4px; cursor: pointer; }}
                .network-controls button:hover {{ background: #007bff; color: white; }}
                .network-controls button.active {{ background: #007bff; color: white; }}
                .tooltip {{ position: absolute; background: rgba(0,0,0,0.8); color: white; padding: 8px; border-radius: 4px; font-size: 12px; pointer-events: none; z-index: 1000; }}
            </style>
            <script src="https://d3js.org/d3.v7.min.js"></script>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Audit de maillage interne</h1>
                    <p><strong>Site:</strong> {website_url}</p>
                    <p><strong>Date:</strong> {datetime.now().strftime("%d/%m/%Y à %H:%M")}</p>
                </div>
                
                <div class="meta">
                    <strong>Fichier source :</strong> {os.path.basename(source_file)}<br>
                    <strong>Script :</strong> Audit automatisé de maillage interne v2.0"""
        
        if url_filter:
            html_content += f"""<br>
                    <strong>🎯 Filtre appliqué:</strong> URLs commençant par {url_filter}"""
        
        html_content += f"""
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
                    <h2>Score de qualité éditorial</h2>
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
        
        # Graphique de réseau du maillage interne
        if 'network_data' in analysis and analysis['network_data']['nodes']:
            network_data = analysis['network_data']
            html_content += f"""
            <div class="section">
                <h2>Graphique du maillage interne</h2>
                <p>Visualisation interactive des liens éditoriaux entre les pages. La taille des nœuds correspond au nombre de liens entrants.</p>
                
                <div class="network-controls">
                    <button onclick="resetZoom()" class="active">Réinitialiser vue</button>
                    <button onclick="toggleLabels()">Basculer libellés</button>
                    <button onclick="highlightOrphans()">Surligner orphelines</button>
                </div>
                
                <div id="network-graph"></div>
                
                <p style="margin-top: 15px; color: #6c757d; font-size: 0.9em;">
                    <strong>Légende :</strong> 
                    Taille = liens entrants | 
                    Vert = bien connecté | 
                    Jaune = moyennement connecté | 
                    Rouge = peu connecté
                </p>
            </div>
            
            <script>
            // Données du réseau
            const networkData = {json.dumps(network_data, ensure_ascii=False)};
            
            // Configuration du graphique
            const width = 1160;
            const height = 600;
            const margin = {{top: 20, right: 20, bottom: 20, left: 20}};
            
            // Créer le SVG
            const svg = d3.select("#network-graph")
                .append("svg")
                .attr("width", width)
                .attr("height", height);
            
            const g = svg.append("g");
            
            // Zoom
            const zoom = d3.zoom()
                .scaleExtent([0.1, 3])
                .on("zoom", function(event) {{
                    g.attr("transform", event.transform);
                }});
            
            svg.call(zoom);
            
            // Échelles pour la taille et couleur des nœuds
            const maxInbound = d3.max(networkData.nodes, d => d.inbound) || 1;
            const radiusScale = d3.scaleSqrt()
                .domain([0, maxInbound])
                .range([4, 25]);
            
            const colorScale = d3.scaleLinear()
                .domain([0, maxInbound * 0.3, maxInbound * 0.7, maxInbound])
                .range(['#dc3545', '#ffc107', '#28a745', '#007bff']);
            
            // Simulation de forces
            const simulation = d3.forceSimulation(networkData.nodes)
                .force("link", d3.forceLink(networkData.edges).id(d => d.id).distance(80))
                .force("charge", d3.forceManyBody().strength(-300))
                .force("center", d3.forceCenter(width / 2, height / 2))
                .force("collision", d3.forceCollide().radius(d => radiusScale(d.inbound) + 2));
            
            // Créer les liens
            const links = g.append("g")
                .selectAll("line")
                .data(networkData.edges)
                .enter().append("line")
                .attr("stroke", "#999")
                .attr("stroke-opacity", 0.6)
                .attr("stroke-width", 1);
            
            // Créer les nœuds
            const nodes = g.append("g")
                .selectAll("circle")
                .data(networkData.nodes)
                .enter().append("circle")
                .attr("r", d => radiusScale(d.inbound))
                .attr("fill", d => colorScale(d.inbound))
                .attr("stroke", "#fff")
                .attr("stroke-width", 1.5)
                .call(d3.drag()
                    .on("start", dragstarted)
                    .on("drag", dragged)
                    .on("end", dragended));
            
            // Labels des nœuds
            const labels = g.append("g")
                .selectAll("text")
                .data(networkData.nodes)
                .enter().append("text")
                .text(d => d.label)
                .attr("font-size", "10px")
                .attr("text-anchor", "middle")
                .attr("dy", ".35em")
                .attr("fill", "#333")
                .style("pointer-events", "none")
                .style("opacity", 0.8);
            
            // Tooltip
            const tooltip = d3.select("body").append("div")
                .attr("class", "tooltip")
                .style("opacity", 0);
            
            // Events pour les nœuds
            nodes.on("mouseover", function(event, d) {{
                    tooltip.transition().duration(200).style("opacity", .9);
                    tooltip.html(`
                        <strong>${{d.label}}</strong><br/>
                        Liens entrants: ${{d.inbound}}<br/>
                        Liens sortants: ${{d.outbound}}<br/>
                        <small>${{d.id}}</small>
                    `)
                    .style("left", (event.pageX + 10) + "px")
                    .style("top", (event.pageY - 28) + "px");
                }})
                .on("mouseout", function(d) {{
                    tooltip.transition().duration(500).style("opacity", 0);
                }});
            
            // Animation de la simulation
            simulation.on("tick", () => {{
                links
                    .attr("x1", d => d.source.x)
                    .attr("y1", d => d.source.y)
                    .attr("x2", d => d.target.x)
                    .attr("y2", d => d.target.y);
                
                nodes
                    .attr("cx", d => d.x)
                    .attr("cy", d => d.y);
                
                labels
                    .attr("x", d => d.x)
                    .attr("y", d => d.y);
            }});
            
            // Fonctions de contrôle
            let labelsVisible = true;
            let orphansHighlighted = false;
            
            function resetZoom() {{
                svg.transition().duration(750).call(
                    zoom.transform,
                    d3.zoomIdentity
                );
            }}
            
            function toggleLabels() {{
                labelsVisible = !labelsVisible;
                labels.style("opacity", labelsVisible ? 0.8 : 0);
                
                // Mettre à jour le bouton
                d3.select('button:nth-child(2)')
                    .classed('active', labelsVisible);
            }}
            
            function highlightOrphans() {{
                orphansHighlighted = !orphansHighlighted;
                
                nodes.attr("stroke", d => {{
                    if (orphansHighlighted && d.inbound === 0) {{
                        return "#ff0000";
                    }}
                    return "#fff";
                }})
                .attr("stroke-width", d => {{
                    if (orphansHighlighted && d.inbound === 0) {{
                        return 3;
                    }}
                    return 1.5;
                }});
                
                // Mettre à jour le bouton
                d3.select('button:nth-child(3)')
                    .classed('active', orphansHighlighted);
            }}
            
            // Fonctions de drag
            function dragstarted(event, d) {{
                if (!event.active) simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            }}
            
            function dragged(event, d) {{
                d.fx = event.x;
                d.fy = event.y;
            }}
            
            function dragended(event, d) {{
                if (!event.active) simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            }}
            </script>
            """
        
        # Analyses de qualité du contenu
        if 'content_quality' in analysis:
            content_analysis = analysis['content_quality']
            
            # Analyse du nombre de mots
            if 'word_analysis' in content_analysis:
                word_data = content_analysis['word_analysis']
                html_content += f"""
                <div class="section">
                    <h2>Qualité du contenu</h2>
                    <h3>Analyse du nombre de mots</h3>
                    
                    <div class="chart-container">
                        <div class="chart">
                            <h4>Répartition</h4>
                            <p>Total : <strong>{word_data['total_pages']:,}</strong> pages</p>
                            <p>📈 Moyenne: <strong>{word_data['avg_words']:.0f}</strong> mots</p>
                            <p>📊 Médiane: <strong>{word_data['median_words']:.0f}</strong> mots</p>
                        </div>
                        <div class="chart">
                            <h4>Classification</h4>
                            <p>Contenu thin (&lt;300) : <strong>{len(word_data['thin_content'])}</strong></p>
                            <p>Contenu qualité (300-1500) : <strong>{len(word_data['quality_content'])}</strong></p>
                            <p>Contenu riche (&gt;1500) : <strong>{len(word_data['rich_content'])}</strong></p>
                        </div>
                    </div>
                """
                
                # Afficher les pages thin content comme recommandations
                if word_data['thin_content']:
                    html_content += """
                    <div class="warning">
                        <h4>Pages avec contenu thin (&lt; 300 mots)</h4>
                        <p>Ces pages ont peu de contenu et devraient être évitées pour le maillage entrant ou enrichies :</p>
                        <ul>
                    """
                    for page in word_data['thin_content'][:10]:  # Limiter à 10
                        html_content += f"<li><strong>{page['word_count']} mots</strong> - {page['url']}</li>"
                    if len(word_data['thin_content']) > 10:
                        html_content += f"<li><em>... et {len(word_data['thin_content']) - 10} autres pages</em></li>"
                    html_content += "</ul></div>"
                
                html_content += "</div>"
            
            # Analyse de cohérence Title/H1
            if 'title_h1_coherence' in content_analysis:
                coherence_data = content_analysis['title_h1_coherence']
                html_content += f"""
                <div class="section">
                    <h2>Cohérence title / H1</h2>
                    
                    <div class="chart-container">
                        <div class="chart">
                            <h4>Statistiques</h4>
                            <p>Pages analysées : <strong>{coherence_data['total_pages_with_both']:,}</strong></p>
                            <p>✅ Identiques: <strong>{len(coherence_data['identical'])}</strong></p>
                            <p>🟡 Similaires: <strong>{len(coherence_data['similar'])}</strong></p>
                            <p>🔴 Différents: <strong>{len(coherence_data['different'])}</strong></p>
                        </div>
                        <div class="chart">
                            <h4>Problèmes détectés</h4>
                            <p>❌ H1 manquant: <strong>{len(coherence_data['missing_h1'])}</strong></p>
                            <p>❌ Title manquant: <strong>{len(coherence_data['missing_title'])}</strong></p>
                        </div>
                    </div>
                """
                
                # Afficher les incohérences
                if coherence_data['different']:
                    html_content += """
                    <div class="warning">
                        <h4>Pages avec title et H1 très différents</h4>
                        <p>Ces pages ont une incohérence qui peut nuire au SEO :</p>
                        <table>
                            <tr><th>URL</th><th>Title</th><th>H1</th></tr>
                    """
                    for page in coherence_data['different'][:5]:  # Limiter à 5
                        html_content += f"""<tr>
                            <td class='url'>{page['url']}</td>
                            <td>{page['title'][:60]}{'...' if len(page['title']) > 60 else ''}</td>
                            <td>{page['h1'][:60]}{'...' if len(page['h1']) > 60 else ''}</td>
                        </tr>"""
                    html_content += "</table></div>"
                
                html_content += "</div>"
            
            # Analyse des pages de conversion
            if 'conversion_pages' in content_analysis:
                conversion_data = content_analysis['conversion_pages']
                html_content += f"""
                <div class="section">
                    <h2>Pages de conversion identifiées</h2>
                    <p>Ces pages sont cruciales pour votre business et doivent être bien maillées !</p>
                    
                    <div class="success">
                        <p><strong>🎯 {conversion_data['total_conversion_pages']} pages de conversion trouvées</strong> 
                        ({conversion_data['conversion_rate_potential']:.1f}% du site)</p>
                    </div>
                    
                    <div class="chart-container">
                """
                
                # Afficher par catégorie
                categories_with_pages = {k: v for k, v in conversion_data['by_category'].items() if v}
                for category, pages in categories_with_pages.items():
                    html_content += f"""
                    <div class="chart">
                        <h4>{category.title().lower().capitalize()}</h4>
                        <p><strong>{len(pages)} pages</strong></p>
                        <ul>
                    """
                    for page in pages[:3]:  # Afficher les 3 premières
                        html_content += f"<li>{page['url']}</li>"
                    if len(pages) > 3:
                        html_content += f"<li><em>... et {len(pages) - 3} autres</em></li>"
                    html_content += "</ul></div>"
                
                html_content += """
                    </div>
                    
                    <div class="recommendations">
                        <h4>Recommandations pour les pages de conversion</h4>
                        <ul>
                            <li><strong>Maillage entrant renforcé</strong> : Ces pages doivent recevoir plus de liens éditoriaux</li>
                            <li><strong>Ancres contextuelles</strong> : Utilisez des ancres qui expliquent la valeur ajoutée</li>
                            <li><strong>Position stratégique</strong> : Placez les liens dans le contenu, pas seulement en navigation</li>
                            <li><strong>Pages de contenu vers conversion</strong> : Liez depuis vos articles vers ces pages</li>
                        </ul>
                    </div>
                </div>
                """
        
        # Qualité des ancres
        if 'anchor_quality' in analysis:
            anchor_quality = analysis['anchor_quality']
            html_content += f"""
            <div class="section">
                <h2>Qualité des ancres éditoriales</h2>
                <div class="chart-container">
                    <div class="chart">
                        <h4>Répartition</h4>
                        <p>Bonne qualité : <strong>{len(anchor_quality.get('good_quality', []))}</strong></p>
                        <p>Trop courtes : <strong>{len(anchor_quality.get('too_short', []))}</strong></p>
                        <p>Trop longues : <strong>{len(anchor_quality.get('too_long', []))}</strong></p>
                        <p>Sur-optimisées : <strong>{len(anchor_quality.get('keyword_stuffed', []))}</strong></p>
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
                <h2>Distribution thématique</h2>
            """
            
            if thematic.get('top_anchor_keywords'):
                # Créer des graphiques simples en barres avec CSS
                keywords_data = list(thematic['top_anchor_keywords'].items())[:10]  # Top 10
                max_count = max([count for _, count in keywords_data]) if keywords_data else 1
                
                html_content += """
                <div class="chart-container">
                    <div class="chart">
                        <h4>Mots-clés principaux dans les ancres</h4>
                        <div class="bar-chart">
                """
                
                for keyword, count in keywords_data:
                    percentage = (count / max_count) * 100
                    html_content += f"""
                            <div class="bar-item">
                                <span class="bar-label">{keyword}</span>
                                <div class="bar-container">
                                    <div class="bar-fill" style="width: {percentage}%"></div>
                                    <span class="bar-value">{count}</span>
                                </div>
                            </div>
                    """
                
                html_content += """
                        </div>
                    </div>
                """
            
            if thematic.get('destination_categories'):
                categories_data = list(thematic['destination_categories'].items())
                total_categories = sum([count for _, count in categories_data]) if categories_data else 1
                
                html_content += """
                    <div class="chart">
                        <h4>Types de pages liées</h4>
                        <div class="pie-chart">
                """
                
                colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF']
                for i, (category, count) in enumerate(categories_data):
                    percentage = (count / total_categories) * 100
                    color = colors[i % len(colors)]
                    html_content += f"""
                            <div class="pie-item">
                                <span class="pie-color" style="background-color: {color}"></span>
                                <span class="pie-label">{category}: {count} ({percentage:.1f}%)</span>
                            </div>
                    """
                
                html_content += """
                        </div>
                    </div>
                </div>
                """
            else:
                html_content += """
                </div>
                """
            
            # Afficher aussi le nuage de mots-clés en complément
            if thematic.get('top_anchor_keywords'):
                html_content += """
                <h4>Nuage de mots-clés</h4>
                <div class="keyword-cloud">
                """
                for keyword, count in list(thematic['top_anchor_keywords'].items())[:15]:
                    html_content += f"""<span class="keyword-tag">{keyword} ({count})</span>"""
                html_content += "</div>"
            
            html_content += "</div>"
        
        # Analyse sémantique avancée CamemBERT
        if 'advanced_semantic' in analysis and analysis['advanced_semantic']:
            html_content += self.generate_semantic_analysis_section(analysis['advanced_semantic'])
        
        # Pages les plus liées
        if analysis['most_linked_pages']:
            html_content += """
            <div class="section">
                <h2>Pages les plus liées (liens entrants éditoriaux)</h2>
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
                <h2>Pages orphelines</h2>
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
                <h2>Ancres potentiellement sur-optimisées</h2>
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
                <h2>Recommandations prioritaires</h2>
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
        csv_export_file = self.generate_csv_export(analysis, website_url, source_file, url_filter)
        
        return report_file

    def generate_csv_export(self, analysis, website_url, source_file, url_filter=None):
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
                
                # Option de filtrage par préfixe d'URL
                print("\n🎯 FILTRAGE D'URLs (optionnel)")
                print("Vous pouvez limiter l'analyse à une section spécifique du site.")
                print("Exemple: https://monsite.com/blog/ pour ne garder que les pages du blog")
                
                url_filter = input("🔍 Préfixe d'URL à conserver (vide = tout le site): ").strip()
                if url_filter and not url_filter.startswith('http'):
                    print("⚠️  Le filtre doit commencer par http:// ou https://")
                    url_filter = None
                
                if url_filter:
                    print(f"✅ Filtrage activé: seules les URLs commençant par '{url_filter}' seront analysées")
                
                csv_file = self.run_new_crawl(website_url, url_filter)
                if csv_file:
                    input("\n⏸️  Appuyez sur Entrée pour lancer l'analyse...")
                    self.analyze_csv(csv_file, website_url, url_filter)
                
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
                            
                            # Option de filtrage pour CSV existant aussi
                            url_filter = None
                            if website_url:
                                print("\n🎯 FILTRAGE D'URLs (optionnel)")
                                url_filter = input("🔍 Préfixe d'URL à conserver (vide = tout): ").strip() or None
                                if url_filter and not url_filter.startswith('http'):
                                    print("⚠️  Le filtre doit commencer par http:// ou https://")
                                    url_filter = None
                            
                            self.analyze_csv(selected_file, website_url, url_filter)
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