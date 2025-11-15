# Flask/app_factory.py - VERSION OPTIMISÉE
import os
import logging
from flask import Flask

logger = logging.getLogger(__name__)

def create_app():
    """Factory pour créer l'application Flask"""
    
    # Chemins des dossiers
    flask_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(flask_dir)
    template_dir = os.path.join(base_dir, 'templates')
    static_dir = os.path.join(base_dir, 'static')
    
    print(f"📂 Répertoire Flask: {flask_dir}")
    print(f"📂 Répertoire base: {base_dir}")
    print(f"📂 Dossier templates: {template_dir}")
    print(f"📂 Dossier static: {static_dir}")
    
    # Vérifier/créer les dossiers
    if not os.path.exists(template_dir):
        print(f"⚠️ ATTENTION: Le dossier templates n'existe pas: {template_dir}")
        os.makedirs(template_dir, exist_ok=True)
        print(f"✅ Création du dossier templates: {template_dir}")
    
    if not os.path.exists(static_dir):
        print(f"⚠️ ATTENTION: Le dossier static n'existe pas: {static_dir}")
        os.makedirs(static_dir, exist_ok=True)
        print(f"✅ Création du dossier static: {static_dir}")
    
    # Créer l'application Flask
    app = Flask(__name__, 
                template_folder=template_dir,
                static_folder=static_dir)
    
    # Configuration
    from .config import DB_PATH
    app.config['DATABASE_PATH'] = DB_PATH
    
    # Initialisation des managers
    from .database import DatabaseManager
    from .theme_manager import ThemeManager
    from .theme_manager_advanced import AdvancedThemeManager 
    from .theme_analyzer import ThemeAnalyzer
    from .rss_manager import RSSManager
    from .bayesian_analyzer import BayesianSentimentAnalyzer  
    from .corroboration_engine import CorroborationEngine     
    from .database_migrations import run_migrations
    from .llama_client import get_llama_client
    from .sentiment_analyzer import SentimentAnalyzer
    from .batch_sentiment_analyzer import create_batch_analyzer
    
    db_manager = DatabaseManager()
    
    # Exécuter les migrations
    run_migrations(db_manager)

    # Création de tous les managers
    theme_manager = ThemeManager(db_manager)
    advanced_theme_manager = AdvancedThemeManager(db_manager)
    theme_analyzer = ThemeAnalyzer(db_manager)
    rss_manager = RSSManager(db_manager)
    bayesian_analyzer = BayesianSentimentAnalyzer()          
    corroboration_engine = CorroborationEngine()             
    llama_client = get_llama_client()
    sentiment_analyzer = SentimentAnalyzer()

    # Créer l'analyseur batch
    batch_analyzer = create_batch_analyzer(
        sentiment_analyzer,
        corroboration_engine,
        bayesian_analyzer
    )
    
    # Stocker dans la config de l'app pour y accéder globalement
    app.config['BATCH_ANALYZER'] = batch_analyzer
    app.config['SENTIMENT_ANALYZER'] = sentiment_analyzer
    app.config['CORROBORATION_ENGINE'] = corroboration_engine
    app.config['BAYESIAN_ANALYZER'] = bayesian_analyzer
    
    # CORRECTION : Enregistrement SÉQUENTIEL des routes pour éviter les conflits
    
    # 1. D'abord les Blueprints (avec préfixes uniques)
    from .weak_indicators_routes import weak_indicators_bp
    from .alerts_system_routes import alerts_system_bp
    from .websdr_routes import websdr_bp  # Si vous avez ce fichier

    # CORRECTION : Utiliser des préfixes différents pour éviter les conflits
    app.register_blueprint(weak_indicators_bp, url_prefix='/weak-indicators')
    app.register_blueprint(alerts_system_bp, url_prefix='/alerts')
    # app.register_blueprint(websdr_bp, url_prefix='/websdr')  # Décommentez si nécessaire
    
    # 2. Ensuite les routes principales
    from .routes import register_routes
    from .routes_advanced import register_advanced_routes
    from .routes_social import register_social_routes
    from .routes_archiviste import register_archiviste_routes

    # Enregistrement des routes principales - PASSER LES ANALYZERS
    register_routes(app, db_manager, theme_manager, theme_analyzer, rss_manager, 
                   advanced_theme_manager, llama_client, sentiment_analyzer, batch_analyzer)
    
    register_advanced_routes(app, db_manager, bayesian_analyzer, corroboration_engine) 
    
    # 3. Enfin les routes spécialisées
    register_social_routes(app, db_manager)
    register_archiviste_routes(app, db_manager)

    # CORRECTION : Initialiser les tables SDR
    @app.before_request
    def initialize_on_first_request():
        """Initialisation au premier requête"""
        if not hasattr(app, 'initialized'):
            try:
                from .weak_indicators_routes import init_sdr_tables
                init_sdr_tables()
                print("✅ Tables SDR initialisées avec succès")
                
                # Initialisation des exports
                from .data_exporter import DataExporter
                from .config import DB_PATH
                exporter = DataExporter(DB_PATH)
                exporter.export_daily_analytics()
                print("✅ Export initial créé")
                
                app.initialized = True
                
            except Exception as e:
                print(f"❌ Erreur initialisation: {e}")
    
    print("✅ Toutes les routes enregistrées avec succès")
    
    # Afficher toutes les routes pour le débogage
    print("\n📋 Routes enregistrées:")
    for rule in app.url_map.iter_rules():
        print(f"  {rule.endpoint}: {rule.rule} [{', '.join(rule.methods)}]")

    return app