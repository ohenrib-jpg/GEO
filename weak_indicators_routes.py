from flask import Blueprint, jsonify, request
import sqlite3
import json
from datetime import datetime

weak_indicators_bp = Blueprint('weak_indicators', __name__)

@weak_indicators_bp.route('/weak-indicators')
def weak_indicators_page():
    return render_template('weak-indicators.html')

@weak_indicators_bp.route('/api/weak-indicators/countries')
def get_monitored_countries():
    """Retourne la liste des pays surveillés"""
    try:
        conn = sqlite3.connect('instance/geopol.db')
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
            # ... autres pays du G20
        ]
        return jsonify(default_countries)

@weak_indicators_bp.route('/api/travel-advice/<country>')
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

@weak_indicators_bp.route('/api/sdr-streams', methods=['GET', 'POST'])
def manage_sdr_streams():
    """Gestion des flux SDR"""
    if request.method == 'GET':
        # Retourner les flux sauvegardés
        return jsonify([])
    else:
        # Sauvegarder un nouveau flux
        data = request.json
        return jsonify({'status': 'success'})

@weak_indicators_bp.route('/api/economic-data/<country>/<indicator>')
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