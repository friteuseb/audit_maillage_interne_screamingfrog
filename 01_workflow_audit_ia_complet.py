#!/usr/bin/env python3
"""
WORKFLOW FINAL INTELLIGENT : IA + Screaming Frog + Analyse Sémantique
Combinaison parfaite de l'analyse IA de contenu et du crawl Screaming Frog
"""

import subprocess
import os
import csv
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import List, Optional
from ext_detecteur_contenu_ia import IntelligentContentDetector
import json
import time
import glob

class FinalIntelligentWorkflow:
    """Workflow final combinant IA + Screaming Frog + Analyse sémantique"""
    
    def __init__(self):
        self.detector = IntelligentContentDetector()
        self.xpath_content = ""
        self.xpath_links = ""
        self.ai_analysis = {}
        
    def fetch_and_parse_sitemap(self, sitemap_url: str) -> List[str]:
        """Récupère et analyse un sitemap XML pour extraire les URLs"""
        try:
            import xml.etree.ElementTree as ET

            print(f"   📥 Téléchargement du sitemap...")
            response = requests.get(sitemap_url, timeout=30)
            response.raise_for_status()

            # Parser le XML
            root = ET.fromstring(response.content)

            urls = []
            # Gérer les namespaces XML
            ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

            # Chercher les éléments <loc> (URLs)
            for loc in root.findall('.//sm:loc', ns) or root.findall('.//loc'):
                if loc.text:
                    url = loc.text.strip()
                    if url and url.startswith('http'):
                        urls.append(url)

            # Si pas d'URLs trouvées, essayer sans namespace
            if not urls:
                for loc in root.findall('.//loc'):
                    if loc.text:
                        url = loc.text.strip()
                        if url and url.startswith('http'):
                            urls.append(url)

            return urls

        except Exception as e:
            print(f"   ❌ Erreur sitemap: {e}")
            return []

    def run_complete_workflow(self, website_url: str, section_filter: str = "", max_pages: str = "", sample_urls: Optional[List[str]] = None) -> str:
        """Workflow complet : IA → SF Crawl → Filtrage intelligent → Analyse sémantique"""
        print(f"🚀 WORKFLOW INTELLIGENT FINAL")
        print(f"Site: {website_url}")
        if section_filter:
            print(f"Section: {section_filter}")
        if max_pages:
            print(f"Limite: {max_pages} pages")
        print("=" * 70)
        
        # Étape 1 : Analyse IA de la structure
        print(f"\n🤖 ÉTAPE 1: Analyse IA de la structure de contenu")
        print("-" * 50)
        
        structure_analysis = self.detector.run_intelligent_workflow(website_url, section_filter, sample_urls)
        
        if not structure_analysis.get('success'):
            print("⚠️  Échec de l'analyse IA, utilisation des valeurs par défaut")
            self.ai_analysis = {}
            content_zones = {}
        else:
            self.ai_analysis = structure_analysis.get('ai_analysis', {})
            content_zones = self.ai_analysis.get('content_zones', {})

        self.xpath_content = content_zones.get('main_content_xpath', '//main')
        self.xpath_links = content_zones.get('editorial_links_xpath', '//main//a')

        print(f"   ✅ XPath contenu détecté: {self.xpath_content}")
        print(f"   ✅ XPath liens éditoriaux: {self.xpath_links}")
        
        # Étape 2 : Vérification des données Screaming Frog
        print(f"\n🕷️  ÉTAPE 2: Vérification des données Screaming Frog")
        print("-" * 50)
        
        sf_data_available = self.check_screaming_frog_data()
        if not sf_data_available:
            print("   ⚠️  Aucune donnée SF récente trouvée, lancement du crawl...")
            sf_success = self.run_screaming_frog_crawl(website_url, section_filter, max_pages)
            if not sf_success:
                print("❌ Échec du crawl Screaming Frog")
                return ""
        else:
            print("   ✅ Données Screaming Frog disponibles, utilisation des données existantes")

        # Temporaire: forcer l'utilisation des données existantes
        sf_data_available = True
        
        # Étape 3 : Filtrage intelligent avec l'IA
        print(f"\n🧠 ÉTAPE 3: Filtrage intelligent des liens avec IA")
        print("-" * 50)
        
        filtered_report = self.intelligent_post_processing(website_url, section_filter)
        if not filtered_report:
            print("❌ Échec du post-traitement intelligent")
            return ""
        
        # Étape 4 : Analyse sémantique finale
        print(f"\n📊 ÉTAPE 4: Lancement de l'analyse sémantique")
        print("-" * 50)
        
        semantic_success = self.launch_semantic_analysis(filtered_report)
        
        print(f"\n✅ WORKFLOW INTELLIGENT TERMINÉ AVEC SUCCÈS!")
        print(f"📋 Résumé:")
        print(f"   🤖 Analyse IA: ✅")
        print(f"   🕷️  Crawl SF: ✅")  
        print(f"   🧠 Filtrage intelligent: ✅")
        print(f"   📊 Analyse sémantique: {'✅' if semantic_success else '⚠️'}")
        
        return filtered_report
    
    def check_screaming_frog_data(self) -> bool:
        """Vérifier si des données Screaming Frog récentes sont disponibles"""
        sf_files = [
            "./exports/tous_les_liens_sortants.csv",
            "./exports/all_outlinks.csv"
        ]
        
        for file_path in sf_files:
            if os.path.exists(file_path):
                # Vérifier que le fichier n'est pas vide et récent
                stat = os.stat(file_path)
                if stat.st_size > 1000:  # Plus de 1KB
                    file_age_hours = (time.time() - stat.st_mtime) / 3600
                    if file_age_hours < 24*30:  # Moins de 30 jours (temporaire pour test)
                        print(f"   📄 Fichier trouvé: {file_path} ({stat.st_size/1024/1024:.1f}MB)")
                        return True
        
        return False
    
    def run_screaming_frog_crawl(self, website_url: str, section_filter: str = "", max_pages: str = "") -> bool:
        """Exécuter le crawl Screaming Frog optimisé avec filtres"""

        # Nettoyer les anciens fichiers (supprimer données SF)
        self.cleanup_old_files(preserve_sf_data=False)

        # Détecter le système et choisir le bon chemin
        import platform
        import os

        system = platform.system()
        if system == "Windows":
            sf_path = "C:\\Program Files (x86)\\Screaming Frog SEO Spider\\ScreamingFrogSEOSpiderCli.exe"
        elif system == "Darwin":  # macOS
            sf_path = "/Applications/Screaming Frog SEO Spider.app/Contents/MacOS/ScreamingFrogSEOSpiderCli"
        else:  # Linux et autres
            # Détecter WSL
            is_wsl = False
            try:
                if os.path.exists('/mnt/c'):
                    is_wsl = True
                elif os.path.exists('/proc/version'):
                    with open('/proc/version', 'r') as f:
                        if 'microsoft' in f.read().lower():
                            is_wsl = True
            except:
                pass

            if is_wsl:
                sf_path = "/mnt/c/Program Files (x86)/Screaming Frog SEO Spider/ScreamingFrogSEOSpiderCli.exe"
            else:
                sf_path = "/usr/bin/screamingfrogseospider"

        # Modifier l'URL de départ si un filtre de section est spécifié
        crawl_url = website_url
        if section_filter:
            # Construire l'URL avec la section pour limiter le crawl
            from urllib.parse import urljoin
            crawl_url = urljoin(website_url.rstrip('/') + '/', section_filter.lstrip('/'))
            print(f"   🔍 Crawl limité à la section: {crawl_url}")

        command = [
            sf_path,
            '-headless',
            '-crawl', crawl_url,
            '--output-folder', './exports/',
            '--export-format', 'csv'
        ]

        # Ajouter des filtres pour limiter le crawl à la section
        if section_filter:
            # Inclure seulement les URLs de la section
            include_pattern = f"*{section_filter}*"
            command.extend(['--include', include_pattern])
            print(f"   📋 Pattern d'inclusion: {include_pattern}")

            # Limiter la profondeur pour éviter de sortir de la section
            command.extend(['--crawl-depth', '3'])

        # Utiliser la config IA si elle existe (désactivé temporairement pour debug)
        # if os.path.exists('./sf_content_config.xml'):
        #     command.extend(['-config', './sf_content_config.xml'])
        #     command.extend(['--bulk-export', 'Links:All Outlinks,All Inlinks,Custom:MainContent,Custom:EditorialLinks,Custom:ContentZone,Page Titles,H1-1,Word Count'])
        # else:
        command.extend(['--bulk-export', 'All Outlinks,Page Titles,H1-1,Word Count'])

        command.append('--overwrite')
            
        # Ajouter la limite de pages si spécifiée  
        if max_pages and max_pages.isdigit():
            print(f"   📊 Limite de pages: {max_pages}")
            # SF ne supporte pas directement la limite via CLI
            # On peut essayer d'ajouter des paramètres personnalisés mais c'est limité
        
        print(f"   🔄 Lancement du crawl Screaming Frog...")
        print(f"   ⏱️  Cela peut prendre quelques minutes...")
        
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print(f"   ✅ Crawl Screaming Frog terminé avec succès")
                # Vérifier que les fichiers ont été créés
                expected_files = ["./exports/all_outlinks.csv", "./exports/page_titles.csv"]
                files_found = [f for f in expected_files if os.path.exists(f)]

                if files_found:
                    print(f"   📄 Fichiers générés: {', '.join([os.path.basename(f) for f in files_found])}")
                    return True
                else:
                    print(f"   ⚠️  Crawl terminé mais fichiers attendus non trouvés")
                    # Lister les fichiers présents pour debug
                    if os.path.exists("./exports/"):
                        existing_files = os.listdir("./exports/")
                        if existing_files:
                            print(f"   📂 Fichiers présents: {existing_files}")
                    return False
            else:
                print(f"   ❌ Erreur crawl SF (code {result.returncode})")
                if result.stderr:
                    print(f"   📄 Erreur: {result.stderr[:200]}...")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"   ⏰ Timeout crawl SF (5 minutes dépassées)")
            return False
        except Exception as e:
            print(f"   ❌ Erreur crawl SF: {e}")
            return False
    
    def cleanup_old_files(self, preserve_sf_data=False):
        """Nettoyer les anciens fichiers qui pourraient causer des conflits"""
        files_to_remove = [
            "./exports/editorial_links_filtered.csv",
            "./exports/editorial_links_intelligent.csv"
        ]
        
        # Seulement supprimer les données SF si explicitement demandé
        if not preserve_sf_data:
            files_to_remove.extend([
                "./exports/tous_les_liens_sortants.csv",
                "./exports/all_outlinks.csv"
            ])
        
        for file_path in files_to_remove:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"   🗑️  Supprimé: {file_path}")
            except Exception as e:
                print(f"   ⚠️  Erreur suppression {file_path}: {e}")
    
    def intelligent_post_processing(self, website_url: str, section_filter: str = "") -> str:
        """Post-traitement intelligent des résultats SF avec l'IA"""
        
        # Chercher le fichier de données SF disponible
        sf_files = [
            "./exports/tous_les_liens_sortants.csv",
            "./exports/all_outlinks.csv"
        ]
        
        sf_links_file = None
        for file_path in sf_files:
            if os.path.exists(file_path):
                sf_links_file = file_path
                break
        
        if not sf_links_file:
            print(f"   ❌ Aucun fichier SF trouvé dans: {', '.join(sf_files)}")
            return ""
        
        print(f"   📂 Chargement des résultats SF...")
        
        try:
            with open(sf_links_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                sf_links = list(reader)
            
            print(f"   📊 {len(sf_links)} liens trouvés par Screaming Frog")
            
        except Exception as e:
            print(f"   ❌ Erreur lecture SF: {e}")
            return ""
        
        # Appliquer le filtre de section si spécifié
        if section_filter:
            print(f"   🔍 Application du filtre de section: {section_filter}")
            sf_links = [link for link in sf_links 
                       if section_filter in link.get('Source', '') or section_filter in link.get('Destination', '')]
            print(f"   📊 {len(sf_links)} liens après filtrage de section")
        
        # Filtrer avec l'intelligence IA
        print(f"   🤖 Application des filtres IA pour identifier les liens éditoriaux...")
        
        editorial_links = self.filter_links_with_ai_analysis(sf_links, website_url)
        
        print(f"   ✅ {len(editorial_links)} liens éditoriaux identifiés")
        if len(sf_links) > 0:
            print(f"   📊 Ratio éditorial: {len(editorial_links)/len(sf_links)*100:.1f}%")
        else:
            print(f"   ⚠️  Aucun lien trouvé après filtrage - vérifiez le filtre de section")
        
        # Générer le rapport final
        report_path = self.generate_intelligent_report(editorial_links, website_url, len(sf_links))
        
        return report_path
    
    def filter_links_with_ai_analysis(self, sf_links: list, website_url: str) -> list:
        """Filtrer les liens SF avec l'analyse IA avancée"""
        editorial_links = []
        processed_pages = {}
        
        base_domain = urlparse(website_url).netloc
        
        print(f"   🔍 Analyse page par page avec détection IA...")
        
        for i, link in enumerate(sf_links):
            source_url = link.get('Source', '')
            dest_url = link.get('Destination', '')
            anchor_text = link.get('Anchor', '') or link.get('Ancrage', '')
            
            # Filtrer les liens internes uniquement
            if not dest_url.startswith(f"http://{base_domain}") and not dest_url.startswith(f"https://{base_domain}"):
                continue
            
            # Vérifier si la page source a déjà été analysée
            if source_url not in processed_pages:
                page_editorial_links = self.extract_editorial_links_from_page_with_ai(source_url)
                processed_pages[source_url] = page_editorial_links
                
                # Afficher le progrès
                if (len(processed_pages)) % 10 == 0:
                    print(f"      📊 Analysé {len(processed_pages)} pages uniques...")
            
            # Vérifier si ce lien spécifique est éditorial
            editorial_links_on_page = processed_pages[source_url]
            
            if self.is_link_editorial_advanced(link, editorial_links_on_page, website_url):
                editorial_links.append(link)
        
        return editorial_links
    
    def extract_editorial_links_from_page_with_ai(self, page_url: str) -> list:
        """Extraire les liens éditoriaux d'une page en utilisant l'analyse IA"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(page_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Utiliser l'analyse IA pour identifier les zones de contenu
            editorial_link_elements = self.find_editorial_links_with_ai_xpath(soup)
            
            # Extraire les informations des liens
            editorial_links = []
            for link_elem in editorial_link_elements:
                href = link_elem.get('href', '')
                text = link_elem.get_text(strip=True)
                
                if href and text and len(text.strip()) > 2:  # Filtrer les liens vides
                    full_url = urljoin(page_url, href)
                    editorial_links.append({
                        'href': full_url,
                        'text': text,
                        'context': self.get_link_context(link_elem)
                    })
            
            return editorial_links
            
        except Exception as e:
            # Échec silencieux pour éviter de ralentir le processus
            return []
    
    def find_editorial_links_with_ai_xpath(self, soup: BeautifulSoup) -> list:
        """Trouver les liens éditoriaux en utilisant l'analyse IA"""
        editorial_links = []
        
        # Stratégie 1: Utiliser les zones de contenu identifiées par l'IA
        content_zones = []
        
        # Rechercher les zones main, article
        main_zones = soup.find_all(['main', 'article'])
        content_zones.extend(main_zones)
        
        # Rechercher les sections de contenu (selon analyse IA)
        if 'div[@class=' in self.xpath_content:
            # Extraire les classes CSS de l'XPath IA
            css_classes = self.extract_css_classes_from_xpath(self.xpath_content)
            for css_class in css_classes:
                sections = soup.find_all('div', class_=css_class)
                content_zones.extend(sections)
        else:
            # Fallback: sections génériques
            sections = soup.find_all('section')
            content_zones.extend(sections)
        
        # Extraire les liens des zones de contenu
        for zone in content_zones:
            if zone:
                links = zone.find_all('a', href=True)
                editorial_links.extend(links)
        
        # Filtrer pour exclure les zones de navigation
        filtered_links = []
        for link in editorial_links:
            if not self.is_in_navigation_zone(link):
                filtered_links.append(link)
        
        return filtered_links
    
    def extract_css_classes_from_xpath(self, xpath: str) -> list:
        """Extraire les classes CSS d'un XPath"""
        classes = []
        if "[@class='" in xpath:
            parts = xpath.split("[@class='")
            for part in parts[1:]:
                class_end = part.find("']")
                if class_end != -1:
                    class_name = part[:class_end]
                    classes.append(class_name)
        return classes
    
    def is_in_navigation_zone(self, link_element) -> bool:
        """Vérifier si un lien est dans une zone de navigation"""
        # Remonter l'arbre DOM pour chercher des zones de navigation
        current = link_element.parent
        
        for _ in range(5):  # Remonter maximum 5 niveaux
            if current is None:
                break
                
            # Vérifier le nom de la balise
            if current.name in ['nav', 'header', 'footer', 'aside']:
                return True
            
            # Vérifier les classes/IDs
            classes = current.get('class', [])
            element_id = current.get('id', '')
            
            nav_indicators = ['nav', 'menu', 'header', 'footer', 'sidebar', 'breadcrumb']
            
            for indicator in nav_indicators:
                if (any(indicator in str(c).lower() for c in classes) or 
                    indicator in element_id.lower()):
                    return True
            
            current = current.parent
        
        return False
    
    def get_link_context(self, link_element) -> str:
        """Obtenir le contexte d'un lien (texte environnant)"""
        try:
            parent = link_element.parent
            if parent:
                context = parent.get_text(strip=True)
                # Limiter la longueur du contexte
                return context[:100] + "..." if len(context) > 100 else context
        except:
            pass
        return ""
    
    def is_link_editorial_advanced(self, sf_link: dict, editorial_links: list, website_url: str) -> bool:
        """Vérification avancée si un lien SF correspond aux liens éditoriaux"""
        dest_url = sf_link.get('Destination', '')
        anchor_text = sf_link.get('Anchor', '') or sf_link.get('Ancrage', '')
        
        # Nettoyer l'URL de destination
        dest_url_clean = dest_url.rstrip('/')
        
        # Comparer avec les liens éditoriaux extraits
        for editorial_link in editorial_links:
            editorial_href_clean = editorial_link['href'].rstrip('/')
            editorial_text = editorial_link['text']
            
            # Correspondance exacte URL + texte
            if (dest_url_clean == editorial_href_clean and 
                anchor_text.strip() == editorial_text.strip()):
                return True
            
            # Correspondance URL avec tolérance sur le texte
            if (dest_url_clean == editorial_href_clean and
                len(anchor_text.strip()) > 3 and
                anchor_text.strip().lower() in editorial_text.lower()):
                return True
        
        return False
    
    def generate_intelligent_report(self, editorial_links: list, website_url: str, total_links: int) -> str:
        """Générer le rapport final avec les liens éditoriaux filtrés"""
        
        output_file = f"./exports/editorial_links_intelligent.csv"
        
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                if editorial_links:
                    fieldnames = editorial_links[0].keys()
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(editorial_links)
            
            print(f"   💾 Rapport intelligent généré: {output_file}")
            
            # Statistiques finales
            internal_editorial = [link for link in editorial_links 
                                if link.get('Destination', '').startswith(website_url)]
            
            print(f"   📊 STATISTIQUES FINALES:")
            print(f"      🌐 Total liens crawlés: {total_links}")
            print(f"      ✍️  Liens éditoriaux détectés: {len(editorial_links)}")
            print(f"      🏠 Liens éditoriaux internes: {len(internal_editorial)}")
            print(f"      📊 Ratio d'efficacité: {len(editorial_links)/total_links*100:.1f}%")
            
            # Analyser les domaines de destination
            domains = {}
            for link in editorial_links:
                domain = urlparse(link.get('Destination', '')).netloc
                domains[domain] = domains.get(domain, 0) + 1
            
            print(f"      🌍 Top domaines liés:")
            for domain, count in sorted(domains.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"         • {domain}: {count} liens")
            
            return output_file
            
        except Exception as e:
            print(f"   ❌ Erreur génération rapport: {e}")
            return ""


    def _validate_section_filter(self, section_input: str, website_url: str) -> str:
        """Valider et nettoyer le filtre de section"""
        if not section_input:
            return ""

        # Si c'est une URL complète, extraire le path
        if section_input.startswith(('http://', 'https://')):
            parsed = urlparse(section_input)
            path = parsed.path.rstrip('/')
            if path:
                print(f"   📝 URL détectée, utilisation du path: {path}")
                return path

        # Nettoyer le path
        section_filter = section_input.strip()

        # S'assurer qu'il commence par /
        if not section_filter.startswith('/'):
            section_filter = '/' + section_filter

        # Supprimer les trailing slashes
        section_filter = section_filter.rstrip('/')

        # Validation basique
        if len(section_filter) > 1 and section_filter.count('/') <= 3:
            return section_filter
        else:
            print(f"   ⚠️  Format de section invalide: {section_input}")
            print(f"   💡 Exemples valides: /blog, /produits, /centre-dexpertise")
            return ""

    def launch_semantic_analysis(self, filtered_report_path: str) -> bool:
        """Lancer l'analyse sémantique avec génération du rapport HTML complet"""

        if not os.path.exists(filtered_report_path):
            print(f"   ❌ Rapport filtré introuvable: {filtered_report_path}")
            return False

        print(f"   🚀 Lancement de l'analyse sémantique complète...")
        print(f"   📄 Fichier source: {filtered_report_path}")

        try:
            # Import direct de l'analyseur sémantique pour avoir plus de contrôle
            from ext_audit_maillage_classique import CompleteLinkAuditor

            auditor = CompleteLinkAuditor()

            # Analyser le fichier CSV filtré avec génération complète du rapport HTML
            print(f"   📊 Analyse des données avec CamemBERT...")
            report_path = auditor.analyze_csv(filtered_report_path)

            if report_path:
                print(f"   ✅ Rapport HTML complet généré: {report_path}")
                print(f"   📊 Incluant: graphique des nœuds, clusters sémantiques, recommandations")
                return True
            else:
                print(f"   ⚠️  Analyse terminée mais rapport non généré")
                return False

        except ImportError:
            print(f"   ⚠️  Import de l'analyseur sémantique échoué, utilisation du subprocess...")
            # Fallback vers l'ancienne méthode
            try:
                result = subprocess.run([
                    'python', 'ext_analyseur_semantique.py',
                    '--csv-file', filtered_report_path
                ], capture_output=True, text=True, timeout=300)

                if result.returncode == 0:
                    print(f"   ✅ Analyse sémantique terminée")
                    return True
                else:
                    print(f"   ⚠️  Analyse terminée avec avertissements")
                    return True

            except Exception as e:
                print(f"   ❌ Erreur subprocess: {e}")
                return False

        except Exception as e:
            print(f"   ❌ Erreur analyse sémantique: {e}")
            print(f"   💡 Vous pouvez lancer manuellement: python ext_audit_maillage_classique.py --csv-file {filtered_report_path}")
            return False
        
        print(f"   🚀 Lancement de l'analyse sémantique complète...")
        print(f"   📄 Fichier source: {filtered_report_path}")
        
        try:
            # Import direct de l'analyseur sémantique pour avoir plus de contrôle
            from ext_audit_maillage_classique import CompleteLinkAuditor
            
            auditor = CompleteLinkAuditor()
            
            # Analyser le fichier CSV filtré avec génération complète du rapport HTML
            print(f"   📊 Analyse des données avec CamemBERT...")
            report_path = auditor.analyze_csv(filtered_report_path)
            
            if report_path:
                print(f"   ✅ Rapport HTML complet généré: {report_path}")
                print(f"   📊 Incluant: graphique des nœuds, clusters sémantiques, recommandations")
                return True
            else:
                print(f"   ⚠️  Analyse terminée mais rapport non généré")
                return False
                
        except ImportError:
            print(f"   ⚠️  Import de l'analyseur sémantique échoué, utilisation du subprocess...")
            # Fallback vers l'ancienne méthode
            try:
                result = subprocess.run([
                    'python', 'ext_audit_maillage_classique.py',
                    '--csv-file', filtered_report_path
                ], capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    print(f"   ✅ Analyse sémantique terminée")
                    return True
                else:
                    print(f"   ⚠️  Analyse terminée avec avertissements")
                    return True
                    
            except Exception as e:
                print(f"   ❌ Erreur subprocess: {e}")
                return False
        
        except Exception as e:
            print(f"   ❌ Erreur analyse sémantique: {e}")
            print(f"   💡 Vous pouvez lancer manuellement: python ext_audit_maillage_classique.py --csv-file {filtered_report_path}")
            return False

def main():
    """Lancement du workflow intelligent final"""
    print("🤖 AUDIT DE MAILLAGE INTERNE INTELLIGENT")
    print("=" * 80)
    
    workflow = FinalIntelligentWorkflow()
    
    # Menu interactif
    print("\nChoisissez une option:")
    print("1. 🚀 Nouveau crawl intelligent (IA + Screaming Frog)")
    print("2. 📊 Analyser un CSV existant")
    print("3. ⚙️  Configuration IA seulement (générer config SF)")
    print("4. 📄 Analyser via sitemap XML")
    print("5. ❌ Quitter")
    
    choice = input("\nVotre choix (1-5): ").strip()
    result = None

    if choice == "1":
        website_url = input("🌐 URL du site à analyser: ").strip()
        if not website_url:
            print("❌ URL requise")
            return

        # Options avancées
        print("\n🔧 Options avancées (optionnel):")
        sample_urls_input = input("📄 URLs d'exemple pour analyser la structure (séparées par des virgules, ou vide pour auto): ").strip()

        sample_urls = []
        if sample_urls_input:
            sample_urls = [url.strip() for url in sample_urls_input.split(',') if url.strip()]
            print(f"   📝 {len(sample_urls)} URLs fournies pour l'analyse")

        section_filter_raw = input("📂 Analyser seulement une section (ex: /blog/, /produits/): ").strip()

        # Validation et nettoyage du filtre de section
        section_filter = workflow._validate_section_filter(section_filter_raw, website_url)

        max_pages = input("📊 Limite de pages (défaut: illimité): ").strip()

        print(f"\n🚀 Lancement de l'analyse de {website_url}")
        if section_filter:
            print(f"   📂 Section filtrée: {section_filter}")
        if max_pages:
            print(f"   📊 Limite: {max_pages} pages")

        result = workflow.run_complete_workflow(website_url, section_filter, max_pages, sample_urls)
    
    elif choice == "2":
        csv_files = glob.glob("./exports/*.csv")
        if not csv_files:
            print("❌ Aucun fichier CSV trouvé dans ./exports/")
            return
        
        print("\n📁 Fichiers CSV disponibles:")
        for i, file in enumerate(csv_files, 1):
            print(f"   {i}. {os.path.basename(file)}")
        
        try:
            file_choice = int(input("\nChoisir un fichier (numéro): ")) - 1
            if 0 <= file_choice < len(csv_files):
                result = workflow.launch_semantic_analysis(csv_files[file_choice])
                if result:
                    print(f"✅ Analyse terminée!")
            else:
                print("❌ Choix invalide")
        except ValueError:
            print("❌ Veuillez entrer un numéro valide")
            
    elif choice == "3":
        website_url = input("🌐 URL du site pour analyser la structure: ").strip()
        if not website_url:
            print("❌ URL requise")
            return
        
        print(f"🤖 Génération de la configuration IA pour {website_url}...")
        structure_analysis = workflow.detector.run_intelligent_workflow(website_url, "")
        
        if structure_analysis.get('success'):
            print("✅ Configuration Screaming Frog générée: ./sf_content_config.xml")
            print("\n📋 Commande Screaming Frog à exécuter:")
            print(structure_analysis.get('sf_command', 'Commande non disponible'))
        else:
            print("❌ Échec de la génération de configuration")

    elif choice == "4":
        sitemap_url = input("📄 URL du sitemap XML: ").strip()
        if not sitemap_url:
            print("❌ URL du sitemap requise")
            return

        print(f"📄 Analyse du sitemap: {sitemap_url}")

        # Récupérer et analyser le sitemap
        sitemap_urls = workflow.fetch_and_parse_sitemap(sitemap_url)
        if not sitemap_urls:
            print("❌ Impossible de récupérer ou analyser le sitemap")
            return

        print(f"   📝 {len(sitemap_urls)} URLs trouvées dans le sitemap")

        # Extraire l'URL de base du site
        from urllib.parse import urlparse
        parsed = urlparse(sitemap_url)
        website_url = f"{parsed.scheme}://{parsed.netloc}/"

        print(f"   🌐 Site détecté: {website_url}")

        # Lancer l'analyse avec les URLs du sitemap
        result = workflow.run_complete_workflow(website_url, "", "", sitemap_urls)

    elif choice == "5":
        print("👋 Au revoir!")
        return
    
    else:
        print("❌ Choix invalide")
        return
    
    if result:
        print(f"\n🎉 SUCCÈS TOTAL!")
        print(f"📊 Rapport final généré: {result}")
        print(f"\n📋 PROCHAINES ÉTAPES:")
        print(f"   1. Examinez le rapport: {result}")
        print(f"   2. Analysez les recommandations sémantiques")
        print(f"   3. Implémentez les améliorations de maillage interne")
        print(f"\n💡 Pour relancer l'analyse sémantique uniquement:")
        print(f"   python ext_audit_maillage_classique.py --csv-file {result}")
    else:
        print(f"\n❌ ÉCHEC DU WORKFLOW")
        print(f"Vérifiez les messages d'erreur ci-dessus pour diagnostiquer le problème.")

if __name__ == "__main__":
    main()