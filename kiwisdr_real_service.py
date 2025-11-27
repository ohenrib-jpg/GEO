# Flask/kiwisdr_real_service.py
# IMPORTANT : Créer aussi une table kiwisdr_servers dans le schéma DB
"""
Service optimisé pour récupérer les serveurs KiwiSDR réels
Utilise les APIs publiques et répertoires officiels
"""

import logging
import requests
from datetime import datetime
from typing import Dict, List, Any
from bs4 import BeautifulSoup
import re
import json

logger = logging.getLogger(__name__)


class KiwiSDRRealService:
    """
    Service pour interagir avec le réseau KiwiSDR mondial
    """
    
    # URLs des répertoires KiwiSDR
    KIWISDR_OFFICIAL_LIST = "http://kiwisdr.com/public/"
    LINKFANEL_DIRECTORY = "http://rx.linkfanel.net/"
    
    # Timeout pour les requêtes
    REQUEST_TIMEOUT = 15
    
    @classmethod
    def get_active_servers(cls) -> Dict[str, Any]:
        """
        Récupère la liste des serveurs KiwiSDR actifs
        Essaie plusieurs sources pour maximiser la fiabilité
        """
        logger.info("🔍 Recherche serveurs KiwiSDR actifs...")
        
        # Essayer les différentes sources dans l'ordre
        servers = []
        
        # 1. Essayer le répertoire officiel KiwiSDR
        try:
            servers = cls._fetch_from_official_list()
            if servers:
                logger.info(f"✅ {len(servers)} serveurs depuis KiwiSDR officiel")
                return cls._format_response(servers, 'kiwisdr_official')
        except Exception as e:
            logger.warning(f"⚠️ Échec KiwiSDR officiel: {e}")
        
        # 2. Essayer LinkFanel (répertoire communautaire)
        try:
            servers = cls._fetch_from_linkfanel()
            if servers:
                logger.info(f"✅ {len(servers)} serveurs depuis LinkFanel")
                return cls._format_response(servers, 'linkfanel')
        except Exception as e:
            logger.warning(f"⚠️ Échec LinkFanel: {e}")
        
        # 3. Fallback : serveurs connus stables
        logger.warning("⚠️ Utilisation liste fallback")
        servers = cls._get_fallback_servers()
        return cls._format_response(servers, 'fallback')
    
    @classmethod
    def _fetch_from_official_list(cls) -> List[Dict[str, Any]]:
        """
        Récupère depuis le répertoire officiel KiwiSDR
        """
        try:
            response = requests.get(
                cls.KIWISDR_OFFICIAL_LIST,
                params={'ajax': '1'},
                headers={
                    'User-Agent': 'Mozilla/5.0 (GeoPolMonitor/1.0)',
                    'Accept': 'application/json, text/html'
                },
                timeout=cls.REQUEST_TIMEOUT
            )
            
            if response.status_code != 200:
                logger.warning(f"⚠️ Status code {response.status_code} from official list")
                return []
            
            # Essayer de parser comme JSON
            try:
                data = response.json()
                return cls._parse_official_json(data)
            except json.JSONDecodeError:
                # Si pas JSON, essayer HTML
                return cls._parse_official_html(response.text)
                
        except requests.RequestException as e:
            logger.error(f"❌ Erreur requête officielle: {e}")
            return []
    
    @classmethod
    def _parse_official_json(cls, data: Any) -> List[Dict[str, Any]]:
        """Parse la réponse JSON du répertoire officiel"""
        servers = []
        
        if isinstance(data, list):
            for server in data:
                try:
                    # Structure JSON KiwiSDR
                    servers.append({
                        'name': server.get('name', 'Unknown'),
                        'url': server.get('url', ''),
                        'location': server.get('location', 'Unknown'),
                        'antenna': server.get('antenna', ''),
                        'users': server.get('users', 0),
                        'users_max': server.get('users_max', 0),
                        'frequency_range': {
                            'min': server.get('freq_min', 0),
                            'max': server.get('freq_max', 30000)
                        },
                        'status': 'online' if server.get('online', True) else 'offline',
                        'sdr_hw': server.get('sdr_hw', 'KiwiSDR'),
                        'gps': server.get('gps', False)
                    })
                except Exception as e:
                    logger.warning(f"⚠️ Erreur parsing serveur JSON: {e}")
                    continue
        
        return servers
    
    @classmethod
    def _parse_official_html(cls, html: str) -> List[Dict[str, Any]]:
        """Parse la réponse HTML si pas de JSON"""
        servers = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Chercher les liens vers serveurs KiwiSDR
            links = soup.find_all('a', href=re.compile(r':\d{4}'))
            
            for link in links:
                url = link.get('href', '')
                name = link.text.strip()
                
                if url and ':' in url:
                    servers.append({
                        'name': name or f"KiwiSDR {url}",
                        'url': url if url.startswith('http') else f"http://{url}",
                        'location': 'Unknown',
                        'users': 0,
                        'users_max': 4,
                        'frequency_range': {'min': 0, 'max': 30000},
                        'status': 'online'
                    })
        except Exception as e:
            logger.error(f"❌ Erreur parsing HTML: {e}")
        
        return servers
    
    @classmethod
    def _fetch_from_linkfanel(cls) -> List[Dict[str, Any]]:
        """
        Récupère depuis LinkFanel (répertoire communautaire)
        """
        try:
            response = requests.get(
                cls.LINKFANEL_DIRECTORY,
                headers={'User-Agent': 'Mozilla/5.0 (GeoPolMonitor/1.0)'},
                timeout=cls.REQUEST_TIMEOUT
            )
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            servers = []
            
            # Structure LinkFanel : tableau avec serveurs
            rows = soup.find_all('tr')
            
            for row in rows[1:]:  # Skip header
                try:
                    cols = row.find_all('td')
                    if len(cols) < 3:
                        continue
                    
                    # Extraire infos
                    link = row.find('a', href=True)
                    if not link:
                        continue
                    
                    url = link['href']
                    name = link.text.strip()
                    location = cols[1].text.strip() if len(cols) > 1 else 'Unknown'
                    
                    # Utilisateurs (format "X/Y")
                    users_text = cols[2].text.strip() if len(cols) > 2 else '0/4'
                    users_match = re.search(r'(\d+)/(\d+)', users_text)
                    
                    if users_match:
                        users = int(users_match.group(1))
                        users_max = int(users_match.group(2))
                    else:
                        users = 0
                        users_max = 4
                    
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
                    logger.warning(f"⚠️ Erreur parsing row LinkFanel: {e}")
                    continue
            
            return servers
            
        except Exception as e:
            logger.error(f"❌ Erreur LinkFanel: {e}")
            return []
    
    @classmethod
    def _get_fallback_servers(cls) -> List[Dict[str, Any]]:
        """
        Liste de serveurs KiwiSDR connus et stables
        Utilisée en dernier recours
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
                'note': 'WebSDR (compatible KiwiSDR)'
            },
            {
                'name': 'KiwiSDR Finland OH3AC',
                'url': 'http://oh3ac.dy.fi:8073/',
                'location': 'Finland',
                'users': 0,
                'users_max': 4,
                'frequency_range': {'min': 0, 'max': 30000},
                'status': 'online'
            },
            {
                'name': 'KiwiSDR Australia VK2DDS',
                'url': 'http://vk2dds.com:8073/',
                'location': 'Sydney, Australia',
                'users': 0,
                'users_max': 4,
                'frequency_range': {'min': 0, 'max': 30000},
                'status': 'online'
            },
            {
                'name': 'KiwiSDR Japan JA2YKZ',
                'url': 'http://ja2ykz.com:8073/',
                'location': 'Japan',
                'users': 0,
                'users_max': 4,
                'frequency_range': {'min': 0, 'max': 30000},
                'status': 'online'
            },
            {
                'name': 'KiwiSDR USA KA7OEI',
                'url': 'http://ka7oei.com:8073/',
                'location': 'Utah, USA',
                'users': 0,
                'users_max': 4,
                'frequency_range': {'min': 0, 'max': 30000},
                'status': 'online'
            }
        ]
    
    @classmethod
    def _format_response(cls, servers: List[Dict], source: str) -> Dict[str, Any]:
        """Formate la réponse finale"""
        return {
            'total': len(servers),
            'servers': servers,
            'timestamp': datetime.utcnow().isoformat(),
            'success': True,
            'source': source
        }
    
    @classmethod
    def test_server_availability(cls, server_url: str, timeout: int = 5) -> bool:
        """
        Teste si un serveur KiwiSDR est accessible
        """
        try:
            response = requests.head(
                server_url,
                timeout=timeout,
                allow_redirects=True
            )
            return response.status_code == 200
        except:
            return False
    
    @classmethod
    def get_geopolitical_frequencies(cls) -> Dict[str, Dict[str, int]]:
        """
        Retourne les fréquences géopolitiques importantes à surveiller
        """
        return {
            'shortwave_broadcast': {
                'BBC World Service': 12065,
                'Radio France International': 15300,
                'Voice of America': 13670,
                'Radio China International': 11710,
                'Radio Moscow': 12085,
                'Deutsche Welle': 15205
            },
            'utility_stations': {
                'Volmet Weather (Aviation)': 6604,
                'Maritime Safety': 2182,
                'Aircraft Emergency (121.5 MHz)': 121500,
                'Military Satcom': 13900,
                'Diplomatic HF': 5732
            },
            'numbers_stations': {
                'UVB-76 "The Buzzer" (Russia)': 4625,
                'Lincolnshire Poacher (UK)': 13780,
                'Cuban Numbers': 9330,
                'Chinese Military': 8145
            },
            'military_frequencies': {
                'NATO Military': 6998,
                'US Military HFGCS': 11175,
                'Russian Military': 8131,
                'Chinese Military': 8142
            }
        }
    
    @classmethod
    def save_servers_to_db(cls, db_manager, servers: List[Dict]):
        """
        Sauvegarde les serveurs en base de données
        """
        try:
            conn = db_manager.get_connection()
            cur = conn.cursor()
            
            # Vider table existante
            cur.execute("DELETE FROM kiwisdr_servers")
            
            # Insérer nouveaux serveurs
            for server in servers:
                cur.execute("""
                    INSERT INTO kiwisdr_servers 
                    (name, url, location, users, users_max, status, last_seen)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    server['name'],
                    server['url'],
                    server.get('location', 'Unknown'),
                    server.get('users', 0),
                    server.get('users_max', 4),
                    server.get('status', 'online'),
                    datetime.utcnow().isoformat()
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ {len(servers)} serveurs KiwiSDR sauvegardés")
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde serveurs: {e}")


class SDRFrequencyPresets:
    """
    Presets de fréquences géopolitiques prêts à l'emploi
    """
    
    GEOPOLITICAL_PRESETS = [
        {
            'frequency_khz': 2182,
            'name': 'Maritime MF Détresse',
            'description': 'Fréquence de détresse maritime 2182 kHz (obsolète mais surveillée)',
            'category': 'maritime'
        },
        {
            'frequency_khz': 4625,
            'name': 'UVB-76 "The Buzzer"',
            'description': 'Station mystérieuse russe, indicateur d\'activité militaire',
            'category': 'military'
        },
        {
            'frequency_khz': 5732,
            'name': 'Communications Diplomatiques HF',
            'description': 'Bande HF utilisée pour communications diplomatiques',
            'category': 'diplomatic'
        },
        {
            'frequency_khz': 6998,
            'name': 'Militaire OTAN',
            'description': 'Fréquence militaire OTAN standard',
            'category': 'military'
        },
        {
            'frequency_khz': 8992,
            'name': 'Communications Gouvernementales',
            'description': 'Bande HF pour communications gouvernementales',
            'category': 'government'
        },
        {
            'frequency_khz': 11175,
            'name': 'US Military HFGCS',
            'description': 'High Frequency Global Communications System (US)',
            'category': 'military'
        },
        {
            'frequency_khz': 13670,
            'name': 'Voice of America',
            'description': 'Radio internationale américaine',
            'category': 'broadcast'
        },
        {
            'frequency_khz': 14313,
            'name': 'Maritime Mobile Service',
            'description': 'Service mobile maritime international',
            'category': 'maritime'
        },
        {
            'frequency_khz': 15300,
            'name': 'Radio France International',
            'description': 'Radio internationale française',
            'category': 'broadcast'
        },
        {
            'frequency_khz': 121500,
            'name': 'Aviation Urgence (121.5 MHz)',
            'description': 'Fréquence d\'urgence aviation civile',
            'category': 'aviation'
        }
    ]
    
    @classmethod
    def install_presets(cls, db_manager):
        """
        Installe les presets de fréquences géopolitiques
        """
        try:
            conn = db_manager.get_connection()
            cur = conn.cursor()
            
            count = 0
            for preset in cls.GEOPOLITICAL_PRESETS:
                try:
                    cur.execute("""
                        INSERT OR IGNORE INTO kiwisdr_monitored_frequencies 
                        (frequency_khz, name, description, active)
                        VALUES (?, ?, ?, 1)
                    """, (
                        preset['frequency_khz'],
                        preset['name'],
                        preset['description']
                    ))
                    if cur.rowcount > 0:
                        count += 1
                except Exception as e:
                    logger.warning(f"⚠️ Erreur insertion preset {preset['name']}: {e}")
                    continue
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ {count} presets géopolitiques installés")
            return count
            
        except Exception as e:
            logger.error(f"❌ Erreur installation presets: {e}")
            return 0