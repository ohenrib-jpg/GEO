import feedparser
import logging
import sqlite3
from datetime import datetime
from typing import List, Dict, Any
from .database import DatabaseManager
from .sentiment_analyzer import SentimentAnalyzer
from .theme_analyzer import ThemeAnalyzer

logger = logging.getLogger(__name__)

class RSSManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.sentiment_analyzer = SentimentAnalyzer()
        self.theme_analyzer = ThemeAnalyzer(db_manager)
    
    def parse_feed(self, feed_url: str) -> List[Dict[str, Any]]:
        """Parse un flux RSS et retourne les articles"""
        try:
            logger.info(f"📡 Parsing flux RSS: {feed_url}")
            feed = feedparser.parse(feed_url)
            
            if hasattr(feed, 'bozo') and feed.bozo:
                logger.warning(f"⚠️ Flux RSS avec erreurs: {feed_url} - {feed.bozo_exception}")
            
            articles = []
            
            for entry in feed.entries:
                try:
                    # Extraction des données de l'article
                    title = entry.get('title', 'Sans titre').strip()
                    link = entry.get('link', '').strip()
                    
                    if not link:
                        logger.debug("Article sans lien, ignoré")
                        continue
                    
                    # Conversion de la date
                    published = entry.get('published_parsed', entry.get('updated_parsed'))
                    if published:
                        pub_date = datetime(*published[:6])
                    else:
                        pub_date = datetime.now()
                    
                    # Contenu de l'article
                    content = ''
                    if hasattr(entry, 'summary') and entry.summary:
                        content = entry.summary
                    if hasattr(entry, 'content') and entry.content:
                        content = entry.content[0].value if not content else content
                    if hasattr(entry, 'description') and entry.description and not content:
                        content = entry.description
                    
                    # Nettoyer le contenu
                    content = content.strip() if content else ''
                    
                    article_data = {
                        'title': title,
                        'content': content,
                        'link': link,
                        'pub_date': pub_date,
                        'feed_url': feed_url
                    }
                    
                    articles.append(article_data)
                    
                except Exception as e:
                    logger.error(f"❌ Erreur traitement article individuel: {e}")
                    continue
            
            logger.info(f"✅ {len(articles)} articles parsés depuis {feed_url}")
            return articles
            
        except Exception as e:
            logger.error(f"❌ Erreur parsing flux {feed_url}: {e}")
            return []
    
    def process_article(self, article_data: Dict[str, Any]) -> int:
        """
        Traite un article : sauvegarde + analyse sentiment + analyse thèmes
        Retourne l'ID de l'article sauvegardé
        """
        conn = None
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Vérifie si l'article existe déjà
            cursor.execute("SELECT id FROM articles WHERE link = ?", (article_data['link'],))
            existing = cursor.fetchone()
            
            if existing:
                logger.debug(f"📝 Article déjà existant: {article_data['title'][:50]}...")
                return existing[0]
            
            # Analyse des sentiments
            sentiment_result = self.sentiment_analyzer.analyze_article(
                article_data['title'], 
                article_data['content']
            )
            
            # Sauvegarde de l'article
            cursor.execute("""
                INSERT INTO articles 
                (title, content, link, pub_date, feed_url, sentiment_score, sentiment_type)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                article_data['title'],
                article_data['content'],
                article_data['link'],
                article_data['pub_date'],
                article_data['feed_url'],
                sentiment_result['score'],
                sentiment_result['type']
            ))
            
            article_id = cursor.lastrowid
            
            # Analyse des thèmes
            if article_data['content']:  # Ne pas analyser si contenu vide
                try:
                    theme_scores = self.theme_analyzer.analyze_article(
                        article_data['content'],
                        article_data['title']
                    )
                    
                    # Sauvegarde de l'analyse des thèmes
                    if theme_scores:
                        self.theme_analyzer.save_theme_analysis(article_id, theme_scores)
                except Exception as e:
                    logger.warning(f"⚠️ Erreur analyse thèmes pour l'article {article_id}: {e}")
            
            conn.commit()
            logger.info(f"✅ Article traité: {article_data['title'][:50]}... (ID: {article_id})")
            return article_id
            
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed: articles.link" in str(e):
                logger.debug(f"🔁 Doublon détecté et ignoré: {article_data['link']}")
                return -1  # Code spécial pour doublon
            else:
                logger.error(f"❌ Erreur intégrité BDD: {e}")
                if conn:
                    conn.rollback()
                return -1
        except Exception as e:
            logger.error(f"❌ Erreur traitement article: {e}")
            if conn:
                conn.rollback()
            return -1
        finally:
            if conn:
                conn.close()
    
    def update_feeds(self, feed_urls: List[str]) -> Dict[str, Any]:
        """Met à jour tous les flux RSS"""
        results = {
            'total_articles': 0,
            'new_articles': 0,
            'errors': [],
            'feeds_processed': 0
        }
        
        for feed_url in feed_urls:
            try:
                logger.info(f"🔄 Traitement du flux: {feed_url}")
                articles = self.parse_feed(feed_url)
                results['total_articles'] += len(articles)
                
                new_articles_count = 0
                for article in articles:
                    article_id = self.process_article(article)
                    if article_id > 0:
                        new_articles_count += 1
                
                results['new_articles'] += new_articles_count
                results['feeds_processed'] += 1
                
                logger.info(f"📊 Flux {feed_url}: {len(articles)} articles trouvés, {new_articles_count} nouveaux")
                        
            except Exception as e:
                error_msg = f"Erreur flux {feed_url}: {e}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
        
        logger.info(f"🎯 Mise à jour terminée: {results['new_articles']} nouveaux articles sur {results['total_articles']} trouvés")
        return results

    def get_article_count(self) -> int:
        """Retourne le nombre total d'articles dans la base"""
        conn = None
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM articles")
            count = cursor.fetchone()[0]
            return count
        except Exception as e:
            logger.error(f"Erreur comptage articles: {e}")
            return 0
        finally:
            if conn:
                conn.close()

    def cleanup_old_articles(self, days_old: int = 30):
        """Nettoie les articles plus vieux que X jours"""
        conn = None
        try:
            cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days_old)
            
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # D'abord supprimer les analyses de thèmes associées
            cursor.execute("""
                DELETE FROM theme_analyses 
                WHERE article_id IN (
                    SELECT id FROM articles WHERE pub_date < ?
                )
            """, (cutoff_date,))
            
            # Puis supprimer les articles
            cursor.execute("DELETE FROM articles WHERE pub_date < ?", (cutoff_date,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            logger.info(f"🧹 {deleted_count} articles vieux de plus de {days_old} jours supprimés")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Erreur nettoyage articles: {e}")
            if conn:
                conn.rollback()
            return 0
        finally:
            if conn:
                conn.close()