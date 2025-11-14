# Flask/routes_archiviste.py
"""
Routes API pour l'archiviste - Analyse historique
"""

from flask import request, jsonify, render_template
import logging
from datetime import datetime, timedelta
from .database import DatabaseManager
from .archiviste import get_archiviste

logger = logging.getLogger(__name__)

def register_archiviste_routes(app, db_manager: DatabaseManager):
    """
    Enregistre les routes pour l'archiviste
    """
    archiviste = get_archiviste(db_manager)
    
    @app.route('/archiviste')
    def archiviste_page():
        """Page principale archiviste"""
        return render_template('archiviste.html')

    # ============================================================
    # ROUTES D'ANALYSE HISTORIQUE
    # ============================================================
    
    @app.route('/api/archiviste/analyze-period', methods=['POST'])
    def analyze_historical_period():
        """
        Analyse une période historique
        """
        try:
            data = request.get_json() or {}
            period_key = data.get('period_key')
            theme = data.get('theme')
            max_items = int(data.get('max_items', 50))
            
            if not period_key:
                return jsonify({
                    'success': False,
                    'error': 'Période requise'
                }), 400
            
            if period_key not in archiviste.historical_periods:
                return jsonify({
                    'success': False,
                    'error': f'Période inconnue: {period_key}',
                    'available_periods': list(archiviste.historical_periods.keys())
                }), 400
            
            result = archiviste.analyze_historical_period(period_key, theme, max_items)
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Erreur analyze period: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/archiviste/compare-eras', methods=['POST'])
    def compare_current_vs_historical():
        """
        Compare l'analyse actuelle avec les périodes historiques
        """
        try:
            data = request.get_json() or {}
            current_analysis = data.get('current_analysis')
            historical_periods = data.get('historical_periods', ['1990-2000', '2000-2010', '2010-2020', '2020-2025'])
            
            if not current_analysis:
                return jsonify({
                    'success': False,
                    'error': 'Analyse actuelle requise'
                }), 400
            
            result = archiviste.compare_current_vs_historical(current_analysis, historical_periods)
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Erreur compare eras: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/archiviste/periods', methods=['GET'])
    def get_historical_periods():
        """
        Récupère la liste des périodes historiques disponibles
        """
        try:
            return jsonify({
                'success': True,
                'periods': archiviste.historical_periods,
                'themes': list(archiviste.historical_themes.keys())
            })
            
        except Exception as e:
            logger.error(f"Erreur get periods: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/archiviste/search-archive', methods=['POST'])
    def search_archive_content():
        """
        Recherche dans les archives Archive.org
        """
        try:
            data = request.get_json() or {}
            query = data.get('query', '')
            collection = data.get('collection', 'newspapers')
            start_date = data.get('start_date')
            end_date = data.get('end_date')
            limit = int(data.get('limit', 20))
            
            items = archiviste.search_archive_collection(
                query=query,
                collection=collection,
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )
            
            return jsonify({
                'success': True,
                'items': items,
                'count': len(items)
            })
            
        except Exception as e:
            logger.error(f"Erreur search archive: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/archiviste/analyses-history', methods=['GET'])
    def get_historical_analyses():
        """
        Récupère l'historique des analyses
        """
        try:
            limit = int(request.args.get('limit', 10))
            
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT period_key, period_name, theme, total_items, avg_sentiment_score,
                       emotional_intensity, top_themes, created_at
                FROM historical_analyses
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            
            analyses = []
            for row in cursor.fetchall():
                analyses.append({
                    'period_key': row[0],
                    'period_name': row[1],
                    'theme': row[2],
                    'total_items': row[3],
                    'avg_sentiment_score': row[4],
                    'emotional_intensity': row[5],
                    'top_themes': row[6] if row[6] else '[]',
                    'created_at': row[7]
                })
            
            conn.close()
            
            return jsonify({
                'success': True,
                'analyses': analyses
            })
            
        except Exception as e:
            logger.error(f"Erreur get analyses history: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/archiviste/trends-evolution', methods=['GET'])
    def get_trends_evolution():
        """
        Récupère l'évolution des tendances sur plusieurs périodes
        """
        try:
            period_key = request.args.get('period_key')
            theme = request.args.get('theme')
            
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT period_key, period_name, theme, total_items, avg_sentiment_score,
                       emotional_intensity, created_at
                FROM historical_analyses
            """
            params = []
            
            conditions = []
            if period_key:
                conditions.append("period_key = ?")
                params.append(period_key)
            
            if theme:
                conditions.append("theme = ?")
                params.append(theme)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY created_at DESC"
            
            cursor.execute(query, params)
            
            trends = []
            for row in cursor.fetchall():
                trends.append({
                    'period_key': row[0],
                    'period_name': row[1],
                    'theme': row[2],
                    'total_items': row[3],
                    'avg_sentiment_score': row[4],
                    'emotional_intensity': row[5],
                    'created_at': row[6]
                })
            
            conn.close()
            
            return jsonify({
                'success': True,
                'trends': trends
            })
            
        except Exception as e:
            logger.error(f"Erreur get trends evolution: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/archiviste/current-analysis', methods=['POST'])
    def generate_current_analysis():
        """
        Génère l'analyse actuelle pour comparaison avec l'historique
        """
        try:
            data = request.get_json() or {}
            days = int(data.get('days', 30))  # Par défaut, dernière mois
            
            # Utiliser les données actuelles RSS
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Récupérer les articles RSS récents
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, title, content, sentiment_score, sentiment_type
                FROM articles
                WHERE pub_date >= ?
                ORDER BY pub_date DESC
                LIMIT 500
            """, (cutoff_date,))
            
            rss_articles = []
            for row in cursor.fetchall():
                rss_articles.append({
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'sentiment_score': row[3],
                    'sentiment_type': row[4]
                })
            
            # Calculer les statistiques actuelles
            if rss_articles:
                total_articles = len(rss_articles)
                avg_sentiment = sum(art['sentiment_score'] for art in rss_articles) / total_articles
                
                sentiment_dist = {'positive': 0, 'negative': 0, 'neutral': 0}
                for art in rss_articles:
                    sentiment_type = art['sentiment_type']
                    sentiment_dist[sentiment_type] = sentiment_dist.get(sentiment_type, 0) + 1
                
                current_analysis = {
                    'period': 'current',
                    'period_name': 'Actuel (30 derniers jours)',
                    'statistics': {
                        'total_items': total_articles,
                        'average_sentiment_score': round(avg_sentiment, 4),
                        'sentiment_distribution': {
                            'positive': sentiment_dist['positive'],
                            'negative': sentiment_dist['negative'],
                            'neutral': sentiment_dist['neutral'],
                            'positive_percent': round(sentiment_dist['positive'] / total_articles * 100, 1),
                            'negative_percent': round(sentiment_dist['negative'] / total_articles * 100, 1),
                            'neutral_percent': round(sentiment_dist['neutral'] / total_articles * 100, 1)
                        },
                        'emotional_intensity': archiviste._calculate_emotional_intensity(
                         sentiment_dist, avg_sentiment
                    )
                    },
                    'analysis_date': datetime.now().isoformat()
                }
                
                return jsonify({
                    'success': True,
                    'current_analysis': current_analysis
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Aucun article récent trouvé pour l\'analyse'
                })
            
        except Exception as e:
            logger.error(f"Erreur generate current analysis: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    logger.info("✅ Routes archiviste enregistrées")
