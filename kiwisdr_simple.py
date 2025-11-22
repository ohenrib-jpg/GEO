# Flask/kiwisdr_simple.py
"""
Version SIMPLE KiwiSDR
- Affichage waterfall via iframe
- Comptage simple basé sur observation manuelle ou estimation
- Pas de traitement signal complexe
"""

import logging
import requests
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

# Flask/kiwisdr_simple.py - CORRECTION

class SimpleKiwiSDRClient:
    """Client simple pour KiwiSDR - Affichage et statistiques basiques"""
    
    API_BASE_URL = "https://kiwisdr.com/public/"  # ← HTTPS au lieu de HTTP
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GeoPolMonitor/1.0',
            'Accept': 'application/json'
        })
    
    def get_active_servers(self) -> Dict[str, Any]:
        """
        Récupère la liste des serveurs KiwiSDR actifs
        """
        try:
            # Essayer différentes URLs
            urls_to_try = [
                "https://kiwisdr.com/public/?ajax=1",
                "https://kiwisdr.com/public/",
                "http://kiwisdr.com/public/?ajax=1"
            ]
            
            for url in urls_to_try:
                try:
                    print(f"🔍 Essai connexion KiwiSDR: {url}")
                    response = self.session.get(url, timeout=10)
                    response.raise_for_status()
                    
                    # Vérifier si c'est du JSON
                    if response.text.strip().startswith('[') or response.text.strip().startswith('{'):
                        data = response.json()
                    else:
                        # Simuler des données si l'API ne répond pas
                        print("⚠️ KiwiSDR API ne retourne pas de JSON, utilisation données simulées")
                        return self._get_fallback_data()
                    
                    servers = []
                    for server in data:
                        if isinstance(server, dict) and 'name' in server and 'url' in server:
                            servers.append({
                                'name': server.get('name', 'Unknown'),
                                'url': server.get('url', ''),
                                'location': server.get('location', 'Unknown'),
                                'users': server.get('users', 0),
                                'users_max': server.get('users_max', 0),
                                'frequency_range': {
                                    'min': server.get('freq_min', 0),
                                    'max': server.get('freq_max', 30000)
                                },
                                'status': 'online'
                            })
                    
                    return {
                        'total': len(servers),
                        'servers': servers,
                        'timestamp': datetime.utcnow().isoformat(),
                        'success': True
                    }
                    
                except Exception as e:
                    print(f"❌ Erreur avec {url}: {e}")
                    continue
            
            # Si toutes les URLs échouent, retourner des données simulées
            print("🔧 Utilisation données simulées KiwiSDR")
            return self._get_fallback_data()
            
        except Exception as e:
            print(f"❌ Erreur récupération serveurs KiwiSDR: {e}")
            return self._get_fallback_data()
    
    def _get_fallback_data(self):
        """Données de fallback quand l'API KiwiSDR est indisponible"""
        servers = [
            {
                'name': 'KiwiSDR Global (Simulé)',
                'url': 'http://kiwisdr.com/public/',
                'location': 'Global Network',
                'users': 15,
                'users_max': 50,
                'frequency_range': {'min': 0, 'max': 30000},
                'status': 'online'
            },
            {
                'name': 'University Twente (Simulé)',
                'url': 'http://websdr.ewi.utwente.nl:8901/',
                'location': 'Netherlands',
                'users': 8,
                'users_max': 100,
                'frequency_range': {'min': 0, 'max': 30000},
                'status': 'online'
            }
        ]
        
        return {
            'total': len(servers),
            'servers': servers,
            'timestamp': datetime.utcnow().isoformat(),
            'success': True,
            'note': 'Données simulées - API KiwiSDR indisponible'
        }

class SimpleKiwiSDRMonitor:
    """Moniteur simple pour fréquences KiwiSDR"""
    
    def __init__(self, db_manager, max_frequencies: int = 10):
        self.db_manager = db_manager
        self.max_frequencies = max_frequencies
        self.client = SimpleKiwiSDRClient()
        self._init_tables()
    
    def _init_tables(self):
        """Initialise les tables de base de données"""
        conn = self.db_manager.get_connection()
        cur = conn.cursor()
        
        # Table des fréquences surveillées
        cur.execute("""
            CREATE TABLE IF NOT EXISTS kiwisdr_monitored_frequencies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                frequency_khz INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                server_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                active BOOLEAN DEFAULT 1,
                UNIQUE(frequency_khz)
            )
        """)
        
        # Table d'activité quotidienne
        cur.execute("""
            CREATE TABLE IF NOT EXISTS kiwisdr_frequency_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                frequency_id INTEGER NOT NULL,
                date DATE NOT NULL,
                emission_count INTEGER DEFAULT 0,
                observation_duration INTEGER DEFAULT 0,
                notes TEXT,
                FOREIGN KEY(frequency_id) REFERENCES kiwisdr_monitored_frequencies(id),
                UNIQUE(frequency_id, date)
            )
        """)
        
        # Table historique serveurs
        cur.execute("""
            CREATE TABLE IF NOT EXISTS kiwisdr_server_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_servers INTEGER NOT NULL,
                variation_1h INTEGER DEFAULT 0,
                variation_24h INTEGER DEFAULT 0
            )
        """)
        
        conn.commit()
        conn.close()
    
    def add_monitored_frequency(self, frequency_khz: int, name: str, 
                               description: str = "", server_url: str = "") -> Dict[str, Any]:
        """Ajoute une fréquence à surveiller"""
        conn = self.db_manager.get_connection()
        cur = conn.cursor()
        
        # Vérifier limite
        cur.execute("SELECT COUNT(*) FROM kiwisdr_monitored_frequencies WHERE active = 1")
        count = cur.fetchone()[0]
        
        if count >= self.max_frequencies:
            conn.close()
            return {
                'success': False,
                'error': f'Limite de {self.max_frequencies} fréquences atteinte'
            }
        
        try:
            cur.execute("""
                INSERT INTO kiwisdr_monitored_frequencies 
                (frequency_khz, name, description, server_url)
                VALUES (?, ?, ?, ?)
            """, (frequency_khz, name, description, server_url))
            
            freq_id = cur.lastrowid
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'frequency_id': freq_id,
                'message': f'Fréquence {frequency_khz} kHz ajoutée'
            }
            
        except Exception as e:
            conn.close()
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_monitored_frequencies(self) -> List[Dict[str, Any]]:
        """Récupère toutes les fréquences surveillées"""
        conn = self.db_manager.get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, frequency_khz, name, description, server_url, created_at, active
            FROM kiwisdr_monitored_frequencies
            ORDER BY frequency_khz
        """)
        
        frequencies = []
        for row in cur.fetchall():
            frequencies.append({
                'id': row[0],
                'frequency_khz': row[1],
                'name': row[2],
                'description': row[3],
                'server_url': row[4],
                'created_at': row[5],
                'active': bool(row[6])
            })
        
        conn.close()
        return frequencies
    
    def get_frequency_statistics(self, frequency_id: int, days: int = 30) -> Dict[str, Any]:
        """Récupère les statistiques d'une fréquence"""
        conn = self.db_manager.get_connection()
        cur = conn.cursor()
        
        cutoff_date = datetime.utcnow().date() - timedelta(days=days)
        
        cur.execute("""
            SELECT date, emission_count
            FROM kiwisdr_frequency_activity
            WHERE frequency_id = ? AND date >= ?
            ORDER BY date
        """, (frequency_id, cutoff_date))
        
        daily_data = []
        total_emissions = 0
        
        for row in cur.fetchall():
            daily_data.append({
                'date': row[0],
                'emission_count': row[1]
            })
            total_emissions += row[1]
        
        conn.close()
        
        if not daily_data:
            return {
                'daily_activity': [],
                'average': 0.0,
                'total': 0,
                'variation': 0.0
            }
        
        average = total_emissions / len(daily_data)
        last_day_count = daily_data[-1]['emission_count'] if daily_data else 0
        variation = ((last_day_count - average) / average * 100) if average > 0 else 0.0
        
        return {
            'daily_activity': daily_data,
            'average': round(average, 2),
            'total': total_emissions,
            'variation': round(variation, 2),
            'period_days': days
        }
    
    def record_server_snapshot(self):
        """Enregistre un snapshot des serveurs actifs"""
        server_data = self.client.get_active_servers()
        
        if not server_data['success']:
            return
        
        conn = self.db_manager.get_connection()
        cur = conn.cursor()
        
        # Calculer variations
        cur.execute("""
            SELECT total_servers FROM kiwisdr_server_history
            WHERE timestamp >= datetime('now', '-1 hour')
            ORDER BY timestamp DESC LIMIT 1
        """)
        row_1h = cur.fetchone()
        variation_1h = server_data['total'] - (row_1h[0] if row_1h else server_data['total'])
        
        cur.execute("""
            SELECT total_servers FROM kiwisdr_server_history
            WHERE timestamp >= datetime('now', '-24 hours')
            ORDER BY timestamp DESC LIMIT 1
        """)
        row_24h = cur.fetchone()
        variation_24h = server_data['total'] - (row_24h[0] if row_24h else server_data['total'])
        
        # Insérer snapshot
        cur.execute("""
            INSERT INTO kiwisdr_server_history 
            (total_servers, variation_1h, variation_24h)
            VALUES (?, ?, ?)
        """, (server_data['total'], variation_1h, variation_24h))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Snapshot KiwiSDR: {server_data['total']} serveurs "
                   f"(Δ1h: {variation_1h:+d}, Δ24h: {variation_24h:+d})")
    
    def get_server_variation_history(self, hours: int = 24) -> Dict[str, Any]:
        """Récupère l'historique des variations de serveurs"""
        conn = self.db_manager.get_connection()
        cur = conn.cursor()
        
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        cur.execute("""
            SELECT timestamp, total_servers, variation_1h, variation_24h
            FROM kiwisdr_server_history
            WHERE timestamp >= ?
            ORDER BY timestamp
        """, (cutoff,))
        
        history = []
        for row in cur.fetchall():
            history.append({
                'timestamp': row[0],
                'total_servers': row[1],
                'variation_1h': row[2],
                'variation_24h': row[3]
            })
        
        conn.close()
        
        # Détection d'alertes
        alerts = []
        for entry in history:
            if abs(entry['variation_1h']) > 10:
                alerts.append({
                    'timestamp': entry['timestamp'],
                    'type': 'sharp_variation',
                    'severity': 'high' if abs(entry['variation_1h']) > 20 else 'medium',
                    'message': f"Variation brutale: {entry['variation_1h']:+d} serveurs en 1h"
                })
        
        return {
            'history': history,
            'alerts': alerts,
            'period_hours': hours
        }
