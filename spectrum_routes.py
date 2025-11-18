# Flask/spectrum_routes.py
"""
Routes API pour le monitoring automatique du spectre
"""

from flask import Blueprint, jsonify, request
import logging
from datetime import datetime
import threading

logger = logging.getLogger(__name__)

spectrum_bp = Blueprint('spectrum', __name__, url_prefix='/api/spectrum')

# Stockage des tâches de monitoring actives
active_monitors = {}


def register_spectrum_routes(app, db_manager):
    """Enregistre les routes de monitoring automatique"""
    
    from .spectrum_analyzer import (
        AutomatedSpectrumMonitor, 
        simulate_spectrum_data,
        SpectrumAnalyzer
    )
    
    monitor = AutomatedSpectrumMonitor(db_manager)
    analyzer = SpectrumAnalyzer(db_manager)
    
    @spectrum_bp.route('/sources', methods=['GET'])
    def get_available_sources():
        """
        Retourne les sources de données disponibles
        GET /api/spectrum/sources
        """
        try:
            sources = monitor.get_available_sources()
            
            return jsonify({
                'success': True,
                'sources': sources,
                'recommendations': {
                    'rtlsdr': 'Meilleure qualité, local, temps réel',
                    'websdr': 'Disponible partout, partagé, limité'
                }
            })
        except Exception as e:
            logger.error(f"Erreur sources: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @spectrum_bp.route('/analyze', methods=['POST'])
    def analyze_spectrum():
        """
        Analyse un spectre et détecte les pics
        POST /api/spectrum/analyze
        Body: {
            "frequency_khz": 14300,
            "span_khz": 10,
            "threshold_db": -80,
            "source": "websdr" | "rtlsdr" | "simulate"
        }
        """
        try:
            data = request.get_json()
            
            frequency_khz = data.get('frequency_khz')
            span_khz = data.get('span_khz', 10)
            threshold_db = data.get('threshold_db', -80)
            source = data.get('source', 'websdr')
            
            if not frequency_khz:
                return jsonify({
                    'success': False,
                    'error': 'frequency_khz requis'
                }), 400
            
            # Récupérer les données spectrales
            if source == 'simulate':
                logger.info("📊 Utilisation données simulées")
                frequencies, power_spectrum = simulate_spectrum_data(
                    frequency_khz, 
                    span_khz
                )
            else:
                spectrum_data = monitor._get_spectrum_data(
                    frequency_khz, 
                    span_khz
                )
                
                if spectrum_data is None:
                    return jsonify({
                        'success': False,
                        'error': 'Impossible de récupérer le spectre'
                    }), 503
                
                frequencies, power_spectrum = spectrum_data
            
            # Détecter les pics
            peaks = analyzer.detect_peaks_in_spectrum(
                frequencies,
                power_spectrum,
                threshold_db=threshold_db,
                min_distance=1.0
            )
            
            return jsonify({
                'success': True,
                'frequency_khz': frequency_khz,
                'span_khz': span_khz,
                'threshold_db': threshold_db,
                'source': source,
                'peaks_detected': len(peaks),
                'peaks': peaks[:20],  # Limiter à 20 pics max
                'spectrum': {
                    'frequencies': frequencies.tolist()[:100],  # Échantillonner
                    'powers': power_spectrum.tolist()[:100],
                    'note': 'Spectre échantillonné pour limiter la taille'
                },
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Erreur analyse: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @spectrum_bp.route('/monitor/start', methods=['POST'])
    def start_monitoring():
        """
        Démarre un monitoring automatique sur une fréquence
        POST /api/spectrum/monitor/start
        Body: {
            "frequency_id": 1,
            "frequency_khz": 14300,
            "duration_minutes": 60,
            "scan_interval_seconds": 300
        }
        """
        try:
            data = request.get_json()
            
            frequency_id = data.get('frequency_id')
            frequency_khz = data.get('frequency_khz')
            duration_minutes = data.get('duration_minutes', 60)
            scan_interval_seconds = data.get('scan_interval_seconds', 300)
            
            if not frequency_id or not frequency_khz:
                return jsonify({
                    'success': False,
                    'error': 'frequency_id et frequency_khz requis'
                }), 400
            
            # Vérifier si déjà en cours
            if frequency_id in active_monitors:
                return jsonify({
                    'success': False,
                    'error': 'Monitoring déjà actif sur cette fréquence'
                }), 409
            
            # Démarrer le monitoring dans un thread séparé
            def run_monitor():
                try:
                    result = monitor.monitor_frequency(
                        frequency_id,
                        frequency_khz,
                        duration_minutes,
                        scan_interval_seconds
                    )
                    
                    logger.info(f"✅ Monitoring terminé: {result['total_peaks_detected']} pics")
                    
                except Exception as e:
                    logger.error(f"Erreur monitoring thread: {e}")
                finally:
                    # Retirer de la liste des actifs
                    if frequency_id in active_monitors:
                        del active_monitors[frequency_id]
            
            thread = threading.Thread(target=run_monitor, daemon=True)
            thread.start()
            
            # Enregistrer comme actif
            active_monitors[frequency_id] = {
                'thread': thread,
                'frequency_khz': frequency_khz,
                'started_at': datetime.utcnow().isoformat(),
                'duration_minutes': duration_minutes
            }
            
            return jsonify({
                'success': True,
                'message': 'Monitoring démarré en arrière-plan',
                'frequency_id': frequency_id,
                'frequency_khz': frequency_khz,
                'duration_minutes': duration_minutes,
                'scan_interval_seconds': scan_interval_seconds,
                'estimated_end': datetime.utcnow().isoformat()
            }), 202  # Accepted
            
        except Exception as e:
            logger.error(f"Erreur démarrage monitoring: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @spectrum_bp.route('/monitor/status', methods=['GET'])
    def get_monitoring_status():
        """
        État des monitorings actifs
        GET /api/spectrum/monitor/status
        """
        try:
            statuses = []
            
            for freq_id, info in active_monitors.items():
                statuses.append({
                    'frequency_id': freq_id,
                    'frequency_khz': info['frequency_khz'],
                    'started_at': info['started_at'],
                    'duration_minutes': info['duration_minutes'],
                    'status': 'running' if info['thread'].is_alive() else 'completed'
                })
            
            return jsonify({
                'success': True,
                'active_monitors': len([s for s in statuses if s['status'] == 'running']),
                'monitors': statuses
            })
            
        except Exception as e:
            logger.error(f"Erreur statut monitoring: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @spectrum_bp.route('/monitor/stop/<int:frequency_id>', methods=['POST'])
    def stop_monitoring(frequency_id):
        """
        Arrête un monitoring en cours
        POST /api/spectrum/monitor/stop/1
        """
        try:
            if frequency_id not in active_monitors:
                return jsonify({
                    'success': False,
                    'error': 'Aucun monitoring actif sur cette fréquence'
                }), 404
            
            # Note: On ne peut pas vraiment arrêter proprement un thread Python
            # On retire juste de la liste des actifs
            del active_monitors[frequency_id]
            
            return jsonify({
                'success': True,
                'message': 'Monitoring arrêté',
                'note': 'Le scan en cours se terminera naturellement'
            })
            
        except Exception as e:
            logger.error(f"Erreur arrêt monitoring: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @spectrum_bp.route('/test', methods=['GET'])
    def test_spectrum_analysis():
        """
        Test du système d'analyse avec données simulées
        GET /api/spectrum/test?frequency_khz=14300
        """
        try:
            frequency_khz = request.args.get('frequency_khz', 14300, type=int)
            
            # Générer données simulées
            logger.info(f"🧪 Test avec données simulées à {frequency_khz} kHz")
            
            frequencies, power_spectrum = simulate_spectrum_data(
                frequency_khz,
                span_khz=10,
                num_emissions=5
            )
            
            # Détecter les pics
            peaks = analyzer.detect_peaks_in_spectrum(
                frequencies,
                power_spectrum,
                threshold_db=-80,
                min_distance=1.0
            )
            
            return jsonify({
                'success': True,
                'test_mode': True,
                'frequency_khz': frequency_khz,
                'peaks_detected': len(peaks),
                'peaks': peaks,
                'spectrum_sample': {
                    'frequencies': frequencies[::10].tolist(),  # 1 point sur 10
                    'powers': power_spectrum[::10].tolist()
                },
                'message': 'Données simulées - Vérifiez que des pics sont détectés'
            })
            
        except Exception as e:
            logger.error(f"Erreur test: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # Enregistrer le blueprint
    app.register_blueprint(spectrum_bp)
    
    logger.info("✅ Routes monitoring automatique enregistrées")
