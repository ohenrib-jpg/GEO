from flask import Flask, render_template, request, jsonify, send_file, Response
from datetime import datetime, timedelta
import json
import logging
import csv
from io import StringIO, BytesIO
from xhtml2pdf import pisa
import tempfile
import sqlite3
import os
from .database import DatabaseManager
from .theme_manager import ThemeManager
from .theme_analyzer import ThemeAnalyzer
from .rss_manager import RSSManager
from .anomaly_detector import AnomalyDetector  # AJOUTER CET IMPORT

logger = logging.getLogger(__name__)

def register_routes(app: Flask, db_manager: DatabaseManager, theme_manager: ThemeManager,
                    theme_analyzer: ThemeAnalyzer, rss_manager: RSSManager, 
                    advanced_theme_manager=None, anomaly_detector=None):  # AJOUTER anomaly_detector
    # Si advanced_theme_manager n'est pas fourni, créer une instance
    if advanced_theme_manager is None:
        from .theme_manager_advanced import AdvancedThemeManager
        advanced_theme_manager = AdvancedThemeManager(db_manager)
    
    # Si anomaly_detector n'est pas fourni, créer une instance
    if anomaly_detector is None:
        anomaly_detector = AnomalyDetector(db_manager)


    @app.route('/')
    def index():
        """Page principale"""
        return render_template('index.html')

    @app.route('/dashboard')
    def dashboard():
        """Tableau de bord avec statistiques"""
        return render_template('dashboard.html')

    @app.route('/social')
    def social_page():
        """Page d'analyse des réseaux sociaux"""
        return render_template('social.html')

    @app.route('/archiviste')
    def archiviste_page():
        """Page d'analyse historique"""
        return render_template('archiviste.html')

    # API Routes - Thèmes
    @app.route('/api/themes', methods=['GET'])
    def get_themes():
        """Récupère tous les thèmes"""
        try:
            themes = theme_manager.get_all_themes()
            return jsonify({'themes': themes})
        except Exception as e:
            logger.error(f"Erreur récupération thèmes: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/themes', methods=['POST'])
    def create_theme():
        """Crée un nouveau thème"""
        try:
            data = request.get_json()
            theme_id = data.get('id')
            name = data.get('name')
            keywords = data.get('keywords', [])
            color = data.get('color', '#6366f1')
            description = data.get('description', '')

            if not theme_id or not name:
                return jsonify({'error': 'ID et nom requis'}), 400

            success = theme_manager.create_theme(theme_id, name, keywords, color, description)

            if success:
                return jsonify({'message': 'Thème créé avec succès'})
            else:
                return jsonify({'error': 'Erreur création thème'}), 500

        except Exception as e:
            logger.error(f"Erreur création thème: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/themes/<theme_id>', methods=['PUT'])
    def update_theme(theme_id):
        """Met à jour un thème"""
        try:
            data = request.get_json()
            success = theme_manager.update_theme(
                theme_id,
                name=data.get('name'),
                keywords=data.get('keywords'),
                color=data.get('color'),
                description=data.get('description')
            )

            if success:
                theme_analyzer.clear_cache()
                return jsonify({'message': 'Thème mis à jour avec succès'})
            else:
                return jsonify({'error': 'Thème non trouvé'}), 404

        except Exception as e:
            logger.error(f"Erreur mise à jour thème: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/themes/<theme_id>', methods=['DELETE'])
    def delete_theme(theme_id):
        """Supprime un thème"""
        try:
            success = theme_manager.delete_theme(theme_id)

            if success:
                return jsonify({'message': 'Thème supprimé avec succès'})
            else:
                return jsonify({'error': 'Erreur suppression thème'}), 500

        except Exception as e:
            logger.error(f"Erreur suppression thème: {e}")
            return jsonify({'error': str(e)}), 500

    # API Routes - Articles
    @app.route('/api/articles')
    def get_articles():
        """Récupère les articles avec filtres"""
        try:
            theme = request.args.get('theme')
            sentiment = request.args.get('sentiment')
            limit = int(request.args.get('limit', 50))
            offset = int(request.args.get('offset', 0))

            conn = db_manager.get_connection()
            cursor = conn.cursor()

            query = """
                SELECT a.id, a.title, a.content, a.link, a.pub_date, a.sentiment_type, a.sentiment_score
                FROM articles a
            """
            params = []

            if theme:
                query += """
                    JOIN theme_analyses ta ON a.id = ta.article_id
                    JOIN themes t ON ta.theme_id = t.id
                    WHERE t.id = ? AND ta.confidence >= 0.3
                """
                params.append(theme)
            else:
                query += " WHERE 1=1"

            if sentiment and sentiment != 'all':
                query += " AND a.sentiment_type = ?"
                params.append(sentiment)

            query += " ORDER BY a.pub_date DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)
            articles = []

            for row in cursor.fetchall():
                articles.append({
                    'id': row[0],
                    'title': row[1],
                    'content': row[2][:200] + '...' if row[2] and len(row[2]) > 200 else row[2],
                    'link': row[3],
                    'pub_date': row[4],
                    'sentiment': row[5],
                    'sentiment_score': row[6]
                })

            conn.close()
            return jsonify({'articles': articles})

        except Exception as e:
            logger.error(f"Erreur récupération articles: {e}")
            return jsonify({'error': str(e)}), 500

    # API Routes - Statistiques
    @app.route('/api/stats')
    def get_stats():
        """Récupère les statistiques pour le dashboard"""
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM articles")
            total_articles = cursor.fetchone()[0]

            cursor.execute("""
                SELECT sentiment_type, COUNT(*) 
                FROM articles 
                WHERE sentiment_type IS NOT NULL
                GROUP BY sentiment_type
            """)
            sentiment_stats = {row[0]: row[1] for row in cursor.fetchall()}

            sentiment_distribution = {
                'positive': sentiment_stats.get('positive', 0),
                'negative': sentiment_stats.get('negative', 0),
                'neutral': sentiment_stats.get('neutral', 0)
            }

            cursor.execute("""
                SELECT 
                    t.id, 
                    t.name, 
                    t.color,
                    COUNT(DISTINCT ta.article_id) as article_count
                FROM themes t
                LEFT JOIN theme_analyses ta ON t.id = ta.theme_id AND ta.confidence >= 0.3
                GROUP BY t.id, t.name, t.color
                ORDER BY article_count DESC
            """)

            theme_stats = {}
            for row in cursor.fetchall():
                theme_id, name, color, count = row
                theme_stats[theme_id] = {
                    'name': name,
                    'color': color,
                    'article_count': count
                }

            cursor.execute("""
                SELECT 
                    DATE(pub_date) as date,
                    sentiment_type,
                    COUNT(*) as count
                FROM articles
                WHERE pub_date >= DATE('now', '-7 days')
                GROUP BY DATE(pub_date), sentiment_type
                ORDER BY date
            """)

            timeline_data = {}
            for row in cursor.fetchall():
                date, sentiment, count = row
                if date not in timeline_data:
                    timeline_data[date] = {'date': date, 'positive': 0, 'negative': 0, 'neutral': 0}
                if sentiment:
                    timeline_data[date][sentiment] = count

            timeline = list(timeline_data.values())

            week_ago = datetime.now() - timedelta(days=7)
            cursor.execute("""
                SELECT COUNT(*) 
                FROM articles 
                WHERE pub_date >= ?
            """, (week_ago,))
            recent_articles = cursor.fetchone()[0]

            conn.close()

            logger.info(f"📊 Stats: {total_articles} articles, {len(theme_stats)} thèmes")

            return jsonify({
                'total_articles': total_articles,
                'sentiment_distribution': sentiment_distribution,
                'theme_stats': theme_stats,
                'recent_articles': recent_articles,
                'timeline_data': timeline
            })

        except Exception as e:
            logger.error(f"Erreur récupération stats: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500

    @app.route('/api/stats/timeline')
    def get_timeline():
        """Récupère les données de timeline sur les 30 derniers jours"""
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT 
                    DATE(pub_date) as date,
                    sentiment_type,
                    COUNT(*) as count
                FROM articles
                WHERE pub_date >= DATE('now', '-30 days')
                GROUP BY DATE(pub_date), sentiment_type
                ORDER BY date
            """)

            timeline_data = {}
            for row in cursor.fetchall():
                date, sentiment, count = row
                if date not in timeline_data:
                    timeline_data[date] = {'date': date, 'positive': 0, 'negative': 0, 'neutral': 0}
                if sentiment:
                    timeline_data[date][sentiment] = count

            timeline = list(timeline_data.values())
            conn.close()

            return jsonify({'timeline': timeline})

        except Exception as e:
            logger.error(f"Erreur récupération timeline: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/update-feeds', methods=['POST'])
    def update_feeds():
        """Met à jour les flux RSS"""
        try:
            data = request.get_json()
            feed_urls = data.get('feeds', [])

            if not feed_urls:
                return jsonify({'error': 'Aucun flux fourni'}), 400

            results = rss_manager.update_feeds(feed_urls)

            return jsonify({
                'message': 'Mise à jour terminée',
                'results': results
            })

        except Exception as e:
            logger.error(f"Erreur mise à jour flux: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/themes/<theme_id>/articles')
    def get_theme_articles(theme_id):
        """Récupère les articles pour un thème spécifique"""
        try:
            limit = int(request.args.get('limit', 50))
            articles = theme_analyzer.get_articles_by_theme(theme_id, limit)
            return jsonify({'articles': articles})
        except Exception as e:
            logger.error(f"Erreur récupération articles thème: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/test-feed')
    def test_feed():
        """Teste un flux RSS et retourne les informations"""
        try:
            feed_url = request.args.get('url')
            if not feed_url:
                return jsonify({'error': 'URL manquante'}), 400

            articles = rss_manager.parse_feed(feed_url)

            return jsonify({
                'success': True,
                'feed_url': feed_url,
                'articles_found': len(articles),
                'articles': articles[:3]
            })

        except Exception as e:
            url = request.args.get('url', 'URL inconnue')
            logger.error(f"Erreur test flux {url}: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/sources')
    def get_sources():
        """Récupère toutes les sources RSS uniques"""
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT DISTINCT feed_url 
                FROM articles 
                WHERE feed_url IS NOT NULL
                ORDER BY feed_url
            """)

            sources = [row[0] for row in cursor.fetchall()]
            conn.close()

            return jsonify({'sources': sources})

        except Exception as e:
            logger.error(f"Erreur récupération sources: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/articles/filter')
    def filter_articles():
        """Filtre les articles selon plusieurs critères"""
        try:
            theme = request.args.get('theme')
            sentiment = request.args.get('sentiment')
            source = request.args.get('source')
            date_from = request.args.get('date_from')
            date_to = request.args.get('date_to')
            search = request.args.get('search', '')
            limit = int(request.args.get('limit', 100))

            conn = db_manager.get_connection()
            cursor = conn.cursor()

            query = """
                SELECT DISTINCT a.id, a.title, a.content, a.link, a.pub_date, 
                       a.sentiment_type, a.sentiment_score, a.feed_url
                FROM articles a
            """

            joins = []
            conditions = []
            params = []

            if theme and theme != 'all':
                joins.append("""
                    LEFT JOIN theme_analyses ta ON a.id = ta.article_id
                """)
                conditions.append("ta.theme_id = ? AND ta.confidence >= 0.3")
                params.append(theme)

            if sentiment and sentiment != 'all':
                conditions.append("a.sentiment_type = ?")
                params.append(sentiment)

            if source and source != 'all':
                conditions.append("a.feed_url = ?")
                params.append(source)

            if date_from:
                conditions.append("DATE(a.pub_date) >= ?")
                params.append(date_from)

            if date_to:
                conditions.append("DATE(a.pub_date) <= ?")
                params.append(date_to)

            if search:
                conditions.append("(a.title LIKE ? OR a.content LIKE ?)")
                search_pattern = f"%{search}%"
                params.extend([search_pattern, search_pattern])

            query += " ".join(joins)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY a.pub_date DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)

            articles = []
            for row in cursor.fetchall():
                articles.append({
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'link': row[3],
                    'pub_date': row[4],
                    'sentiment': row[5],
                    'sentiment_score': row[6],
                    'feed_url': row[7]
                })

            conn.close()
            return jsonify({'articles': articles})

        except Exception as e:
            logger.error(f"Erreur filtrage articles: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/articles/export')
    def export_articles():
        """Exporte les articles filtrés en CSV"""
        try:
            theme = request.args.get('theme')
            sentiment = request.args.get('sentiment')
            source = request.args.get('source')
            date_from = request.args.get('date_from')
            date_to = request.args.get('date_to')
            search = request.args.get('search', '')

            conn = db_manager.get_connection()
            cursor = conn.cursor()

            query = """
                SELECT DISTINCT a.id, a.title, a.content, a.link, a.pub_date, 
                       a.sentiment_type, a.sentiment_score, a.feed_url
                FROM articles a
            """

            joins = []
            conditions = []
            params = []

            if theme and theme != 'all':
                joins.append("LEFT JOIN theme_analyses ta ON a.id = ta.article_id")
                conditions.append("ta.theme_id = ? AND ta.confidence >= 0.3")
                params.append(theme)

            if sentiment and sentiment != 'all':
                conditions.append("a.sentiment_type = ?")
                params.append(sentiment)

            if source and source != 'all':
                conditions.append("a.feed_url = ?")
                params.append(source)

            if date_from:
                conditions.append("DATE(a.pub_date) >= ?")
                params.append(date_from)

            if date_to:
                conditions.append("DATE(a.pub_date) <= ?")
                params.append(date_to)

            if search:
                conditions.append("(a.title LIKE ? OR a.content LIKE ?)")
                search_pattern = f"%{search}%"
                params.extend([search_pattern, search_pattern])

            query += " ".join(joins)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY a.pub_date DESC LIMIT 1000"

            cursor.execute(query, params)

            output = StringIO()
            writer = csv.writer(output)

            writer.writerow(['ID', 'Titre', 'Contenu', 'Lien', 'Date', 'Sentiment', 'Score', 'Source'])

            for row in cursor.fetchall():
                writer.writerow(row)

            conn.close()

            output.seek(0)
            return Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={
                    'Content-Disposition': 'attachment; filename=articles_export.csv'
                }
            )

        except Exception as e:
            logger.error(f"Erreur export articles: {e}")
            return jsonify({'error': str(e)}), 500

    # NOUVELLES ROUTES AVANCÉES
    @app.route('/api/themes/advanced', methods=['POST'])
    def create_advanced_theme():
        """Crée un thème avec configuration avancée"""
        try:
            data = request.get_json()
            result = advanced_theme_manager.create_advanced_theme(data)

            if result['success']:
                return jsonify(result), 200
            else:
                return jsonify(result), 400

        except Exception as e:
            logger.error(f"Erreur création thème avancé: {e}")
            return jsonify({
                'success': False,
                'error': f'Erreur serveur: {str(e)}'
            }), 500

    @app.route('/api/themes/<theme_id>/details')
    def get_theme_details(theme_id):
        """Récupère les détails complets d'un thème"""
        try:
            theme = advanced_theme_manager.get_theme_with_details(theme_id)

            if not theme:
                return jsonify({'error': 'Thème non trouvé'}), 404

            return jsonify({'theme': theme})

        except Exception as e:
            logger.error(f"Erreur récupération détails: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/themes/<theme_id>/statistics')
    def get_theme_statistics_advanced(theme_id):
        """Récupère les statistiques avancées d'un thème"""
        try:
            stats = advanced_theme_manager.get_theme_statistics(theme_id)
            return jsonify({'statistics': stats})

        except Exception as e:
            logger.error(f"Erreur statistiques: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/themes/<theme_id>/keywords/<keyword>/weight', methods=['PUT'])
    def update_keyword_weight(theme_id, keyword):
        """Met à jour le poids d'un mot-clé"""
        try:
            data = request.get_json()
            new_weight = data.get('weight')

            if new_weight is None:
                return jsonify({'error': 'Poids requis'}), 400

            success = advanced_theme_manager.update_keyword_weight(
                theme_id, keyword, float(new_weight)
            )

            if success:
                return jsonify({'message': 'Poids mis à jour'})
            else:
                return jsonify({'error': 'Erreur mise à jour'}), 500

        except Exception as e:
            logger.error(f"Erreur update poids: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/themes/<theme_id>/synonyms', methods=['POST'])
    def add_theme_synonym(theme_id):
        """Ajoute un synonyme à un mot-clé"""
        try:
            data = request.get_json()
            original_word = data.get('original_word')
            synonym = data.get('synonym')

            if not original_word or not synonym:
                return jsonify({'error': 'Mot original et synonyme requis'}), 400

            success = advanced_theme_manager.add_synonym(
                theme_id, original_word, synonym
            )

            if success:
                return jsonify({'message': 'Synonyme ajouté'})
            else:
                return jsonify({'error': 'Erreur ajout synonyme'}), 500

        except Exception as e:
            logger.error(f"Erreur ajout synonyme: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/themes/<theme_id>/suggest-keywords')
    def suggest_theme_keywords(theme_id):
        """Suggère de nouveaux mots-clés pour un thème"""
        try:
            limit = int(request.args.get('limit', 10))
            suggestions = advanced_theme_manager.suggest_new_keywords(theme_id, limit)

            return jsonify({'suggestions': suggestions})

        except Exception as e:
            logger.error(f"Erreur suggestion mots-clés: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/themes/<theme_id>/export')
    def export_theme_configuration(theme_id):
        """Exporte la configuration d'un thème"""
        try:
            config = advanced_theme_manager.export_theme_config(theme_id)

            return Response(
                json.dumps(config, ensure_ascii=False, indent=2),
                mimetype='application/json',
                headers={
                    'Content-Disposition': f'attachment; filename=theme_{theme_id}.json'
                }
            )

        except Exception as e:
            logger.error(f"Erreur export thème: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/themes/import', methods=['POST'])
    def import_theme_configuration():
        """Importe une configuration de thème"""
        try:
            config = request.get_json()
            success = advanced_theme_manager.import_theme_config(config)

            if success:
                return jsonify({'message': 'Thème importé avec succès'})
            else:
                return jsonify({'error': 'Erreur import'}), 500

        except Exception as e:
            logger.error(f"Erreur import thème: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/reanalyze-articles', methods=['POST'])
    def reanalyze_articles():
        """Ré-analyse tous les articles avec les thèmes actuels"""
        try:
            logger.info("🔄 Démarrage de la ré-analyse des articles...")
            theme_analyzer.reanalyze_all_articles()

            conn = db_manager.get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM articles")
            total_articles = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(DISTINCT article_id) 
                FROM theme_analyses 
                WHERE confidence >= 0.2
            """)
            analyzed_articles = cursor.fetchone()[0]

            cursor.execute("""
                SELECT theme_id, COUNT(DISTINCT article_id) as count
                FROM theme_analyses
                WHERE confidence >= 0.2
                GROUP BY theme_id
            """)

            theme_counts = {row[0]: row[1] for row in cursor.fetchall()}
            conn.close()

            return jsonify({
                'success': True,
                'message': 'Ré-analyse terminée avec succès',
                'results': {
                    'total_articles': total_articles,
                    'analyzed_articles': analyzed_articles,
                    'themes_detected': len(theme_counts),
                    'theme_distribution': theme_counts
                }
            })

        except Exception as e:
            logger.error(f"Erreur ré-analyse: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

  # ===== PAGES HTML ========================

    @app.route('/social')
    def social_page():
        """Page d'analyse des réseaux sociaux"""
        return render_template('social.html')

    @app.route('/archiviste')
    def archiviste_page():
        """Page d'analyse historique"""
        return render_template('archiviste.html')

    # ===== ROUTES ALERTES =================

    @app.route('/api/anomalies/sentiment')
    def get_sentiment_anomalies():
        """Récupère les anomalies de sentiment"""
        try:
            days = int(request.args.get('days', 7))
            threshold = float(request.args.get('threshold', 2.0))
        
            anomalies = anomaly_detector.detect_sentiment_anomalies(days, threshold)
            return jsonify({'anomalies': anomalies, 'count': len(anomalies)})
        except Exception as e:
            logger.error(f"Erreur récupération anomalies sentiment: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/anomalies/theme/<theme_id>')
    def get_theme_anomalies(theme_id):
        """Récupère les anomalies pour un thème spécifique"""
        try:
            days = int(request.args.get('days', 7))
            anomalies = anomaly_detector.detect_theme_anomalies(theme_id, days)
            return jsonify({'theme_id': theme_id, 'anomalies': anomalies})
        except Exception as e:
            logger.error(f"Erreur récupération anomalies thème {theme_id}: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/anomalies/report')
    def get_anomaly_report():
        """Génère un rapport complet des anomalies"""
        try:
            days = int(request.args.get('days', 7))
            report = anomaly_detector.get_comprehensive_anomaly_report(days)
            return jsonify(report)
        except Exception as e:
            logger.error(f"Erreur génération rapport anomalies: {e}")
            return jsonify({'error': str(e)}), 500

    # ===== FONCTIONS INTERNES POUR IA =====
    def generate_ia_analysis(articles, report_type, themes, start_date, end_date):
        """
        Génère l'analyse IA avec le serveur Llama
        Utilise llama_client.py pour la communication
        """
        from .llama_client import get_llama_client
        
        # Préparer le contexte pour Llama
        sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
        for article in articles:
            sentiment = article.get('sentiment', 'neutral')
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        
        context = {
            'period': f"{start_date or 'début'} → {end_date or 'aujourd\'hui'}",
            'themes': themes if themes else ['Tous thèmes'],
            'sentiment_positive': sentiment_counts.get('positive', 0),
            'sentiment_negative': sentiment_counts.get('negative', 0),
            'sentiment_neutral': sentiment_counts.get('neutral', 0),
            'total_articles': len(articles)
        }
        
        # Appel au client Llama
        llama_client = get_llama_client()
        result = llama_client.generate_analysis(
            report_type=report_type,
            articles=articles,
            context=context
        )
        
        # Convertir le markdown en HTML (conversion améliorée)
        analysis_text = result.get('analysis', '')
        
        # Nettoyer le texte des balises ChatML résiduelles
        analysis_text = analysis_text.replace('<|im_start|>', '').replace('<|im_end|>', '')
        
        # Conversion markdown → HTML
        lines = analysis_text.split('\n')
        html_lines = []
        in_list = False
        
        for line in lines:
            line = line.strip()
            
            if not line:
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                html_lines.append('<br>')
                continue
            
            # Titres H2
            if line.startswith('## '):
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                html_lines.append(f'<h2>{line[3:]}</h2>')
            
            # Titres H3
            elif line.startswith('### '):
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                html_lines.append(f'<h3>{line[4:]}</h3>')
            
            # Listes
            elif line.startswith('- ') or line.startswith('* '):
                if not in_list:
                    html_lines.append('<ul>')
                    in_list = True
                html_lines.append(f'<li>{line[2:]}</li>')
            
            # Texte gras **texte**
            elif '**' in line:
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                line = line.replace('**', '<strong>', 1).replace('**', '</strong>', 1)
                html_lines.append(f'<p>{line}</p>')
            
            # Paragraphe normal
            else:
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                html_lines.append(f'<p>{line}</p>')
        
        if in_list:
            html_lines.append('</ul>')
        
        html_content = '\n'.join(html_lines)
        
        # Ajouter un badge de statut
        if result.get('success'):
            status_badge = f'''
            <div style="background: #d4edda; border: 1px solid #c3e6cb; padding: 10px; border-radius: 5px; margin-bottom: 15px;">
                <strong style="color: #155724;">✅ Analyse générée par IA Llama 3.2</strong><br>
                <small>Modèle: {result.get('model_used', 'llama3.2-3b-Q4_K_M')}</small>
            </div>
            '''
        else:
            status_badge = f'''
            <div style="background: #fff3cd; border: 1px solid #ffeeba; padding: 10px; border-radius: 5px; margin-bottom: 15px;">
                <strong style="color: #856404;">⚠️ Mode dégradé</strong><br>
                <small>Raison: {result.get('error', 'Serveur Llama indisponible')}</small>
            </div>
            '''
        
        html_content = status_badge + html_content
        
        return {
            'html_content': html_content,
            'recommendations': '',
            'llama_success': result.get('success', False),
            'llama_error': result.get('error')
        }

    # ===== ROUTES IA =====
    @app.route('/api/generate-ia-report', methods=['POST'])
    def generate_ia_report():
        """Génère un rapport d'analyse IA à partir des articles"""
        try:
            data = request.get_json()
            
            report_type = data.get('report_type', 'geopolitique')
            start_date = data.get('start_date')
            end_date = data.get('end_date')
            themes = data.get('themes', [])
            include_sentiment = data.get('include_sentiment', True)
            include_sources = data.get('include_sources', True)
            generate_pdf = data.get('generate_pdf', False)
            
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            query = "SELECT id, title, content, pub_date, sentiment_type, feed_url FROM articles WHERE 1=1"
            params = []
            
            if start_date:
                query += " AND DATE(pub_date) >= ?"
                params.append(start_date)
            if end_date:
                query += " AND DATE(pub_date) <= ?"
                params.append(end_date)
            if themes:
                placeholders = ','.join('?' * len(themes))
                query += f" AND id IN (SELECT DISTINCT article_id FROM theme_analyses WHERE theme_id IN ({placeholders}) AND confidence >= 0.3)"
                params.extend(themes)
            
            query += " ORDER BY pub_date DESC LIMIT 100"
            
            cursor.execute(query, params)
            articles = []
            for row in cursor.fetchall():
                articles.append({
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'pub_date': row[3],
                    'sentiment': row[4],
                    'source': row[5]
                })
            
            conn.close()
            
            if not articles:
                return jsonify({
                    'success': False,
                    'error': 'Aucun article trouvé avec les critères sélectionnés'
                }), 400
            
            # APPEL AU CLIENT LLAMA
            analysis_result = generate_ia_analysis(
                articles, 
                report_type, 
                themes,
                start_date,
                end_date
            )
            
            response_data = {
                'success': True,
                'report_type': report_type,
                'articles_analyzed': len(articles),
                'themes_covered': themes,
                'period': f"{start_date} to {end_date}" if start_date and end_date else "Toutes périodes",
                'analysis_html': analysis_result['html_content'],
                'recommendations': analysis_result.get('recommendations', ''),
                'llama_status': {
                    'success': analysis_result.get('llama_success', False),
                    'error': analysis_result.get('llama_error'),
                    'mode': 'IA' if analysis_result.get('llama_success') else 'Dégradé'
                }
            }
            
            if generate_pdf:
                response_data['pdf_generation_available'] = True
            
            return jsonify(response_data)
            
        except Exception as e:
            logger.error(f"Erreur génération rapport IA: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': f'Erreur génération rapport IA: {str(e)}'
            }), 500

    @app.route('/api/generate-pdf', methods=['POST'])
    def generate_pdf_report():
        """Génère un PDF à partir du contenu de l'analyse IA"""
        try:
            data = request.get_json()
            html_content = data.get('html_content', '')
            title = data.get('title', 'Rapport GEOPOL')
            report_type = data.get('type', 'geopolitique')

            if not html_content:
                return jsonify({
                    'success': False,
                    'error': 'Contenu HTML requis'
                }), 400

            # Créer le HTML complet pour le PDF
            full_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>{title}</title>
                <style>
                    @page {{
                        size: a4;
                        margin: 2cm;
                    }}
                    body {{
                        font-family: 'Helvetica', sans-serif;
                        margin: 0;
                        padding: 0;
                        line-height: 1.4;
                        color: #000;
                        font-size: 12px;
                    }}
                    .header {{
                        text-align: center;
                        margin-bottom: 30px;
                        border-bottom: 2px solid #3498db;
                        padding-bottom: 15px;
                    }}
                    h1 {{
                        color: #2c3e50;
                        margin-bottom: 8px;
                        font-size: 18px;
                    }}
                    .timestamp {{
                        color: #7f8c8d;
                        font-size: 10px;
                    }}
                    .content {{
                        margin-top: 15px;
                    }}
                    .footer {{
                        margin-top: 30px;
                        text-align: center;
                        font-size: 9px;
                        color: #95a5a6;
                        border-top: 1px solid #bdc3c7;
                        padding-top: 10px;
                    }}
                    h2 {{
                        font-size: 14px;
                        color: #2c3e50;
                        margin-top: 20px;
                        margin-bottom: 10px;
                    }}
                    h3 {{
                        font-size: 12px;
                        color: #34495e;
                        margin-top: 15px;
                        margin-bottom: 8px;
                    }}
                    p, li {{
                        font-size: 11px;
                        margin-bottom: 8px;
                    }}
                    ul {{
                        margin-left: 20px;
                    }}
                    .status-badge {{
                        padding: 8px;
                        border-radius: 4px;
                        margin-bottom: 15px;
                        font-size: 10px;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>{title}</h1>
                    <p class="timestamp">Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} • GEOPOL Analytics</p>
                </div>
                <div class="content">
                    {html_content}
                </div>
                <div class="footer">
                    Rapport généré automatiquement par GEOPOL avec Llama 3.2
                </div>
            </body>
            </html>
            """

            # Générer le PDF avec xhtml2pdf
            pdf_buffer = BytesIO()
            pisa_status = pisa.CreatePDF(
                BytesIO(full_html.encode('UTF-8')),
                dest=pdf_buffer,
                encoding='UTF-8'
            )

            if pisa_status.err:
                return jsonify({
                    'success': False,
                    'error': 'Erreur lors de la génération du PDF'
                }), 500

            pdf_buffer.seek(0)

            # Créer un fichier temporaire pour l'envoi
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                tmp_file.write(pdf_buffer.getvalue())
                pdf_path = tmp_file.name

            try:
                return send_file(
                    pdf_path,
                    as_attachment=True,
                    download_name=f"rapport_{report_type}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mimetype='application/pdf'
                )
            finally:
                # Nettoyer le fichier temporaire après l'envoi
                try:
                    os.remove(pdf_path)
                except Exception as e:
                    logger.warning(f"Erreur lors de la suppression du fichier temporaire {pdf_path}: {e}")

        except Exception as e:
            logger.error(f"Erreur génération PDF: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': f'Erreur génération PDF: {str(e)}'
            }), 500

    logger.info("✅ Routes enregistrées avec intégration Llama")