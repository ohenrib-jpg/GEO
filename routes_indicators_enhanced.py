# Flask/routes_indicators_enhanced.py
"""
Routes Flask pour le dashboard économique amélioré
Utilise le connecteur unifié (Eurostat + INSEE + yFinance)
"""

from flask import Blueprint, jsonify, request, render_template
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def create_indicators_blueprint_enhanced(db_manager):
    """Crée le blueprint amélioré des indicateurs économiques"""
    
    indicators_bp = Blueprint('indicators', __name__, url_prefix='/indicators')
    
    # Initialiser le connecteur unifié
    from .enhanced_indicators_connector import EnhancedIndicatorsConnector
    
    connector = EnhancedIndicatorsConnector(db_manager)
    
    # === PAGE PRINCIPALE ===
    @indicators_bp.route('/')
    def indicators_page():
        """Page principale du dashboard"""
        return render_template('indicators_dashboard.html')
    
    # === API DASHBOARD COMPLET ===
    @indicators_bp.route('/api/dashboard')
    def get_dashboard():
        """
        Récupère toutes les données du dashboard
        Endpoint principal recommandé
        """
        try:
            data = connector.get_dashboard_data()
            return jsonify(data)
            
        except Exception as e:
            logger.error(f"❌ Erreur get_dashboard: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # === API INDICATEURS (rétrocompatibilité) ===
    @indicators_bp.route('/api/data')
    def get_indicators_data():
        """
        API rétrocompatible pour les indicateurs
        Récupère les données des indicateurs
        """
        try:
            # Récupérer toutes les données
            dashboard = connector.get_dashboard_data()
            
            # Formater pour rétrocompatibilité
            result = {
                'success': True,
                'indicators': {},
                'stats': {
                    'total': len(dashboard['indicators']),
                    'successful': len(dashboard['indicators']),
                    'failed': 0
                },
                'timestamp': dashboard['timestamp']
            }
            
            # Convertir au format attendu
            for ind_id, indicator in dashboard['indicators'].items():
                result['indicators'][ind_id] = {
                    'success': True,
                    'indicator_id': indicator['id'],
                    'indicator_name': indicator['name'],
                    'current_value': indicator['value'],
                    'unit': indicator['unit'],
                    'period': indicator['period'],
                    'change_percent': indicator['change_percent'],
                    'change_direction': indicator['change_direction'],
                    'source': indicator['source'],
                    'category': indicator['category'],
                    'description': indicator['description'],
                    'last_update': indicator['last_update'],
                    'reliability': indicator['reliability']
                }
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"❌ Erreur get_indicators_data: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @indicators_bp.route('/api/available')
    def get_available_indicators():
        """Liste des indicateurs disponibles"""
        try:
            result = connector.get_available_indicators()
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"❌ Erreur get_available_indicators: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @indicators_bp.route('/api/indicator/<indicator_id>')
    def get_single_indicator(indicator_id):
        """Récupère un indicateur spécifique"""
        try:
            result = connector.get_indicator_by_id(indicator_id)
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"❌ Erreur get_single_indicator: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # === API DONNÉES FINANCIÈRES ===
    @indicators_bp.route('/api/indices')
    def get_financial_indices():
        """Récupère les indices boursiers"""
        try:
            dashboard = connector.get_dashboard_data()
            return jsonify(dashboard['financial_markets'])
            
        except Exception as e:
            logger.error(f"❌ Erreur get_financial_indices: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @indicators_bp.route('/api/historical/<symbol>')
    def get_historical_data(symbol):
        """Données historiques d'un indice"""
        try:
            period = request.args.get('period', '6mo')
            result = connector.yfinance.get_historical_data(symbol, period)
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"❌ Erreur get_historical_data: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # === RAFRAÎCHISSEMENT ===
    @indicators_bp.route('/api/refresh', methods=['POST'])
    def force_refresh():
        """Force le rafraîchissement de toutes les sources"""
        try:
            logger.info("🔄 Rafraîchissement forcé demandé")
            result = connector.force_refresh()
            
            return jsonify({
                'success': True,
                'message': 'Données rafraîchies',
                'data': result
            })
            
        except Exception as e:
            logger.error(f"❌ Erreur force_refresh: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # === STATUT DU SYSTÈME ===
    @indicators_bp.route('/api/status')
    def get_status():
        """Statut détaillé du système"""
        try:
            dashboard = connector.get_dashboard_data()
            
            return jsonify({
                'success': True,
                'system_status': 'operational',
                'data_sources': dashboard['sources_status'],
                'data_quality': dashboard['summary']['data_quality'],
                'total_indicators': dashboard['summary']['total_indicators'],
                'reliability_breakdown': dashboard['summary']['by_reliability'],
                'timestamp': datetime.now().isoformat(),
                'note': 'Dashboard éducatif - Sources: Eurostat (officiel), INSEE (scraping), Yahoo Finance'
            })
            
        except Exception as e:
            logger.error(f"❌ Erreur get_status: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # === GESTION DES PRÉFÉRENCES (maintenu pour compatibilité) ===
    @indicators_bp.route('/api/preferences', methods=['GET', 'POST'])
    def manage_preferences():
        """Sauvegarde/récupère les préférences utilisateur"""
        try:
            if request.method == 'POST':
                data = request.get_json()
                selected_indicators = data.get('selected_indicators', [])
                
                # Sauvegarder en DB
                if db_manager:
                    conn = db_manager.get_connection()
                    cur = conn.cursor()
                    
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS user_indicator_preferences (
                            user_id TEXT PRIMARY KEY,
                            selected_indicators TEXT,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    import json
                    cur.execute("""
                        INSERT OR REPLACE INTO user_indicator_preferences 
                        (user_id, selected_indicators, updated_at)
                        VALUES (?, ?, ?)
                    """, ('default', json.dumps(selected_indicators), datetime.now().isoformat()))
                    
                    conn.commit()
                    conn.close()
                
                return jsonify({
                    'success': True,
                    'message': 'Préférences sauvegardées',
                    'selected_indicators': selected_indicators
                })
            
            else:  # GET
                if db_manager:
                    conn = db_manager.get_connection()
                    cur = conn.cursor()
                    
                    cur.execute("""
                        SELECT selected_indicators FROM user_indicator_preferences 
                        WHERE user_id = 'default'
                    """)
                    
                    row = cur.fetchone()
                    conn.close()
                    
                    if row:
                        import json
                        selected = json.loads(row[0])
                    else:
                        selected = ['eurostat_gdp', 'eurostat_unemployment', 'eurostat_hicp', 'insee_inflation']
                else:
                    selected = ['eurostat_gdp', 'eurostat_unemployment', 'eurostat_hicp', 'insee_inflation']
                
                return jsonify({
                    'success': True,
                    'selected_indicators': selected
                })
                
        except Exception as e:
            logger.error(f"❌ Erreur manage_preferences: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # === ENDPOINT DE SANTÉ ===
    @indicators_bp.route('/api/health')
    def health_check():
        """Health check endpoint"""
        try:
            dashboard = connector.get_dashboard_data()
            
            # Vérifier que nous avons au moins quelques données
            has_data = len(dashboard['indicators']) > 0
            
            return jsonify({
                'status': 'healthy' if has_data else 'degraded',
                'indicators_count': len(dashboard['indicators']),
                'data_quality': dashboard['summary']['data_quality'],
                'sources': dashboard['sources_status'],
                'timestamp': datetime.now().isoformat()
            }), 200 if has_data else 503
            
        except Exception as e:
            logger.error(f"❌ Erreur health_check: {e}")
            return jsonify({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 503
    
    return indicators_bp