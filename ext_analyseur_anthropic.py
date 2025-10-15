#!/usr/bin/env python3
"""
Analyseur intelligent de contenu HTML avec l'API Anthropic
"""

import os
import requests
from typing import Dict, List, Tuple, Optional
import json
import time
from urllib.parse import urlparse
import re

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("⚠️  Module anthropic non installé. Installez avec: pip install anthropic")

class AnthropicContentAnalyzer:
    """Analyseur de contenu HTML intelligent avec Claude"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        self.client = None
        
        if ANTHROPIC_AVAILABLE and self.api_key:
            try:
                self.client = anthropic.Anthropic(api_key=self.api_key)
                print("✅ API Anthropic initialisée")
            except Exception as e:
                print(f"❌ Erreur initialisation Anthropic: {e}")
                self.client = None
        else:
            print("⚠️  API Anthropic non disponible (clé manquante ou module absent)")
    
    def is_available(self) -> bool:
        """Vérifier si l'analyseur est disponible"""
        return self.client is not None
    
    def fetch_page_content(self, url: str, timeout: int = 10) -> Optional[str]:
        """Récupérer le contenu HTML d'une page"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"❌ Erreur récupération {url}: {e}")
            return None
    
    def analyze_editorial_zones(self, html_content: str, url: str) -> Dict:
        """Analyser les zones éditoriales d'une page HTML avec Claude"""
        if not self.client:
            return {"error": "API Anthropic non disponible"}
        
        # Nettoyer le HTML (garder seulement la structure importante)
        cleaned_html = self._clean_html_for_analysis(html_content)
        
        prompt = f"""Analysez cette page HTML et identifiez les zones de contenu éditorial vs navigation.

URL: {url}

HTML (extrait):
```html
{cleaned_html[:8000]}  
```

Identifiez et classifiez tous les liens <a> présents selon ces catégories :

1. **ÉDITORIAL** : Liens dans le contenu principal (articles, descriptions, textes informatifs)
2. **NAVIGATION** : Liens de menu, header, footer, breadcrumb, pagination  
3. **SIDEBAR** : Liens dans barres latérales, widgets
4. **CALL-TO-ACTION** : Boutons d'action (contact, devis, inscription)

Pour chaque lien trouvé, retournez UNIQUEMENT un JSON valide au format :

```json
{{
    "links": [
        {{
            "href": "URL_du_lien",
            "text": "Texte_du_lien", 
            "category": "EDITORIAL|NAVIGATION|SIDEBAR|CALL_TO_ACTION",
            "context": "Description_brève_du_contexte",
            "confidence": 0.95
        }}
    ],
    "zones_identified": {{
        "main_content": "Description de la zone de contenu principal",
        "navigation": "Description des zones de navigation",
        "editorial_quality": "Évaluation de la qualité éditoriale (1-10)"
    }}
}}
```

Analysez le HTML et répondez UNIQUEMENT avec le JSON, sans explication."""

        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",  # Modèle rapide et économique
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parser la réponse JSON
            content = response.content[0].text.strip()
            
            # Nettoyer le JSON (enlever les éventuels markdown)
            if content.startswith('```json'):
                content = content.split('```json')[1].split('```')[0].strip()
            elif content.startswith('```'):
                content = content.split('```')[1].strip()
            
            return json.loads(content)
            
        except json.JSONDecodeError as e:
            print(f"❌ Erreur parsing JSON: {e}")
            print(f"Réponse brute: {content[:200]}...")
            return {"error": "Réponse JSON invalide"}
            
        except Exception as e:
            print(f"❌ Erreur API Anthropic: {e}")
            return {"error": str(e)}
    
    def _clean_html_for_analysis(self, html: str) -> str:
        """Nettoyer le HTML pour garder seulement la structure pertinente"""
        
        # Enlever les scripts, styles, commentaires
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
        
        # Garder seulement les balises structurelles importantes
        important_tags = [
            'html', 'body', 'header', 'nav', 'main', 'article', 'section', 
            'aside', 'footer', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'p', 'a', 'ul', 'ol', 'li', 'span'
        ]
        
        # Pattern pour garder seulement les balises importantes avec leurs attributs class/id
        pattern = r'<(?!/?)(' + '|'.join(important_tags) + r')(\s+[^>]*)?>'
        
        # Simplifier en gardant la structure
        lines = html.split('\n')
        cleaned_lines = []
        
        for line in lines[:200]:  # Limiter à 200 lignes pour éviter le spam
            line = line.strip()
            if line and (any(tag in line.lower() for tag in important_tags) or '<a ' in line.lower()):
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def batch_analyze_pages(self, urls: List[str], max_pages: int = 10) -> Dict[str, Dict]:
        """Analyser plusieurs pages en lot"""
        if not self.client:
            return {}
        
        results = {}
        processed = 0
        
        print(f"🤖 Analyse IA de {min(len(urls), max_pages)} pages...")
        
        for url in urls[:max_pages]:
            if processed >= max_pages:
                break
                
            print(f"   🔍 Analyse: {url}")
            
            # Récupérer le contenu
            html_content = self.fetch_page_content(url)
            if not html_content:
                continue
            
            # Analyser avec Claude
            analysis = self.analyze_editorial_zones(html_content, url)
            if "error" not in analysis:
                results[url] = analysis
                processed += 1
                print(f"      ✅ {len(analysis.get('links', []))} liens analysés")
            else:
                print(f"      ❌ Erreur: {analysis['error']}")
            
            # Rate limiting (éviter de saturer l'API)
            time.sleep(1)
        
        print(f"✅ {processed} pages analysées avec succès")
        return results
    
    def improve_screaming_frog_classification(self, sf_links: List[Dict], sample_urls: List[str]) -> Dict:
        """Améliorer la classification Screaming Frog avec l'IA"""
        if not self.client or not sample_urls:
            return {"improved_links": sf_links, "corrections": 0}
        
        # Analyser un échantillon de pages avec l'IA
        ai_analysis = self.batch_analyze_pages(sample_urls, max_pages=5)
        
        if not ai_analysis:
            return {"improved_links": sf_links, "corrections": 0}
        
        # Créer un mapping des corrections basé sur l'analyse IA
        corrections = 0
        improved_links = []
        
        for link in sf_links:
            source_url = link.get('Source', '')
            link_text = link.get('Ancrage', '') or link.get('Texte Alt', '')
            dest_url = link.get('Destination', '')
            
            # Chercher si cette page a été analysée par l'IA
            ai_page_data = None
            for analyzed_url, data in ai_analysis.items():
                if source_url.startswith(analyzed_url.split('?')[0]):  # Match base URL
                    ai_page_data = data
                    break
            
            if ai_page_data and 'links' in ai_page_data:
                # Chercher le lien correspondant dans l'analyse IA
                ai_link = self._find_matching_link(link_text, dest_url, ai_page_data['links'])
                
                if ai_link:
                    # Ajuster la classification selon l'IA
                    original_mechanical = link.get('is_mechanical', False)
                    ai_editorial = ai_link['category'] in ['EDITORIAL', 'CALL_TO_ACTION']
                    
                    if original_mechanical and ai_editorial:
                        # Screaming Frog dit mécanique, IA dit éditorial -> Corriger
                        link['is_mechanical'] = False
                        link['ai_corrected'] = True
                        link['ai_category'] = ai_link['category']
                        link['ai_confidence'] = ai_link['confidence']
                        corrections += 1
                        
                    elif not original_mechanical and not ai_editorial:
                        # Screaming Frog dit éditorial, IA dit navigation -> Corriger
                        link['is_mechanical'] = True
                        link['ai_corrected'] = True
                        link['ai_category'] = ai_link['category']
                        link['ai_confidence'] = ai_link['confidence']
                        corrections += 1
            
            improved_links.append(link)
        
        print(f"🤖 IA a corrigé {corrections} classifications de liens")
        
        return {
            "improved_links": improved_links, 
            "corrections": corrections,
            "ai_analysis_summary": {
                "pages_analyzed": len(ai_analysis),
                "total_links_found": sum(len(data.get('links', [])) for data in ai_analysis.values())
            }
        }
    
    def _find_matching_link(self, text: str, dest_url: str, ai_links: List[Dict]) -> Optional[Dict]:
        """Trouver le lien correspondant dans l'analyse IA"""
        text_clean = text.lower().strip()
        dest_clean = dest_url.lower().strip()
        
        for ai_link in ai_links:
            ai_text = ai_link.get('text', '').lower().strip()
            ai_href = ai_link.get('href', '').lower().strip()
            
            # Match exact du texte
            if text_clean == ai_text:
                return ai_link
            
            # Match partiel du texte + URL similaire
            if (text_clean in ai_text or ai_text in text_clean) and dest_clean.endswith(ai_href.split('/')[-1]):
                return ai_link
        
        return None

# Instance globale
_anthropic_analyzer = None

def get_anthropic_analyzer(api_key: str = None) -> AnthropicContentAnalyzer:
    """Obtenir l'instance singleton de l'analyseur Anthropic"""
    global _anthropic_analyzer
    if _anthropic_analyzer is None:
        _anthropic_analyzer = AnthropicContentAnalyzer(api_key)
    return _anthropic_analyzer