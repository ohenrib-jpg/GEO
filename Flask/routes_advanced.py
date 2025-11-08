# Flask/routes_advanced.py
"""
Routes API pour les fonctionnalités avancées :
- Analyse bayésienne
- Corroboration d'articles
"""

from flask import request, jsonify
import logging
import sqlite3
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def register_advanced_routes(app, db_manager, bayesian_analyzer, corroboration_engine):
    """
    Enregistre les routes avancées dans l'application Flask
    
    Args:
        app: Instance Flask
        db_manager: Gestionnaire de base de données
        bayesian_analyzer: Instance de BayesianSentimentAnalyzer
        corroboration_engine: Instance de CorroborationEngine
    """
    
    # ============================================================
    # ROUTES BAYÉSIENNES
    # ============================================================
    
    @app.route('/api/bayesian/analyze-article/<int:article_id>', methods=['POST'])
    def analyze_article_bayesian(article_id):
        """
        Analyse bayésienne d'un article spécifique
        """
        try:
            # Récupérer l'article
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, title, content, pub_date, sentiment_score, 
                       sentiment_type, feed_url
                FROM articles WHERE id = ?
            """, (article_id,))
            
            row = cursor.fetchone()
            if not row:
                return jsonify({'error': 'Article non trouvé'}), 404
            
            article_data = {
                'id': row[0],
                'title': row[1],
                'content': row[2],
                'pub_date': row[3],
                'sentiment_score': row[4],
                'sentiment_type': row[5],
                'feed_url': row[6],
                'sentiment_confidence': 0.7  # Valeur par défaut
            }
            
            # Récupérer les thèmes
            cursor.execute("""
                SELECT theme_id, confidence
                FROM theme_analyses
                WHERE article_id = ?
            """, (article_id,))
            
            themes = [{'id': row[0], 'confidence': row[1]} 
                     for row in cursor.fetchall()]
            article_data['themes'] = themes
            
            conn.close()
            
            # Récupérer les corroborations
            corroboration_data = bayesian_analyzer._get_corroboration_from_db(
                article_id, 
                db_manager
            )
            
            # Analyse bayésienne
            analysis = bayesian_analyzer.analyze_article_sentiment(
                article_data,
                corroboration_data
            )
            
            # Sauvegarder
            bayesian_analyzer._save_bayesian_analysis(
                article_id,
                analysis,
                db_manager
            )
            
            return jsonify({
                'success': True,
                'article_id': article_id,
                'analysis': analysis
            })
            
        except Exception as e:
            logger.error(f"Erreur analyse bayésienne: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/bayesian/batch-analyze', methods=['POST'])
    def batch_analyze_bayesian():
        """
        Analyse bayésienne en batch de plusieurs articles
        """
        try:
            data = request.get_json()
            article_ids = data.get('article_ids', [])
            
            if not article_ids:
                # Si aucun ID fourni, analyser tous les articles récents
                conn = db_manager.get_connection()
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id FROM articles 
                    WHERE pub_date >= DATE('now', '-7 days')
                    ORDER BY pub_date DESC
                    LIMIT 100
                """)
                
                article_ids = [row[0] for row in cursor.fetchall()]
                conn.close()
            
            # Récupérer les articles
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            placeholders = ','.join('?' * len(article_ids))
            cursor.execute(f"""
                SELECT id, title, content, pub_date, sentiment_score, 
                       sentiment_type, feed_url
                FROM articles 
                WHERE id IN ({placeholders})
            """, article_ids)
            
            articles = []
            for row in cursor.fetchall():
                articles.append({
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'pub_date': row[3],
                    'sentiment_score': row[4],
                    'sentiment_type': row[5],
                    'feed_url': row[6],
                    'sentiment_confidence': 0.7
                })
            
            conn.close()
            
            # Analyse batch
            results = bayesian_analyzer.batch_analyze_articles(
                articles,
                db_manager
            )
            
            return jsonify({
                'success': True,
                'results': results
            })
            
        except Exception as e:
            logger.error(f"Erreur batch bayésien: {e}")
            return jsonify({'error': str(e)}), 500
    
    # ============================================================
    # ROUTES CORROBORATION
    # ============================================================
    
    @app.route('/api/corroboration/find/<int:article_id>', methods=['GET'])
    def find_article_corroborations(article_id):
        """
        Trouve les articles corroborants pour un article donné
        """
        try:
            # Récupérer l'article source
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, title, content, pub_date, feed_url
                FROM articles WHERE id = ?
            """, (article_id,))
            
            row = cursor.fetchone()
            if not row:
                return jsonify({'error': 'Article non trouvé'}), 404
            
            article = {
                'id': row[0],
                'title': row[1],
                'content': row[2],
                'pub_date': row[3],
                'feed_url': row[4]
            }
            
            # Récupérer les thèmes de l'article
            cursor.execute("""
                SELECT theme_id
                FROM theme_analyses
                WHERE article_id = ?
            """, (article_id,))
            
            article['themes'] = [row[0] for row in cursor.fetchall()]
            
            # Récupérer les articles récents (7 derniers jours)
            cursor.execute("""
                SELECT id, title, content, pub_date, feed_url, 
                       sentiment_type, sentiment_score
                FROM articles 
                WHERE pub_date >= DATE('now', '-7 days')
                AND id != ?
                ORDER BY pub_date DESC
                LIMIT 200
            """, (article_id,))
            
            candidates = []
            for row in cursor.fetchall():
                cand = {
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'pub_date': row[3],
                    'feed_url': row[4],
                    'sentiment_type': row[5],
                    'sentiment_score': row[6]
                }
                
                # Récupérer les thèmes du candidat
                cursor.execute("""
                    SELECT theme_id
                    FROM theme_analyses
                    WHERE article_id = ?
                """, (cand['id'],))
                
                cand['themes'] = [r[0] for r in cursor.fetchall()]
                candidates.append(cand)
            
            conn.close()
            
            # Trouver les corroborations
            threshold = float(request.args.get('threshold', 0.65))
            top_n = int(request.args.get('top_n', 10))
            
            corroborations = corroboration_engine.find_corroborations(
                article,
                candidates,
                threshold=threshold,
                top_n=top_n
            )
            
            # Sauvegarder dans la base
            if corroborations:
                corroboration_engine._save_corroborations(
                    article_id,
                    corroborations,
                    db_manager
                )
            
            return jsonify({
                'success': True,
                'article_id': article_id,
                'corroborations': corroborations
            })
            
        except Exception as e:
            logger.error(f"Erreur recherche corroboration: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/corroboration/batch-process', methods=['POST'])
    def batch_process_corroborations():
        """
        Traite la corroboration pour plusieurs articles
        """
        try:
            data = request.get_json()
            article_ids = data.get('article_ids', [])
            
            if not article_ids:
                # Traiter tous les articles récents
                conn = db_manager.get_connection()
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id FROM articles 
                    WHERE pub_date >= DATE('now', '-7 days')
                    ORDER BY pub_date DESC
                    LIMIT 100
                """)
                
                article_ids = [row[0] for row in cursor.fetchall()]
                conn.close()
            
            # Récupérer tous les articles
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            # Articles à traiter
            placeholders = ','.join('?' * len(article_ids))
            cursor.execute(f"""
                SELECT id, title, content, pub_date, feed_url
                FROM articles 
                WHERE id IN ({placeholders})
            """, article_ids)
            
            articles = []
            for row in cursor.fetchall():
                art = {
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'pub_date': row[3],
                    'feed_url': row[4]
                }
                
                # Récupérer les thèmes
                cursor.execute("""
                    SELECT theme_id
                    FROM theme_analyses
                    WHERE article_id = ?
                """, (art['id'],))
                art['themes'] = [r[0] for r in cursor.fetchall()]
                
                articles.append(art)
            
            # Pool de candidats (articles récents)
            cursor.execute("""
                SELECT id, title, content, pub_date, feed_url,
                       sentiment_type, sentiment_score
                FROM articles 
                WHERE pub_date >= DATE('now', '-7 days')
                ORDER BY pub_date DESC
                LIMIT 300
            """)
            
            recent_articles = []
            for row in cursor.fetchall():
                cand = {
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'pub_date': row[3],
                    'feed_url': row[4],
                    'sentiment_type': row[5],
                    'sentiment_score': row[6]
                }
                
                cursor.execute("""
                    SELECT theme_id
                    FROM theme_analyses
                    WHERE article_id = ?
                """, (cand['id'],))
                cand['themes'] = [r[0] for r in cursor.fetchall()]
                
                recent_articles.append(cand)
            
            conn.close()
            
            # Traitement batch
            stats = corroboration_engine.batch_process_articles(
                articles,
                recent_articles,
                db_manager
            )
            
            return jsonify({
                'success': True,
                'stats': stats
            })
            
        except Exception as e:
            logger.error(f"Erreur batch corroboration: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/corroboration/stats/<int:article_id>')
    def get_article_corroboration_stats(article_id):
        """
        Récupère les statistiques de corroboration pour un article
        """
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            # Nombre de corroborations
            cursor.execute("""
                SELECT COUNT(*), AVG(similarity_score)
                FROM article_corroborations
                WHERE article_id = ?
            """, (article_id,))
            
            row = cursor.fetchone()
            count = row[0] if row else 0
            avg_similarity = row[1] if row else 0
            
            # Corroborations détaillées
            cursor.execute("""
                SELECT ac.similar_article_id, ac.similarity_score,
                       a.title, a.sentiment_type
                FROM article_corroborations ac
                JOIN articles a ON ac.similar_article_id = a.id
                WHERE ac.article_id = ?
                ORDER BY ac.similarity_score DESC
                LIMIT 10
            """, (article_id,))
            
            corroborations = []
            for row in cursor.fetchall():
                corroborations.append({
                    'article_id': row[0],
                    'similarity': row[1],
                    'title': row[2],
                    'sentiment': row[3]
                })
            
            conn.close()
            
            return jsonify({
                'article_id': article_id,
                'corroboration_count': count,
                'average_similarity': round(avg_similarity, 4) if avg_similarity else 0,
                'top_corroborations': corroborations
            })
            
        except Exception as e:
            logger.error(f"Erreur stats corroboration: {e}")
            return jsonify({'error': str(e)}), 500
    
     # ============================================================
    # ROUTE COMBINÉE : ANALYSE COMPLÈTE
    # ============================================================
    
    @app.route('/api/advanced/full-analysis/<int:article_id>', methods=['POST'])
    def full_advanced_analysis(article_id):
        """
        Analyse complète : corroboration + bayésien
        """
        try:
            # 1. Trouver les corroborations
            corr_response = find_article_corroborations(article_id)
            corr_data = corr_response.get_json()
            
            if not corr_data.get('success'):
                return jsonify({'error': 'Erreur corroboration'}), 500
            
            # 2. Analyse bayésienne avec corroborations
            bayes_response = analyze_article_bayesian(article_id)
            bayes_data = bayes_response.get_json()
            
            if not bayes_data.get('success'):
                return jsonify({'error': 'Erreur bayésienne'}), 500
            
            return jsonify({
                'success': True,
                'article_id': article_id,
                'corroboration': {
                    'count': len(corr_data.get('corroborations', [])),
                    'articles': corr_data.get('corroborations', [])
                },
                'bayesian_analysis': bayes_data.get('analysis', {})
            })
            
        except Exception as e:
            logger.error(f"Erreur analyse complète: {e}")
            return jsonify({'error': str(e)}), 500
    
    # ============================================================
    # ROUTE POUR L'HISTORIQUE DES ANALYSES
    # ============================================================
    
    @app.route('/api/analyzed-articles')
    def get_analyzed_articles():
        """
        Récupère la liste des articles ayant été analysés avec le système avancé
        """
        try:
            limit = int(request.args.get('limit', 50))
            
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            # Articles avec analyse bayésienne OU corroboration
            cursor.execute("""
                SELECT DISTINCT 
                    a.id,
                    a.title,
                    a.content,
                    a.pub_date,
                    a.sentiment_score,
                    a.sentiment_type,
                    a.bayesian_confidence,
                    a.bayesian_evidence_count,
                    a.analyzed_at,
                    (SELECT COUNT(*) FROM article_corroborations 
                     WHERE article_id = a.id) as corroboration_count
                FROM articles a
                WHERE (a.bayesian_confidence IS NOT NULL 
                       OR EXISTS (
                           SELECT 1 FROM article_corroborations 
                           WHERE article_id = a.id
                       ))
                ORDER BY a.analyzed_at DESC, a.pub_date DESC
                LIMIT ?
            """, (limit,))
            
            articles = []
            for row in cursor.fetchall():
                articles.append({
                    'id': row[0],
                    'title': row[1],
                    'content': row[2][:200] if row[2] else '',
                    'pub_date': row[3],
                    'sentiment_score': row[4],
                    'sentiment_type': row[5],
                    'bayesian_confidence': row[6],
                    'bayesian_evidence_count': row[7],
                    'analyzed_at': row[8],
                    'corroboration_count': row[9]
                })
            
            conn.close()
            
            return jsonify(articles)
            
        except Exception as e:
            logger.error(f"Erreur récupération articles analysés: {e}")
            return jsonify({'error': str(e)}), 500
    
    logger.info("✅ Routes avancées enregistrées (avec /api/analyzed-articles)")
