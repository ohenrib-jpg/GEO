# Flask/routes_geo_narrative.py
def register_geo_narrative_routes(app, db_manager):
    
    @app.route('/api/geo-narrative/patterns')
    def get_geo_narrative_patterns():
        """Récupère les patterns narratifs transnationaux"""
        try:
            days = int(request.args.get('days', 7))
            min_countries = int(request.args.get('min_countries', 2))
            
            analyzer = app.config['GEO_NARRATIVE_ANALYZER']
            patterns = analyzer.detect_transnational_patterns(days, min_countries)
            
            return jsonify({
                'success': True,
                'patterns': patterns,
                'period_days': days,
                'min_countries': min_countries
            })
            
        except Exception as e:
            logger.error(f"Erreur patterns géo-narratifs: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/geo-narrative/influence-map')
    def get_influence_map():
        """Génère la carte d'influence entre pays"""
        try:
            analyzer = app.config['GEO_NARRATIVE_ANALYZER']
            influence_data = analyzer.generate_influence_network()
            
            return jsonify({
                'success': True,
                'influence_network': influence_data
            })
            
        except Exception as e:
            logger.error(f"Erreur carte influence: {e}")
            return jsonify({'error': str(e)}), 500