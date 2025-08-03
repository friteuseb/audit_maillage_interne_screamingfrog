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
- **Score de qualité** des ancres (0-100)
- **Analyse thématique** avec nuage de mots-clés
- **Identification des pages orphelines**
- **Détection d'ancres sur-optimisées**

### 📊 Rapports Complets
- **Rapport HTML** interactif avec visualisations
- **Export CSV** des recommandations avec priorités
- **Métriques SEO** détaillées
- **Recommandations personnalisées**

### 🛠️ Flexibilité
- **Crawl automatique** via Screaming Frog
- **Analyse de CSV existants**
- **Configuration personnalisable**
- **Gestion robuste des erreurs**

## 🚀 Installation

### Prérequis
- Python 3.7+
- Screaming Frog SEO Spider (pour les nouveaux crawls)

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
  }
}
```

## 📖 Utilisation

### 1. Script Principal (Interactif)
```bash
python audit_maillage.py
```

Menu interactif avec options :
1. **Nouveau crawl** Screaming Frog + Analyse
2. **Analyser un CSV existant**
3. **Lister les CSV disponibles**
4. **Configuration**

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
- Dashboard avec métriques clés
- Score de qualité éditorial avec barre de progression
- Analyse détaillée des ancres
- Distribution thématique avec nuage de mots-clés
- Pages les plus liées et pages orphelines
- Recommandations personnalisées

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
1. **Crawlez tout le site** avec Screaming Frog
2. **Exportez "All Outlinks"** en CSV
3. **Vérifiez la configuration** des patterns d'ancres
4. **Analysez le rapport HTML** pour comprendre la situation
5. **Utilisez le CSV de recommandations** pour prioriser les actions

### Seuils Recommandés
- **Ratio éditorial** : > 50%
- **Liens par page** : 2-3 liens éditoriaux minimum
- **Score qualité** : > 70/100
- **Répétition d'ancre** : < 5 occurrences

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
}
```

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

## 🤝 Support

Pour toute question ou problème :
1. Vérifiez que le fichier CSV contient les colonnes Source/Destination
2. Consultez les messages d'erreur pour diagnostic
3. Validez la configuration JSON
4. Testez avec un petit échantillon de données

## 📝 License

Ce projet est sous licence libre. Utilisez et modifiez selon vos besoins.

---

**🎯 Focus : Liens Éditoriaux Uniquement**  
Cet outil se concentre exclusivement sur l'analyse des liens éditoriaux pour optimiser votre SEO, en filtrant automatiquement tous les liens de navigation et mécaniques.