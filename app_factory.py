# Flask/app_factory.py - VERSION CORRIGÉE
import sys
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
    db_manager = DatabaseManager()  # db_manager doit être créé avant d'être utilisé
    
    # Exécuter les migrations
    from .database_migrations import run_migrations
    run_migrations(db_manager)

    # ✅ AJOUT DU NOUVEL ANALYSEUR
    try:
        from .geo_narrative_analyzer import GeoNarrativeAnalyzer
        geo_narrative_analyzer = GeoNarrativeAnalyzer(db_manager)
        print("✅ GeoNarrativeAnalyzer initialisé avec succès")
    except ImportError as e:
        print(f"❌ GeoNarrativeAnalyzer non disponible: {e}")
        geo_narrative_analyzer = None

    # Création de tous les managers
    from .theme_manager import ThemeManager
    from .theme_manager_advanced import AdvancedThemeManager 
    from .theme_analyzer import ThemeAnalyzer
    from .rss_manager import RSSManager
    from .bayesian_analyzer import BayesianSentimentAnalyzer  
    from .corroboration_engine import CorroborationEngine     
    from .llama_client import get_llama_client
    from .sentiment_analyzer import SentimentAnalyzer
    from .batch_sentiment_analyzer import create_batch_analyzer
    from .alerts_routes import register_alerts_routes

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
    app.config['GEO_NARRATIVE_ANALYZER'] = geo_narrative_analyzer
    
    # CORRECTION : Enregistrement SÉQUENTIEL des routes pour éviter les conflits
    
    # 1. D'abord les Blueprints (avec préfixes uniques)
    from .weak_indicators_routes import weak_indicators_bp
    from .alerts_system_routes import alerts_system_bp
    
    # CORRECTION : Utiliser des préfixes différents pour éviter les conflits
    app.register_blueprint(weak_indicators_bp, url_prefix='/weak-indicators')  
    app.register_blueprint(alerts_system_bp, url_prefix='/alerts')  
    
    # 2. ✅ AJOUT DES NOUVELLES ROUTES SDR UNIFIÉES
    try:
        from .sdr_unified_routes import register_unified_sdr_routes
        register_unified_sdr_routes(app, db_manager)
        print("✅ Routes SDR unifiées enregistrées")
    except ImportError as e:
        print(f"❌ Routes SDR unifiées non disponibles: {e}")
    except Exception as e:
        print(f"❌ Erreur enregistrement routes SDR: {e}")
    
    # 3. Ensuite les routes principales
    from .routes import register_routes
    from .routes_advanced import register_advanced_routes
    from .routes_social import register_social_routes
    from .routes_archiviste import register_archiviste_routes
    from .kiwisdr_schema_fix import fix_kiwisdr_schema
    fix_kiwisdr_schema(db_manager)
    # Enregistrement des routes principales - PASSER LES ANALYZERS
    register_routes(app, db_manager, theme_manager, theme_analyzer, rss_manager, 
                   advanced_theme_manager, llama_client, sentiment_analyzer, batch_analyzer)
    
    register_advanced_routes(app, db_manager, bayesian_analyzer, corroboration_engine) 
    
    # 4. Routes spécialisées
    register_social_routes(app, db_manager)
    register_archiviste_routes(app, db_manager)
    fix_kiwisdr_schema(db_manager)
    register_alerts_routes(app, db_manager)

    # Routes KiwiSDR et Stock - VÉRIFIER LA DISPONIBILITÉ
    try:
        from .kiwisdr_routes import register_kiwisdr_routes
        register_kiwisdr_routes(app, db_manager)
        print("✅ Routes KiwiSDR enregistrées (compatibilité)")
    except ImportError as e:
        print(f"ℹ️ Routes KiwiSDR non disponibles: {e}")
    
    try:
        from .stock_routes import register_stock_routes
        register_stock_routes(app, db_manager)
        print("✅ Routes Stock enregistrées")
    except ImportError as e:
        print(f"ℹ️ Routes Stock non disponibles: {e}")

    # ✅ INITIALISATION DES INDICATEURS FAIBLES
    try:
        from .weak_indicators_routes import init_weak_indicators
        init_weak_indicators(db_manager)
        print("✅ Système indicateurs faibles initialisé")
    except Exception as e:
        print(f"❌ Erreur initialisation indicateurs faibles: {e}")

    # Afficher toutes les routes pour le débogage
    print("\n📋 Routes enregistrées:")
    for rule in app.url_map.iter_rules():
        if any(part in rule.rule for part in ['api', 'weak-indicators', 'alerts', 'sdr']):
            print(f"  {rule.endpoint}: {rule.rule} [{', '.join(rule.methods)}]")

    # === CORRECTION : INITIALISATION IMMÉDIATE ET SIMPLE ===
    try:
        print("🔄 Initialisation du serveur...")

        # Initialisation SDR
        from .weak_indicators_routes import init_weak_indicators_tables
        init_weak_indicators_tables(db_manager)
        print("✅ Tables indicateurs faibles initialisées")

        from .sdr_config import initialize_sdr_streams
        try:
             sdr_count = initialize_sdr_streams(db_manager)
             print(f"🎯 {sdr_count} flux SDR configurés")
        except Exception as e:
             print(f"⚠️ Erreur initialisation SDR: {e}")

        # Export initial
        from .data_exporter import DataExporter
        from .config import DB_PATH
        exporter = DataExporter(DB_PATH)
        exporter.export_daily_analytics()
        print("✅ Export initial créé")

        print("🎉 Application Flask initialisée avec succès!")

    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {e}")
        print("⚠️  L'application démarre malgré l'erreur d'initialisation")

    return app