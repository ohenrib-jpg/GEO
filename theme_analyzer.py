# Flask/theme_analyzer.py - VERSION AMÉLIORÉE
import re
import logging
import math
from typing import List, Dict, Any
from collections import Counter
from .database import DatabaseManager

logger = logging.getLogger(__name__)

class ThemeAnalyzer:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.themes_cache = None
        self.stop_words = {
            'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'et', 'ou', 'mais', 'donc', 'or', 'ni', 'car',
            'je', 'tu', 'il', 'elle', 'on', 'nous', 'vous', 'ils', 'elles',
            'me', 'te', 'se', 'lui', 'leur', 'y', 'en',
            'ce', 'cette', 'ces', 'cet', 'cette',
            'dans', 'sur', 'sous', 'entre', 'avant', 'après', 'pendant', 'pour', 'contre', 'depuis', 'jusque',
            'très', 'plus', 'moins', 'aussi', 'autant', 'mieux', 'mieux',
            'être', 'avoir', 'faire', 'aller', 'venir', 'pouvoir', 'vouloir', 'devoir',
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may', 'might', 'must'
        }
    
    def _get_themes_with_keywords(self) -> Dict[str, Dict[str, Any]]:
        """Récupère les thèmes avec leurs mots-clés (avec cache)"""
        if self.themes_cache is None:
            themes_data = self.db_manager.get_themes()
            self.themes_cache = {
                theme['id']: {
                    'name': theme['name'],
                    'keywords': [kw.lower() for kw in theme['keywords']],
                    'color': theme['color']
                }
                for theme in themes_data
            }
            logger.info(f"📚 {len(self.themes_cache)} thèmes chargés en cache")
        return self.themes_cache
    
    def clear_cache(self):
        """Vide le cache des thèmes (utile après modification)"""
        self.themes_cache = None
        logger.info("🔄 Cache des thèmes vidé")
    
    def _extract_ngrams(self, text: str, n: int = 2) -> List[str]:
        """Extrait les n-grammes du texte"""
        words = re.findall(r'\b[a-zA-ZàâäéèêëïîôùûüçÀÂÄÉÈÊËÏÎÔÙÛÜÇ]+\b', text.lower())
        # Filtrer les stop words
        words = [w for w in words if w not in self.stop_words and len(w) > 2]
        if n == 1:
            return words
        return [' '.join(words[i:i+n]) for i in range(len(words)-n+1)]
    
    def _calculate_tfidf(self, term: str, doc_freq: int, total_docs: int, term_freq: int) -> float:
        """Calcule le score TF-IDF pour un terme"""
        if doc_freq == 0 or term_freq == 0:
            return 0.0
        tf = math.log(1 + term_freq)  # Log frequency weighting
        idf = math.log(total_docs / doc_freq)
        return tf * idf
    
    def analyze_article(self, article_text: str, article_title: str = "") -> Dict[str, float]:
        """
        Analyse un article et retourne les thèmes détectés avec leur score de confiance
        Utilise une approche TF-IDF améliorée pour plus d'objectivité
        """
        if not article_text:
            return {}
        
        # Combine titre et contenu pour l'analyse
        full_text = f"{article_title} {article_text}".lower()
        themes_data = self._get_themes_with_keywords()
        results = {}
        
        # Extraction de tokens pour calcul TF-IDF
        unigrams = self._extract_ngrams(full_text, 1)
        bigrams = self._extract_ngrams(full_text, 2)
        all_tokens = unigrams + bigrams
        
        # Comptage des fréquences
        token_freq = Counter(all_tokens)
        total_tokens = len(all_tokens)
        
        # Estimation du nombre total de documents (articles) dans la base
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM articles")
        total_docs = cursor.fetchone()[0] or 1000  # Valeur par défaut si vide
        conn.close()
        
        for theme_id, theme_info in themes_data.items():
            score = 0
            matches_found = 0
            total_keywords = len(theme_info['keywords'])
            
            if total_keywords == 0:
                continue
            
            theme_specific_score = 0
            
            for keyword in theme_info['keywords']:
                # Recherche exacte du mot-clé
                exact_matches = token_freq.get(keyword.lower(), 0)
                
                if exact_matches > 0:
                    matches_found += 1
                    # Calcul TF-IDF simplifié
                    # Ici on approxime la fréquence documentaire
                    doc_freq = max(1, exact_matches)  # Approximation
                    tfidf_score = self._calculate_tfidf(keyword, doc_freq, total_docs, exact_matches)
                    theme_specific_score += tfidf_score
            
            # Score pondéré par la couverture thématique
            if matches_found > 0:
                coverage_ratio = matches_found / total_keywords
                # Normalisation avec racine carrée pour éviter la saturation
                normalized_score = math.sqrt(theme_specific_score / max(1, total_tokens)) * coverage_ratio
                
                # Appliquer un seuil minimum pour éviter les faux positifs
                if normalized_score >= 0.01:  # Seuil scientifique
                    results[theme_id] = min(normalized_score, 1.0)
                
                logger.debug(f"Thème '{theme_id}': {matches_found}/{total_keywords} mots-clés, score={normalized_score:.4f}")
        
        if results:
            logger.info(f"✅ {len(results)} thème(s) détecté(s) dans l'article")
        else:
            logger.debug("⚠️ Aucun thème détecté dans l'article")
        
        return results
    
    def save_theme_analysis(self, article_id: int, theme_scores: Dict[str, float]):
        """Sauvegarde l'analyse des thèmes pour un article"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            # Supprime les analyses précédentes pour cet article
            cursor.execute("DELETE FROM theme_analyses WHERE article_id = ?", (article_id,))
            
            # Insère les nouvelles analyses
            saved_count = 0
            for theme_id, confidence in theme_scores.items():
                if confidence >= 0.01:  # Seuil minimal scientifique
                    cursor.execute("""
                        INSERT INTO theme_analyses (article_id, theme_id, confidence)
                        VALUES (?, ?, ?)
                    """, (article_id, theme_id, confidence))
                    saved_count += 1
            
            conn.commit()
            logger.info(f"💾 {saved_count} analyse(s) de thème sauvegardée(s) pour l'article {article_id}")
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde analyse thèmes: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def reanalyze_all_articles(self):
        """Ré-analyse tous les articles existants avec les thèmes actuels"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            # Vider le cache pour avoir les thèmes à jour
            self.clear_cache()
            
            # Récupérer tous les articles
            cursor.execute("SELECT id, title, content FROM articles")
            articles = cursor.fetchall()
            
            logger.info(f"🔄 Ré-analyse de {len(articles)} articles...")
            
            for article_id, title, content in articles:
                theme_scores = self.analyze_article(content, title)
                if theme_scores:
                    self.save_theme_analysis(article_id, theme_scores)
            
            conn.close()
            logger.info(f"✅ Ré-analyse terminée pour {len(articles)} articles")
            
        except Exception as e:
            logger.error(f"Erreur ré-analyse articles: {e}")
            conn.close()
    
    def get_articles_by_theme(self, theme_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Récupère les articles pour un thème donné"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT a.id, a.title, a.content, a.link, a.pub_date, a.sentiment_type, ta.confidence
            FROM articles a
            JOIN theme_analyses ta ON a.id = ta.article_id
            WHERE ta.theme_id = ? AND ta.confidence >= 0.01
            ORDER BY ta.confidence DESC, a.pub_date DESC
            LIMIT ?
        """, (theme_id, limit))
        
        articles = []
        for row in cursor.fetchall():
            articles.append({
                'id': row[0],
                'title': row[1],
                'content': row[2],
                'link': row[3],
                'pub_date': row[4],
                'sentiment': row[5],
                'confidence': row[6]
            })
        
        conn.close()
        logger.info(f"📰 {len(articles)} article(s) trouvé(s) pour le thème '{theme_id}'")
        return articles
    
    def get_theme_statistics(self) -> Dict[str, int]:
        """Retourne le nombre d'articles par thème"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT theme_id, COUNT(DISTINCT article_id) as count
            FROM theme_analyses
            WHERE confidence >= 0.01
            GROUP BY theme_id
        """)
        
        stats = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        
        logger.info(f"📊 Statistiques: {len(stats)} thèmes avec articles")
        return stats
