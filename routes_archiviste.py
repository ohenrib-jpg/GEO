# Flask/routes_archiviste.py
from flask import Blueprint, jsonify, request, render_template
import logging

logger = logging.getLogger(__name__)

def create_archiviste_blueprint(db_manager, archiviste):
    """Crée le blueprint pour les routes Archiviste"""
    
    archiviste_bp = Blueprint('archiviste', __name__, url_prefix='/archiviste')
    
    @archiviste_bp.route('/')
    def archiviste_page():
        """Page principale Archiviste"""
        return render_template('archiviste.html')
    
    @archiviste_bp.route('/api/periods')
    def get_historical_periods():
        """Retourne les périodes historiques disponibles"""
        try:
            if hasattr(archiviste, 'historical_periods'):
                periods = archiviste.historical_periods
                return jsonify({
                    'success': True,
                    'periods': periods
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Archiviste non initialisé correctement'
                }), 500
        except Exception as e:
            logger.error(f"❌ Erreur get_historical_periods: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @archiviste_bp.route('/api/themes')
    def get_archiviste_themes():
        """Retourne les thèmes pour Archiviste"""
        try:
            if archiviste and hasattr(archiviste, 'get_available_themes'):
                themes = archiviste.get_available_themes()
                return jsonify({
                    'success': True,
                    'themes': themes
                })
            else:
                # Fallback avec des thèmes de base
                fallback_themes = [
                    {'id': 1, 'name': 'Géopolitique', 'keywords': ['politique', 'international', 'diplomatie']},
                    {'id': 2, 'name': 'Conflits', 'keywords': ['guerre', 'conflit', 'tensions']},
                    {'id': 3, 'name': 'Économie', 'keywords': ['économie', 'commerce', 'finance']}
                ]
                return jsonify({
                    'success': True,
                    'themes': fallback_themes
                })
        except Exception as e:
            logger.error(f"❌ Erreur get_archiviste_themes: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @archiviste_bp.route('/api/stats')
    def get_archiviste_stats():
        """Retourne les statistiques Archiviste"""
        try:
            # Statistiques de base
            stats = {
                'total_analyses': 0,
                'available_periods': 9,  # Périodes prédéfinies
                'available_themes': 3,   # Thèmes de base
                'recent_analyses': []
            }
            
            # Essayer de récupérer les vraies stats si disponibles
            if archiviste and hasattr(archiviste, 'get_analyses_history'):
                try:
                    analyses_history = archiviste.get_analyses_history(limit=5)
                    stats['total_analyses'] = len(analyses_history)
                    stats['recent_analyses'] = analyses_history
                except:
                    pass  # Garder les valeurs par défaut en cas d'erreur
            
            return jsonify({
                'success': True,
                'stats': stats
            })
            
        except Exception as e:
            logger.error(f"❌ Erreur get_archiviste_stats: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @archiviste_bp.route('/api/analyze-period', methods=['POST'])
    def analyze_historical_period():
        """Analyse une période historique avec un thème"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'Données JSON requises'
                }), 400
                
            period_key = data.get('period_key')
            theme_id = data.get('theme_id')
            
            print(f"🔍 Analyse demandée - Période: {period_key}, Thème ID: {theme_id}")
            
            if not period_key:
                return jsonify({
                    'success': False,
                    'error': 'period_key requis'
                }), 400
            
            if theme_id is None:
                return jsonify({
                    'success': False,
                    'error': 'theme_id requis'
                }), 400
                
            # Convertir theme_id en entier
            try:
                theme_id = int(theme_id)
            except (ValueError, TypeError):
                return jsonify({
                    'success': False,
                    'error': f'theme_id doit être un nombre, reçu: {theme_id}'
                }), 400
            
            # Vérifier si la période existe
            if not hasattr(archiviste, 'historical_periods') or period_key not in archiviste.historical_periods:
                available_periods = list(archiviste.historical_periods.keys()) if hasattr(archiviste, 'historical_periods') else []
                return jsonify({
                    'success': False,
                    'error': f'Période inconnue: {period_key}',
                    'available_periods': available_periods
                }), 400
            
            # Vérifier si la méthode d'analyse existe
            if not hasattr(archiviste, 'analyze_period_with_theme'):
                return jsonify({
                    'success': False,
                    'error': 'Fonction d\'analyse non disponible'
                }), 501
            
            print(f"🎯 Lancement analyse - Période: {period_key}, Thème ID: {theme_id}")
            result = archiviste.analyze_period_with_theme(period_key, theme_id)
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"❌ Erreur analyze_historical_period: {e}")
            return jsonify({
                'success': False, 
                'error': f'Erreur serveur: {str(e)}'
            }), 500
    
    return archiviste_bp
