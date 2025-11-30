# Flask/sdr_surveillance_system.py
"""
Système de surveillance SDR optimisé pour GEOPOL Analytics
Détection de blackouts et pics d'activité sur fréquences géopolitiques
"""

import logging
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from dataclasses import dataclass
from enum import Enum
import json
import sqlite3

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    CRITICAL = "critical"

class AnomalyType(Enum):
    BLACKOUT = "blackout"
    PEAK_ACTIVITY = "peak_activity"
    SERVER_DROP = "server_drop"
    FREQUENCY_SURGE = "frequency_surge"

@dataclass
class SurveillanceConfig:
    """Configuration de surveillance"""
    # Seuils d'alertes
    blackout_threshold: float = 0.5  # 50% de serveurs perdus
    peak_threshold_std: float = 2.5  # 2.5 écarts-types
    min_observation_hours: int = 24
    correlation_window_hours: int = 6
    
    # Intervalles de surveillance
    kiwisdr_check_interval: int = 300  # 5 minutes
    frequency_scan_interval: int = 600  # 10 minutes
    
    # Seuils statistiques
    min_servers_alert: int = 3
    activity_baseline_days: int = 7

class SDRSurveillanceSystem:
    """
    Système principal de surveillance SDR
    Design pattern : Observer + Strategy pour gestion asynchrone
    """
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.config = SurveillanceConfig()
        self.alert_handlers = []
        self._init_database()
        
        # État du système
        self.kiwisdr_baseline = 0
        self.frequency_baselines = {}
        self.last_anomalies = []
        
    def _init_database(self):
        """Initialise les tables de surveillance"""
        conn = self.db_manager.get_connection()
        cur = conn.cursor()
        
        # Table d'alertes SDR
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sdr_anomaly_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                anomaly_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                description TEXT NOT NULL,
                confidence REAL DEFAULT 0.0,
                affected_servers TEXT,
                affected_frequencies TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                acknowledged BOOLEAN DEFAULT 0,
                correlation_id TEXT
            )
        """)
        
        # Table de métriques temporelles
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sdr_temporal_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_type TEXT NOT NULL,
                value REAL NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        """)
        
        # Table de corrélation d'événements
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sdr_event_correlations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                source TEXT NOT NULL,
                confidence REAL DEFAULT 0.0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                related_events TEXT
            )
        """)
        
        # Index pour performances
        cur.execute("CREATE INDEX IF NOT EXISTS idx_sdr_alerts_time ON sdr_anomaly_alerts(timestamp)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_sdr_metrics_time ON sdr_temporal_metrics(timestamp)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_sdr_metrics_type ON sdr_temporal_metrics(metric_type)")
        
        conn.commit()
        conn.close()
        
        logger.info("✅ Tables de surveillance SDR initialisées")

    async def start_continuous_monitoring(self):
        """Démarre la surveillance continue en arrière-plan"""
        logger.info("🚀 Démarrage surveillance SDR continue...")
        
        while True:
            try:
                await self._monitoring_cycle()
                await asyncio.sleep(self.config.kiwisdr_check_interval)
            except Exception as e:
                logger.error(f"❌ Erreur cycle surveillance: {e}")
                await asyncio.sleep(60)  # Attente en cas d'erreur

    async def _monitoring_cycle(self):
        """Exécute un cycle complet de surveillance"""
        tasks = [
            self._monitor_kiwisdr_network(),
            self._monitor_frequency_activity(),
            self._check_correlations()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log des résultats
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"❌ Tâche {i} échouée: {result}")

    async def _monitor_kiwisdr_network(self):
        """Surveillance du réseau KiwiSDR pour détecter les blackouts"""
        try:
            from .kiwisdr_realistic import KiwiSDRServerFinder
            finder = KiwiSDRServerFinder()
            
            server_data = finder.get_active_servers()
            
            if not server_data['success']:
                logger.warning("⚠️ Impossible de récupérer les serveurs KiwiSDR")
                return
            
            current_servers = server_data['total']
            
            # Calculer la baseline si nécessaire
            if self.kiwisdr_baseline == 0:
                self.kiwisdr_baseline = current_servers
                logger.info(f"📊 Baseline KiwiSDR établie: {current_servers} serveurs")
                return
            
            # Détection d'anomalie
            server_drop_ratio = (self.kiwisdr_baseline - current_servers) / self.kiwisdr_baseline
            
            if server_drop_ratio >= self.config.blackout_threshold:
                await self._trigger_alert(
                    anomaly_type=AnomalyType.BLACKOUT,
                    severity=AlertSeverity.CRITICAL,
                    description=f"Blackout détecté: {server_drop_ratio:.1%} de serveurs perdus",
                    confidence=min(0.9, server_drop_ratio),
                    affected_servers=current_servers
                )
            
            # Mise à jour adaptive de la baseline
            self.kiwisdr_baseline = 0.9 * self.kiwisdr_baseline + 0.1 * current_servers
            
            # Stocker la métrique
            self._store_temporal_metric(
                metric_type="kiwisdr_server_count",
                value=current_servers,
                metadata={"baseline": self.kiwisdr_baseline}
            )
            
        except Exception as e:
            logger.error(f"❌ Erreur surveillance KiwiSDR: {e}")

    async def _monitor_frequency_activity(self):
        """Surveillance de l'activité sur les fréquences cibles"""
        try:
            conn = self.db_manager.get_connection()
            cur = conn.cursor()
            
            # Récupérer les fréquences actives
            cur.execute("""
                SELECT id, frequency_khz, name 
                FROM kiwisdr_monitored_frequencies 
                WHERE active = 1
            """)
            
            frequencies = cur.fetchall()
            conn.close()
            
            for freq_id, freq_khz, name in frequencies:
                await self._analyze_frequency_activity(freq_id, freq_khz, name)
                
        except Exception as e:
            logger.error(f"❌ Erreur surveillance fréquences: {e}")

    async def _analyze_frequency_activity(self, freq_id: int, freq_khz: int, name: str):
        """Analyse l'activité d'une fréquence spécifique"""
        try:
            # Récupérer l'historique récent
            activity_data = self._get_frequency_activity(freq_id, hours=24)
            
            if len(activity_data) < 6:  # Minimum 6 heures de données
                return
            
            emissions = [data['emission_count'] for data in activity_data]
            timestamps = [data['timestamp'] for data in activity_data]
            
            # Calcul statistique
            current_activity = emissions[-1] if emissions else 0
            baseline = self._calculate_baseline(emissions[:-1])  # Exclure dernière heure
            
            # Détection de pic
            if self._detect_activity_peak(current_activity, baseline):
                await self._trigger_alert(
                    anomaly_type=AnomalyType.PEAK_ACTIVITY,
                    severity=AlertSeverity.HIGH,
                    description=f"Pic d'activité sur {name} ({freq_khz} kHz)",
                    confidence=0.8,
                    affected_frequencies=[freq_khz]
                )
            
            # Mise à jour de la baseline
            self._update_frequency_baseline(freq_id, current_activity)
            
        except Exception as e:
            logger.error(f"❌ Erreur analyse fréquence {freq_id}: {e}")

    def _get_frequency_activity(self, freq_id: int, hours: int = 24) -> List[Dict]:
        """Récupère l'activité d'une fréquence sur une période"""
        conn = self.db_manager.get_connection()
        cur = conn.cursor()
        
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        cur.execute("""
            SELECT emission_count, timestamp 
            FROM kiwisdr_frequency_activity 
            WHERE frequency_id = ? AND timestamp >= ?
            ORDER BY timestamp
        """, (freq_id, cutoff))
        
        activity = []
        for row in cur.fetchall():
            activity.append({
                'emission_count': row[0],
                'timestamp': row[1]
            })
        
        conn.close()
        return activity

    def _calculate_baseline(self, values: List[float]) -> Dict[str, float]:
        """Calcule la baseline statistique"""
        if not values:
            return {'mean': 0, 'std': 1}
        
        arr = np.array(values)
        return {
            'mean': float(np.mean(arr)),
            'std': float(np.std(arr)) if len(arr) > 1 else 1.0
        }

    def _detect_activity_peak(self, current: float, baseline: Dict[str, float]) -> bool:
        """Détecte un pic d'activité anormal"""
        if baseline['std'] == 0:
            return current > baseline['mean'] * 2  # Doublement si pas de variance
        
        z_score = (current - baseline['mean']) / baseline['std']
        return z_score > self.config.peak_threshold_std

    def _update_frequency_baseline(self, freq_id: int, current_value: float):
        """Met à jour la baseline d'une fréquence (moyenne mobile)"""
        if freq_id not in self.frequency_baselines:
            self.frequency_baselines[freq_id] = current_value
        else:
            # Moyenne mobile exponentielle
            alpha = 0.1  # Facteur de lissage
            self.frequency_baselines[freq_id] = (
                alpha * current_value + 
                (1 - alpha) * self.frequency_baselines[freq_id]
            )

    async def _check_correlations(self):
        """Vérifie les corrélations entre événements"""
        try:
            # Récupérer les alertes récentes
            recent_alerts = self._get_recent_alerts(hours=self.config.correlation_window_hours)
            
            if len(recent_alerts) < 2:
                return
            
            # Recherche de patterns
            blackout_alerts = [a for a in recent_alerts if a['anomaly_type'] == AnomalyType.BLACKOUT.value]
            peak_alerts = [a for a in recent_alerts if a['anomaly_type'] == AnomalyType.PEAK_ACTIVITY.value]
            
            # Alerte si blackout + pics simultanés
            if blackout_alerts and peak_alerts:
                await self._trigger_correlation_alert(blackout_alerts, peak_alerts)
                
        except Exception as e:
            logger.error(f"❌ Erreur corrélation: {e}")

    async def _trigger_alert(self, anomaly_type: AnomalyType, severity: AlertSeverity,
                           description: str, confidence: float = 0.0, 
                           affected_servers: Any = None, affected_frequencies: Any = None):
        """Déclenche une alerte d'anomalie"""
        try:
            conn = self.db_manager.get_connection()
            cur = conn.cursor()
            
            correlation_id = f"{anomaly_type.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M')}"
            
            cur.execute("""
                INSERT INTO sdr_anomaly_alerts 
                (anomaly_type, severity, description, confidence, 
                 affected_servers, affected_frequencies, correlation_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                anomaly_type.value,
                severity.value,
                description,
                confidence,
                json.dumps(affected_servers) if affected_servers else None,
                json.dumps(affected_frequencies) if affected_frequencies else None,
                correlation_id
            ))
            
            conn.commit()
            conn.close()
            
            logger.warning(f"🚨 ALERTE {severity.value}: {description}")
            
            # Notification aux handlers
            for handler in self.alert_handlers:
                try:
                    handler.handle_alert({
                        'type': anomaly_type.value,
                        'severity': severity.value,
                        'description': description,
                        'confidence': confidence,
                        'timestamp': datetime.utcnow().isoformat()
                    })
                except Exception as e:
                    logger.error(f"❌ Erreur handler alerte: {e}")
                    
        except Exception as e:
            logger.error(f"❌ Erreur déclenchement alerte: {e}")

    async def _trigger_correlation_alert(self, blackout_alerts: List, peak_alerts: List):
        """Déclenche une alerte de corrélation"""
        description = (
            f"Corrélation détectée: {len(blackout_alerts)} blackout(s) "
            f"et {len(peak_alerts)} pic(s) d'activité dans la même fenêtre temporelle"
        )
        
        await self._trigger_alert(
            anomaly_type=AnomalyType.SERVER_DROP,
            severity=AlertSeverity.HIGH,
            description=description,
            confidence=0.7,
            affected_servers=len(blackout_alerts),
            affected_frequencies=[alert.get('affected_frequencies') for alert in peak_alerts]
        )

    def _store_temporal_metric(self, metric_type: str, value: float, metadata: Dict = None):
        """Stocke une métrique temporelle"""
        conn = self.db_manager.get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO sdr_temporal_metrics (metric_type, value, metadata)
            VALUES (?, ?, ?)
        """, (metric_type, value, json.dumps(metadata) if metadata else None))
        
        conn.commit()
        conn.close()

    def _get_recent_alerts(self, hours: int = 24) -> List[Dict]:
        """Récupère les alertes récentes"""
        conn = self.db_manager.get_connection()
        cur = conn.cursor()
        
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        cur.execute("""
            SELECT anomaly_type, severity, description, confidence, 
                   affected_servers, affected_frequencies, timestamp
            FROM sdr_anomaly_alerts
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
        """, (cutoff,))
        
        alerts = []
        for row in cur.fetchall():
            alerts.append({
                'anomaly_type': row[0],
                'severity': row[1],
                'description': row[2],
                'confidence': row[3],
                'affected_servers': row[4],
                'affected_frequencies': row[5],
                'timestamp': row[6]
            })
        
        conn.close()
        return alerts

    # === API pour le frontend ===
    
    def get_surveillance_dashboard(self) -> Dict[str, Any]:
        """Données pour le dashboard de surveillance"""
        try:
            # Alertes récentes (24h)
            recent_alerts = self._get_recent_alerts(hours=24)
            
            # Métriques KiwiSDR
            conn = self.db_manager.get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT value, timestamp 
                FROM sdr_temporal_metrics 
                WHERE metric_type = 'kiwisdr_server_count' 
                AND timestamp >= datetime('now', '-7 days')
                ORDER BY timestamp
            """)
            
            server_metrics = []
            for row in cur.fetchall():
                server_metrics.append({
                    'value': row[0],
                    'timestamp': row[1]
                })
            
            # Statistiques d'activité
            cur.execute("""
                SELECT COUNT(*) as total_alerts,
                       SUM(CASE WHEN severity = 'critical' THEN 1 ELSE 0 END) as critical_alerts,
                       SUM(CASE WHEN anomaly_type = 'blackout' THEN 1 ELSE 0 END) as blackout_alerts
                FROM sdr_anomaly_alerts 
                WHERE timestamp >= datetime('now', '-24 hours')
            """)
            
            stats_row = cur.fetchone()
            conn.close()
            
            return {
                'success': True,
                'current_servers': self.kiwisdr_baseline,
                'recent_alerts': recent_alerts[:10],  # 10 plus récentes
                'server_metrics': server_metrics,
                'alert_stats': {
                    'total_24h': stats_row[0] if stats_row else 0,
                    'critical_24h': stats_row[1] if stats_row else 0,
                    'blackout_24h': stats_row[2] if stats_row else 0
                },
                'frequency_baselines': self.frequency_baselines,
                'last_update': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur dashboard surveillance: {e}")
            return {'success': False, 'error': str(e)}

    def get_anomaly_statistics(self, days: int = 7) -> Dict[str, Any]:
        """Statistiques des anomalies sur une période"""
        try:
            conn = self.db_manager.get_connection()
            cur = conn.cursor()
            
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            # Distribution par type et sévérité
            cur.execute("""
                SELECT anomaly_type, severity, COUNT(*) as count
                FROM sdr_anomaly_alerts
                WHERE timestamp >= ?
                GROUP BY anomaly_type, severity
                ORDER BY count DESC
            """, (cutoff,))
            
            distribution = []
            for row in cur.fetchall():
                distribution.append({
                    'type': row[0],
                    'severity': row[1],
                    'count': row[2]
                })
            
            # Tendances temporelles
            cur.execute("""
                SELECT DATE(timestamp) as date, 
                       COUNT(*) as alert_count,
                       AVG(confidence) as avg_confidence
                FROM sdr_anomaly_alerts
                WHERE timestamp >= ?
                GROUP BY DATE(timestamp)
                ORDER BY date
            """, (cutoff,))
            
            trends = []
            for row in cur.fetchall():
                trends.append({
                    'date': row[0],
                    'alert_count': row[1],
                    'avg_confidence': float(row[2]) if row[2] else 0
                })
            
            conn.close()
            
            return {
                'success': True,
                'distribution': distribution,
                'trends': trends,
                'period_days': days
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur statistiques anomalies: {e}")
            return {'success': False, 'error': str(e)}

# === Routes API ===

def create_sdr_surveillance_routes(app, db_manager):
    """Crée les routes API pour la surveillance SDR"""
    
    surveillance_system = SDRSurveillanceSystem(db_manager)
    
    @app.route('/api/sdr-surveillance/dashboard', methods=['GET'])
    def get_sdr_surveillance_dashboard():
        """Dashboard de surveillance SDR"""
        return jsonify(surveillance_system.get_surveillance_dashboard())
    
    @app.route('/api/sdr-surveillance/statistics')
    def get_sdr_anomaly_statistics():
        """Statistiques des anomalies SDR"""
        days = request.args.get('days', 7, type=int)
        return jsonify(surveillance_system.get_anomaly_statistics(days))
    
    @app.route('/api/sdr-surveillance/alerts/recent')
    def get_recent_sdr_alerts():
        """Alertes SDR récentes"""
        hours = request.args.get('hours', 24, type=int)
        alerts = surveillance_system._get_recent_alerts(hours)
        return jsonify({
            'success': True,
            'alerts': alerts,
            'total': len(alerts)
        })
    
    @app.route('/api/sdr-surveillance/start', methods=['POST'])
    def start_sdr_surveillance():
        """Démarre la surveillance SDR en arrière-plan"""
        try:
            # Démarrer dans un thread séparé
            import threading
            def run_surveillance():
                asyncio.run(surveillance_system.start_continuous_monitoring())
            
            thread = threading.Thread(target=run_surveillance, daemon=True)
            thread.start()
            
            return jsonify({
                'success': True,
                'message': 'Surveillance SDR démarrée',
                'thread_alive': thread.is_alive()
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    logger.info("✅ Routes surveillance SDR créées")
    return surveillance_system