# 🔗 Audit de Maillage Interne

Un outil Python avancé pour analyser et optimiser le maillage interne de votre site web en se concentrant uniquement sur les **liens éditoriaux** (contenu). 

**🆕 Version 3.0** : Intelligence artificielle universelle avec Anthropic Claude pour détection automatique des zones de contenu sur tout site web.

## 🎯 Objectif

Cet outil permet d'effectuer un audit complet du maillage interne en :
- **🤖 Analyse IA universelle** des structures de contenu de tout site web
- Distinguant automatiquement les liens **éditoriaux** des liens **mécaniques** (navigation)
- **📂 Filtrage par section** avec échantillonnage intelligent des pages spécifiques
- Analysant la qualité des ancres de liens
- Identifiant les pages orphelines
- Générant des recommandations SEO actionnables

## ✨ Fonctionnalités

### 🤖 Intelligence Artificielle Universelle (v3.0)
- **Détecteur intelligent de contenu** avec Anthropic Claude
- **Échantillonnage stratégique** priorisant les pages de la section ciblée
- **Génération automatique** des configurations Screaming Frog optimisées
- **XPath intelligent** adapté à chaque structure de site web
- **Configuration API économique** : 1 appel par analyse (~$0.002)
- **Support universel** : fonctionne sur tout type de site (Shopify, WordPress, custom, etc.)

### 🎯 Filtrage par Section Spécialisé
- **Analyse ciblée** de sections spécifiques (ex: `/blogs/`, `/produits/`)
- **Échantillonnage IA optimisé** : 80% des pages analysées dans la section cible
- **Context minimal** : homepage uniquement pour référence structurelle
- **Configuration adaptative** : XPath générés spécifiquement pour la section

### 🔍 Analyse Avancée
- **Détection intelligente** des liens éditoriaux vs mécaniques
- **Score de qualité** des ancres (0-100) basé sur le ratio éditorial
- **Analyse thématique** avec nuage de mots-clés
- **Identification des pages orphelines**
- **Détection d'ancres sur-optimisées**
- **📝 Analyse de qualité du contenu** : nombre de mots, thin content
- **🏷️ Cohérence Title/H1** : détection des incohérences sémantiques
- **💰 Pages de conversion** : identification et priorisation automatique
- **🧠 Clustering sémantique IA** : analyse des groupes thématiques (SF v22+)
- **🔗 Recommandations de maillage IA** : suggestions basées sur la similarité sémantique

### 📊 Rapports Complets
- **Rapport HTML** interactif avec visualisations
- **🕸️ Graphique de réseau interactif** du maillage interne (D3.js)
- **Export CSV** des recommandations avec priorités
- **Métriques SEO** détaillées
- **Recommandations personnalisées**

### 🛠️ Workflow Intelligent (v3.0)
- **3 modes d'utilisation** :
  1. 🚀 Nouveau crawl intelligent (IA + Screaming Frog)
  2. 📊 Analyser un CSV existant
  3. ⚙️ Configuration IA seulement (générer config SF)
- **Intégration transparente** Anthropic ↔ Screaming Frog ↔ CamemBERT
- **Gestion robuste des erreurs**

## 🚀 Installation

### Prérequis
- Python 3.7+
- Screaming Frog SEO Spider (v16+ pour crawls basiques, v22+ pour clustering sémantique)
- **🔑 Clé API Anthropic** pour l'intelligence artificielle (obligatoire v3.0)
- API AI optionnelle (OpenAI, Gemini, Ollama) pour l'analyse sémantique CamemBERT

### Installation
```bash
# Cloner le projet
git clone <votre-repo>
cd automate_internallinking_audit

# Installer les dépendances IA
pip install anthropic beautifulsoup4 requests python-dotenv

# Configurer l'API Anthropic
cp .env.example .env
# Éditer .env et ajouter votre clé API Anthropic
```

## ⚙️ Configuration

### 1. Configuration API Anthropic (.env)
```env
# Clé API Anthropic (obligatoire pour v3.0)
ANTHROPIC_API_KEY=your_api_key_here

# Configuration optionnelle
ANTHROPIC_MODEL=claude-3-haiku-20240307
MAX_TOKENS=2000
```

### 2. Configuration Audit (ext_configuration_audit.json)
```json
{
  "screaming_frog_path": "/chemin/vers/ScreamingFrogSEOSpiderCli.exe",
  "export_path": "./exports/",
  "mechanical_anchor_patterns": [
    "^(accueil|home|menu|navigation)$",
    "^(suivant|précédent|next|previous|page \\d+)$",
    "^(lire la suite|en savoir plus|voir plus|read more)$"
  ],
  "analysis_thresholds": {
    "max_anchor_repetition": 5,
    "min_editorial_links_per_page": 2
  },
  "semantic_analysis": {
    "enable_semantic_analysis": false,
    "similarity_threshold": 0.85,
    "min_cluster_size": 3,
    "ai_provider": "openai"
  }
}
```

## 📖 Utilisation

### 1. Workflow Intelligent (Recommandé v3.0)
```bash
python 01_workflow_audit_ia_complet.py
```

**Menu interactif** avec 4 options :
1. **🚀 Nouveau crawl intelligent** : IA + Screaming Frog + Analyse complète
2. **📊 Analyser un CSV existant** : Import fichier avec analyse sémantique
3. **⚙️ Configuration IA seulement** : Générer config SF sans crawl
4. **❌ Quitter**

### 2. Script Principal (Classique)
```bash
python ext_audit_maillage_classique.py
```

Menu interactif avec options traditionnelles.

### 3. Script Simple (CSV direct)
```bash
python ext_analyse_csv_simple.py
```

## 🤖 Workflow Intelligent v3.0

### Étapes du Processus
1. **🤖 Analyse IA de la structure** : 
   - Échantillonnage stratégique (80% pages ciblées)
   - Détection zones de contenu avec Anthropic Claude
   - Génération XPath adaptatifs

2. **🕷️ Crawl Screaming Frog automatisé** :
   - Configuration optimisée générée par IA  
   - Export multi-formats automatique
   - Gestion des erreurs intégrée

3. **🧠 Filtrage intelligent** :
   - Application filtres de section
   - Détection liens éditoriaux vs mécaniques
   - Classification avancée par IA

4. **📊 Analyse sémantique finale** :
   - CamemBERT français pour clustering
   - Rapport HTML avec visualisations
   - Recommandations personnalisées

### 🎯 Filtrage par Section v3.0

**Format simplifié** pour la section :
- **Blogs** : `/blogs/`
- **Produits** : `/produits/`
- **Documentation** : `/docs/`

**L'IA analysera automatiquement** :
- 3-4 pages de la section spécifiée (priorité absolue)
- 1 page générale (homepage pour contexte)
- **Configuration adaptée** à la structure détectée

**Exemple d'utilisation** :
```
🌐 URL du site : https://monoreilleretmoi.com
📂 Section : /blogs/
📊 Limite : 50

→ IA analyse 4 pages blogs + homepage
→ Génère XPath spécialisé pour articles
→ SF crawle avec config optimisée
→ Filtre uniquement les liens /blogs/
→ Analyse sémantique finale
```

## 📋 Format CSV Attendu

L'outil supporte les exports Screaming Frog avec colonnes :
- **Source** : URL de la page source
- **Destination** : URL de destination du lien
- **Ancrage** : Texte d'ancre du lien
- **Origine du lien** : Type de lien (navigation, contenu, etc.)
- **Chemin du lien** : XPath ou sélecteur CSS

## 📊 Sorties Générées

### Rapport HTML (`audit_report_YYYYMMDD_HHMMSS.html`)
- **Dashboard** avec métriques clés et score qualité
- **🤖 Configuration IA** : XPath générés et zones détectées
- **🕸️ Graphique de réseau interactif** du maillage interne
- **📝 Analyse de qualité du contenu**
- **🏷️ Cohérence Title/H1**
- **💰 Pages de conversion identifiées** 
- **🧠 Analyse sémantique CamemBERT** (si activée)
- **Recommandations personnalisées** basées sur l'analyse IA

### Export CSV (`recommendations_YYYYMMDD_HHMMSS.csv`)
- **Type** : Catégorie du problème
- **Priorité** : Haute/Moyenne/Basse
- **URL** : Page concernée
- **Problème** : Description du problème
- **Recommandation** : Action à effectuer
- **Détails** : Informations complémentaires

## 🎯 Types d'Analyses

### Intelligence Artificielle (v3.0)
- **Détection universelle** de structures de contenu
- **Adaptation automatique** aux frameworks (Shopify, WordPress, etc.)
- **Échantillonnage intelligent** par section
- **Génération XPath spécialisés**

### Liens Éditoriaux vs Mécaniques
- **Éditoriaux** : Liens dans le contenu, contextuel, SEO-friendly
- **Mécaniques** : Navigation, footer, breadcrumb, pagination

### Qualité des Ancres
- ✅ **Bonnes** : 2-6 mots, descriptives
- ⚠️ **Courtes** : < 4 caractères
- ⚠️ **Longues** : > 8 mots  
- 🚫 **Sur-optimisées** : Keyword stuffing détecté

## 💰 Coûts API v3.0

### Anthropic Claude (Obligatoire)
- **Modèle utilisé** : claude-3-haiku-20240307 (économique)
- **Usage** : 1 appel par analyse de site
- **Coût estimé** : ~$0.002 par analyse
- **Tokens** : ~2000 tokens par analyse

### Analyse Sémantique (Optionnelle)
- **CamemBERT** : Gratuit (modèle local)
- **OpenAI/Gemini** : Seulement si clustering IA activé (SF v22+)

## 📁 Structure du Projet v3.0

```
automate_internallinking_audit/
├── 01_workflow_audit_ia_complet.py    # 🆕 Workflow IA principal
├── ext_detecteur_contenu_ia.py        # 🆕 Détecteur IA Anthropic
├── ext_audit_maillage_classique.py    # Script classique
├── ext_analyse_csv_simple.py          # Script simple
├── ext_analyseur_anthropic.py         # 🆕 Analyseur Anthropic
├── ext_analyseur_semantique.py        # Analyseur sémantique CamemBERT
├── ext_installer_dependances_semantiques.py # Script d'installation
├── .env.example                   # 🆕 Template configuration API
├── .env                          # Configuration API (ignoré par Git)
├── ext_configuration_audit.json      # Configuration audit
├── ext_config_screaming_frog.xml     # 🆕 Config SF générée par IA
├── exports/                      # Dossier de sortie
│   ├── *.html                   # Rapports HTML
│   ├── *.csv                    # Exports et recommandations
│   └── *.seospider             # Fichiers Screaming Frog
└── README.md                    # Cette documentation
```

## 🆕 Fonctionnalités v3.0 - Intelligence Artificielle

### 🤖 Détection Universelle de Contenu
- **Anthropic Claude** : Analyse et compréhension des structures HTML
- **Compatibilité universelle** : Shopify, WordPress, sites custom
- **XPath adaptatifs** : Générés spécifiquement pour chaque site
- **Exclusion intelligente** : Navigation, footer, sidebar automatiquement ignorés

### 📂 Échantillonnage Spécialisé par Section
- **Priorisation massive** : 80% des pages dans la section ciblée
- **Context minimal** : Homepage uniquement pour référence
- **Stratégie adaptative** : 
  - Section `/blogs/` → 3 articles + homepage
  - Section `/produits/` → 3 fiches produit + homepage
  - Pas de section → Échantillonnage général équilibré

### ⚙️ Génération Automatique Configuration Screaming Frog
- **XPath spécialisés** pour zones de contenu détectées
- **Filtres avancés** : Exclusion boutons, liens navigation
- **Config XML optimisée** : Prête à l'emploi pour SF
- **Validation automatique** : Test de cohérence des sélecteurs

### 🔗 Workflow Hybride IA + SF + CamemBERT
1. **Anthropic Claude** → Détection structure
2. **Screaming Frog** → Crawl optimisé  
3. **IA Python** → Filtrage intelligent
4. **CamemBERT** → Analyse sémantique
5. **Rapport final** → Synthèse complète

### 💡 Optimisations Intelligentes
- **Cache intelligent** : Évite les appels API redondants
- **Gestion d'erreurs** : Fallbacks et modes dégradés
- **Performance** : Traitement optimisé des gros datasets
- **Économie API** : Usage minimal et ciblé d'Anthropic

## 🆕 Nouvelles Fonctionnalités v2.1

### 🧠 Analyse Sémantique NLP Avancée (CamemBERT)
- **CamemBERT français** : Modèle de vectorisation spécialisé pour le français
- **Données enrichies** : Titles + H1 + H2 + H3 + Meta descriptions + Keywords + Alt text
- **Cache intelligent** : Embeddings sauvegardés pour éviter le recalcul
- **Clustering sémantique** : Regroupement automatique des thèmes par IA
- **Cohérence ancres ↔ contenus** : Score de pertinence des liens (0-100%)
- **Opportunités de maillage** : Détection de pages similaires non liées
- **Filtrage des stop words** : Suppression de 200+ mots vides français

### 🎨 Interface Épurée
- **Suppression des icônes** : Interface plus professionnelle et épurée
- **Capitalisation cohérente** : Une seule majuscule en début de phrase
- **Design moderne** : Rapport HTML plus lisible et élégant

### 📊 Graphiques Thématiques Visuels
- **Graphique en barres** : Distribution des mots-clés principaux avec scores
- **Graphique en camembert** : Répartition des types de pages liées
- **Styles CSS avancés** : Graphiques responsives et colorés
- **Nuage de mots** : Complément visuel pour les termes identifiés

## 💡 Conseils d'Utilisation v3.0

### Pour un Audit Optimal avec IA
1. **🔑 Configurez votre API Anthropic** dans `.env`
2. **🎯 Choisissez votre section** : `/blogs/`, `/produits/`, etc.
3. **🚀 Lancez le workflow intelligent** : `python 01_workflow_audit_ia_complet.py`
4. **⚙️ Laissez l'IA analyser** : Détection automatique des structures
5. **🕷️ SF crawle avec config optimisée** : XPath générés par IA
6. **📊 Analysez le rapport final** : Visualisations et recommandations

### 🎯 Filtrage par Section Optimisé
**✅ Formats recommandés :**
- **Blogs** : `/blogs/` → IA analyse 3 articles + homepage
- **E-commerce** : `/produits/` → IA analyse 3 fiches + homepage  
- **Documentation** : `/docs/` → IA analyse 3 pages doc + homepage

**📊 Résultat attendu :**
```
🎯 Échantillonnage stratégique sur https://monsite.com
   📂 Focus sur la section: /blogs/
   🎯 15 pages trouvées dans /blogs/
   📊 Répartition: 4 pages section / 1 pages générales
   ✅ 5 pages stratégiquement échantillonnées
```

### Seuils Recommandés
- **Ratio éditorial** : > 50% (idéal : > 70%)
- **Liens par page** : 2-3 liens éditoriaux minimum
- **Score qualité** : > 70/100
- **Répétition d'ancre** : < 5 occurrences
- **API Anthropic** : ~$1 pour 500 analyses de sites

## 🔧 Personnalisation

### Configuration API Anthropic
```env
ANTHROPIC_API_KEY=sk-ant-api03-xxx
ANTHROPIC_MODEL=claude-3-haiku-20240307
MAX_TOKENS=2000
```

### Ajouter des Patterns d'Ancres Mécaniques
```json
"mechanical_anchor_patterns": [
  "^(votre|pattern|custom)$",
  "^\\d+$"
]
```

### Modifier les Seuils d'Analyse
```json
"analysis_thresholds": {
  "max_anchor_repetition": 3,
  "min_editorial_links_per_page": 3,
  "max_outbound_links_per_page": 100
}
```

## 🤝 Support v3.0

### 🆘 Troubleshooting Intelligence Artificielle
- **"API Anthropic non disponible"** : Vérifiez votre clé dans `.env`
- **"Échec de l'analyse IA"** : Vérifiez votre connexion internet
- **"Aucune page trouvée dans section"** : Format `/section/` avec slashes
- **Configuration SF échoue** : Vérifiez le chemin Screaming Frog
- **Coûts API élevés** : 1 appel par site analysé (~$0.002)

### 📋 Diagnostic Rapide
1. **Testez la configuration** : Option 3 du menu (config IA seulement)
2. **Vérifiez les logs** : Messages détaillés dans la console  
3. **Validez votre section** : Format `/section/` requis
4. **Contrôlez l'API** : Crédits Anthropic disponibles

## 📝 License

Ce projet est sous licence libre. Utilisez et modifiez selon vos besoins.

---

**🎯 Focus v3.0 : IA Universelle + Liens Éditoriaux**  
Cette version révolutionne l'audit de maillage en utilisant l'intelligence artificielle Anthropic Claude pour comprendre automatiquement la structure de tout site web, générer des configurations optimisées et analyser spécifiquement les sections ciblées avec une précision inégalée.