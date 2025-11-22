# Flask/routes_indicateurs.py (VERSION CORRIGÉE)
from flask import Blueprint, jsonify, request, render_template
import logging
from datetime import datetime
from .indicateurs_francais import IndicateursFrancais

logger = logging.getLogger(__name__)

def create_indicateurs_blueprint(db_manager):
    indicateurs_bp = Blueprint('indicateurs', __name__, url_prefix='/indicateurs')
    indicateurs_manager = IndicateursFrancais(db_manager)
    
    @indicateurs_bp.route('/')
    def indicateurs_page():
        return render_template('indicateurs-francais.html')
    
    @indicateurs_bp.route('/api/indicators')
    def get_indicators():
        try:
            result = indicateurs_manager.get_all_indicators()
            return jsonify(result)
        except Exception as e:
            logger.error(f"❌ Erreur get_indicators: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @indicateurs_bp.route('/api/indicator/<indicator_name>')
    def get_single_indicator(indicator_name):
        try:
            if hasattr(indicateurs_manager, f'get_{indicator_name}_data'):
                method = getattr(indicateurs_manager, f'get_{indicator_name}_data')
                result = method()
                return jsonify(result)
            else:
                return jsonify({'success': False, 'error': f'Indicateur {indicator_name} non trouvé'}), 404
        except Exception as e:
            logger.error(f"❌ Erreur get_single_indicator: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @indicateurs_bp.route('/api/historical')
    def get_historical_data():
        try:
            period = request.args.get('period', '6M')
            result = indicateurs_manager.get_historical_data(period)
            return jsonify(result)
        except Exception as e:
            logger.error(f"❌ Erreur get_historical_data: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @indicateurs_bp.route('/api/status')
    def get_api_status():
        try:
            status = indicateurs_manager.get_api_status()
            return jsonify(status)
        except Exception as e:
            logger.error(f"❌ Erreur get_api_status: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @indicateurs_bp.route('/api/detailed-status')
    def get_detailed_status():
        try:
            indicators_status = {
                'pib': indicateurs_manager.get_pib_data()['success'],
                'chomage': indicateurs_manager.get_chomage_data()['success'],
                'inflation': indicateurs_manager.get_inflation_data()['success'],
                'production': indicateurs_manager.get_production_data()['success'],
                'commerce': indicateurs_manager.get_commerce_data()['success'],
                'deficit': indicateurs_manager.get_deficit_data()['success'],
                'construction': indicateurs_manager.get_construction_data()['success'],
                'cac40': indicateurs_manager.get_cac40_data()['success']
            }
            
            available_count = sum(indicators_status.values())
            total_count = len(indicators_status)
            
            return jsonify({
                'success': True,
                'indicators_status': indicators_status,
                'available_count': available_count,
                'total_count': total_count,
                'availability_rate': f"{(available_count/total_count)*100:.1f}%",
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"❌ Erreur get_detailed_status: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    return indicateurs_bp