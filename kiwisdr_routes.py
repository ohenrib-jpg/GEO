# Flask/kiwisdr_routes.py - VERSION CORRIGÉE COMPLÈTE
"""
Routes Flask pour KiwiSDR - Version réaliste
Basé sur l'observation manuelle assistée
"""

from flask import Blueprint, jsonify, request
import logging
from datetime import datetime
import urllib.parse

logger = logging.getLogger(__name__)

kiwisdr_bp = Blueprint('kiwisdr', __name__, url_prefix='/api/kiwisdr')

# Déclaration globale pour éviter les erreurs
monitor = None

def register_kiwisdr_routes(app, db_manager):
    """Enregistre les routes KiwiSDR"""
    
    from .kiwisdr_realistic import KiwiSDRManualMonitor, GEOPOLITICAL_FREQUENCIES
    
    # Rendre monitor global pour cette fonction
    global monitor
    monitor = KiwiSDRManualMonitor(db_manager)
    
    @kiwisdr_bp.route('/servers', methods=['GET'])
    def get_servers():
        """
        Récupère la liste des serveurs KiwiSDR actifs
        GET /api/kiwisdr/servers
        """
        try:
            data = monitor.server_finder.get_active_servers()
            return jsonify(data)
        except Exception as e:
            logger.error(f"❌ Erreur récupération serveurs: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'total': 0,
                'servers': []
            }), 500
    
    @kiwisdr_bp.route('/servers/test/<path:server_url>', methods=['GET'])
    def test_server(server_url):
        """
        Teste la disponibilité d'un serveur
        GET /api/kiwisdr/servers/test/http://example.com:8073
        """
        try:
            # Décoder l'URL
            decoded_url = urllib.parse.unquote(server_url)
            
            is_available = monitor.server_finder.test_server_availability(decoded_url)
            
            return jsonify({
                'success': True,
                'server_url': decoded_url,
                'available': is_available,
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @kiwisdr_bp.route('/servers/snapshot', methods=['POST'])
    def create_server_snapshot():
        """
        Crée un snapshot des serveurs actifs
        POST /api/kiwisdr/servers/snapshot
        """
        try:
            result = monitor.create_server_snapshot()
            
            if result['success']:
                return jsonify(result), 201
            else:
                return jsonify(result), 500
        except Exception as e:
            logger.error(f"❌ Erreur création snapshot: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @kiwisdr_bp.route('/servers/history', methods=['GET'])
    def get_server_history():
        """
        Historique des variations de serveurs
        GET /api/kiwisdr/servers/history?hours=24
        """
        try:
            hours = request.args.get('hours', 24, type=int)
            history = monitor.get_server_variation_history(hours)
            
            return jsonify({
                'success': True,
                **history
            })
        except Exception as e:
            logger.error(f"❌ Erreur historique serveurs: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @kiwisdr_bp.route('/frequencies', methods=['GET', 'POST'])
    def manage_frequencies():
        """
        Gestion des fréquences surveillées
        GET /api/kiwisdr/frequencies - Liste toutes
        POST /api/kiwisdr/frequencies - Ajoute une nouvelle
        """
        try:
            if request.method == 'GET':
                frequencies = monitor.get_monitored_frequencies()
                
                return jsonify({
                    'success': True,
                    'frequencies': frequencies,
                    'total': len(frequencies)
                })
            
            else:  # POST
                data = request.get_json()
                
                if not data or 'frequency_khz' not in data or 'name' not in data:
                    return jsonify({
                        'success': False,
                        'error': 'Champs requis: frequency_khz, name'
                    }), 400
                
                result = monitor.add_monitored_frequency(
                    frequency_khz=int(data['frequency_khz']),
                    name=data['name'],
                    description=data.get('description', '')
                )
                
                if result['success']:
                    return jsonify(result), 201
                else:
                    return jsonify(result), 400
        
        except Exception as e:
            logger.error(f"❌ Erreur gestion fréquences: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @kiwisdr_bp.route('/frequencies/<int:frequency_id>', methods=['GET', 'DELETE'])
    def manage_frequency(frequency_id):
        """
        Gestion d'une fréquence spécifique
        GET /api/kiwisdr/frequencies/1?days=30 - Statistiques
        DELETE /api/kiwisdr/frequencies/1 - Désactive
        """
        try:
            if request.method == 'GET':
                days = request.args.get('days', 30, type=int)
                stats = monitor.get_frequency_statistics(frequency_id, days)
                
                return jsonify({
                    'success': True,
                    'frequency_id': frequency_id,
                    **stats
                })
            
            else:  # DELETE
                conn = db_manager.get_connection()
                cur = conn.cursor()
                
                cur.execute("""
                    UPDATE kiwisdr_monitored_frequencies 
                    SET active = 0 
                    WHERE id = ?
                """, (frequency_id,))
                
                success = cur.rowcount > 0
                conn.commit()
                conn.close()
                
                if success:
                    return jsonify({
                        'success': True,
                        'message': 'Fréquence désactivée'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Fréquence non trouvée'
                    }), 404
        
        except Exception as e:
            logger.error(f"❌ Erreur gestion fréquence {frequency_id}: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @kiwisdr_bp.route('/frequencies/<int:frequency_id>/waterfall', methods=['GET'])
    def get_waterfall_url(frequency_id):
        """
        Génère l'URL du waterfall pour une fréquence
        GET /api/kiwisdr/frequencies/1/waterfall?server_url=...
        """
        try:
            # Récupérer la fréquence
            conn = db_manager.get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT frequency_khz, name 
                FROM kiwisdr_monitored_frequencies 
                WHERE id = ? AND active = 1
            """, (frequency_id,))
            
            row = cur.fetchone()
            conn.close()
            
            if not row:
                return jsonify({
                    'success': False,
                    'error': 'Fréquence non trouvée'
                }), 404
            
            frequency_khz, name = row
            
            # Récupérer l'URL du serveur (paramètre ou premier serveur disponible)
            server_url = request.args.get('server_url')
            
            if not server_url:
                # Prendre le premier serveur disponible
                servers_data = monitor.server_finder.get_active_servers()
                if servers_data['servers']:
                    server_url = servers_data['servers'][0]['url']
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Aucun serveur KiwiSDR disponible'
                    }), 503
            
            # Générer l'URL du waterfall
            zoom = request.args.get('zoom', 10, type=int)
            waterfall_url = monitor.get_waterfall_url(server_url, frequency_khz, zoom)
            
            return jsonify({
                'success': True,
                'frequency_id': frequency_id,
                'name': name,
                'frequency_khz': frequency_khz,
                'waterfall_url': waterfall_url,
                'server_url': server_url,
                'instructions': {
                    'fr': 'Ouvrez cette URL dans un navigateur pour observer le waterfall',
                    'usage': 'Comptez manuellement les émissions et enregistrez via /record-manual'
                }
            })
        
        except Exception as e:
            logger.error(f"❌ Erreur waterfall: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @kiwisdr_bp.route('/frequencies/<int:frequency_id>/record-manual', methods=['POST'])
    def record_manual_observation(frequency_id):
        """
        Enregistre une observation MANUELLE
        POST /api/kiwisdr/frequencies/1/record-manual
        Body: {
            "emission_count": 15,
            "duration_minutes": 30,
            "notes": "Forte activité vers 14h",
            "observer": "user"
        }
        """
        try:
            data = request.get_json()
            
            if not data or 'emission_count' not in data:
                return jsonify({
                    'success': False,
                    'error': 'Champ requis: emission_count'
                }), 400
            
            result = monitor.record_manual_observation(
                frequency_id=frequency_id,
                emission_count=int(data['emission_count']),
                duration_minutes=data.get('duration_minutes', 30),
                notes=data.get('notes', ''),
                observer=data.get('observer', 'user')
            )
            
            if result['success']:
                return jsonify(result), 201
            else:
                return jsonify(result), 500
        
        except Exception as e:
            logger.error(f"❌ Erreur enregistrement observation: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @kiwisdr_bp.route('/frequencies/preset/geopolitical', methods=['POST'])
    def add_geopolitical_frequencies():
        """
        Ajoute les fréquences géopolitiques prédéfinies
        POST /api/kiwisdr/frequencies/preset/geopolitical
        """
        try:
            added = []
            errors = []
            
            for freq_preset in GEOPOLITICAL_FREQUENCIES:
                result = monitor.add_monitored_frequency(
                    frequency_khz=freq_preset['frequency_khz'],
                    name=freq_preset['name'],
                    description=freq_preset['description']
                )
                
                if result['success']:
                    added.append(freq_preset['name'])
                else:
                    errors.append(f"{freq_preset['name']}: {result.get('error', 'Erreur')}")
            
            return jsonify({
                'success': True,
                'added': len(added),
                'added_frequencies': added,
                'errors': errors,
                'message': f"{len(added)}/{len(GEOPOLITICAL_FREQUENCIES)} fréquences ajoutées"
            })
        
        except Exception as e:
            logger.error(f"❌ Erreur ajout presets: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @kiwisdr_bp.route('/dashboard', methods=['GET'])
    def get_dashboard_data():
        """
        Données complètes pour le tableau de bord
        GET /api/kiwisdr/dashboard
        """
        try:
            # Serveurs actifs
            servers = monitor.server_finder.get_active_servers()
            
            # Historique serveurs (24h)
            server_history = monitor.get_server_variation_history(hours=24)
            
            # Fréquences surveillées
            frequencies = monitor.get_monitored_frequencies()
            
            # Activité récente de chaque fréquence
            frequencies_activity = []
            for freq in frequencies:
                if freq['active']:
                    stats = monitor.get_frequency_statistics(freq['id'], days=7)
                    frequencies_activity.append({
                        'frequency': freq,
                        'stats': stats
                    })
            
            return jsonify({
                'success': True,
                'servers': {
                    'current': servers,
                    'history': server_history
                },
                'frequencies': {
                    'monitored': frequencies,
                    'activity': frequencies_activity,
                    'total': len(frequencies)
                },
                'timestamp': datetime.utcnow().isoformat()
            })
        
        except Exception as e:
            logger.error(f"❌ Erreur dashboard: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    # ===== NOUVELLES ROUTES POUR L'ANALYSE AUTOMATIQUE =====
    
    @kiwisdr_bp.route('/frequencies/<int:frequency_id>/analyze-auto', methods=['POST'])
    def analyze_frequency_auto(frequency_id):
        """
        Analyse automatique d'une fréquence via traitement du signal
        POST /api/kiwisdr/frequencies/1/analyze-auto
        """
        try:
            # Récupérer les infos de la fréquence
            conn = db_manager.get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT frequency_khz, name FROM kiwisdr_monitored_frequencies 
                WHERE id = ? AND active = 1
            """, (frequency_id,))
            
            row = cur.fetchone()
            conn.close()
            
            if not row:
                return jsonify({
                    'success': False,
                    'error': 'Fréquence non trouvée'
                }), 404
            
            frequency_khz, name = row
            
            # Récupérer un serveur disponible
            servers_data = monitor.server_finder.get_active_servers()
            if not servers_data['servers']:
                return jsonify({
                    'success': False,
                    'error': 'Aucun serveur KiwiSDR disponible'
                }), 503
            
            server_url = servers_data['servers'][0]['url']
            
            # Lancer l'analyse automatique
            from .sdr_spectrum_analyzer import SpectrumAnalyzer
            analyzer = SpectrumAnalyzer(db_manager)
            result = analyzer.analyze_kiwisdr_spectrum(server_url, frequency_khz)
            
            return jsonify({
                'success': True,
                'frequency_id': frequency_id,
                'frequency_khz': frequency_khz,
                'name': name,
                'analysis': result,
                'server_used': server_url
            })
            
        except Exception as e:
            logger.error(f"❌ Erreur analyse automatique: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @kiwisdr_bp.route('/frequencies/<int:frequency_id>/start-monitoring', methods=['POST'])
    def start_auto_monitoring(frequency_id):
        """
        Démarre la surveillance automatique continue
        POST /api/kiwisdr/frequencies/1/start-monitoring
        Body: {"interval_minutes": 5}
        """
        try:
            data = request.get_json()
            interval = data.get('interval_minutes', 5)
            
            # Récupérer les infos de la fréquence
            conn = db_manager.get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT frequency_khz FROM kiwisdr_monitored_frequencies 
                WHERE id = ? AND active = 1
            """, (frequency_id,))
            
            row = cur.fetchone()
            conn.close()
            
            if not row:
                return jsonify({
                    'success': False,
                    'error': 'Fréquence non trouvée'
                }), 404
            
            frequency_khz = row[0]
            
            # Récupérer un serveur
            servers_data = monitor.server_finder.get_active_servers()
            if not servers_data['servers']:
                return jsonify({
                    'success': False,
                    'error': 'Aucun serveur disponible'
                }), 503
            
            server_url = servers_data['servers'][0]['url']
            
            # Démarrer la surveillance
            from .sdr_spectrum_analyzer import AutomatedSDRMonitor
            auto_monitor = AutomatedSDRMonitor(db_manager)
            success = auto_monitor.start_continuous_monitoring(
                frequency_id, server_url, frequency_khz, interval
            )
            
            if success:
                return jsonify({
                    'success': True,
                    'message': f'Surveillance automatique démarrée: {frequency_khz} kHz',
                    'interval_minutes': interval,
                    'server': server_url
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Surveillance déjà en cours'
                }), 400
                
        except Exception as e:
            logger.error(f"❌ Erreur démarrage surveillance: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @kiwisdr_bp.route('/frequencies/<int:frequency_id>/stop-monitoring', methods=['POST'])
    def stop_auto_monitoring(frequency_id):
        """
        Arrête la surveillance automatique
        POST /api/kiwisdr/frequencies/1/stop-monitoring
        """
        try:
            from .sdr_spectrum_analyzer import AutomatedSDRMonitor
            auto_monitor = AutomatedSDRMonitor(db_manager)
            success = auto_monitor.stop_continuous_monitoring(frequency_id)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Surveillance automatique arrêtée'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Aucune surveillance active trouvée'
                }), 404
                
        except Exception as e:
            logger.error(f"❌ Erreur arrêt surveillance: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    # Enregistrer le blueprint
    app.register_blueprint(kiwisdr_bp)
    
    logger.info("✅ Routes KiwiSDR enregistrées (version réaliste)")