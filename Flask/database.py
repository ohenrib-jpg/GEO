import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Dict, Any
from .config import DB_PATH, DEFAULT_THEMES

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialise la base de données avec les tables nécessaires"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Table des thèmes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS themes (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                keywords TEXT,
                color TEXT DEFAULT '#6366f1',
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table des articles
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                link TEXT UNIQUE,
                pub_date DATETIME,
                feed_url TEXT,
                sentiment_score REAL,
                sentiment_type TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table d'association articles-thèmes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS theme_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER,
                theme_id TEXT,
                confidence REAL DEFAULT 0.5,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
                FOREIGN KEY (theme_id) REFERENCES themes(id) ON DELETE CASCADE
            )
        """)
        
        # Index pour les performances
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_pub_date ON articles(pub_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_feed_url ON articles(feed_url)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_theme_analyses_article ON theme_analyses(article_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_theme_analyses_theme ON theme_analyses(theme_id)")
        
        conn.commit()
        conn.close()
        
        # Peupler avec les thèmes par défaut
        self._populate_default_themes()
    
    def _populate_default_themes(self):
        """Ajoute les thèmes par défaut à la base"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        for theme_id, theme_data in DEFAULT_THEMES.items():
            cursor.execute("""
                INSERT OR IGNORE INTO themes (id, name, keywords, color)
                VALUES (?, ?, ?, ?)
            """, (
                theme_id,
                theme_id.capitalize(),
                json.dumps(theme_data['keywords'], ensure_ascii=False),
                theme_data['color']
            ))
        
        conn.commit()
        conn.close()
    
    def get_connection(self):
        """Retourne une connexion à la base de données"""
        return sqlite3.connect(self.db_path)
    
    def execute_query(self, query: str, params: tuple = ()):
        """Exécute une requête et retourne le résultat"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchall()
        conn.commit()
        conn.close()
        return result
    
    def get_themes(self) -> List[Dict[str, Any]]:
        """Récupère tous les thèmes avec leurs mots-clés"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, keywords, color, description FROM themes")
        
        themes = []
        for row in cursor.fetchall():
            theme_id, name, keywords_json, color, description = row
            themes.append({
                'id': theme_id,
                'name': name,
                'keywords': json.loads(keywords_json) if keywords_json else [],
                'color': color,
                'description': description
            })
        
        conn.close()
        return themes