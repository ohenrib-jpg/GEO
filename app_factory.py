# Flask/app_factory.py - VERSION COMPLÃˆTE CORRIGÃ‰E
import os
import sys
from flask import Flask
import logging

# Ajouter le rÃ©pertoire parent au chemin Python pour les imports absolus
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

def create_app():
    """Factory pour crÃ©er l'application Flask"""
    
    # Obtenir le chemin absolu du rÃ©pertoire racine
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_dir = os.path.join(base_dir, 'templates')
    static_dir = os.path.join(base_dir, 'static')
    
    print(f"ðŸ“ Dossier templates: {template_dir}")
    print(f"ðŸ“ Dossier static: {static_dir}")
    
    # VÃ©rifier si les dossiers existent
    if not os.path.exists(template_dir):
        print(f"âœ… CrÃ©ation du dossier templates: {template_dir}")
        os.makedirs(template_dir, exist_ok=True)
    
    if not os.path.exists(static_dir):
        print(f"âœ… CrÃ©ation du dossier static: {static_dir}")
        os.makedirs(static_dir, exist_ok=True)
    
    app = Flask(__name__, 
                template_folder=template_dir,
                static_folder=static_dir)
    
    # Configuration - IMPORT ABSOLU
    from Flask.config import DB_PATH
    app.config['DATABASE_PATH'] = DB_PATH
    
    print("ðŸš€ DÃ©marrage des migrations de base de donnÃ©es...")
    
    # 1. Migration de base
    from Flask.database_migration_fix import safe_migration
    safe_migration(DB_PATH)
    
    # 2. Migration RoBERTa
    from Flask.database_migration_sentiment import migrate_sentiment_columns
    migrate_sentiment_columns(DB_PATH)
    
    # 3. Migration avancÃ©e
    from Flask.database_migrations import run_migrations
    from Flask.database import DatabaseManager
    db_manager = DatabaseManager()
    run_migrations(db_manager)
    
    print("âœ… Toutes les migrations terminÃ©es!")
    
    # Initialisation des managers - IMPORTS ABSOLUS
    from Flask.theme_manager import ThemeManager
    from Flask.theme_manager_advanced import AdvancedThemeManager 
    from Flask.theme_analyzer import ThemeAnalyzer
    from Flask.rss_manager import RSSManager
    from Flask.sentiment_analyzer import SentimentAnalyzer
    from Flask.bayesian_analyzer import BayesianSentimentAnalyzer  
    from Flask.corroboration_engine import CorroborationEngine     
    
    theme_manager = ThemeManager(db_manager)
    advanced_theme_manager = AdvancedThemeManager(db_manager)
    theme_analyzer = ThemeAnalyzer(db_manager)
    rss_manager = RSSManager(db_manager)
    
    # INITIALISATION RoBERTa
    print("ðŸ”§ Initialisation de l'analyseur de sentiment...")
    sentiment_analyzer = SentimentAnalyzer()
    bayesian_analyzer = BayesianSentimentAnalyzer()          
    corroboration_engine = CorroborationEngine()
    
    # Injecter l'analyseur de sentiment dans RSSManager
    rss_manager.sentiment_analyzer = sentiment_analyzer
    print("âœ… Analyseur de sentiment injectÃ© dans RSSManager")
    
    # Enregistrement des routes - IMPORTS ABSOLUS
    from Flask.routes import register_routes
    from Flask.routes_advanced import register_advanced_routes

    # Enregistrer les routes
    register_routes(app, db_manager, theme_manager, theme_analyzer, rss_manager, advanced_theme_manager, sentiment_analyzer)
    register_advanced_routes(app, db_manager, bayesian_analyzer, corroboration_engine)
    
    print("ðŸŽ‰ Application Flask initialisÃ©e avec RoBERTa!")
    return app

# Permet l'exÃ©cution directe pour tests
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)