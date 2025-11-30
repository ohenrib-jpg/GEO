# Flask/app_factory.py - VERSION CORRIGÉE AVEC SDR AUTOMATIQUE

import sys
import os
from dotenv import load_dotenv
import logging
from flask import Flask, jsonify, request
import signal
import psutil
import time
import threading

load_dotenv()
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
    db_manager = DatabaseManager()
    
    # Exécuter les migrations
    from .database_migrations import run_migrations
    run_migrations(db_manager)

    # ============================================================
    # INITIALISATION SYSTÈME SDR AUTOMATIQUE
    # ============================================================
    print("\n📡 Initialisation Système SDR Automatique...")
    
    try:
        # Import du système d'analyse automatique
        from .sdr_spectrum_analyzer import SpectrumAnalyzer, AutomatedSDRMonitor
        
        # Initialisation des analyseurs
        sdr_spectrum_analyzer = SpectrumAnalyzer(db_manager)
        sdr_auto_monitor = AutomatedSDRMonitor(db_manager)
        
        # Stockage dans la config de l'app
        app.config['SDR_SPECTRUM_ANALYZER'] = sdr_spectrum_analyzer
        app.config['SDR_AUTO_MONITOR'] = sdr_auto_monitor
        
        print("✅ Système SDR automatique initialisé:")
        print("   • SpectrumAnalyzer (détection automatique des émissions)")
        print("   • AutomatedSDRMonitor (surveillance continue)")
        
    except ImportError as e:
        print(f"❌ Erreur import système SDR automatique: {e}")
        print("💡 Installation requise: pip install scipy numpy")
    except Exception as e:
        print(f"❌ Erreur initialisation SDR automatique: {e}")
        import traceback
        traceback.print_exc()

    # ============================================================
    # INITIALISATION INDICATEURS FAIBLES AVEC SDR AUTOMATIQUE
    # ============================================================
    print("\n📡 Initialisation Indicateurs Faibles avec SDR Automatique...")
    try:
        # Import LOCAL pour éviter conflit
        from Flask.init_weak_indicators_db import (
            init_weak_indicators_database, 
            populate_initial_data
        )
        
        # Initialiser les tables
        init_success = init_weak_indicators_database('instance/geopol.db')
        
        if init_success:
            print("✅ Tables indicateurs faibles créées")
            
            # Peupler avec données initiales
            populate_initial_data('instance/geopol.db')
            print("✅ Données initiales insérées")
        else:
            print("⚠️ Problème initialisation tables indicateurs faibles")
            
    except Exception as e:
        print(f"❌ Erreur init indicateurs faibles: {e}")
        import traceback
        traceback.print_exc()
    
    print()

    # ============================================================
    # INITIALISATION DES COMPOSANTS DE BASE
    # ============================================================
    
    # 1. Managers principaux
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
    from .continuous_learning import start_passive_learning, stop_passive_learning
    from .learning_routes import create_learning_blueprint
    
    # Initialisation des managers de base
    theme_manager = ThemeManager(db_manager)
    advanced_theme_manager = AdvancedThemeManager(db_manager)
    theme_analyzer = ThemeAnalyzer(db_manager)
    rss_manager = RSSManager(db_manager)
    bayesian_analyzer = BayesianSentimentAnalyzer()          
    corroboration_engine = CorroborationEngine()             
    llama_client = get_llama_client()
    sentiment_analyzer = SentimentAnalyzer()
    
    print("✅ Managers principaux initialisés")

    # ============================================================
    # INITIALISATION GEO NARRATIVE ANALYZER
    # ============================================================
    try:
        from .geo_narrative_analyzer import GeoNarrativeAnalyzer
        geo_narrative_analyzer = GeoNarrativeAnalyzer(db_manager)
        print("✅ GeoNarrativeAnalyzer initialisé avec succès")
    except ImportError as e:
        print(f"❌ GeoNarrativeAnalyzer non disponible: {e}")
        geo_narrative_analyzer = None

    # ============================================================
    # INITIALISATION MODULE ENTITÉS GÉOPOLITIQUES
    # ============================================================
    print("\n🌍 Initialisation du module Entités Géopolitiques...")
    
    entity_extractor = None
    entity_db_manager = None
    
    try:
        from .geopolitical_entity_extractor import GeopoliticalEntityExtractor
        from .entity_database_manager import EntityDatabaseManager
        from .entity_routes import register_entity_routes
        
        # Créer l'extracteur d'entités
        entity_extractor = GeopoliticalEntityExtractor(model_name="fr_core_news_lg")
        print("✅ Extracteur d'entités SpaCy initialisé")
        
        # Créer le gestionnaire de base de données d'entités
        entity_db_manager = EntityDatabaseManager(db_manager)
        print("✅ Gestionnaire BDD entités initialisé")
        
        # Enregistrer les routes
        register_entity_routes(app, db_manager, entity_extractor, entity_db_manager)
        print("✅ Routes API entités enregistrées")
        
        # Stocker dans la config de l'app
        app.config['ENTITY_EXTRACTOR'] = entity_extractor
        app.config['ENTITY_DB_MANAGER'] = entity_db_manager
        
        print("🎉 Module Entités Géopolitiques prêt !")
        
    except ImportError as e:
        print(f"⚠️ Module entités non disponible: {e}")
        print("💡 Installation requise: pip install spacy")
        print("💡 Modèle requis: python -m spacy download fr_core_news_lg")
    except Exception as e:
        print(f"❌ Erreur initialisation entités: {e}")
        import traceback
        traceback.print_exc()
    
    print()

    # ============================================================
    # ROUTES SDR AVEC ANALYSE AUTOMATIQUE
    # ============================================================
    print("\n📡 Enregistrement des Routes SDR avec Analyse Automatique...")
    
    try:
        # Routes KiwiSDR avec analyse automatique
        from .kiwisdr_routes import register_kiwisdr_routes
        register_kiwisdr_routes(app, db_manager)
        print("✅ Routes KiwiSDR avec analyse automatique enregistrées")
        
        # Routes SDR unifiées
        from .sdr_unified_routes import register_unified_sdr_routes
        register_unified_sdr_routes(app, db_manager)
        print("✅ Routes SDR unifiées enregistrées")
        
        # Routes surveillance SDR
        from .sdr_surveillance_system import create_sdr_surveillance_routes
        create_sdr_surveillance_routes(app, db_manager)
        print("✅ Routes surveillance SDR enregistrées")
        
    except ImportError as e:
        print(f"❌ Erreur import routes SDR: {e}")
    except Exception as e:
        print(f"❌ Erreur enregistrement routes SDR: {e}")
        import traceback
        traceback.print_exc()

    # ============================================================
    # ROUTES INDICATEURS FAIBLES INTÉGRÉES
    # ============================================================
    try:
        from .weak_indicators_routes_integration import register_integrated_routes
        register_integrated_routes(app, db_manager)
        print("✅ Routes indicateurs faibles intégrées enregistrées")
    except Exception as e:
        print(f"❌ Erreur routes indicateurs faibles: {e}")

    # ============================================================
    # INTÉGRATION GÉO-NARRATIVE + ENTITÉS
    # ============================================================
    print("\n🔗 Initialisation Intégration Geo-Narrative + Entités...")

    geo_entity_integration = None

    try:
        # Vérifier que tous les composants sont disponibles
        if geo_narrative_analyzer and entity_extractor and entity_db_manager:
            from .geo_entity_integration import GeoEntityIntegration
            
            # Créer l'intégrateur
            geo_entity_integration = GeoEntityIntegration(
                geo_narrative_analyzer=geo_narrative_analyzer,
                entity_extractor=entity_extractor,
                entity_db_manager=entity_db_manager
            )
        
            # Stocker dans la config de l'app
            app.config['GEO_ENTITY_INTEGRATION'] = geo_entity_integration
        
            print("✅ GeoEntityIntegration initialisé avec succès")
            print("   🔄 Composants connectés:")
            print("      • GeoNarrativeAnalyzer")
            print("      • GeopoliticalEntityExtractor") 
            print("      • EntityDatabaseManager")
        
        else:
            print("⚠️ Composants manquants pour l'intégration:")
            if not geo_narrative_analyzer:
                print("   ❌ GeoNarrativeAnalyzer non disponible")
            if not entity_extractor:
                print("   ❌ GeopoliticalEntityExtractor non disponible")
            if not entity_db_manager:
                print("   ❌ EntityDatabaseManager non disponible")
        
    except Exception as e:
        print(f"❌ Erreur initialisation intégration: {e}")
        import traceback
        traceback.print_exc()
    
    print()

    # ============================================================
    # CRÉATION DE L'ANALYSEUR BATCH
    # ============================================================
    batch_analyzer = create_batch_analyzer(
        sentiment_analyzer,
        corroboration_engine,
        bayesian_analyzer
    )
    
    # Stocker dans la config de l'app
    app.config['BATCH_ANALYZER'] = batch_analyzer
    app.config['SENTIMENT_ANALYZER'] = sentiment_analyzer
    app.config['CORROBORATION_ENGINE'] = corroboration_engine
    app.config['BAYESIAN_ANALYZER'] = bayesian_analyzer
    app.config['GEO_NARRATIVE_ANALYZER'] = geo_narrative_analyzer

    # ============================================================
    # ROUTES INTÉGRÉES GÉO-ENTITY
    # ============================================================
    try:
        if geo_entity_integration is not None:
            from .routes_geo_entity_integrated import register_integrated_routes
            
            register_integrated_routes(
                app=app,
                db_manager=db_manager,
                geo_narrative_analyzer=geo_narrative_analyzer,
                entity_extractor=entity_extractor,
                entity_db_manager=entity_db_manager,
                geo_entity_integration=geo_entity_integration
            )
            print("✅ Routes intégrées Geo-Entity enregistrées")
            
            # Afficher les routes disponibles
            print("📍 Routes intégrées:")
            for rule in app.url_map.iter_rules():
                if 'geo-entity' in rule.rule:
                    methods = ', '.join(m for m in rule.methods if m not in ['HEAD', 'OPTIONS'])
                    print(f"  • {rule.rule:55} [{methods}]")
        else:
            print("⚠️ GeoEntityIntegration non disponible, routes intégrées non enregistrées")
        
    except Exception as e:
        print(f"❌ Erreur enregistrement routes intégrées: {e}")
        import traceback
        traceback.print_exc()

    # ============================================================
    # ARCHIVISTE COMPARATIF
    # ============================================================
    print("\n🔄 Initialisation Archiviste Comparatif...")
    
    try:
        # Importer le module comparatif
        from .archiviste_comparative import ComparativeArchiviste
        from .routes_archiviste import create_archiviste_blueprint
        
        # Créer l'instance avec le sentiment_analyzer
        comparative_archiviste = ComparativeArchiviste(
            db_manager=db_manager,
            sentiment_analyzer=sentiment_analyzer
        )
        
        # Enregistrer le blueprint
        archiviste_bp = create_archiviste_blueprint(
            db_manager=db_manager,
            comparative_archiviste=comparative_archiviste
        )
        app.register_blueprint(archiviste_bp)
        
        print("✅ Archiviste Comparatif initialisé avec succès")
        print("📊 Routes Archiviste:")
        for rule in app.url_map.iter_rules():
            if 'archiviste' in rule.rule:
                print(f"  • {rule.rule} [{', '.join(rule.methods)}]")
        
    except ImportError as e:
        print(f"⚠️ Module archiviste_comparative non trouvé: {e}")
        print("   → Utilisation du module archiviste_enhanced (legacy)")
        
        # Fallback sur l'ancien module
        try:
            from .archiviste_enhanced import EnhancedArchiviste
            archiviste = EnhancedArchiviste(db_manager)
            
            from .routes_archiviste import create_archiviste_blueprint
            archiviste_bp = create_archiviste_blueprint(db_manager, archiviste)
            app.register_blueprint(archiviste_bp)
            
            print("✅ Archiviste Enhanced (legacy) initialisé")
            
        except Exception as e2:
            print(f"❌ Erreur initialisation Archiviste legacy: {e2}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Erreur initialisation Archiviste Comparatif: {e}")
        import traceback
        traceback.print_exc()
    
    print()

    # ============================================================
    # ASSISTANT IA MISTRAL
    # ============================================================
    try:
        from .assistant_routes import create_assistant_blueprint
        assistant_bp = create_assistant_blueprint(db_manager)
        app.register_blueprint(assistant_bp)
        print("✅ Routes Assistant IA avec accès aux données ajoutées")
    except Exception as e:
        print(f"❌ Erreur routes assistant: {e}")

    # ============================================================
    # ENREGISTREMENT DES ROUTES PRINCIPALES
    # ============================================================
    from .routes import register_routes
    from .routes_advanced import register_advanced_routes
    from .routes_social import register_social_routes
    from .kiwisdr_schema_fix import fix_kiwisdr_schema

    # Fixer le schéma KiwiSDR
    fix_kiwisdr_schema(db_manager)

    # Enregistrement des routes
    register_routes(app, db_manager, theme_manager, theme_analyzer, rss_manager, 
                   advanced_theme_manager, llama_client, sentiment_analyzer, batch_analyzer)
    
    register_advanced_routes(app, db_manager, bayesian_analyzer, corroboration_engine) 
    register_social_routes(app, db_manager)
    register_alerts_routes(app, db_manager)
    
    print("✅ Routes principales enregistrées")
    
    # ============================================================
    # ROUTES STOCK (si disponibles)
    # ============================================================
    try:
        from .stock_routes import register_stock_routes
        register_stock_routes(app, db_manager)
        print("✅ Routes Stock enregistrées")
    except ImportError as e:
        print(f"ℹ️ Routes Stock non disponibles: {e}")
    except Exception as e:
        print(f"❌ Erreur routes stock: {e}")

    # ============================================================
    # INITIALISATION DES DONNÉES RÉELLES
    # ============================================================
    try:
        from .real_sdr_manager import RealSDRManager
        from .real_travel_advisories import RealTravelAdvisories       
    
        # Initialiser avec des données réelles au démarrage
        if db_manager:
            try:
                sdr_manager = RealSDRManager(db_manager)
                sdr_manager.update_sdr_streams_from_reality()
                print("✅ Données SDR réelles initialisées")
            except Exception as e:
                print(f"⚠️ Erreur initialisation SDR réels: {e}")
    
        print("✅ Modules données réelles disponibles")
    except ImportError as e:
        print(f"ℹ️ Modules données réelles non disponibles: {e}")

    # ============================================================
    # VÉRIFICATION ET CORRECTION BASE DE DONNÉES ARCHIVISTE
    # ============================================================
    try:
        from .archiviste_db_fix import fix_archiviste_database, get_database_status
        
        print("\n🔍 Vérification base de données Archiviste...")
        status = get_database_status()
        
        if status['issues'] or not all(status['archiviste_tables'].values()):
            print("🔧 Correction nécessaire de la base de données...")
            fix_archiviste_database()
            print("✅ Base de données Archiviste corrigée")
        else:
            print("✅ Base de données Archiviste OK")
        
        # Afficher le statut
        status = get_database_status()
        print(f"📊 Archiviste - Thèmes: {status['theme_count']}, "
              f"Tables: {len([t for t in status['archiviste_tables'].values() if t])}/3, "
              f"Items: {status.get('archiviste_items_count', 0)}")
        
    except Exception as e:
        print(f"⚠️ Vérification base de données Archiviste échouée: {e}")

    # ============================================================
    # ROUTES GÉO-NARRATIVE
    # ============================================================
    try:
        from .routes_geo_narrative import register_geo_narrative_routes
        
        if geo_narrative_analyzer:
            register_geo_narrative_routes(app, db_manager, geo_narrative_analyzer)
            print("✅ Routes Géo-Narrative enregistrées")
        
            # Afficher les routes disponibles
            print("📍 Routes geo-narrative:")
            for rule in app.url_map.iter_rules():
                if 'geo-narrative' in rule.rule:
                    methods = ', '.join(m for m in rule.methods if m not in ['HEAD', 'OPTIONS'])
                    print(f"  • {rule.rule:50} [{methods}]")
        else:
            print("⚠️ GeoNarrativeAnalyzer non disponible, routes non enregistrées")
    except Exception as e:
        print(f"❌ Erreur enregistrement routes géo-narrative: {e}")
        import traceback
        traceback.print_exc()

    # ============================================================
    # AFFICHAGE DES ROUTES (DEBUG)
    # ============================================================
    print("\n📋 Routes enregistrées importantes:")
    important_prefixes = ['api', 'weak-indicators', 'alerts', 'sdr', 'archiviste', 'kiwisdr']
    for rule in app.url_map.iter_rules():
        if any(prefix in rule.rule for prefix in important_prefixes):
            methods = ', '.join(m for m in rule.methods if m not in ['HEAD', 'OPTIONS'])
            print(f"  • {rule.endpoint:40} {rule.rule:50} [{methods}]")

    # ============================================================
    # INITIALISATION AVIS AUX VOYAGEURS
    # ============================================================
    try:
        from .travel_advisories_manager import TravelAdvisoriesManager
        # L'initialisation se fera automatiquement via les routes
        print("✅ Module Avis aux Voyageurs disponible")
    except ImportError as e:
        print(f"ℹ️ Module Avis aux Voyageurs non disponible: {e}")

    # ============================================================
    # INITIALISATION APPRENTISSAGE CONTINU
    # ============================================================
    print("\n🧠 Initialisation Apprentissage Continu...")
    try:
        learning_engine = start_passive_learning(db_manager, sentiment_analyzer)
        app.config['LEARNING_ENGINE'] = learning_engine
        print("✅ Apprentissage continu démarré")
    
        # Enregistrer le blueprint
        learning_bp = create_learning_blueprint(db_manager)
        app.register_blueprint(learning_bp)
        print("✅ Routes apprentissage enregistrées")
    
    except Exception as e:
        print(f"❌ Erreur initialisation apprentissage: {e}")
        import traceback
        traceback.print_exc()

    # ============================================================
    # DASHBOARD INDICATEURS ÉCONOMIQUES
    # ============================================================
    print("\n📊 Initialisation Dashboard Indicateurs Économiques Amélioré...")
    try:
        from .routes_indicators_enhanced import create_indicators_blueprint_enhanced
        
        # Créer et enregistrer le blueprint
        indicators_bp = create_indicators_blueprint_enhanced(db_manager)
        app.register_blueprint(indicators_bp)
        
        print("✅ Dashboard Indicateurs Amélioré enregistré")
        print("   📍 URL principale : /indicators/")
        print("   📡 Sources de données :")
        print("      • 🇪🇺 Eurostat (API officielle)")
        print("      • 🇫🇷 INSEE (scraping page d'accueil)")
        print("      • 📈 yFinance (marchés financiers)")
        print("   🎓 Usage : Éducation & Recherche")
        
        # Afficher les endpoints disponibles
        print("   🔗 Endpoints principaux :")
        print("      • GET  /indicators/               → Page dashboard")
        print("      • GET  /indicators/api/dashboard  → Toutes les données")
        print("      • GET  /indicators/api/status     → Statut système")
        print("      • POST /indicators/api/refresh    → Rafraîchir données")
        
    except ImportError as e:
        print(f"❌ Erreur import dashboard indicateurs : {e}")
        print("💡 Vérifiez que les fichiers suivants existent :")
        print("   • Flask/routes_indicators_enhanced.py")
        print("   • Flask/enhanced_indicators_connector.py")
        print("   • Flask/insee_scraper.py")
        print("   • Flask/eurostat_connector.py")
        print("   • Flask/yfinance_connector.py")
        
    except Exception as e:
        print(f"❌ Erreur dashboard indicateurs : {e}")
        import traceback

    # ============================================================
    # INITIALISATION FINALE
    # ============================================================
    try:
        print("\n🔄 Initialisation finale du serveur...")

        # Initialisation SDR (configuration des flux)
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

        print("\n🎉 Application Flask initialisée avec succès!")
        print("="*70)
        print("📡 SYSTÈME SDR AUTOMATIQUE ACTIF")
        print("   • Détection automatique des émissions radio")
        print("   • Surveillance continue des fréquences géopolitiques")
        print("   • Analyse spectrale en temps réel")
        print("="*70)

    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation finale: {e}")
        print("⚠️ L'application démarre malgré l'erreur d'initialisation")

    # ============================================================
    # ROUTES DE GESTION DU SYSTÈME
    # ============================================================
    
    @app.route('/api/shutdown', methods=['POST'])
    def shutdown():
        """Endpoint pour arrêter proprement tous les services GEOPOL"""
        try:
            print("\n🔴 Demande d'arrêt propre reçue...")
            services_stopped = []
            
            # Arrêter l'apprentissage passif
            try:
                stop_passive_learning()
                services_stopped.append("Apprentissage Continu")
                print("  ✅ Apprentissage continu arrêté")
            except Exception as e:
                print(f"  ⚠️ Erreur arrêt apprentissage: {e}")
            
            def shutdown_services():
                time.sleep(0.5)
                
                try:
                    # Arrêter le serveur Llama (Mistral)
                    print("  → Recherche du serveur Mistral...")
                    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                        try:
                            if 'llama-server.exe' in proc.info['name'].lower():
                                print(f"  → Arrêt du serveur IA (PID: {proc.info['pid']})")
                                proc.terminate()
                                services_stopped.append("Serveur IA Mistral")
                                
                                try:
                                    proc.wait(timeout=5)
                                    print("  ✅ Serveur IA arrêté proprement")
                                except psutil.TimeoutExpired:
                                    print("  ⚠️ Forçage de l'arrêt...")
                                    proc.kill()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
                    
                    # Arrêter Flask
                    print("  → Arrêt du serveur Flask...")
                    services_stopped.append("Serveur Flask")
                    os.kill(os.getpid(), signal.SIGTERM)
                    
                except Exception as e:
                    print(f"  ❌ Erreur lors de l'arrêt: {e}")
            
            shutdown_thread = threading.Thread(target=shutdown_services, daemon=True)
            shutdown_thread.start()
            
            return jsonify({
                'status': 'success',
                'message': 'Arrêt en cours...',
                'services_stopped': services_stopped
            }), 200
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/health', methods=['GET'])
    def health():
        """Endpoint de santé pour vérifier que le serveur est actif"""
        return jsonify({
            'status': 'ok',
            'services': {
                'flask': 'running',
                'database': 'ok',
                'archiviste': 'ok' if 'archiviste' in str(app.url_map) else 'disabled',
                'sdr_auto': 'active' if app.config.get('SDR_SPECTRUM_ANALYZER') else 'disabled'
            }
        }), 200

    # ============================================================
    # COMMANDES CLI - INDICATEURS ÉCONOMIQUES
    # ============================================================
    
    @app.cli.command('test-indicators')
    def test_indicators_command():
        '''Teste le système d'indicateurs économiques'''
        print("🧪 Test du système d'indicateurs économiques...\n")
        
        try:
            import sys
            import os
            
            # Ajouter le dossier Flask au path
            flask_dir = os.path.dirname(os.path.abspath(__file__))
            if flask_dir not in sys.path:
                sys.path.insert(0, flask_dir)
            
            from test_enhanced_system import run_all_tests
            success = run_all_tests()
            
            if success:
                print("\n✅ Tous les tests sont passés")
            else:
                print("\n⚠️ Certains tests ont échoué")
        
        except Exception as e:
            print(f"\n❌ Erreur lors des tests : {e}")
            import traceback
            traceback.print_exc()
    
    @app.cli.command('refresh-insee')
    def refresh_insee_command():
        '''Force le rafraîchissement des données INSEE'''
        print("🔄 Rafraîchissement forcé des données INSEE...\n")
        
        try:
            from .insee_scraper import INSEEScraper
            
            scraper = INSEEScraper()
            data = scraper.force_refresh()
            
            if data.get('success'):
                print("✅ Données INSEE rafraîchies")
                print(f"   Source : {data.get('source')}")
                print(f"   Indicateurs : {len(data.get('indicators', {}))}")
                
                for key, ind in data['indicators'].items():
                    print(f"   • {ind['name']} : {ind['value']} {ind['unit']}")
            else:
                print("⚠️ Échec du rafraîchissement")
        
        except Exception as e:
            print(f"❌ Erreur : {e}")
            import traceback
            traceback.print_exc()
    
    @app.cli.command('check-indicators-sources')
    def check_indicators_sources_command():
        '''Vérifie le statut de toutes les sources de données économiques'''
        print("🔍 Vérification des sources de données économiques...\n")
        
        try:
            from .enhanced_indicators_connector import EnhancedIndicatorsConnector
            
            connector = EnhancedIndicatorsConnector(db_manager)
            data = connector.get_dashboard_data()
            
            print("📡 Statut des sources :")
            for source, status in data['sources_status'].items():
                icon = '✅' if status == 'operational' else '❌'
                print(f"   {icon} {source:15} : {status}")
            
            print(f"\n📊 Qualité globale : {data['summary']['data_quality']}")
            print(f"📈 Total indicateurs : {data['summary']['total_indicators']}")
            
            print("\n🔍 Répartition par fiabilité :")
            for reliability, count in data['summary']['by_reliability'].items():
                icon = '🔵' if reliability == 'official' else '🟢' if reliability == 'scraped' else '🟡'
                print(f"   {icon} {reliability:10} : {count}")
            
            print("\n📋 Répartition par source :")
            for source, count in data['summary']['by_source'].items():
                print(f"   • {source:30} : {count}")
        
        except Exception as e:
            print(f"❌ Erreur : {e}")
            import traceback
            traceback.print_exc()

    # ============================================================
    # FONCTIONS EXPOSÉES GLOBALEMENT
    # ============================================================
    
    def get_geo_narrative_analyzer():
        return app.config.get('GEO_NARRATIVE_ANALYZER')
    
    app.get_geo_narrative_analyzer = get_geo_narrative_analyzer

    def get_geo_entity_integration():
        return app.config.get('GEO_ENTITY_INTEGRATION')

    app.get_geo_entity_integration = get_geo_entity_integration

    def get_entity_extractor():
        return app.config.get('ENTITY_EXTRACTOR')
    
    def get_entity_db_manager():
        return app.config.get('ENTITY_DB_MANAGER')
    
    app.get_entity_extractor = get_entity_extractor
    app.get_entity_db_manager = get_entity_db_manager

    # Fonctions SDR automatique
    def get_sdr_spectrum_analyzer():
        return app.config.get('SDR_SPECTRUM_ANALYZER')
    
    def get_sdr_auto_monitor():
        return app.config.get('SDR_AUTO_MONITOR')
    
    app.get_sdr_spectrum_analyzer = get_sdr_spectrum_analyzer
    app.get_sdr_auto_monitor = get_sdr_auto_monitor

    return app