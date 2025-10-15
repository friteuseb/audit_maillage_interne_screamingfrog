#!/usr/bin/env python3
"""
Détecteur intelligent de zones de contenu avec Anthropic + Screaming Frog
Workflow : Échantillonnage → IA → Config auto SF → Crawl optimisé
"""

import os
import requests
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Tuple, Optional
import json
import time
from bs4 import BeautifulSoup
import re
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("⚠️  Module anthropic non installé. Installez avec: pip install anthropic")

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    print("⚠️  Module beautifulsoup4 non installé. Installez avec: pip install beautifulsoup4")

class IntelligentContentDetector:
    """Détecteur intelligent de contenu avec IA"""
    
    def __init__(self):
        self.anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        self.client = None
        
        if ANTHROPIC_AVAILABLE and self.anthropic_key:
            try:
                self.client = anthropic.Anthropic(api_key=self.anthropic_key)
                print("✅ API Anthropic initialisée")
            except Exception as e:
                print(f"❌ Erreur Anthropic: {e}")
                self.client = None
        else:
            print("⚠️  API Anthropic non disponible (vérifiez .env)")
    
    def sample_pages_strategically(self, website_url: str, max_samples: int = 5, section_filter: str = "") -> List[str]:
        """Échantillonnage stratégique pour analyse universelle"""
        print(f"🎯 Échantillonnage stratégique sur {website_url}")
        if section_filter:
            print(f"   📂 Focus sur la section: {section_filter}")
        
        sample_urls = []
        
        # 1. Toujours inclure l'accueil (structure de base)
        sample_urls.append(website_url.rstrip('/') + '/')
        
        # 2. Essayer de récupérer le sitemap pour diversité
        all_urls = self._get_all_urls_from_sitemap(website_url)
        
        if not all_urls:
            print("   📝 Pas de sitemap, échantillonnage manuel...")
            all_urls = self._manual_deep_sampling(website_url)
        
        # 3. Échantillonnage stratégique par types de pages
        if section_filter:
            # Prioriser massivement les pages de la section spécifiée
            section_urls = [url for url in all_urls if section_filter in url]
            if section_urls:
                print(f"   🎯 {len(section_urls)} pages trouvées dans {section_filter}")
                # Prendre au MAXIMUM 4 pages de la section ciblée (limiter par taille échantillon)
                section_sample_size = min(len(section_urls), max_samples - 1, 4)
                strategic_samples = self._strategic_page_selection(section_urls, section_sample_size)
                sample_urls.extend(strategic_samples)

                # Ajouter SEULEMENT 1 page générale pour le contexte global (homepage uniquement)
                remaining_slots = max_samples - len(sample_urls)
                if remaining_slots > 0:
                    # Ne prendre que la homepage si elle n'est pas déjà dans la section
                    homepage = website_url.rstrip('/') + '/'
                    if homepage not in sample_urls and remaining_slots >= 1:
                        sample_urls.insert(0, homepage)  # Homepage en premier pour contexte

                print(f"   📊 Répartition: {len([u for u in sample_urls if section_filter in u])} pages section / {len([u for u in sample_urls if section_filter not in u])} pages générales")
            else:
                print(f"   ⚠️  Aucune page trouvée dans {section_filter} via sitemap, tentative de découverte approfondie...")
                # Essayer de découvrir les pages de section par d'autres moyens
                discovered_section_urls = self._discover_section_pages(website_url, section_filter)
                if discovered_section_urls:
                    print(f"   ✅ {len(discovered_section_urls)} pages de section découvertes")
                    section_sample_size = min(len(discovered_section_urls), max_samples - 1, 4)
                    strategic_samples = self._strategic_page_selection(discovered_section_urls, section_sample_size)
                    sample_urls.extend(strategic_samples)

                    # Ajouter homepage pour contexte
                    homepage = website_url.rstrip('/') + '/'
                    if homepage not in sample_urls:
                        sample_urls.insert(0, homepage)
                else:
                    print(f"   ❌ Aucune page trouvée dans {section_filter}, échantillonnage général...")
                    strategic_samples = self._strategic_page_selection(all_urls, max_samples - 1)
                    sample_urls.extend(strategic_samples)
        else:
            strategic_samples = self._strategic_page_selection(all_urls, max_samples - 1)
            sample_urls.extend(strategic_samples)
        
        # Nettoyer et dédupliquer
        final_samples = list(dict.fromkeys(sample_urls))[:max_samples]  # Préserve l'ordre
        
        print(f"   ✅ {len(final_samples)} pages stratégiquement échantillonnées:")
        for i, url in enumerate(final_samples, 1):
            page_type = self._classify_page_type(url)
            section_info = f" [{section_filter}]" if section_filter and section_filter in url else ""
            print(f"      {i}. {page_type}{section_info}: {url}")
        
        return final_samples
    
    def _get_all_urls_from_sitemap(self, website_url: str) -> List[str]:
        """Récupérer toutes les URLs du sitemap"""
        sitemap_urls = [
            urljoin(website_url, 'sitemap.xml'),
            urljoin(website_url, 'sitemap_index.xml'),
            urljoin(website_url, 'robots.txt')
        ]
        
        for sitemap_url in sitemap_urls:
            try:
                response = requests.get(sitemap_url, timeout=10)
                if response.status_code == 200:
                    if 'sitemap.xml' in sitemap_url:
                        return self._extract_urls_from_sitemap(response.text, website_url)
                    elif 'robots.txt' in sitemap_url:
                        sitemap_line = [line for line in response.text.split('\n') 
                                      if 'sitemap' in line.lower()]
                        if sitemap_line:
                            sitemap_from_robots = sitemap_line[0].split(': ')[1].strip()
                            response = requests.get(sitemap_from_robots, timeout=10)
                            return self._extract_urls_from_sitemap(response.text, website_url)
            except Exception:
                continue
        
        return []
    
    def _strategic_page_selection(self, all_urls: List[str], max_samples: int) -> List[str]:
        """Sélection stratégique de pages représentatives"""
        if not all_urls:
            return []
        
        # Classifier les URLs par type
        classified = {
            'content': [],      # Articles, pages de contenu
            'product': [],      # Produits, services
            'category': [],     # Catégories, sections
            'contact': [],      # Contact, à propos
            'other': []
        }
        
        for url in all_urls:
            page_type = self._classify_page_type(url)
            
            if page_type in ['Article/Blog', 'Contenu spécifique']:
                classified['content'].append(url)
            elif page_type in ['Produit/Service']:
                classified['product'].append(url)
            elif page_type in ['Page section']:
                classified['category'].append(url)
            elif page_type in ['Page contact']:
                classified['contact'].append(url)
            else:
                classified['other'].append(url)
        
        # Sélectionner représentativement
        selected = []
        priorities = ['content', 'product', 'contact', 'category', 'other']
        
        # Distribuer équitablement
        remaining = max_samples
        for priority in priorities:
            urls = classified[priority]
            if urls and remaining > 0:
                # Prendre 1-2 URLs par catégorie selon disponibilité
                take = min(len(urls), max(1, remaining // (len(priorities) - priorities.index(priority))))
                selected.extend(urls[:take])
                remaining -= take
        
        return selected[:max_samples]
    
    def _classify_page_type(self, url: str) -> str:
        """Classifier le type d'une page par son URL"""
        url_lower = url.lower()
        
        if any(term in url_lower for term in ['contact', 'about', 'propos']):
            return "Page contact"
        elif any(term in url_lower for term in ['blog', 'article', 'actualit', 'news']):
            return "Article/Blog"
        elif any(term in url_lower for term in ['produit', 'service', 'expertise', 'solution']):
            return "Produit/Service"
        elif url.count('/') <= 3 and not url.endswith('.html'):
            return "Page section"
        else:
            return "Contenu spécifique"
    
    def _discover_section_pages(self, website_url: str, section_filter: str) -> List[str]:
        """Découvrir les pages d'une section spécifique par exploration approfondie"""
        discovered_urls = []

        try:
            # 1. Essayer directement l'URL de section
            section_url = urljoin(website_url, section_filter.lstrip('/'))
            if self._test_url_exists(section_url):
                discovered_urls.append(section_url)
                print(f"   📍 Section trouvée: {section_url}")

            # 2. Essayer des patterns communs pour cette section
            base_url = website_url.rstrip('/')
            common_patterns = [
                f"{section_filter}/",  # /section/
                f"{section_filter}",   # /section
                f"{section_filter}/index.html",
                f"{section_filter}/page/1/",
                f"{section_filter}/1/",  # pagination
            ]

            for pattern in common_patterns:
                test_url = urljoin(base_url, pattern.lstrip('/'))
                if test_url not in discovered_urls and self._test_url_exists(test_url):
                    discovered_urls.append(test_url)
                    print(f"   📍 Pattern trouvé: {test_url}")

            # 3. Explorer depuis la homepage pour trouver des liens vers la section
            response = requests.get(website_url, timeout=10)
            if response.status_code == 200 and BS4_AVAILABLE:
                soup = BeautifulSoup(response.text, 'html.parser')
                links = soup.find_all('a', href=True)

                base_domain = urlparse(website_url).netloc
                for link in links:
                    href = link['href']
                    full_url = urljoin(website_url, href)

                    if (base_domain in full_url and
                        section_filter in full_url and
                        full_url not in discovered_urls and
                        not any(skip in full_url.lower() for skip in ['#', 'javascript:', 'mailto:'])):
                        discovered_urls.append(full_url)
                        if len(discovered_urls) >= 5:  # Limite pour éviter trop de requêtes
                            break

            # 4. Si toujours rien, essayer des recherches par mots-clés dans l'URL
            if not discovered_urls:
                # Essayer de deviner des URLs basées sur des mots-clés
                keywords = section_filter.strip('/').split('-')
                if keywords:
                    # Essayer des combinaisons simples
                    for keyword in keywords[:2]:  # Prendre max 2 mots-clés
                        test_url = f"{base_url}/{keyword}/"
                        if self._test_url_exists(test_url):
                            discovered_urls.append(test_url)
                            print(f"   📍 Mot-clé trouvé: {test_url}")

        except Exception as e:
            print(f"   ⚠️  Erreur découverte section: {e}")

        return discovered_urls

    def _test_url_exists(self, url: str) -> bool:
        """Tester si une URL existe (HEAD request)"""
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.head(url, headers=headers, timeout=5, allow_redirects=True)
            return response.status_code < 400
        except:
            return False

    def _manual_deep_sampling(self, website_url: str) -> List[str]:
        """Échantillonnage manuel plus approfondi"""
        urls = []
        
        try:
            response = requests.get(website_url, timeout=10)
            if response.status_code == 200 and BS4_AVAILABLE:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Chercher tous les liens internes
                links = soup.find_all('a', href=True)
                base_domain = urlparse(website_url).netloc
                
                for link in links:
                    href = link['href']
                    full_url = urljoin(website_url, href)
                    
                    if (base_domain in full_url and 
                        full_url not in urls and
                        not any(skip in full_url.lower() for skip in [
                            '#', 'javascript:', 'mailto:', 'tel:', 'wp-content', 
                            'wp-admin', 'feed', 'tag', 'author', '?'
                        ])):
                        urls.append(full_url)
                        
                        if len(urls) >= 50:  # Limite pour éviter trop de requêtes
                            break
        
        except Exception:
            pass
        
        return urls
    
    def _extract_urls_from_sitemap(self, sitemap_content: str, base_url: str) -> List[str]:
        """Extraire URLs du sitemap XML"""
        urls = []
        
        if not BS4_AVAILABLE:
            # Fallback regex
            url_pattern = r'<loc>(.*?)</loc>'
            urls = re.findall(url_pattern, sitemap_content)
        else:
            # BeautifulSoup parsing
            try:
                soup = BeautifulSoup(sitemap_content, 'xml')
                urls = [loc.text for loc in soup.find_all('loc')]
            except:
                # Fallback regex si XML parsing échoue
                url_pattern = r'<loc>(.*?)</loc>'
                urls = re.findall(url_pattern, sitemap_content)
        
        # Filtrer pour garder seulement les URLs du domaine
        base_domain = urlparse(base_url).netloc
        filtered_urls = []
        
        for url in urls:
            if base_domain in url and not any(skip in url.lower() for skip in [
                'wp-content', 'wp-admin', 'feed', 'sitemap', 'category', 'tag'
            ]):
                filtered_urls.append(url)
        
        return filtered_urls
    
    def _manual_sampling(self, website_url: str, max_samples: int) -> List[str]:
        """Échantillonnage manuel en explorant la page d'accueil"""
        sample_urls = [website_url]  # Toujours inclure l'accueil
        
        try:
            response = requests.get(website_url, timeout=10)
            if response.status_code == 200 and BS4_AVAILABLE:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Trouver des liens internes
                links = soup.find_all('a', href=True)
                base_domain = urlparse(website_url).netloc
                
                for link in links:
                    href = link['href']
                    full_url = urljoin(website_url, href)
                    
                    if (base_domain in full_url and 
                        full_url not in sample_urls and
                        not any(skip in full_url.lower() for skip in [
                            '#', 'javascript:', 'mailto:', 'tel:', 'contact', 'mentions'
                        ])):
                        sample_urls.append(full_url)
                        
                        if len(sample_urls) >= max_samples:
                            break
        
        except Exception as e:
            print(f"   ❌ Erreur échantillonnage manuel: {e}")
        
        return sample_urls
    
    def analyze_content_structure_with_ai(self, sample_urls: List[str], section_filter: str = "") -> Dict:
        """Analyser la structure des contenus avec Anthropic"""
        if not self.client:
            return {"error": "API Anthropic non disponible"}

        print(f"🤖 Analyse IA de la structure de contenu...")

        # Prioriser les pages de section si un filtre est spécifié
        analysis_urls = sample_urls[:3]  # Par défaut les 3 premières

        if section_filter:
            section_pages = [url for url in sample_urls if section_filter in url]
            general_pages = [url for url in sample_urls if section_filter not in url]

            if section_pages:
                # Prendre jusqu'à 2 pages de section + 1 page générale pour contexte
                analysis_urls = section_pages[:2]
                if general_pages and len(analysis_urls) < 3:
                    analysis_urls.append(general_pages[0])  # Homepage pour contexte
                print(f"   🎯 Priorisation des pages de section: {len(section_pages)} trouvées")
            else:
                print(f"   📝 Aucune page de section dans l'échantillon, analyse générale")

        # Récupérer le HTML des pages sélectionnées
        html_samples = []
        for url in analysis_urls:
            print(f"   📥 Récupération: {url}")
            html_content = self._fetch_html(url)
            if html_content:
                # Nettoyer le HTML pour l'analyse
                cleaned_html = self._clean_html_for_ai(html_content)
                html_samples.append({
                    'url': url,
                    'html': cleaned_html[:6000]  # Limiter la taille
                })

            time.sleep(1)  # Rate limiting
        
        if not html_samples:
            return {"error": "Aucune page HTML récupérée"}
        
        # Créer le prompt pour Claude
        prompt = self._create_structure_analysis_prompt(html_samples)
        
        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parser la réponse JSON
            content = response.content[0].text.strip()
            
            # Nettoyer le JSON
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].strip()
            
            result = json.loads(content)
            print(f"   ✅ Structure analysée avec succès")
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"   ❌ Erreur parsing JSON: {e}")
            print(f"   Réponse: {content[:200]}...")
            return {"error": "Réponse JSON invalide"}
            
        except Exception as e:
            print(f"   ❌ Erreur API: {e}")
            return {"error": str(e)}
    
    def _create_structure_analysis_prompt(self, html_samples: List[Dict]) -> str:
        """Créer le prompt avancé pour analyser la structure universellement"""
        
        prompt = f"""Tu es un expert en analyse de structure HTML pour l'extraction de contenu éditorial. 

OBJECTIF : Analyser ces pages et créer des XPath universels qui fonctionneront sur TOUT le site.

RÈGLES CRITIQUES :
1. CONTENU ÉDITORIAL = texte informatif, articles, descriptions produits, blog posts
2. NAVIGATION = header, menu, footer, sidebar, breadcrumb, pagination, liens "en savoir plus"
3. Préférer les balises sémantiques (main, article, section) aux classes CSS
4. XPath doit être RESTRICTIF plutôt que permissif (mieux vaut manquer quelques liens que inclure la navigation)
5. ÉVITER ABSOLUMENT les identifiants uniques (post-1234, article-567, id="content-789") - utiliser UNIQUEMENT des patterns généraux qui fonctionnent sur TOUTES les pages similaires
6. Si une classe contient un numéro, c'est probablement unique - l'ignorer et utiliser la balise seule

PAGES À ANALYSER :
"""
        
        for i, sample in enumerate(html_samples, 1):
            prompt += f"\n=== PAGE {i}: {sample['url']} ===\n"
            # Ajouter une analyse contextuelle de chaque page
            page_context = self._analyze_page_context(sample['url'])
            prompt += f"CONTEXTE: {page_context}\n\n"
            prompt += f"```html\n{sample['html']}\n```\n"
        
        prompt += f"""

ANALYSE REQUISE :

1. IDENTIFICATION DES ZONES :
   - Où est le contenu principal sur chaque page ?
   - Quelles balises/classes sont utilisées de manière cohérente ?
   - Y a-t-il des balises sémantiques (main, article, section) ?
   
2. PATTERNS DE NAVIGATION À EXCLURE :
   - Header/footer/nav évidents
   - Sidebars avec liens de navigation  
   - Breadcrumbs, pagination
   - Liens "call-to-action" génériques
   
3. VALIDATION CROISÉE :
   - Les XPath fonctionnent-ils sur les 3 pages ?
   - Ratio réaliste de liens éditoriaux (10-30% du total) ?
   - Pas de sur-inclusion de navigation ?

RÉPONSE OBLIGATOIRE (JSON uniquement) :

```json
{{
  "analysis_summary": {{
    "site_structure": "Description de la structure détectée",
    "main_content_pattern": "Pattern principal identifié",
    "navigation_patterns": ["patterns de navigation identifiés"],
    "editorial_link_ratio_estimate": "estimation du % de liens éditoriaux attendu"
  }},
  "content_zones": {{
    "main_content_xpath": "XPath le plus restrictif pour le contenu principal",
    "editorial_links_xpath": "XPath ultra-précis pour SEULEMENT les liens éditoriaux",
    "content_text_xpath": "XPath pour le texte du contenu principal"
  }},
  "exclusion_zones": {{
    "header_xpath": "XPath pour header à exclure",
    "footer_xpath": "XPath pour footer à exclure", 
    "navigation_xpath": "XPath pour navigation à exclure",
    "sidebar_xpath": "XPath pour sidebar à exclure (si existe)"
  }},
  "validation": {{
    "xpath_tested_on_all_pages": true/false,
    "estimated_editorial_ratio": "pourcentage estimé",
    "confidence_level": "high|medium|low",
    "fallback_needed": true/false
  }},
  "xpath_alternatives": {{
    "primary": "XPath principal recommandé",
    "fallback": "XPath de secours si le principal échoue",
    "explanation": "Pourquoi ces choix"
  }}
}}
```

IMPORTANT : Privilégie la PRÉCISION sur la EXHAUSTIVITÉ. Mieux vaut identifier 80% des vrais liens éditoriaux que d'inclure des liens de navigation."""
        
        return prompt

    def _generalize_xpath_patterns(self, content_zones: Dict) -> Dict:
        """Généraliser les XPath trop spécifiques pour une meilleure universalité"""
        import re

        generalized = content_zones.copy()

        for key in ['main_content_xpath', 'editorial_links_xpath', 'content_text_xpath']:
            if key in generalized and generalized[key]:
                xpath = generalized[key]

                # Supprimer les identifiants uniques (post-1234, article-567, etc.)
                xpath = re.sub(r'\[contains\(@class,\s*[\'"]\w+-\d+[\'"]\)\]', '', xpath)
                xpath = re.sub(r'\[contains\(@id,\s*[\'"]\w+-\d+[\'"]\)\]', '', xpath)

                # Nettoyer les doubles crochets
                xpath = re.sub(r'\[\]\[', '[', xpath)
                xpath = re.sub(r'\]\[\]', ']', xpath)

                # Si le XPath devient trop vide, utiliser des fallbacks
                if not xpath or xpath in ['//', '//*']:
                    if key == 'main_content_xpath':
                        xpath = '//main | //article | //[contains(@class, "content")] | //[contains(@class, "post")]'
                    elif key == 'editorial_links_xpath':
                        xpath = '//main//a | //article//a'
                    elif key == 'content_text_xpath':
                        xpath = '//main//text() | //article//text()'

                generalized[key] = xpath

        return generalized

    def _analyze_page_context(self, url: str) -> str:
        """Analyser le contexte d'une page pour aider l'IA"""
        
        if 'contact' in url.lower():
            return "Page contact - Contenu informatif + formulaire"
        elif 'blog' in url.lower() or 'article' in url.lower():
            return "Page article/blog - Contenu éditorial principal"
        elif any(term in url.lower() for term in ['produit', 'service', 'expertise']):
            return "Page produit/service - Description + liens connexes"
        elif url.count('/') <= 3:
            return "Page accueil/section - Mix contenu + navigation"
        else:
            return "Page de contenu spécifique - Contenu informatif attendu"
    
    def generate_screaming_frog_config(self, ai_analysis: Dict, output_path: str = "./sf_content_config.xml") -> str:
        """Générer le fichier de configuration Screaming Frog"""
        if "content_zones" not in ai_analysis:
            print("❌ Analyse IA invalide pour générer la config")
            return ""
        
        print(f"⚙️  Génération config Screaming Frog...")
        
        content_zones = ai_analysis["content_zones"]

        # Généraliser les XPath trop spécifiques
        content_zones = self._generalize_xpath_patterns(content_zones)

        # Template XML pour Screaming Frog
        xml_config = f"""<?xml version="1.0" encoding="UTF-8"?>
<seospiderconfig>
  <configuration>
    <extraction>
      <!-- Contenu principal -->
      <custom name="MainContent" 
              xpath="{content_zones.get('content_text_xpath', '//main//text() | //article//text()')}"
              type="text"/>
      
      <!-- Liens éditoriaux seulement -->
      <custom name="EditorialLinks" 
              xpath="{content_zones.get('editorial_links_xpath', '//main//a | //article//a')}"
              type="links"/>
      
      <!-- Zone de contenu complète -->
      <custom name="ContentZone" 
              xpath="{content_zones.get('main_content_xpath', '//main | //article')}"
              type="html"/>
    </extraction>
    
    <!-- Paramètres optimisés -->
    <crawl>
      <respectRobots>true</respectRobots>
      <followInternalNofollow>false</followInternalNofollow>
      <crawlSubdomains>false</crawlSubdomains>
    </crawl>
  </configuration>
</seospiderconfig>"""

        # Sauvegarder
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(xml_config)
            
            print(f"   ✅ Config sauvée: {output_path}")
            print(f"   🎯 XPath contenu: {content_zones.get('main_content_xpath', 'default')}")
            print(f"   🔗 XPath liens: {content_zones.get('editorial_links_xpath', 'default')}")
            
            return output_path
            
        except Exception as e:
            print(f"   ❌ Erreur sauvegarde: {e}")
            return ""
    
    def run_intelligent_workflow(self, website_url: str, section_filter: str = "", sample_urls: Optional[List[str]] = None) -> Dict:
        """Exécuter le workflow complet"""
        print(f"🚀 WORKFLOW INTELLIGENT - {website_url}")
        print("=" * 60)
        
        results = {
            "success": False,
            "steps_completed": [],
            "errors": [],
            "config_file": "",
            "ai_analysis": {}
        }
        
        try:
            # Étape 1 : Échantillonnage stratégique ou URLs fournies
            if sample_urls and len(sample_urls) > 0:
                print(f"\n📊 ÉTAPE 1: Utilisation des URLs fournies ({len(sample_urls)} pages)")
                results["steps_completed"].append("sampling")
                results["sample_urls"] = sample_urls
            else:
                print(f"\n📊 ÉTAPE 1: Échantillonnage stratégique de pages")
                sample_urls = self.sample_pages_strategically(website_url, max_samples=5, section_filter=section_filter)

                if not sample_urls:
                    results["errors"].append("Aucune page échantillonnée")
                    return results

                results["steps_completed"].append("sampling")
                results["sample_urls"] = sample_urls
            
            # Étape 2 : Analyse IA
            print(f"\n🤖 ÉTAPE 2: Analyse IA de la structure")
            ai_analysis = self.analyze_content_structure_with_ai(sample_urls, section_filter)
            
            if "error" in ai_analysis:
                results["errors"].append(f"Analyse IA: {ai_analysis['error']}")
                return results
            
            results["steps_completed"].append("ai_analysis")
            results["ai_analysis"] = ai_analysis
            
            # Étape 3 : Génération config SF
            print(f"\n⚙️  ÉTAPE 3: Génération config Screaming Frog")
            config_file = self.generate_screaming_frog_config(ai_analysis)
            
            if not config_file:
                results["errors"].append("Échec génération config SF")
                return results
            
            results["steps_completed"].append("config_generation")
            results["config_file"] = config_file
            
            # Étape 4 : Préparation commande SF
            print(f"\n🕷️  ÉTAPE 4: Préparation crawl Screaming Frog")
            sf_command = self._generate_sf_command(website_url, config_file)
            results["sf_command"] = sf_command
            results["steps_completed"].append("sf_preparation")
            
            print(f"\n✅ WORKFLOW TERMINÉ AVEC SUCCÈS")
            print(f"📋 Prochaines étapes:")
            print(f"   1. Exécuter: {sf_command}")
            print(f"   2. Analyser les exports générés")
            print(f"   3. Lancer l'analyse sémantique finale")
            
            results["success"] = True
            
        except Exception as e:
            results["errors"].append(f"Erreur globale: {e}")
            print(f"❌ Erreur workflow: {e}")
        
        return results
    
    def _fetch_html(self, url: str) -> Optional[str]:
        """Récupérer le contenu HTML d'une page"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"   ❌ {url}: {e}")
            return None
    
    def _clean_html_for_ai(self, html: str) -> str:
        """Nettoyer HTML pour l'analyse IA"""
        if not BS4_AVAILABLE:
            # Fallback regex basique
            html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
            html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
            return html[:8000]
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Supprimer scripts, styles, commentaires
            for tag in soup(['script', 'style', 'noscript']):
                tag.decompose()
            
            # Garder seulement la structure importante
            body = soup.find('body')
            if body:
                return str(body)[:8000]
            else:
                return str(soup)[:8000]
                
        except Exception:
            # Fallback
            return html[:8000]
    
    def _generate_sf_command(self, website_url: str, config_file: str) -> str:
        """Générer la commande Screaming Frog optimisée"""
        
        sf_path = '"/mnt/c/Program Files (x86)/Screaming Frog SEO Spider/ScreamingFrogSEOSpiderCli.exe"'
        
        command = f"""{sf_path} \\
  -headless \\
  -crawl {website_url} \\
  -config {config_file} \\
  --output-folder ./exports/ \\
  --export-format csv \\
  --bulk-export "Links:All Outlinks,All Inlinks,Custom:MainContent,Custom:EditorialLinks,Custom:ContentZone,Page Titles,H1-1,Word Count" """
        
        return command

def main():
    """Test du workflow intelligent"""
    print("🧪 Test du détecteur intelligent de contenu")
    print("=" * 60)
    
    # Vérifier la clé API
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ Clé ANTHROPIC_API_KEY manquante dans .env")
        print("💡 Créez un fichier .env avec:")
        print("   ANTHROPIC_API_KEY=votre_clé_ici")
        return
    
    # Créer le détecteur
    detector = IntelligentContentDetector()
    
    if not detector.client:
        print("❌ Impossible d'initialiser l'API Anthropic")
        return
    
    # Lancer le workflow
    website_url = "https://www.reseau-travaux.fr/"
    results = detector.run_intelligent_workflow(website_url)
    
    print(f"\n📊 RÉSULTATS FINAUX:")
    print(f"   ✅ Succès: {results['success']}")
    print(f"   📋 Étapes: {', '.join(results['steps_completed'])}")
    
    if results['errors']:
        print(f"   ❌ Erreurs: {', '.join(results['errors'])}")
    
    if results.get('sf_command'):
        print(f"\n🚀 Commande SF prête à exécuter:")
        print(f"   {results['sf_command']}")

if __name__ == "__main__":
    main()