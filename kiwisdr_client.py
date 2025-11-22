# Flask/kiwisdr_client.py
"""
Client pour interagir avec l'API KiwiSDR
- Récupération de la liste des serveurs actifs
- Surveillance des variations du nombre de serveurs
- Détection d'activité sur des fréquences spécifiques
"""

import requests
import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import time

logger = logging.getLogger(__name__)

class KiwiSDRClient:
    """Client pour l'API KiwiSDR"""
    
    # URL de l'API publique KiwiSDR
    API_BASE_URL = "http://kiwisdr.com/public/"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GeoPolMonitor/1.0'
        })
    
    def get_active_servers(self) -> Dict[str, Any]:
        """
        Récupère la liste des serveurs KiwiSDR actifs
        
        Returns:
            Dict contenant:
                - total: nombre total de serveurs
                - servers: liste des serveurs avec détails
                - timestamp: horodatage de la requête
        """
        try:
            response = self.session.get(f"{self.API_BASE_URL}?ajax", timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            servers = []
            for server in data:
                # Filtrer les serveurs avec informations valides
                if 'name' in server and 'url' in server:
                    servers.append({
                        'name': server.get('name', 'Unknown'),
                        'url': server.get('url', ''),
                        'location': server.get('location', 'Unknown'),
                        'antenna': server.get('antenna', 'Unknown'),
                        'users': server.get('users', 0),
                        'users_max': server.get('users_max', 0),
                        'frequency_range': {
                            'min': server.get('freq_min', 0),
                            'max': server.get('freq_max', 30000)
                        },
                        'status': 'online' if server.get('status', 0) == 0 else 'offline',
                        'last_seen': datetime.utcnow().isoformat()
                    })
            
            return {
                'total': len(servers),
                'servers': servers,
                'timestamp': datetime.utcnow().isoformat(),
                'success': True
            }
            
        except requests.RequestException as e:
            logger.error(f"Erreur récupération serveurs KiwiSDR: {e}")
            return {
                'total': 0,
                'servers': [],
                'timestamp': datetime.utcnow().isoformat(),
                'success': False,
                'error': str(e)
            }
    
    def get_waterfall_data(self, server_url: str, frequency: int, zoom: int = 0) -> Optional[Dict]:
        """
        Récupère les données du waterfall pour une fréquence donnée
        
        Args:
            server_url: URL du serveur KiwiSDR
            frequency: Fréquence en kHz
            zoom: Niveau de zoom (0-14)
            
        Returns:
            Données spectrales brutes ou None en cas d'erreur
        """
        try:
            # Construction de l'URL WebSocket (simplifié pour HTTP)
            ws_url = f"{server_url}/kiwi/{frequency}/{zoom}"
            
            response = self.session.get(ws_url, timeout=5)
            
            if response.status_code == 200:
                return {
                    'frequency': frequency,
                    'data': response.content,
                    'timestamp': datetime.utcnow().isoformat(),
                    'server': server_url
                }
            
            return None
            
        except Exception as e:
            logger.warning(f"Erreur waterfall {server_url} @ {frequency}kHz: {e}")
            return None
    
    def detect_frequency_activity(self, server_url: str, frequency: int, 
                                  threshold: float = 0.5, duration: int = 60) -> Dict[str, Any]:
        """
        Détecte l'activité sur une fréquence donnée
        
        Args:
            server_url: URL du serveur KiwiSDR
            frequency: Fréquence à surveiller (kHz)
            threshold: Seuil de détection (0-1)
            duration: Durée d'observation (secondes)
            
        Returns:
            Statistiques d'activité détectée
        """
        activity_count = 0
        peak_strength = 0.0
        observations = 0
        
        start_time = time.time()
        
        try:
            # Simulation de détection (à remplacer par vraie analyse spectrale)
            # En production, il faudrait utiliser WebSocket pour recevoir les données
            while time.time() - start_time < duration:
                # Ici on devrait analyser les données du waterfall
                # Pour l'instant, on simule une détection
                
                # Dans une vraie implémentation:
                # 1. Se connecter au WebSocket du serveur
                # 2. Recevoir les données spectrales
                # 3. Analyser les pics d'amplitude
                # 4. Compter les dépassements du seuil
                
                observations += 1
                time.sleep(1)
            
            return {
                'frequency': frequency,
                'server': server_url,
                'activity_count': activity_count,
                'peak_strength': peak_strength,
                'observations': observations,
                'duration': duration,
                'timestamp': datetime.utcnow().isoformat(),
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Erreur détection activité: {e}")
            return {
                'frequency': frequency,
                'server': server_url,
                'activity_count': 0,
                'success': False,
                'error': str(e)
            }
    
    def get_server_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """
        Calcule les statistiques sur les serveurs actifs
        
        Args:
            hours: Nombre d'heures pour l'analyse historique
            
        Returns:
            Statistiques agrégées
        """
        current_data = self.get_active_servers()
        
        if not current_data['success']:
            return current_data
        
        return {
            'current_total': current_data['total'],
            'servers_by_region': self._count_by_region(current_data['servers']),
            'total_users': sum(s['users'] for s in current_data['servers']),
            'average_load': self._calculate_average_load(current_data['servers']),
            'timestamp': current_data['timestamp']
        }
    
    def _count_by_region(self, servers: List[Dict]) -> Dict[str, int]:
        """Compte les serveurs par région"""
        regions = {}
        for server in servers:
            location = server.get('location', 'Unknown')
            # Extraction simplifiée du pays/région
            region = location.split(',')[-1].strip() if ',' in location else location
            regions[region] = regions.get(region, 0) + 1
        return regions
    
    def _calculate_average_load(self, servers: List[Dict]) -> float:
        """Calcule la charge moyenne des serveurs"""
        if not servers:
            return 0.0
        
        loads = []
        for server in servers:
            users = server.get('users', 0)
            users_max = server.get('users_max', 1)
            if users_max > 0:
                loads.append(users / users_max)
        
        return sum(loads) / len(loads) if loads else 0.0


class KiwiSDRFrequencyMonitor:
    """
    Moniteur de fréquences spécifiques via KiwiSDR
    Permet de surveiller jusqu'à 10 fréquences simultanément
    """
    
    def __init__(self, db_manager, max_frequencies: int = 10):
        self.db_manager = db_manager
        self.max_frequencies = max_frequencies
        self.client = KiwiSDRClient()
        self._init_tables()
    
    def _init_tables(self):
        """Initialise les tables nécessaires"""
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
                UNIQUE(frequency_khz, server_url)
            )
        """)
        
        # Table d'activité quotidienne par fréquence
        cur.execute("""
            CREATE TABLE IF NOT EXISTS kiwisdr_frequency_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                frequency_id INTEGER NOT NULL,
                date DATE NOT NULL,
                emission_count INTEGER DEFAULT 0,
                peak_strength REAL DEFAULT 0.0,
                observation_duration INTEGER DEFAULT 0,
                FOREIGN KEY(frequency_id) REFERENCES kiwisdr_monitored_frequencies(id),
                UNIQUE(frequency_id, date)
            )
        """)
        
        # Table d'historique des serveurs actifs
        cur.execute("""
            CREATE TABLE IF NOT EXISTS kiwisdr_server_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_servers INTEGER NOT NULL,
                servers_data TEXT,
                variation_1h INTEGER DEFAULT 0,
                variation_24h INTEGER DEFAULT 0
            )
        """)
        
        conn.commit()
        conn.close()
    
    def add_monitored_frequency(self, frequency_khz: int, name: str, 
                               description: str = "", server_url: str = "") -> Dict[str, Any]:
        """
        Ajoute une fréquence à surveiller
        
        Args:
            frequency_khz: Fréquence en kHz
            name: Nom descriptif
            description: Description optionnelle
            server_url: URL du serveur KiwiSDR préféré (optionnel)
        """
        conn = self.db_manager.get_connection()
        cur = conn.cursor()
        
        # Vérifier la limite
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
            logger.error(f"Erreur ajout fréquence: {e}")
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
    
    def record_frequency_activity(self, frequency_id: int, emission_count: int, 
                                  peak_strength: float, duration: int):
        """Enregistre l'activité détectée sur une fréquence"""
        conn = self.db_manager.get_connection()
        cur = conn.cursor()
        
        today = datetime.utcnow().date()
        
        cur.execute("""
            INSERT INTO kiwisdr_frequency_activity 
            (frequency_id, date, emission_count, peak_strength, observation_duration)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(frequency_id, date) 
            DO UPDATE SET 
                emission_count = emission_count + ?,
                peak_strength = MAX(peak_strength, ?),
                observation_duration = observation_duration + ?
        """, (frequency_id, today, emission_count, peak_strength, duration,
              emission_count, peak_strength, duration))
        
        conn.commit()
        conn.close()
    
    def get_frequency_statistics(self, frequency_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Récupère les statistiques d'une fréquence
        
        Returns:
            - daily_activity: activité quotidienne
            - average: moyenne d'émissions par jour
            - variation: variation sur la période
        """
        conn = self.db_manager.get_connection()
        cur = conn.cursor()
        
        cutoff_date = datetime.utcnow().date() - timedelta(days=days)
        
        cur.execute("""
            SELECT date, emission_count, peak_strength
            FROM kiwisdr_frequency_activity
            WHERE frequency_id = ? AND date >= ?
            ORDER BY date
        """, (frequency_id, cutoff_date))
        
        daily_data = []
        total_emissions = 0
        
        for row in cur.fetchall():
            daily_data.append({
                'date': row[0],
                'emission_count': row[1],
                'peak_strength': row[2]
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
        
        # Calcul de la variation (dernier jour vs moyenne)
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
        
        # Calculer les variations
        # Variation 1h
        cur.execute("""
            SELECT total_servers FROM kiwisdr_server_history
            WHERE timestamp >= datetime('now', '-1 hour')
            ORDER BY timestamp DESC LIMIT 1
        """)
        row_1h = cur.fetchone()
        variation_1h = server_data['total'] - (row_1h[0] if row_1h else server_data['total'])
        
        # Variation 24h
        cur.execute("""
            SELECT total_servers FROM kiwisdr_server_history
            WHERE timestamp >= datetime('now', '-24 hours')
            ORDER BY timestamp DESC LIMIT 1
        """)
        row_24h = cur.fetchone()
        variation_24h = server_data['total'] - (row_24h[0] if row_24h else server_data['total'])
        
        # Insérer le snapshot
        cur.execute("""
            INSERT INTO kiwisdr_server_history 
            (total_servers, servers_data, variation_1h, variation_24h)
            VALUES (?, ?, ?, ?)
        """, (server_data['total'], json.dumps(server_data['servers']), 
              variation_1h, variation_24h))
        
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
            if abs(entry['variation_1h']) > 10:  # Seuil: +/- 10 serveurs en 1h
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
