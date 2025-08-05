# 🔗 Audit de Maillage Interne

Un outil Python avancé pour analyser et optimiser le maillage interne de votre site web en se concentrant uniquement sur les **liens éditoriaux** (contenu).

## 🎯 Objectif

Cet outil permet d'effectuer un audit complet du maillage interne en :
- Distinguant automatiquement les liens **éditoriaux** des liens **mécaniques** (navigation)
- Analysant la qualité des ancres de liens
- Identifiant les pages orphelines
- Générant des recommandations SEO actionnables

## ✨ Fonctionnalités

### 🔍 Analyse Avancée
- **Détection intelligente** des liens éditoriaux vs mécaniques
- **Score de qualité** des ancres (0-100) basé sur le ratio éditorial
- **Analyse thématique** avec nuage de mots-clés
- **Identification des pages orphelines**
- **Détection d'ancres sur-optimisées**
- **🎯 Filtrage par préfixe d'URL** pour analyser des sections spécifiques
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

### 🛠️ Flexibilité
- **Crawl automatique** via Screaming Frog avec conversion de chemins WSL
- **Analyse de CSV existants**
- **Configuration personnalisable**
- **Gestion robuste des erreurs**

## 🚀 Installation

### Prérequis
- Python 3.7+
- Screaming Frog SEO Spider (v16+ pour crawls basiques, v22+ pour clustering sémantique)
- API AI optionnelle (OpenAI, Gemini, Ollama) pour l'analyse sémantique

### Installation
```bash
# Cloner le projet
git clone <votre-repo>
cd automate_internallinking_audit

# Installer les dépendances (optionnel, utilise uniquement des modules Python standard)
# Aucune dépendance externe requise !
```

## ⚙️ Configuration

Éditez le fichier `audit_config.json` pour personnaliser l'analyse :

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

### 1. Script Principal (Interactif)
```bash
python audit_maillage.py
```

Menu interactif avec options :
1. **🕷️ Nouveau crawl** Screaming Frog + Analyse (avec filtrage optionnel par URL)
2. **📊 Analyser un CSV existant** (avec filtrage optionnel par URL)
3. **📁 Lister les CSV disponibles**
4. **⚙️ Configuration**

### 2. Script Simple (CSV direct)
```bash
python audit_simple_csv.py
```

Analyse directement le fichier CSV existant.

## 📋 Format CSV Attendu

L'outil supporte les exports Screaming Frog avec colonnes :
- **Source** : URL de la page source
- **Destination** : URL de destination du lien
- **Ancrage** : Texte d'ancre du lien
- **Origine du lien** : Type de lien (navigation, contenu, etc.)
- **Chemin du lien** : XPath ou sélecteur CSS

## 📊 Sorties Générées

### Rapport HTML (`audit_report_YYYYMMDD_HHMMSS.html`)
- **Dashboard** avec métriques clés et score qualité corrigé
- **🕸️ Graphique de réseau interactif** du maillage interne :
  - Nœuds proportionnels aux liens entrants
  - Code couleur selon la connectivité
  - Contrôles interactifs (zoom, labels, orphelines)
  - Tooltips informatifs au survol
- **📝 Analyse de qualité du contenu** :
  - Répartition par nombre de mots (thin/qualité/riche)
  - Statistiques détaillées (moyenne, médiane)
  - Identification des pages à enrichir
- **🏷️ Cohérence Title/H1** :
  - Comparaison sémantique (identiques/similaires/différents)
  - Détection des problèmes SEO
  - Tableau des incohérences majeures
- **💰 Pages de conversion identifiées** :
  - Classification par type (contact, achat, devis, etc.)
  - Recommandations de maillage stratégique
  - Priorisation business
- **🧠 Analyse sémantique IA** (si SF v22+ configuré) :
  - Clustering automatique par thématiques
  - Détection de pages similaires non liées
  - Recommandations de maillage basées sur la proximité sémantique
  - Identification des pages piliers par cluster
- **Analyse détaillée des ancres** avec catégorisation
- **Distribution thématique** avec nuage de mots-clés
- **Pages les plus liées** et pages orphelines
- **Recommandations personnalisées** basées sur l'analyse

### Export CSV (`recommendations_YYYYMMDD_HHMMSS.csv`)
Colonnes :
- **Type** : Catégorie du problème
- **Priorité** : Haute/Moyenne/Basse
- **URL** : Page concernée
- **Problème** : Description du problème
- **Recommandation** : Action à effectuer
- **Détails** : Informations complémentaires

## 🎯 Types d'Analyses

### Liens Éditoriaux vs Mécaniques
- **Éditoriaux** : Liens dans le contenu, contextuel, SEO-friendly
- **Mécaniques** : Navigation, footer, breadcrumb, pagination

### Qualité des Ancres
- ✅ **Bonnes** : 2-6 mots, descriptives
- ⚠️ **Courtes** : < 4 caractères
- ⚠️ **Longues** : > 8 mots  
- 🚫 **Sur-optimisées** : Keyword stuffing détecté

### Problèmes Identifiés
- Pages orphelines (sans liens entrants éditoriaux)
- Ancres répétitives (sur-optimisation)
- Ancres non-descriptives
- Ratio éditorial faible
- Densité de maillage insuffisante

## 📈 Métriques Calculées

- **Ratio éditorial** : % de liens éditoriaux vs total liens internes
- **Score qualité** : 0-100 basé sur la qualité des ancres
- **Maillage moyen** : Nombre de liens éditoriaux par page
- **Pages orphelines** : Pages sans liens entrants éditoriaux
- **Distribution thématique** : Analyse des mots-clés d'ancres

## 🛡️ Gestion d'Erreurs

- Auto-détection de l'encodage CSV (UTF-8, Latin-1, CP1252)
- Détection intelligente du délimiteur (virgule, point-virgule, tabulation)
- Validation des colonnes requises
- Limitation de mémoire (500k lignes max)
- Messages d'erreur explicites avec suggestions

## 💡 Conseils d'Utilisation

### Pour un Audit Optimal
1. **Crawlez tout le site** avec Screaming Frog (v22+ recommandé)
2. **Configurez l'IA sémantique** (optionnel mais puissant) :
   - Config > API Access > AI dans Screaming Frog
   - Choisir OpenAI, Gemini ou Ollama
   - Activer `"enable_semantic_analysis": true` dans audit_config.json
3. **Exportez l'ensemble complet** : Links, Titles, H1, Word Count + Embeddings
4. **Utilisez le filtrage par URL** pour analyser des sections spécifiques
5. **Vérifiez la configuration** des patterns d'ancres
6. **Analysez le rapport HTML complet** :
   - Graphique de réseau pour la visualisation
   - Clustering sémantique pour l'organisation thématique
   - Qualité du contenu pour identifier le thin content
   - Cohérence Title/H1 pour les problèmes SEO
   - Pages de conversion pour la stratégie business
7. **Utilisez le CSV de recommandations** pour prioriser les actions

### 🎯 Filtrage par Section
- **Blog** : `https://monsite.com/blog/` 
- **Boutique** : `https://monsite.com/produits/`
- **Documentation** : `https://monsite.com/docs/`
- **Catégorie** : `https://monsite.com/category/astuces/`

### Seuils Recommandés
- **Ratio éditorial** : > 50% (idéal : > 70%)
- **Liens par page** : 2-3 liens éditoriaux minimum
- **Score qualité** : > 70/100
- **Répétition d'ancre** : < 5 occurrences
- **Qualité du contenu** : > 300 mots par page (éviter thin content)
- **Cohérence Title/H1** : > 80% de similarité sémantique
- **Pages de conversion** : Minimum 2-3 liens entrants éditoriaux par page
- **Clustering sémantique** : Seuil de similarité > 0.85 (IA)
- **Taille des clusters** : Minimum 3 pages par groupe thématique

## 🔧 Personnalisation

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
},
"semantic_analysis": {
  "enable_semantic_analysis": true,
  "similarity_threshold": 0.90,
  "min_cluster_size": 5,
  "ai_provider": "openai"
}
```

### Configurer l'Analyse Sémantique (SF v22+)
```json
"semantic_analysis": {
  "enable_semantic_analysis": true,
  "similarity_threshold": 0.85,
  "min_cluster_size": 3,
  "ai_provider": "openai"
}
```

**Prérequis pour l'IA Sémantique :**
1. Screaming Frog SEO Spider v22.0+
2. API configurée dans SF : `Config > API Access > AI`
3. Clé API valide (OpenAI, Gemini, ou Ollama)
4. Activer dans audit_config.json : `"enable_semantic_analysis": true`

## 📁 Structure du Projet

```
automate_internallinking_audit/
├── audit_maillage.py          # Script principal (interactif)
├── audit_simple_csv.py        # Script simple (analyse directe)
├── audit_config.json          # Configuration
├── exports/                   # Dossier de sortie
│   ├── *.html                # Rapports HTML
│   ├── *.csv                 # Exports de recommandations  
│   └── *.seospider           # Fichiers Screaming Frog
└── README.md                  # Cette documentation
```

## 🆕 Nouvelles Fonctionnalités v2.0

### 🕸️ Graphique de Réseau Interactif
- **Visualisation D3.js** du maillage interne
- **Nœuds proportionnels** au nombre de liens entrants
- **Code couleur** : Rouge → Jaune → Vert → Bleu (connectivité croissante)
- **Contrôles interactifs** :
  - 🔄 Réinitialiser la vue
  - 🏷️ Basculer les libellés
  - 🔍 Surligner les pages orphelines
- **Performance optimisée** : Limite à 100 nœuds les plus connectés

### 📝 Analyse de Qualité du Contenu
- **Détection automatique** des fichiers Screaming Frog (Word Count, Titles, H1)
- **Classification du contenu** :
  - 🔴 Thin content (<300 mots) : À éviter ou enrichir
  - 🟢 Contenu qualité (300-1500 mots) : Optimal pour le maillage
  - 🔵 Contenu riche (>1500 mots) : Pages piliers potentielles
- **Statistiques détaillées** : Moyenne, médiane, distribution
- **Recommandations** : Pages à enrichir ou éviter dans le maillage

### 🏷️ Cohérence Sémantique Title/H1
- **Analyse comparative** entre balises Title et H1
- **Score de similarité** : Identiques, similaires (>70%), différents
- **Détection de problèmes** : Balises manquantes ou incohérentes
- **Impact SEO** : Identification des pages avec incohérences majeures
- **Tableau détaillé** : Comparaison côte-à-côte des balises problématiques

### 💰 Pages de Conversion Business
- **Identification automatique** par patterns d'URL et contenu :
  - 📞 Contact : formulaires, coordonnées
  - 🛒 Achat : commande, panier, checkout
  - 📝 Inscription : register, signup
  - 💼 Devis : estimation, quote, demande
  - 💳 Pricing : tarifs, prix
  - 🎯 Demo : essai, trial, démonstration
- **Priorisation business** : Pages cruciales pour les conversions
- **Recommandations stratégiques** : Comment optimiser le maillage vers ces pages
- **Métriques** : % de pages de conversion sur le site total

### 🧠 Analyse Sémantique IA (Screaming Frog v22+)
- **Clustering automatique** : Groupement thématique des pages par IA
- **Détection de similarité** : Pages sémantiquement proches avec scores
- **Recommandations de maillage IA** :
  - Pages similaires non liées (liens manquants)
  - Opportunités de pages piliers par cluster
  - Optimisation de l'architecture thématique
- **Providers supportés** : OpenAI, Google Gemini, Ollama local
- **Seuils configurables** : Similarité, taille min des clusters
- **Visualisation enrichie** : Graphique réseau coloré par clusters sémantiques

### 🎯 Filtrage par Préfixe d'URL
- **Analyse ciblée** d'une section du site
- **Filtrage inclusif** : garde les liens source OU destination correspondants
- **Validation automatique** des préfixes HTTP/HTTPS
- **Statistiques de filtrage** affichées
- **Compatible** avec crawls et CSV existants

### ⚡ Score de Qualité Amélioré
- **Nouvelle logique** basée sur le ratio éditorial
- **Score de base** selon la proportion de liens éditoriaux :
  - `< 15%` : Score de base 10 (très faible)
  - `15-30%` : Score de base 30
  - `30-50%` : Score de base 50
  - `50-70%` : Score de base 70
  - `> 70%` : Score de base 90 (excellent)
- **Pénalités proportionnelles** à la qualité globale
- **Plafonnement à 100** (correction du bug > 100)

### 🔧 Corrections Techniques
- **Conversion de chemins WSL** pour Screaming Frog sous Windows
- **Debug avancé** des paramètres de crawl
- **Gestion robuste** des encodages CSV
- **Optimisation mémoire** pour gros datasets

### 📊 Export Screaming Frog Enrichi
- **Crawl multi-exports** : Links, Titles, H1, Word Count automatiquement
- **Support IA sémantique** : Embeddings, Similar Pages, Content Clusters (v22+)
- **Détection intelligente** des fichiers CSV par patterns
- **Gestion des erreurs** : Analyse partielle même si certains exports échouent
- **Performance** : Traitement optimisé des gros datasets

### 🚀 Fonctionnalités IA Révolutionnaires (v22+)
- **Maillage intelligent par IA** : Suggestions contextuelles basées sur la compréhension sémantique
- **Architecture thématique optimale** : Organisation automatique par clusters de contenu
- **Détection de gaps sémantiques** : Contenus similaires non connectés
- **Pages piliers automatiques** : Identification des contenus centraux par thème
- **Coûts optimisés** : Environ 5$ pour 50 000 URLs analysées (OpenAI)

## 🤝 Support

Pour toute question ou problème :
1. **Crawls classiques** : Vérifiez que le fichier CSV contient les colonnes Source/Destination
2. **Analyse sémantique** : Vérifiez SF v22+, API configurée, et clé valide
3. **Consultez les messages d'erreur** pour diagnostic détaillé
4. **Validez la configuration JSON** avec les nouveaux paramètres sémantiques
5. **Testez avec un petit échantillon** de données avant les gros crawls

### 🆘 Troubleshooting IA Sémantique
- **"Aucun fichier sémantique trouvé"** : Activez l'API AI dans Screaming Frog
- **Erreurs d'API** : Vérifiez votre clé API et les crédits disponibles
- **Performance lente** : Réduisez le seuil de similarité ou la taille des clusters
- **Coûts élevés** : Utilisez le filtrage par URL pour analyser seulement des sections

## 📝 License

Ce projet est sous licence libre. Utilisez et modifiez selon vos besoins.

---

**🎯 Focus : Liens Éditoriaux + IA Sémantique**  
Cet outil combine l'analyse traditionnelle des liens éditoriaux avec l'intelligence artificielle pour une optimisation SEO de nouvelle génération, utilisant la compréhension sémantique des contenus pour des recommandations de maillage interne ultra-précises.