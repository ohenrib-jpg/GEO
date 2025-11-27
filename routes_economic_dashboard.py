# Geo/Flask/routes_economic_dashboard.py
from flask import Blueprint, jsonify, request, render_template
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def create_economic_dashboard_blueprint(db_manager):
    economic_bp = Blueprint('economic_dashboard', __name__, url_prefix='/economic-dashboard')
    
    from .economic_dashboard import EconomicDashboardManager
    economic_manager = EconomicDashboardManager(db_manager)
    
    @economic_bp.route('/')
    def dashboard_page():
        """Page principale du tableau de bord économique stratégique"""
        return render_template('economic-dashboard.html')
    
    @economic_bp.route('/api/strategic-indicators')
    def get_strategic_indicators():
        """API des indicateurs stratégiques multi-sources"""
        try:
            result = economic_manager.get_strategic_indicators()
            return jsonify(result)
        except Exception as e:
            logger.error(f"❌ Erreur indicateurs stratégiques: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @economic_bp.route('/api/sector-analysis')
    def get_sector_analysis():
        """API de l'analyse sectorielle"""
        try:
            result = economic_manager.get_sector_analysis()
            return jsonify(result)
        except Exception as e:
            logger.error(f"❌ Erreur analyse sectorielle: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @economic_bp.route('/api/country-comparison')
    def get_country_comparison():
        """API des comparaisons par pays"""
        try:
            base_country = request.args.get('base', 'FR')
            result = economic_manager.get_country_comparison(base_country)
            return jsonify(result)
        except Exception as e:
            logger.error(f"❌ Erreur comparaison pays: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @economic_bp.route('/api/widgets-config', methods=['GET', 'POST'])
    def widgets_config():
        """API de configuration des widgets"""
        try:
            user_id = request.args.get('user_id', 'global')
            
            if request.method == 'POST':
                data = request.json
                widget_type = data.get('widget_type')
                config = data.get('config', {})
                
                result = economic_manager.save_widget_config(user_id, widget_type, config)
                return jsonify(result)
            else:
                result = economic_manager.get_widget_config(user_id)
                return jsonify(result)
                
        except Exception as e:
            logger.error(f"❌ Erreur config widgets: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @economic_bp.route('/api/status')
    def get_api_status():
        """Statut de l'API du tableau de bord stratégique"""
        return jsonify({
            'success': True,
            'module': 'Economic Dashboard Stratégique',
            'status': 'operational',
            'version': '1.0',
            'timestamp': datetime.now().isoformat(),
            'features': [
                'Indicateurs multi-sources',
                'Analyse sectorielle', 
                'Comparaisons européennes',
                'Widgets personnalisables'
            ]
        })
    
    @economic_bp.route('/api/eurostat-status')
    def get_eurostat_status():
        """Statut des connecteurs Eurostat"""
        try:
            result = economic_manager.get_eurostat_status()
            return jsonify(result)
        except Exception as e:
            logger.error(f"❌ Erreur statut Eurostat: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @economic_bp.route('/api/eurostat-test')
    def test_eurostat_connection():
        """Test de connexion Eurostat"""
        try:
            from .economic_connectors import EurostatConnector
            eurostat = EurostatConnector()
            
            # Test PIB
            pib_data = eurostat.get_pib_data()
            
            return jsonify({
                'success': True,
                'eurostat_test': 'completed',
                'pib_data_available': pib_data.get('success', False),
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"❌ Test Eurostat échoué: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    # CORRECTION : Cette route doit être DANS la fonction, pas en dehors
    @economic_bp.route('/api/widgets-config', methods=['GET'])
    def get_widgets_config():
        """Endpoint pour la configuration des widgets - VERSION SIMPLIFIÉE"""
        try:
            # Pour l'instant, retourner une configuration par défaut
            default_config = {
                'strategic_indicators': {'position': 0, 'is_visible': True},
                'sector_analysis': {'position': 1, 'is_visible': True},
                'europe_comparison': {'position': 2, 'is_visible': True}
            }
            
            return jsonify({
                'success': True,
                'user_id': 'global',
                'widgets': default_config,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ Erreur widgets config: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'widgets': {}
            }), 500
    
    return economic_bp 