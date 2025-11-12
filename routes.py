# Flask/routes.py
"""
Routes principales de l'application GEOPOL
"""

from flask import render_template, jsonify, request
import logging
from datetime import datetime, timedelta
from .database import DatabaseManager

logger = logging.getLogger(__name__)

def register_routes(app, db_manager, theme_manager, theme_analyzer, rss_manager, sentiment_analyzer, advanced_theme_manager):
    """
    Enregistre toutes les routes de l'application
    """
    
    # ============================================================
    # ROUTES PAGES PRINCIPALES
    # ============================================================

    @app.route('/')
    def index():
        """Page d'accueil"""
        return render_template('index.html')

    @app.route('/dashboard')
    def dashboard():
        """Page dashboard"""
        return render_template('dashboard.html')

    @app.route('/articles')
    def articles_page():
        """Page des articles"""
        return render_template('articles.html')

    @app.route('/themes')
    def themes_page():
        """Page des thèmes"""
        return render_template('themes.html')

    @app.route('/feeds')
    def feeds_page():
        """Page des flux RSS"""
        return render_template('feeds.html')

    @app.route('/settings')
    def settings_page():
        """Page des paramètres"""
        return render_template('settings.html')

    @app.route('/advanced-analysis')
    def advanced_analysis_page():
        """Page d'analyse avancée"""
        return render_template('advanced-analysis.html')

    @app.route('/archiviste')
    def archiviste_page():
        """Page de l'archiviste historique"""
        return render_template('archiviste.html')

    @app.route('/social')
    def social_page():
        """Page des réseaux sociaux"""
        return render_template('social.html')

    @app.route('/weak-indicators')
    def weak_indicators_page():
        """Page des indicateurs faibles"""
        return render_template('weak-indicators.html')

    # ============================================================
    # ROUTES API - STATISTIQUES GLOBALES
    # ============================================================

    @app.route('/api/stats')
    def get_global_stats():
        """Retourne les statistiques globales pour le dashboard"""
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            # Total articles
            cursor.execute("SELECT COUNT(*) FROM articles")
            total_articles = cursor.fetchone()[0]
            
            # Distribution des sentiments
            cursor.execute("""
                SELECT sentiment_type, COUNT(*) 
                FROM articles 
                WHERE sentiment_type IS NOT NULL 
                GROUP BY sentiment_type
            """)
            sentiment_dist = {}
            for row in cursor.fetchall():
                sentiment_dist[row[0]] = row[1]
            
            # Thèmes actifs
            cursor.execute("SELECT COUNT(DISTINCT theme_id) FROM theme_analyses")
            active_themes = cursor.fetchone()[0]
            
            conn.close()
            
            return jsonify({
                'total_articles': total_articles,
                'sentiment_distribution': sentiment_dist,
                'active_themes': active_themes,
                'theme_stats': {}
            })
            
        except Exception as e:
            logger.error(f"Erreur stats globales: {e}")
            return jsonify({
                'total_articles': 0,
                'sentiment_distribution': {},
                'active_themes': 0,
                'theme_stats': {}
            })

    @app.route('/api/sentiment')
    def get_sentiment_overview():
        """Vue d'ensemble des sentiments"""
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    AVG(sentiment_score) as avg_sentiment,
                    COUNT(*) as total_articles,
                    SUM(CASE WHEN sentiment_score > 0.1 THEN 1 ELSE 0 END) as positive,
                    SUM(CASE WHEN sentiment_score < -0.1 THEN 1 ELSE 0 END) as negative,
                    SUM(CASE WHEN sentiment_score BETWEEN -0.1 AND 0.1 THEN 1 ELSE 0 END) as neutral
                FROM articles
                WHERE sentiment_score IS NOT NULL
            """)
            
            row = cursor.fetchone()
            if row:
                total = row[1] or 1
                return jsonify({
                    'average': row[0] or 0,
                    'distribution': {
                        'positive': row[2] or 0,
                        'negative': row[3] or 0,
                        'neutral': row[4] or 0,
                        'positive_percent': round((row[2] or 0) / total * 100, 1),
                        'negative_percent': round((row[3] or 0) / total * 100, 1),
                        'neutral_percent': round((row[4] or 0) / total * 100, 1)
                    }
                })
            
            conn.close()
            return jsonify({'average': 0, 'distribution': {}})
            
        except Exception as e:
            logger.error(f"Erreur sentiment overview: {e}")
            return jsonify({'average': 0, 'distribution': {}})

    @app.route('/api/countries')
    def get_countries_list():
        """Liste des pays pour les indicateurs faibles"""
        default_countries = [
            {'code': 'FR', 'name': 'France'},
            {'code': 'US', 'name': 'United States'},
            {'code': 'CN', 'name': 'China'},
            {'code': 'DE', 'name': 'Germany'},
            {'code': 'GB', 'name': 'United Kingdom'},
            {'code': 'JP', 'name': 'Japan'},
            {'code': 'RU', 'name': 'Russia'}
        ]
        return jsonify(default_countries)

    # ============================================================
    # ROUTES API - THÈMES ET ARTICLES (EXISTANT)
    # ============================================================

    @app.route('/api/themes/statistics')
    def get_themes_statistics():
        """Retourne les statistiques des thèmes"""
        try:
            stats = theme_analyzer.get_theme_statistics()
            return jsonify(stats)
        except Exception as e:
            logger.error(f"Erreur statistiques thèmes: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/articles')
    def get_articles():
        """Retourne les articles avec pagination"""
        try:
            limit = int(request.args.get('limit', 50))
            offset = int(request.args.get('offset', 0))
            
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, title, content, link, pub_date, sentiment_score, sentiment_type
                FROM articles 
                ORDER BY pub_date DESC 
                LIMIT ? OFFSET ?
            """, (limit, offset))
            
            articles = []
            for row in cursor.fetchall():
                articles.append({
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'link': row[3],
                    'pub_date': row[4],
                    'sentiment_score': row[5],
                    'sentiment_type': row[6]
                })
            
            conn.close()
            return jsonify({'articles': articles})
            
        except Exception as e:
            logger.error(f"Erreur récupération articles: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/articles/recent')
    def get_recent_articles():
        """Retourne les articles récents"""
        try:
            limit = int(request.args.get('limit', 10))
            
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, title, content, link, pub_date, sentiment_score, sentiment_type
                FROM articles 
                ORDER BY pub_date DESC 
                LIMIT ?
            """, (limit,))
            
            articles = []
            for row in cursor.fetchall():
                articles.append({
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'link': row[3],
                    'pub_date': row[4],
                    'sentiment_score': row[5],
                    'sentiment_type': row[6]
                })
            
            conn.close()
            return jsonify({'articles': articles})
            
        except Exception as e:
            logger.error(f"Erreur récupération articles récents: {e}")
            return jsonify({'error': str(e)}), 500

    # ============================================================
    # ROUTES API - GESTION DES THÈMES (EXISTANT)
    # ============================================================

    @app.route('/api/themes', methods=['GET'])
    def get_themes():
        """Retourne la liste des thèmes"""
        try:
            themes = theme_manager.get_themes()
            return jsonify(themes)
        except Exception as e:
            logger.error(f"Erreur récupération thèmes: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/themes', methods=['POST'])
    def create_theme():
        """Crée un nouveau thème"""
        try:
            data = request.get_json()
            theme_id = theme_manager.create_theme(
                name=data['name'],
                keywords=data['keywords'],
                description=data.get('description', ''),
                color=data.get('color', '#3B82F6')
            )
            return jsonify({'success': True, 'theme_id': theme_id})
        except Exception as e:
            logger.error(f"Erreur création thème: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/themes/<theme_id>', methods=['DELETE'])
    def delete_theme(theme_id):
        """Supprime un thème"""
        try:
            success = theme_manager.delete_theme(theme_id)
            return jsonify({'success': success})
        except Exception as e:
            logger.error(f"Erreur suppression thème: {e}")
            return jsonify({'error': str(e)}), 500

    # ============================================================
    # ROUTES API - FLUX RSS (EXISTANT)
    # ============================================================

    @app.route('/api/feeds/update', methods=['POST'])
    def update_feeds():
        """Met à jour tous les flux RSS"""
        try:
            data = request.get_json() or {}
            feed_urls = data.get('feed_urls', [])
            
            if not feed_urls:
                # Récupérer les flux de la base
                conn = db_manager.get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT url FROM feeds WHERE active = 1")
                feed_urls = [row[0] for row in cursor.fetchall()]
                conn.close()
            
            results = rss_manager.update_all_feeds(feed_urls)
            return jsonify(results)
            
        except Exception as e:
            logger.error(f"Erreur mise à jour flux: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/feeds/scrape', methods=['POST'])
    def scrape_feeds():
        """Analyse des flux RSS fournis"""
        try:
            data = request.get_json()
            feed_urls = data.get('feed_urls', [])
            
            if not feed_urls:
                return jsonify({'error': 'Aucun flux fourni'}), 400
            
            # Séparer les URLs par lignes si nécessaire
            if isinstance(feed_urls, str):
                feed_urls = [url.strip() for url in feed_urls.split('\n') if url.strip()]
            
            results = rss_manager.update_all_feeds(feed_urls)
            return jsonify(results)
            
        except Exception as e:
            logger.error(f"Erreur scraping flux: {e}")
            return jsonify({'error': str(e)}), 500

    # ============================================================
    # ROUTES API - RÉANALYSE (EXISTANT)
    # ============================================================

    @app.route('/api/reanalyze-articles', methods=['POST'])
    def reanalyze_articles():
        """Ré-analyse tous les articles avec les thèmes actuels"""
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            # Compter les articles
            cursor.execute("SELECT COUNT(*) FROM articles")
            total_articles = cursor.fetchone()[0]
            
            # Ré-analyser
            cursor.execute("SELECT id, title, content FROM articles")
            articles = cursor.fetchall()
            
            analyzed_count = 0
            themes_detected = 0
            
            for article in articles:
                article_id, title, content = article
                themes = theme_analyzer.analyze_article_themes(title + " " + (content or ""))
                
                if themes:
                    themes_detected += len(themes)
                    analyzed_count += 1
                    
                    # Sauvegarder l'analyse
                    for theme_id, confidence in themes:
                        cursor.execute("""
                            INSERT OR REPLACE INTO theme_analyses (article_id, theme_id, confidence)
                            VALUES (?, ?, ?)
                        """, (article_id, theme_id, confidence))
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'results': {
                    'total_articles': total_articles,
                    'analyzed_articles': analyzed_count,
                    'themes_detected': themes_detected
                }
            })
            
        except Exception as e:
            logger.error(f"Erreur ré-analyse: {e}")
            return jsonify({'error': str(e)}), 500

    # ============================================================
    # ROUTES API - INDICATEURS FAIBLES
    # ============================================================

    @app.route('/api/weak-indicators/countries')
    def get_monitored_countries():
        """Retourne la liste des pays surveillés"""
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT country_code, country_name FROM monitored_countries')
            countries = [{'code': row[0], 'name': row[1]} for row in cursor.fetchall()]
            
            conn.close()
            return jsonify(countries)
        except:
            # Retourner une liste par défaut
            default_countries = [
                {'code': 'FR', 'name': 'France'},
                {'code': 'US', 'name': 'United States'},
                {'code': 'CN', 'name': 'China'},
                {'code': 'DE', 'name': 'Germany'},
                {'code': 'GB', 'name': 'United Kingdom'},
                {'code': 'JP', 'name': 'Japan'},
                {'code': 'RU', 'name': 'Russia'}
            ]
            return jsonify(default_countries)

    @app.route('/api/weak-indicators/status')
    def get_weak_indicators_status():
        """Statut global des indicateurs faibles"""
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            # Compter les pays surveillés
            cursor.execute('SELECT COUNT(*) FROM monitored_countries')
            monitored_countries = cursor.fetchone()[0]
            
            # Compter les alertes actives
            cursor.execute('SELECT COUNT(*) FROM weak_indicator_alerts WHERE active = 1')
            active_alerts = cursor.fetchone()[0]
            
            # Compter les flux SDR actifs
            cursor.execute('SELECT COUNT(*) FROM sdr_streams WHERE active = 1')
            active_sdr_streams = cursor.fetchone()[0]
            
            conn.close()
            
            return jsonify({
                'monitored_countries': monitored_countries,
                'active_alerts': active_alerts,
                'active_sdr_streams': active_sdr_streams
            })
            
        except Exception as e:
            logger.error(f"Erreur statut indicateurs faibles: {e}")
            return jsonify({
                'monitored_countries': 7,
                'active_alerts': 0,
                'active_sdr_streams': 0
            })

    @app.route('/api/travel-advice/<country>')
    def get_travel_advice(country):
        """Récupère les conseils aux voyageurs pour un pays"""
        # Implémentation de la récupération des données
        # Soit via l'API publique, soit via web scraping
        return jsonify({
            'country': country,
            'status': 'normal',  # À implémenter
            'last_update': datetime.now().isoformat(),
            'details': {}
        })

    @app.route('/api/sdr-streams', methods=['GET', 'POST'])
    def manage_sdr_streams():
        """Gestion des flux SDR"""
        if request.method == 'GET':
            # Retourner les flux sauvegardés
            return jsonify([])
        else:
            # Sauvegarder un nouveau flux
            data = request.json
            return jsonify({'status': 'success'})

    @app.route('/api/economic-data/<country>/<indicator>')
    def get_economic_data(country, indicator):
        """Récupère les données économiques"""
        # Intégration avec yFinance ou autre source
        return jsonify({
            'country': country,
            'indicator': indicator,
            'data': [],
            'current': 0,
            'trend': 'stable'
        })

    logger.info("✅ Routes principales enregistrées")

    # Retourner l'app pour le chaînage
    return app