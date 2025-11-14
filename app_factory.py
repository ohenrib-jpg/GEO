# Flask/app_factory.py - CORRECTION
import os
import logging
from flask import Flask

logger = logging.getLogger(__name__)

def create_app():
    """Factory pour créer l'application Flask"""
    
    # CORRECTION: Obtenir le chemin absolu du répertoire Flask/ (où se trouve ce fichier)
    flask_dir = os.path.dirname(os.path.abspath(__file__))
    
    # CORRECTION: Le répertoire parent est le répertoire racine du projet
    base_dir = os.path.dirname(flask_dir)
    
    # CORRECTION: Les templates et static sont à la racine du projet
    template_dir = os.path.join(base_dir, 'templates')
    static_dir = os.path.join(base_dir, 'static')
    
    print(f"📂 Répertoire Flask: {flask_dir}")
    print(f"📂 Répertoire base: {base_dir}")
    print(f"📂 Dossier templates: {template_dir}")
    print(f"📂 Dossier static: {static_dir}")
    
    # Vérifier si les dossiers existent
    if not os.path.exists(template_dir):
        print(f"⚠️ ATTENTION: Le dossier templates n'existe pas: {template_dir}")
        os.makedirs(template_dir, exist_ok=True)
        print(f"✅ Création du dossier templates: {template_dir}")
    else:
        print(f"✅ Dossier templates trouvé: {template_dir}")
        # Lister les fichiers dans le dossier templates
        try:
            template_files = os.listdir(template_dir)
            print(f"📄 Fichiers templates trouvés: {template_files}")
        except Exception as e:
            print(f"❌ Erreur lors de la lecture du dossier templates: {e}")
    
    if not os.path.exists(static_dir):
        print(f"⚠️ ATTENTION: Le dossier static n'existe pas: {static_dir}")
        os.makedirs(static_dir, exist_ok=True)
        print(f"✅ Création du dossier static: {static_dir}")
    else:
        print(f"✅ Dossier static trouvé: {static_dir}")
    
    # Créer l'application Flask avec les chemins absolus
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
    
    db_manager = DatabaseManager()
    
    # Exécuter les migrations (une seule fois)
    run_migrations(db_manager)

    theme_manager = ThemeManager(db_manager)
    advanced_theme_manager = AdvancedThemeManager(db_manager)
    theme_analyzer = ThemeAnalyzer(db_manager)
    rss_manager = RSSManager(db_manager)
    bayesian_analyzer = BayesianSentimentAnalyzer()          
    corroboration_engine = CorroborationEngine()             
    llama_client = get_llama_client()
    
    # Enregistrement de TOUTES les routes
    from .routes import register_routes
    from .routes_advanced import register_advanced_routes
    from .routes_social import register_social_routes
    from .routes_archiviste import register_archiviste_routes
    from .weak_indicators_routes import weak_indicators_bp
    from .alerts_system_routes import alerts_system_bp

    # Enregistrement des routes principales
    register_routes(app, db_manager, theme_manager, theme_analyzer, rss_manager, advanced_theme_manager, llama_client)
    register_advanced_routes(app, db_manager, bayesian_analyzer, corroboration_engine) 
    
    # Enregistrement des nouvelles routes
    register_social_routes(app, db_manager)
    register_archiviste_routes(app, db_manager)
    
    # Enregistrement des Blueprints
    app.register_blueprint(weak_indicators_bp, url_prefix='/api')
    app.register_blueprint(alerts_system_bp, url_prefix='/api')
    
    # CORRECTION: Initialiser les tables SDR avec un contexte d'application
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
    
    # Afficher toutes les routes enregistrées pour le débogage
    print("\n📋 Routes enregistrées:")
    for rule in app.url_map.iter_rules():
        print(f"  {rule.endpoint}: {rule.rule} [{', '.join(rule.methods)}]")


    return app