# Flask/routes_indicators.py
"""
Routes Flask pour le dashboard économique Eurostat + yFinance
VERSION ORIGINALE CORRIGÉE
"""

from flask import Blueprint, jsonify, request, render_template
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def create_indicators_blueprint(db_manager):
    """Crée le blueprint des indicateurs économiques"""
    
    indicators_bp = Blueprint('indicators', __name__, url_prefix='/indicators')
    
    # Initialiser les connecteurs
    from .eurostat_connector import EurostatConnector
    from .yfinance_connector import YFinanceConnector
    
    eurostat = EurostatConnector()
    yfinance = YFinanceConnector()
    
    # === PAGE PRINCIPALE ===
    @indicators_bp.route('/')
    def indicators_page():
        """Page principale du dashboard"""
        return render_template('indicators_dashboard.html')
    
    # === API INDICATEURS ===
    @indicators_bp.route('/api/data')
    def get_indicators_data():
        """
        Récupère les données des indicateurs (défaut + personnalisés)
        Query params: ?ids=gdp,unemployment,hicp,trade_balance
        """
        try:
            # Récupérer les IDs depuis les query params
            indicator_ids = request.args.get('ids', 'gdp,unemployment,hicp,trade_balance')
            indicator_ids = [id.strip() for id in indicator_ids.split(',')]
            
            # Limiter à 8 indicateurs max (4 défaut + 4 personnalisés)
            if len(indicator_ids) > 8:
                indicator_ids = indicator_ids[:8]
            
            # Récupérer les données
            result = eurostat.get_multiple_indicators(indicator_ids)
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"❌ Erreur get_indicators_data: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @indicators_bp.route('/api/available')
    def get_available_indicators():
        """Liste des indicateurs disponibles pour sélection"""
        try:
            result = eurostat.get_available_indicators()
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"❌ Erreur get_available_indicators: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @indicators_bp.route('/api/indicator/<indicator_id>')
    def get_single_indicator(indicator_id):
        """Récupère un indicateur spécifique avec historique"""
        try:
            result = eurostat.get_indicator_data(indicator_id, last_n=24)
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"❌ Erreur get_single_indicator: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # === API DONNÉES FINANCIÈRES (yFinance) ===
    @indicators_bp.route('/api/indices')
    def get_financial_indices():
        """Récupère les indices boursiers"""
        try:
            result = yfinance.get_all_indices()
            return jsonify(result)
            
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
            result = yfinance.get_historical_data(symbol, period)
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"❌ Erreur get_historical_data: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # === GESTION DES PRÉFÉRENCES UTILISATEUR ===
    @indicators_bp.route('/api/preferences', methods=['GET', 'POST'])
    def manage_preferences():
        """Sauvegarde/récupère les préférences utilisateur"""
        try:
            if request.method == 'POST':
                data = request.get_json()
                selected_indicators = data.get('selected_indicators', [])
                
                # Sauvegarder en DB (simple pour l'instant)
                conn = db_manager.get_connection()
                cur = conn.cursor()
                
                # Créer table si nécessaire
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS user_indicator_preferences (
                        user_id TEXT PRIMARY KEY,
                        selected_indicators TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Sauvegarder (user_id = 'default' pour l'instant)
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
                    selected = ['gdp', 'unemployment', 'hicp', 'trade_balance']
                
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
    
    # === STATUT ===
    @indicators_bp.route('/api/status')
    def get_status():
        """Statut du système"""
        return jsonify({
            'success': True,
            'system_status': 'operational',
            'data_sources': {
                'eurostat': 'available',
                'yfinance': 'available'
            },
            'timestamp': datetime.now().isoformat(),
            'note': 'Dashboard éducatif et recherche - Sources : Eurostat, Yahoo Finance'
        })
    
    return indicators_bp