#!/usr/bin/env python3
"""
Module d'analyse sémantique avancée avec CamemBERT pour l'audit de maillage interne
"""

import os
import json
import hashlib
import pickle
from collections import defaultdict, Counter
import numpy as np
from typing import Dict, List, Tuple, Optional

# Import conditionnel des dépendances ML
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.cluster import DBSCAN
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False
    print("⚠️  Dépendances ML non installées. Fonctionnalités avancées désactivées.")
    print("💡 Installez avec: pip install sentence-transformers scikit-learn")

class CamemBERTSemanticAnalyzer:
    """Analyseur sémantique avancé avec CamemBERT et cache intelligent"""
    
    def __init__(self, cache_dir="./semantic_cache"):
        self.cache_dir = cache_dir
        self.model = None
        # Modèles français par ordre de préférence
        self.french_models = [
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",  # Multilingue avec bon français
            "sentence-transformers/distiluse-base-multilingual-cased",       # Léger et multilingue
            "all-MiniLM-L6-v2"  # Fallback universel
        ]
        
        # Créer le dossier de cache
        os.makedirs(cache_dir, exist_ok=True)
        
        # Initialiser le modèle si les dépendances sont disponibles
        if DEPENDENCIES_AVAILABLE:
            self._load_model()
    
    def _load_model(self):
        """Charger le meilleur modèle français disponible"""
        if self.model is None and DEPENDENCIES_AVAILABLE:
            print(f"🧠 Chargement du modèle sémantique français...")
            
            for model_name in self.french_models:
                try:
                    print(f"🔄 Tentative: {model_name}")
                    self.model = SentenceTransformer(model_name)
                    print(f"✅ Modèle chargé avec succès: {model_name}")
                    self.current_model_name = model_name
                    break
                except Exception as e:
                    print(f"⚠️  Échec pour {model_name}: {str(e)[:100]}...")
                    continue
            
            if self.model is None:
                print("❌ Impossible de charger un modèle sémantique")
                return False
                
        return self.model is not None
    
    def _get_cache_key(self, text: str) -> str:
        """Générer une clé de cache basée sur le hash du texte"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def _get_cached_embedding(self, text: str) -> Optional[np.ndarray]:
        """Récupérer un embedding depuis le cache"""
        cache_key = self._get_cache_key(text)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
            except Exception:
                # Cache corrompu, supprimer
                os.remove(cache_file)
        return None
    
    def _cache_embedding(self, text: str, embedding: np.ndarray):
        """Sauvegarder un embedding dans le cache"""
        cache_key = self._get_cache_key(text)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")
        
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(embedding, f)
        except Exception as e:
            print(f"⚠️  Impossible de sauvegarder le cache: {e}")
    
    def encode_with_cache(self, texts: List[str]) -> np.ndarray:
        """Encoder des textes avec cache intelligent"""
        if not self._load_model():
            return np.array([])
        
        embeddings = []
        texts_to_encode = []
        cache_indices = {}
        
        # Vérifier le cache pour chaque texte
        for i, text in enumerate(texts):
            if not text or len(text.strip()) < 3:
                embeddings.append(np.zeros(self.model.get_sentence_embedding_dimension()))
                continue
                
            cached_embedding = self._get_cached_embedding(text)
            if cached_embedding is not None:
                embeddings.append(cached_embedding)
            else:
                cache_indices[len(texts_to_encode)] = i
                texts_to_encode.append(text)
                embeddings.append(None)  # Placeholder
        
        # Encoder les textes non mis en cache
        if texts_to_encode:
            print(f"🔄 Encodage de {len(texts_to_encode)} nouveaux textes...")
            new_embeddings = self.model.encode(texts_to_encode, show_progress_bar=True)
            
            # Insérer les nouveaux embeddings et les mettre en cache
            for j, embedding in enumerate(new_embeddings):
                original_idx = cache_indices[j]
                embeddings[original_idx] = embedding
                self._cache_embedding(texts_to_encode[j], embedding)
        
        return np.array(embeddings)
    
    def analyze_semantic_coherence(self, anchors: List[str], page_contents: List[str]) -> List[float]:
        """Analyser la cohérence sémantique entre ancres et contenus de pages"""
        if not anchors or not page_contents:
            return []
        
        print("🔍 Analyse de cohérence sémantique ancres ↔ contenus...")
        
        # Encoder les ancres et contenus
        anchor_embeddings = self.encode_with_cache(anchors)
        content_embeddings = self.encode_with_cache(page_contents)
        
        if anchor_embeddings.size == 0 or content_embeddings.size == 0:
            return [0.0] * len(anchors)
        
        # Calculer la similarité cosinus
        similarities = []
        for i in range(len(anchors)):
            if i < len(content_embeddings):
                sim = cosine_similarity([anchor_embeddings[i]], [content_embeddings[i]])[0][0]
                similarities.append(float(sim))
            else:
                similarities.append(0.0)
        
        return similarities
    
    def cluster_semantic_themes(self, anchor_texts: List[str], min_cluster_size: int = 3) -> Dict[str, List[str]]:
        """Clustering sémantique des ancres par thèmes"""
        if not anchor_texts or len(anchor_texts) < min_cluster_size:
            return {}
        
        print(f"🎯 Clustering sémantique de {len(anchor_texts)} ancres...")
        
        # Filtrer les ancres vides et trop courtes
        filtered_anchors = [anchor for anchor in anchor_texts if anchor and len(anchor.strip()) > 3]
        if len(filtered_anchors) < min_cluster_size:
            return {}
        
        # Détecter si toutes les ancres sont quasi-identiques (faible diversité)
        unique_anchors = set(anchor.lower().strip() for anchor in filtered_anchors)
        diversity_ratio = len(unique_anchors) / len(filtered_anchors)
        
        print(f"📊 Diversité des ancres: {len(unique_anchors)} uniques sur {len(filtered_anchors)} ({diversity_ratio:.2%})")
        
        # Si diversité trop faible (< 30%), pas pertinent de faire du clustering
        if diversity_ratio < 0.3:
            print("⚠️  Diversité insuffisante pour un clustering pertinent")
            print("💡 Recommandation: Diversifier les ancres de liens pour une meilleure analyse sémantique")
            return {}
        
        # Encoder les ancres
        embeddings = self.encode_with_cache(filtered_anchors)
        if embeddings.size == 0:
            return {}
        
        # Clustering DBSCAN avec paramètres ajustés pour éviter un seul gros cluster
        # eps plus petit = clusters plus stricts
        clustering = DBSCAN(eps=0.2, min_samples=min_cluster_size, metric='cosine')
        cluster_labels = clustering.fit_predict(embeddings)
        
        # Si un seul cluster contient >50% des données, essayer avec eps plus petit
        unique_labels, counts = np.unique(cluster_labels, return_counts=True)
        if len(unique_labels) == 2 and -1 in unique_labels:  # Seulement 1 cluster + bruit
            max_cluster_size = counts[unique_labels != -1][0] if len(counts[unique_labels != -1]) > 0 else 0
            if max_cluster_size > len(filtered_anchors) * 0.5:
                print("   🔄 Cluster trop large, affinement avec eps=0.15...")
                clustering = DBSCAN(eps=0.15, min_samples=max(2, min_cluster_size-1), metric='cosine')
                cluster_labels = clustering.fit_predict(embeddings)
        
        # Grouper par clusters
        clusters = defaultdict(list)
        for anchor, label in zip(filtered_anchors, cluster_labels):
            if label != -1:  # Ignorer le bruit (-1)
                clusters[f"Thème {int(label) + 1}"].append(anchor)
        
        # Nommer les clusters intelligemment avec stop words français
        french_stop_words = {
            'dans', 'avec', 'pour', 'sur', 'sous', 'vers', 'chez', 'sans', 'contre',
            'depuis', 'pendant', 'avant', 'après', 'entre', 'parmi', 'selon',
            'notre', 'votre', 'leur', 'cette', 'ces', 'tous', 'toutes',
            'plus', 'moins', 'très', 'bien', 'encore', 'aussi', 'donc'
        }
        
        named_clusters = {}
        for cluster_id, anchors in clusters.items():
            if len(anchors) >= min_cluster_size:
                # Trouver les mots les plus fréquents (hors stop words)
                all_words = []
                for anchor in anchors:
                    words = anchor.lower().split()
                    meaningful_words = [w for w in words if len(w) > 3 and w not in french_stop_words]
                    all_words.extend(meaningful_words)
                
                if all_words:
                    word_freq = Counter(all_words)
                    # Prendre les 2-3 mots les plus fréquents
                    top_words = [word for word, count in word_freq.most_common(3) if count >= 2]
                    if len(top_words) >= 2:
                        cluster_name = " + ".join(top_words[:2]).title()
                    elif len(top_words) == 1:
                        cluster_name = f"{top_words[0].title()} ({len(anchors)} liens)"
                    else:
                        # cluster_id est déjà une string comme "Thème 1", donc on la garde
                        cluster_name = cluster_id
                    
                    named_clusters[cluster_name] = anchors
        
        return named_clusters
    
    def find_semantic_gaps(self, page_contents: Dict[str, str], threshold: float = 0.7) -> List[Tuple[str, str, float]]:
        """Identifier les pages sémantiquement similaires qui ne sont pas liées"""
        if not page_contents or len(page_contents) < 2:
            return []
        
        print(f"🔍 Recherche d'opportunités de maillage sur {len(page_contents)} pages...")
        
        urls = list(page_contents.keys())
        contents = list(page_contents.values())
        
        # Encoder tous les contenus
        embeddings = self.encode_with_cache(contents)
        if embeddings.size == 0:
            return []
        
        # Calculer la matrice de similarité
        similarity_matrix = cosine_similarity(embeddings)
        
        # Trouver les paires similaires
        opportunities = []
        for i in range(len(urls)):
            for j in range(i + 1, len(urls)):
                similarity = similarity_matrix[i][j]
                if similarity > threshold:
                    opportunities.append((urls[i], urls[j], float(similarity)))
        
        # Trier par similarité décroissante
        opportunities.sort(key=lambda x: x[2], reverse=True)
        
        return opportunities[:20]  # Top 20 opportunités
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Obtenir les statistiques du cache"""
        if not os.path.exists(self.cache_dir):
            return {"files": 0, "size_mb": 0}
        
        files = [f for f in os.listdir(self.cache_dir) if f.endswith('.pkl')]
        total_size = sum(os.path.getsize(os.path.join(self.cache_dir, f)) for f in files)
        
        return {
            "files": len(files),
            "size_mb": round(total_size / (1024 * 1024), 2)
        }
    
    def clear_cache(self):
        """Vider le cache"""
        if os.path.exists(self.cache_dir):
            for file in os.listdir(self.cache_dir):
                if file.endswith('.pkl'):
                    os.remove(os.path.join(self.cache_dir, file))
            print("🧹 Cache vidé")

# Instance globale pour éviter de recharger le modèle
_semantic_analyzer = None

def get_semantic_analyzer() -> CamemBERTSemanticAnalyzer:
    """Obtenir l'instance singleton de l'analyseur sémantique"""
    global _semantic_analyzer
    if _semantic_analyzer is None:
        _semantic_analyzer = CamemBERTSemanticAnalyzer()
    return _semantic_analyzer