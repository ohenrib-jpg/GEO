import json
import logging
from typing import List, Dict, Any
from .database import DatabaseManager

logger = logging.getLogger(__name__)

class ThemeManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def get_all_themes(self) -> List[Dict[str, Any]]:
        """Retourne tous les thèmes"""
        return self.db_manager.get_themes()
    
    def get_theme(self, theme_id: str) -> Dict[str, Any]:
        """Retourne un thème spécifique"""
        themes = self.db_manager.get_themes()
        for theme in themes:
            if theme['id'] == theme_id:
                return theme
        return {}
    
    def create_theme(self, theme_id: str, name: str, keywords: List[str], 
                    color: str = '#6366f1', description: str = '') -> bool:
        """Crée un nouveau thème"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO themes (id, name, keywords, color, description)
                VALUES (?, ?, ?, ?, ?)
            """, (
                theme_id,
                name,
                json.dumps(keywords, ensure_ascii=False),
                color,
                description
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Erreur création thème {theme_id}: {e}")
            return False
    
    def update_theme(self, theme_id: str, name: str = None, keywords: List[str] = None,
                    color: str = None, description: str = None) -> bool:
        """Met à jour un thème existant"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Récupère les données actuelles
            current_theme = self.get_theme(theme_id)
            if not current_theme:
                return False
            
            # Met à jour seulement les champs fournis
            update_name = name if name is not None else current_theme['name']
            update_keywords = keywords if keywords is not None else current_theme['keywords']
            update_color = color if color is not None else current_theme['color']
            update_description = description if description is not None else current_theme.get('description', '')
            
            cursor.execute("""
                UPDATE themes 
                SET name = ?, keywords = ?, color = ?, description = ?
                WHERE id = ?
            """, (
                update_name,
                json.dumps(update_keywords, ensure_ascii=False),
                update_color,
                update_description,
                theme_id
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Erreur mise à jour thème {theme_id}: {e}")
            return False
    
    def delete_theme(self, theme_id: str) -> bool:
        """Supprime un thème"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM themes WHERE id = ?", (theme_id,))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Erreur suppression thème {theme_id}: {e}")
            return False
    
    def get_theme_statistics(self) -> Dict[str, Any]:
        """Retourne des statistiques sur l'utilisation des thèmes"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        # Compte le nombre d'articles par thème
        cursor.execute("""
            SELECT t.id, t.name, t.color, COUNT(ta.article_id) as article_count
            FROM themes t
            LEFT JOIN theme_analyses ta ON t.id = ta.theme_id AND ta.confidence >= 0.3
            GROUP BY t.id
            ORDER BY article_count DESC
        """)
        
        stats = {}
        for row in cursor.fetchall():
            theme_id, name, color, count = row
            stats[theme_id] = {
                'name': name,
                'color': color,
                'article_count': count
            }
        
        conn.close()
        return stats