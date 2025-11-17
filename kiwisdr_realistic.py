# Flask/kiwisdr_realistic.py
"""
KiwiSDR - VERSION RÉALISTE
Basée sur l'observation manuelle assistée, pas l'automatisation
"""

import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)


class KiwiSDRServerFinder:
    """
    Trouve les serveurs KiwiSDR actifs via le répertoire officiel
    """
    
    # URL du répertoire officiel KiwiSDR
    DIRECTORY_URL = "http://rx.linkfanel.net/"
    KIWISDR_MAP_URL = "http://kiwisdr.com/public/"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_active_servers(self, timeout: int = 10) -> Dict[str, Any]:
        """
        Récupère les serveurs KiwiSDR actifs depuis le répertoire
        
        Returns:
            {
                'total': int,
                'servers': [
                    {
                        'name': str,
                        'url': str,
                        'location': str,
                        'frequency_range': {'min': int, 'max': int},
                        'users': int,
                        'users_max': int
                    }
                ],
                'timestamp': str
            }
        """
        try:
            logger.info(f"🔍 Recherche serveurs KiwiSDR via {self.DIRECTORY_URL}")
            
            # Essayer le répertoire LinkFanel (le plus fiable)
            response = self.session.get(self.DIRECTORY_URL, timeout=timeout)
            response.raise_for_status()
            
            servers = self._parse_linkfanel_directory(response.text)
            
            if not servers:
                # Fallback : serveurs connus manuellement
                servers = self._get_known_servers()
            
            logger.info(f"✅ {len(servers)} serveurs trouvés")
            
            return {
                'total': len(servers),
                'servers': servers,
                'timestamp': datetime.utcnow().isoformat(),
                'success': True
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération serveurs: {e}")
            return {
                'total': 0,
                'servers': self._get_known_servers(),
                'timestamp': datetime.utcnow().isoformat(),
                'success': False,
                'error': str(e)
            }
    
    def _parse_linkfanel_directory(self, html: str) -> List[Dict[str, Any]]:
        """Parse le répertoire LinkFanel"""
        servers = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Chercher les lignes de serveurs (structure variable)
            rows = soup.find_all('tr')
            
            for row in rows:
                cols = row.find_all('td')
                
                if len(cols) >= 3:
                    # Extraire nom et URL
                    link = row.find('a', href=True)
                    if not link:
                        continue
                    
                    url = link['href']
                    name = link.text.strip()
                    
                    # Extraire localisation
                    location = cols[1].text.strip() if len(cols) > 1 else 'Unknown'
                    
                    # Extraire utilisateurs
                    users_text = cols[2].text.strip() if len(cols) > 2 else '0/0'
                    users_match = re.search(r'(\d+)/(\d+)', users_text)
                    
                    users = int(users_match.group(1)) if users_match else 0
                    users_max = int(users_match.group(2)) if users_match else 4
                    
                    servers.append({
                        'name': name,
                        'url': url,
                        'location': location,
                        'users': users,
                        'users_max': users_max,
                        'frequency_range': {'min': 0, 'max': 30000},
                        'status': 'online' if users < users_max else 'full'
                    })
            
        except Exception as e:
            logger.warning(f"⚠️ Erreur parsing LinkFanel: {e}")
        
        return servers
    
    def _get_known_servers(self) -> List[Dict[str, Any]]:
        """
        Serveurs KiwiSDR connus et stables (fallback)
        """
        return [
            {
                'name': 'University of Twente WebSDR',
                'url': 'http://websdr.ewi.utwente.nl:8901/',
                'location': 'Enschede, Netherlands',
                'users': 0,
                'users_max': 200,
                'frequency_range': {'min': 0, 'max': 30000},
                'status': 'online',
                'note': 'WebSDR, pas KiwiSDR mais compatible'
            },
            {
                'name': 'KiwiSDR Finland',
                'url': 'http://oh3ac.dy.fi:8073/',
                'location': 'Finland',
                'users': 0,
                'users_max': 4,
                'frequency_range': {'min': 0, 'max': 30000},
                'status': 'online'
            },
            {
                'name': 'KiwiSDR Australia',
                'url': 'http://vk2dds.com:8073/',
                'location': 'Australia',
                'users': 0,
                'users_max': 4,
                'frequency_range': {'min': 0, 'max': 30000},
                'status': 'online'
            }
        ]
    
    def test_server_availability(self, server_url: str, timeout: int = 5) -> bool:
        """
        Teste si un serveur KiwiSDR est accessible
        """
        try:
            response = self.session.get(server_url, timeout=timeout)
            return response.status_code == 200
        except:
            return False


class KiwiSDRManualMonitor:
    """
    Système de monitoring manuel assisté pour KiwiSDR
    
    Philosophie : On ne peut PAS automatiser l'analyse spectrale KiwiSDR
    → On fournit des outils pour l'observation manuelle
    """
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.server_finder = KiwiSDRServerFinder()
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                active BOOLEAN DEFAULT 1,
                UNIQUE(frequency_khz)
            )
        """)
        
        # Table d'activité (comptage MANUEL)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS kiwisdr_frequency_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                frequency_id INTEGER NOT NULL,
                date DATE NOT NULL,
                emission_count INTEGER DEFAULT 0,
                observation_duration INTEGER DEFAULT 0,
                notes TEXT,
                observer TEXT,
                FOREIGN KEY(frequency_id) REFERENCES kiwisdr_monitored_frequencies(id),
                UNIQUE(frequency_id, date)
            )
        """)
        
        # Table historique serveurs
        cur.execute("""
            CREATE TABLE IF NOT EXISTS kiwisdr_server_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_servers INTEGER NOT NULL,
                online_servers INTEGER NOT NULL,
                full_servers INTEGER NOT NULL,
                snapshot_data TEXT
            )
        """)
        
        conn.commit()
        conn.close()
        
        logger.info("✅ Tables KiwiSDR initialisées")
    
    def get_waterfall_url(self, server_url: str, frequency_khz: int, 
                          zoom: int = 5, waterfall: str = 'large') -> str:
        """
        Génère l'URL pour accéder au waterfall KiwiSDR
        
        Args:
            server_url: URL du serveur (ex: "http://kiwisdr.example.com:8073")
            frequency_khz: Fréquence en kHz
            zoom: Niveau de zoom (0-14)
            waterfall: Taille ('large', 'medium', 'small')
        
        Returns:
            URL complète pour ouvrir dans un navigateur
        """
        # Format KiwiSDR standard
        # Exemple: http://kiwisdr.com:8073/?f=14300z10
        
        # S'assurer que l'URL se termine sans slash
        base_url = server_url.rstrip('/')
        
        return f"{base_url}/?f={frequency_khz}z{zoom}&wf={waterfall}"
    
    def record_manual_observation(self, frequency_id: int, emission_count: int,
                                  duration_minutes: int = 30, 
                                  notes: str = "", 
                                  observer: str = "user") -> Dict[str, Any]:
        """
        Enregistre une observation MANUELLE d'une fréquence
        
        C'est la méthode principale : l'utilisateur observe le waterfall
        et enregistre manuellement ce qu'il voit
        
        Args:
            frequency_id: ID de la fréquence
            emission_count: Nombre d'émissions observées
            duration_minutes: Durée d'observation
            notes: Notes d'observation
            observer: Nom de l'observateur
        
        Returns:
            Résultat de l'enregistrement
        """
        try:
            conn = self.db_manager.get_connection()
            cur = conn.cursor()
            
            today = datetime.utcnow().date()
            
            # Insérer ou mettre à jour
            cur.execute("""
                INSERT INTO kiwisdr_frequency_activity 
                (frequency_id, date, emission_count, observation_duration, notes, observer)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(frequency_id, date) 
                DO UPDATE SET 
                    emission_count = emission_count + ?,
                    observation_duration = observation_duration + ?,
                    notes = CASE 
                        WHEN notes IS NULL OR notes = '' THEN ?
                        ELSE notes || ' | ' || ?
                    END
            """, (
                frequency_id, today, emission_count, duration_minutes * 60, notes, observer,
                emission_count, duration_minutes * 60, notes, notes
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Observation enregistrée: {emission_count} émissions")
            
            return {
                'success': True,
                'message': f'{emission_count} émissions enregistrées',
                'date': today.isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur enregistrement: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def add_monitored_frequency(self, frequency_khz: int, name: str,
                               description: str = "") -> Dict[str, Any]:
        """Ajoute une fréquence à surveiller"""
        try:
            conn = self.db_manager.get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO kiwisdr_monitored_frequencies 
                (frequency_khz, name, description)
                VALUES (?, ?, ?)
            """, (frequency_khz, name, description))
            
            freq_id = cur.lastrowid
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'frequency_id': freq_id,
                'message': f'Fréquence {frequency_khz} kHz ajoutée'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_monitored_frequencies(self) -> List[Dict[str, Any]]:
        """Récupère toutes les fréquences surveillées"""
        conn = self.db_manager.get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, frequency_khz, name, description, created_at, active
            FROM kiwisdr_monitored_frequencies
            WHERE active = 1
            ORDER BY frequency_khz
        """)
        
        frequencies = []
        for row in cur.fetchall():
            frequencies.append({
                'id': row[0],
                'frequency_khz': row[1],
                'name': row[2],
                'description': row[3],
                'created_at': row[4],
                'active': bool(row[5])
            })
        
        conn.close()
        return frequencies
    
    def get_frequency_statistics(self, frequency_id: int, days: int = 30) -> Dict[str, Any]:
        """Récupère les statistiques d'une fréquence"""
        conn = self.db_manager.get_connection()
        cur = conn.cursor()
        
        cutoff_date = datetime.utcnow().date() - timedelta(days=days)
        
        cur.execute("""
            SELECT date, emission_count, observation_duration, notes
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
                'duration': row[2],
                'notes': row[3]
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
    
    def create_server_snapshot(self) -> Dict[str, Any]:
        """Crée un snapshot des serveurs KiwiSDR actifs"""
        try:
            server_data = self.server_finder.get_active_servers()
            
            if not server_data['success']:
                return {'success': False, 'error': server_data.get('error')}
            
            conn = self.db_manager.get_connection()
            cur = conn.cursor()
            
            # Compter les serveurs online et full
            online = sum(1 for s in server_data['servers'] if s['status'] == 'online')
            full = sum(1 for s in server_data['servers'] if s['status'] == 'full')
            
            # Enregistrer le snapshot
            cur.execute("""
                INSERT INTO kiwisdr_server_snapshots 
                (total_servers, online_servers, full_servers, snapshot_data)
                VALUES (?, ?, ?, ?)
            """, (
                server_data['total'],
                online,
                full,
                str(server_data['servers'])  # JSON sérialisé en string
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"📸 Snapshot créé: {server_data['total']} serveurs")
            
            return {
                'success': True,
                'total_servers': server_data['total'],
                'online_servers': online,
                'full_servers': full,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur snapshot: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_server_variation_history(self, hours: int = 24) -> Dict[str, Any]:
        """Récupère l'historique des variations de serveurs"""
        conn = self.db_manager.get_connection()
        cur = conn.cursor()
        
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        cur.execute("""
            SELECT timestamp, total_servers, online_servers, full_servers
            FROM kiwisdr_server_snapshots
            WHERE timestamp >= ?
            ORDER BY timestamp
        """, (cutoff,))
        
        history = []
        previous_total = None
        
        for row in cur.fetchall():
            current_total = row[1]
            variation_1h = 0
            
            if previous_total is not None:
                variation_1h = current_total - previous_total
            
            history.append({
                'timestamp': row[0],
                'total_servers': current_total,
                'online_servers': row[2],
                'full_servers': row[3],
                'variation_1h': variation_1h
            })
            
            previous_total = current_total
        
        conn.close()
        
        # Détecter les alertes (variations > 10%)
        alerts = []
        if len(history) > 0:
            avg_servers = sum(h['total_servers'] for h in history) / len(history)
            
            for entry in history:
                variation_pct = ((entry['total_servers'] - avg_servers) / avg_servers * 100) if avg_servers > 0 else 0
                
                if abs(variation_pct) > 10:
                    alerts.append({
                        'timestamp': entry['timestamp'],
                        'type': 'variation',
                        'severity': 'high' if abs(variation_pct) > 20 else 'medium',
                        'message': f"Variation de {variation_pct:+.1f}% des serveurs actifs"
                    })
        
        return {
            'history': history,
            'alerts': alerts,
            'period_hours': hours
        }


# Presets de fréquences géopolitiques
GEOPOLITICAL_FREQUENCIES = [
    {
        'frequency_khz': 2182,
        'name': 'Maritime MF Détresse',
        'description': 'Fréquence de détresse maritime 2182 kHz (obsolète mais surveillée)'
    },
    {
        'frequency_khz': 4625,
        'name': 'UVB-76 "The Buzzer"',
        'description': 'Station mystérieuse russe, indicateur d\'activité militaire'
    },
    {
        'frequency_khz': 5732,
        'name': 'Communications Diplomatiques HF',
        'description': 'Bande HF utilisée pour communications diplomatiques'
    },
    {
        'frequency_khz': 6998,
        'name': 'Militaire OTAN',
        'description': 'Fréquence militaire OTAN standard'
    },
    {
        'frequency_khz': 8992,
        'name': 'Communications Gouvernementales',
        'description': 'Bande HF pour communications gouvernementales'
    },
    {
        'frequency_khz': 11175,
        'name': 'Services Étrangers',
        'description': 'Bande HF services étrangers'
    },
    {
        'frequency_khz': 14313,
        'name': 'Maritime Mobile Service',
        'description': 'Service mobile maritime international'
    },
    {
        'frequency_khz': 121500,
        'name': 'Aviation Urgence (121.5 MHz)',
        'description': 'Fréquence d\'urgence aviation civile'
    }
]
