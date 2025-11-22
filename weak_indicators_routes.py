# Flask/weak_indicators_routes.py - VERSION COMPLÈTEMENT CORRIGÉE
"""
Routes des indicateurs faibles avec RTL-SDR - CORRIGÉ
"""

from flask import Blueprint, jsonify, request, render_template
import logging
import numpy as np
from datetime import datetime, timedelta
import json
import subprocess

logger = logging.getLogger(__name__)

weak_indicators_bp = Blueprint('weak_indicators', __name__)

# Variable globale pour stocker db_manager
_db_manager = None

def register_weak_indicators_routes(app, db_manager):
    """Enregistre les routes des indicateurs faibles avec RTL-SDR"""
    global _db_manager
    _db_manager = db_manager
    
    # === ROUTES DE BASE ===
    
    @weak_indicators_bp.route('/')
    def weak_indicators_dashboard():
        """Page principale des indicateurs faibles"""
        return render_template('weak_indicators.html')
    
    @weak_indicators_bp.route('/api/status')
    def get_weak_indicators_status():
        """Statut du système d'indicateurs faibles"""
        try:
            return jsonify({
                "success": True,
                "system": "weak_indicators",
                "status": "active",
                "rtlsdr_available": check_rtlsdr_availability(),
                "last_analysis": datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.error(f"Erreur statut indicateurs: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    @weak_indicators_bp.route('/api/sdr-streams')
    def get_sdr_streams():
        """Retourne tous les flux SDR"""
        try:
            conn = _db_manager.get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT id, name, url, frequency_khz, type, description, active, created_at
                FROM sdr_streams 
                WHERE active = 1
                ORDER BY frequency_khz
            """)
            
            streams = []
            for row in cur.fetchall():
                streams.append({
                    "id": row[0],
                    "name": row[1],
                    "url": row[2],
                    "frequency_khz": row[3],
                    "type": row[4],
                    "description": row[5],
                    "active": bool(row[6]),
                    "created_at": row[7]
                })
            
            conn.close()
            return jsonify(streams)
            
        except Exception as e:
            logger.error(f"Erreur récupération flux SDR: {e}")
            return jsonify({"error": str(e)}), 500

    # === ROUTES RTL-SDR SPÉCIFIQUES ===
    
    @weak_indicators_bp.route('/api/sdr/rtlsdr/analyze', methods=['POST'])
    def analyze_rtlsdr_weak_indicators():
        """Analyse RTL-SDR pour indicateurs faibles"""
        try:
            data = request.get_json()
            frequency_khz = data.get('frequency_khz')
            duration_seconds = data.get('duration_seconds', 60)
            
            if not frequency_khz:
                return jsonify({"error": "frequency_khz requis"}), 400
            
            # Importer dynamiquement pour éviter les dépendances circulaires
            from .rtlsdr_manager import RTLSDRAnalyzer
            analyzer = RTLSDRAnalyzer(_db_manager)
            
            # Capturer les données
            waterfall_data = analyzer.capture_waterfall_data(
                frequency_khz, 
                duration_seconds
            )
            
            # Détecter les émissions
            emissions = analyzer.detect_emissions(frequency_khz)
            
            # Analyser les patterns d'indicateurs faibles
            analysis = analyze_weak_indicators_pattern(
                waterfall_data, 
                emissions, 
                frequency_khz
            )
            
            return jsonify({
                "success": True,
                "frequency_khz": frequency_khz,
                "analysis": analysis,
                "emissions_detected": len(emissions),
                "waterfall_available": True,
                "data_type": waterfall_data.get("type", "unknown")
            })
            
        except Exception as e:
            logger.error(f"Erreur analyse RTL-SDR indicateurs: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    @weak_indicators_bp.route('/api/sdr/rtlsdr/waterfall/embed')
    def get_rtlsdr_waterfall_embed():
        """Retourne le HTML pour embed le waterfall RTL-SDR"""
        frequency_khz = request.args.get('frequency_khz', 14300, type=int)
        width = request.args.get('width', 800, type=int)
        height = request.args.get('height', 400, type=int)
        
        html_content = f"""
        <div id="rtlsdr-waterfall-{frequency_khz}" class="rtlsdr-waterfall-container">
            <div class="waterfall-header">
                <h4>📡 RTL-SDR Waterfall - {frequency_khz} kHz</h4>
                <button onclick="loadRTLSDRAnalysis({frequency_khz})" 
                        class="btn-analysis">Analyser</button>
            </div>
            <div class="waterfall-visualization">
                <canvas id="waterfall-canvas-{frequency_khz}" 
                        width="{width}" height="{height}"></canvas>
            </div>
            <div class="waterfall-controls">
                <button onclick="startRTLSDRObservation({frequency_khz})">
                    🎯 Démarrer observation
                </button>
                <button onclick="captureRTLSDREmission({frequency_khz})">
                    📝 Capturer émission
                </button>
            </div>
        </div>
        <script>
            function loadRTLSDRAnalysis(freq) {{
                fetch('/api/sdr/rtlsdr/waterfall/' + freq)
                    .then(r => r.json())
                    .then(data => {{
                        if (data.success) {{
                            renderWaterfall('waterfall-canvas-' + freq, data.waterfall_data);
                        }}
                    }});
            }}
            
            function startRTLSDRObservation(freq) {{
                // Implémentation observation manuelle
                openManualObservationModal(freq, 'rtlsdr');
            }}
        </script>
        """
        
        return jsonify({
            "html": html_content,
            "frequency_khz": frequency_khz
        })

    @weak_indicators_bp.route('/api/sdr/rtlsdr/emissions')
    def get_rtlsdr_emissions():
        """Récupère les émissions RTL-SDR récentes"""
        try:
            frequency_khz = request.args.get('frequency_khz', 14300, type=int)
            hours = request.args.get('hours', 24, type=int)
            
            from .rtlsdr_manager import RTLSDRAnalyzer
            analyzer = RTLSDRAnalyzer(_db_manager)
            
            emissions = analyzer.detect_emissions(frequency_khz)
            
            # Filtrer par timestamp si nécessaire
            filtered_emissions = [
                {**emission, "timestamp": datetime.utcnow().isoformat()}
                for emission in emissions
            ]
            
            return jsonify({
                "success": True,
                "frequency_khz": frequency_khz,
                "emissions": filtered_emissions,
                "total": len(filtered_emissions)
            })
            
        except Exception as e:
            logger.error(f"Erreur récupération émissions: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    # === ROUTES DE SURVEILLANCE AUTOMATIQUE ===
    
    @weak_indicators_bp.route('/api/monitoring/start', methods=['POST'])
    def start_automatic_monitoring():
        """Démarre une surveillance automatique"""
        try:
            data = request.get_json()
            frequency_khz = data.get('frequency_khz')
            duration_minutes = data.get('duration_minutes', 60)
            
            if not frequency_khz:
                return jsonify({"error": "frequency_khz requis"}), 400
            
            # Démarrer la surveillance en arrière-plan
            monitoring_id = start_background_monitoring(
                frequency_khz, 
                duration_minutes, 
                _db_manager
            )
            
            return jsonify({
                "success": True,
                "monitoring_id": monitoring_id,
                "frequency_khz": frequency_khz,
                "duration_minutes": duration_minutes,
                "started_at": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Erreur démarrage surveillance: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    @weak_indicators_bp.route('/api/monitoring/status/<monitoring_id>')
    def get_monitoring_status(monitoring_id):
        """Statut d'une surveillance en cours"""
        try:
            status = get_monitoring_status_from_db(monitoring_id, _db_manager)
            return jsonify({
                "success": True,
                "monitoring_id": monitoring_id,
                "status": status
            })
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    # === ROUTES D'ANALYSE AVANCÉE ===
    
    @weak_indicators_bp.route('/api/analysis/patterns')
    def analyze_patterns():
        """Analyse les patterns d'indicateurs faibles sur plusieurs fréquences"""
        try:
            frequencies = request.args.get('frequencies', '14300,6998,121500')
            freq_list = [int(f.strip()) for f in frequencies.split(',')]
            
            patterns = {}
            from .rtlsdr_manager import RTLSDRAnalyzer
            analyzer = RTLSDRAnalyzer(_db_manager)
            
            for freq in freq_list:
                emissions = analyzer.detect_emissions(freq)
                waterfall_data = analyzer.capture_waterfall_data(freq, 30)
                
                patterns[freq] = {
                    "emissions_count": len(emissions),
                    "activity_level": calculate_activity_level(emissions),
                    "analysis": analyze_weak_indicators_pattern(waterfall_data, emissions, freq)
                }
            
            return jsonify({
                "success": True,
                "patterns": patterns,
                "frequencies_analyzed": freq_list
            })
            
        except Exception as e:
            logger.error(f"Erreur analyse patterns: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    # Enregistrer le blueprint
    app.register_blueprint(weak_indicators_bp, url_prefix='/weak-indicators')
    logger.info("✅ Routes indicateurs faibles enregistrées (avec RTL-SDR)")

# === FONCTIONS UTILITAIRES ===

def analyze_weak_indicators_pattern(waterfall_data, emissions, target_frequency):
    """Analyse les patterns d'indicateurs faibles"""
    
    analysis = {
        "anomalies": [],
        "activity_level": "low",
        "confidence": 0.0,
        "recommendations": []
    }
    
    if not waterfall_data or "waterfall" not in waterfall_data:
        analysis["anomalies"].append("Données waterfall indisponibles")
        return analysis
    
    try:
        waterfall = np.array(waterfall_data["waterfall"])
        
        # Calculer le niveau d'activité
        activity_score = np.mean(waterfall > -80)  # % de points au-dessus du seuil
        
        if activity_score > 0.3:
            analysis["activity_level"] = "high"
        elif activity_score > 0.1:
            analysis["activity_level"] = "medium"
        
        # Détecter les anomalies
        if len(emissions) > 10:
            analysis["anomalies"].append("Nombre élevé d'émissions détectées")
            analysis["recommendations"].append("Surveillance renforcée recommandée")
        
        # Vérifier la cohérence temporelle
        temporal_variance = np.var(waterfall, axis=0)
        high_variance_freqs = np.sum(temporal_variance > 100)
        
        if high_variance_freqs > 5:
            analysis["anomalies"].append("Variabilité temporelle élevée détectée")
        
        analysis["confidence"] = min(0.9, activity_score * 2)
        
    except Exception as e:
        analysis["anomalies"].append(f"Erreur analyse: {str(e)}")
    
    return analysis

def calculate_activity_level(emissions):
    """Calcule le niveau d'activité basé sur les émissions"""
    if not emissions:
        return "none"
    
    emission_count = len(emissions)
    avg_power = np.mean([e.get('power_db', -100) for e in emissions])
    
    if emission_count > 15 and avg_power > -70:
        return "very_high"
    elif emission_count > 10 and avg_power > -75:
        return "high"
    elif emission_count > 5 and avg_power > -80:
        return "medium"
    elif emission_count > 0:
        return "low"
    else:
        return "none"

def check_rtlsdr_availability():
    """Vérifie la disponibilité de RTL-SDR"""
    try:
        result = subprocess.run(['which', 'rtl_power'], 
                              capture_output=True, timeout=2)
        return result.returncode == 0
    except:
        return False

def start_background_monitoring(frequency_khz, duration_minutes, db_manager):
    """Démarre une surveillance en arrière-plan"""
    import threading
    import time
    
    def monitoring_thread():
        try:
            from .rtlsdr_manager import RTLSDRAnalyzer
            analyzer = RTLSDRAnalyzer(db_manager)
            
            end_time = time.time() + (duration_minutes * 60)
            scan_count = 0
            
            while time.time() < end_time:
                # Capturer les données
                waterfall_data = analyzer.capture_waterfall_data(frequency_khz, 30)
                emissions = analyzer.detect_emissions(frequency_khz)
                
                # Enregistrer dans la base
                save_monitoring_data(
                    frequency_khz, 
                    emissions, 
                    waterfall_data, 
                    db_manager
                )
                
                scan_count += 1
                time.sleep(300)  # 5 minutes entre les scans
                
            logger.info(f"✅ Surveillance terminée: {scan_count} scans effectués")
            
        except Exception as e:
            logger.error(f"Erreur surveillance: {e}")
    
    thread = threading.Thread(target=monitoring_thread, daemon=True)
    thread.start()
    
    return f"monitoring_{frequency_khz}_{int(time.time())}"

def save_monitoring_data(frequency_khz, emissions, waterfall_data, db_manager):
    """Sauvegarde les données de surveillance"""
    try:
        conn = db_manager.get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO weak_indicators_monitoring 
            (frequency_khz, emissions_count, activity_level, timestamp, analysis_data)
            VALUES (?, ?, ?, ?, ?)
        """, (
            frequency_khz,
            len(emissions),
            calculate_activity_level(emissions),
            datetime.utcnow().isoformat(),
            json.dumps({
                "emissions": emissions,
                "waterfall_type": waterfall_data.get("type", "unknown")
            })
        ))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.error(f"Erreur sauvegarde monitoring: {e}")

def get_monitoring_status_from_db(monitoring_id, db_manager):
    """Récupère le statut depuis la base de données"""
    try:
        conn = db_manager.get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT frequency_khz, emissions_count, activity_level, timestamp
            FROM weak_indicators_monitoring
            WHERE monitoring_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (monitoring_id,))
        
        row = cur.fetchone()
        conn.close()
        
        if row:
            return {
                "frequency_khz": row[0],
                "emissions_count": row[1],
                "activity_level": row[2],
                "last_update": row[3],
                "status": "active"
            }
        else:
            return {"status": "not_found"}
            
    except Exception as e:
        logger.error(f"Erreur récupération statut: {e}")
        return {"status": "error", "error": str(e)}

# === INITIALISATION DES TABLES ===

def init_weak_indicators_tables(db_manager):
    """Initialise les tables pour les indicateurs faibles"""
    conn = db_manager.get_connection()
    cur = conn.cursor()
    
    # Table de surveillance
    cur.execute("""
        CREATE TABLE IF NOT EXISTS weak_indicators_monitoring (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            monitoring_id TEXT,
            frequency_khz INTEGER NOT NULL,
            emissions_count INTEGER DEFAULT 0,
            activity_level TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            analysis_data TEXT
        )
    """)
    
    # Table des patterns détectés
    cur.execute("""
        CREATE TABLE IF NOT EXISTS weak_indicators_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            frequency_khz INTEGER NOT NULL,
            pattern_type TEXT,
            confidence REAL,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            details TEXT
        )
    """)
    
    conn.commit()
    conn.close()
    logger.info("✅ Tables indicateurs faibles initialisées")

def init_weak_indicators(db_manager):
    """Initialise le système d'indicateurs faibles"""
    init_weak_indicators_tables(db_manager)
    logger.info("✅ Système indicateurs faibles initialisé")