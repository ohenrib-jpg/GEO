import feedparser
import logging
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
            feed = feedparser.parse(feed_url)
            articles = []
            
            for entry in feed.entries:
                # Extraction des données de l'article
                title = entry.get('title', 'Sans titre')
                link = entry.get('link', '')
                published = entry.get('published_parsed', entry.get('updated_parsed'))
                
                # Conversion de la date
                if published:
                    pub_date = datetime(*published[:6])
                else:
                    pub_date = datetime.now()
                
                # Contenu de l'article
                content = ''
                if hasattr(entry, 'summary'):
                    content = entry.summary
                if hasattr(entry, 'content'):
                    content = entry.content[0].value if entry.content else content
                if hasattr(entry, 'description'):
                    content = entry.description if not content else content
                
                article_data = {
                    'title': title,
                    'content': content,
                    'link': link,
                    'pub_date': pub_date,
                    'feed_url': feed_url
                }
                
                articles.append(article_data)
            
            return articles
            
        except Exception as e:
            logger.error(f"Erreur parsing flux {feed_url}: {e}")
            return []
    
    def process_article(self, article_data: Dict[str, Any]) -> int:
        """
        Traite un article : sauvegarde + analyse sentiment + analyse thèmes
        Retourne l'ID de l'article sauvegardé
        """
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            # Vérifie si l'article existe déjà
            cursor.execute("SELECT id FROM articles WHERE link = ?", (article_data['link'],))
            existing = cursor.fetchone()
            
            if existing:
                logger.info(f"Article déjà existant: {article_data['title']}")
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
            theme_scores = self.theme_analyzer.analyze_article(
                article_data['content'],
                article_data['title']
            )
            
            # Sauvegarde de l'analyse des thèmes
            if theme_scores:
                self.theme_analyzer.save_theme_analysis(article_id, theme_scores)
            
            conn.commit()
            logger.info(f"Article traité: {article_data['title']} (ID: {article_id})")
            return article_id
            
        except Exception as e:
            logger.error(f"Erreur traitement article: {e}")
            conn.rollback()
            return -1
        finally:
            conn.close()
    
    def update_feeds(self, feed_urls: List[str]) -> Dict[str, Any]:
        """Met à jour tous les flux RSS"""
        results = {
            'total_articles': 0,
            'new_articles': 0,
            'errors': []
        }
        
        for feed_url in feed_urls:
            try:
                articles = self.parse_feed(feed_url)
                results['total_articles'] += len(articles)
                
                for article in articles:
                    article_id = self.process_article(article)
                    if article_id > 0:
                        results['new_articles'] += 1
                        
            except Exception as e:
                error_msg = f"Erreur flux {feed_url}: {e}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
        
        return results