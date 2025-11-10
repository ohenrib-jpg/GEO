# Flask/app_factory.py
import os
import sys
from flask import Flask
import logging

# Ajouter le répertoire parent au path pour les imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

def create_app():
    """Factory pour créer l'application Flask"""
    
    # Obtenir le chemin absolu du répertoire racine
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_dir = os.path.join(base_dir, 'templates')
    static_dir = os.path.join(base_dir, 'static')
    
    print(f"📁 Dossier templates: {template_dir}")
    print(f"📁 Dossier static: {static_dir}")
    
    # Vérifier si les dossiers existent
    if not os.path.exists(template_dir):
        print(f"✅ Création du dossier templates: {template_dir}")
        os.makedirs(template_dir, exist_ok=True)
    
    if not os.path.exists(static_dir):
        print(f"✅ Création du dossier static: {static_dir}")
        os.makedirs(static_dir, exist_ok=True)
    
    app = Flask(__name__, 
                template_folder=template_dir,
                static_folder=static_dir)
    
    # Configuration - imports absolus
    from Flask.config import DB_PATH
    app.config['DATABASE_PATH'] = DB_PATH
    
    # Initialisation des managers - imports absolus
    from Flask.database import DatabaseManager
    from Flask.theme_manager import ThemeManager
    from Flask.theme_manager_advanced import AdvancedThemeManager 
    from Flask.theme_analyzer import ThemeAnalyzer
    from Flask.rss_manager import RSSManager
    from Flask.bayesian_analyzer import BayesianSentimentAnalyzer  
    from Flask.corroboration_engine import CorroborationEngine     
    from Flask.database_migrations import run_migrations
    from Flask.social_aggregator import get_social_aggregator
    from Flask.social_comparator import get_social_comparator
    from Flask.routes_social import register_social_routes
    from Flask.archiviste import get_archiviste
    from Flask.routes_archiviste import register_archiviste_routes
    from Flask.anomaly_detector import AnomalyDetector

    db_manager = DatabaseManager()
    
    # Exécuter les migrations (une seule fois)
    run_migrations(db_manager)

    theme_manager = ThemeManager(db_manager)
    advanced_theme_manager = AdvancedThemeManager(db_manager)
    theme_analyzer = ThemeAnalyzer(db_manager) 
    rss_manager = RSSManager(db_manager)
    bayesian_analyzer = BayesianSentimentAnalyzer()          
    corroboration_engine = CorroborationEngine()
    social_aggregator = get_social_aggregator(db_manager)
    social_comparator = get_social_comparator(db_manager)             
    archiviste = get_archiviste(db_manager)
    anomaly_detector = AnomalyDetector(db_manager)

    # Enregistrement des routes - imports absolus
    from Flask.routes import register_routes
    from Flask.routes_advanced import register_advanced_routes

    register_routes(app, db_manager, theme_manager, theme_analyzer, rss_manager, advanced_theme_manager, anomaly_detector)
    register_advanced_routes(app, db_manager, bayesian_analyzer, corroboration_engine)
    register_social_routes(app, db_manager)
    register_archiviste_routes(app, db_manager)

    print("✅ Toutes les routes enregistrées avec succès")
    return app