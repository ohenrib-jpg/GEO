# Flask/gini_scraper.py
"""
Scraper pour l'indice GINI (inégalités de revenus)
Sources : Eurostat + INSEE
"""

import logging
import requests
from datetime import datetime
from typing import Dict, Any, Optional
import json

logger = logging.getLogger(__name__)


class GINIScraper:
    """Scraper pour l'indice GINI des inégalités"""
    
    # URL Eurostat pour GINI
    EUROSTAT_URL = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"
    GINI_DATASET = "ilc_di12"  # Dataset Eurostat pour GINI
    
    # Données fallback (dernières connues)
    FALLBACK_DATA = {
        'value': 29.4,  # GINI France 2023
        'period': '2023',
        'name': 'Indice GINI (inégalités)',
        'unit': 'Points (0-100)',
        'description': 'Mesure des inégalités de revenus (0=égalité parfaite, 100=inégalité maximale)'
    }
    
    def __init__(self, cache_file: str = 'instance/gini_cache.json'):
        self.cache_file = cache_file
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GEO-Educational-Research/1.0',
            'Accept': 'application/json'
        })
        logger.info("✅ GINIScraper initialisé")
    
    def get_gini_data(self) -> Dict[str, Any]:
        """
        Récupère l'indice GINI pour la France
        Méthode 1 : Eurostat API
        Méthode 2 : Cache
        Méthode 3 : Fallback
        """
        # 1. Essayer Eurostat
        try:
            logger.info("📊 Tentative récupération GINI depuis Eurostat...")
            eurostat_data = self._fetch_from_eurostat()
            
            if eurostat_data and eurostat_data.get('success'):
                self._save_to_cache(eurostat_data)
                logger.info("✅ GINI Eurostat récupéré avec succès")
                return eurostat_data
        
        except Exception as e:
            logger.warning(f"⚠️ Erreur Eurostat GINI: {e}")
        
        # 2. Essayer cache
        try:
            cached_data = self._load_from_cache()
            if cached_data and cached_data.get('success'):
                logger.info("📦 Utilisation GINI depuis cache")
                cached_data['note'] = 'Données en cache'
                return cached_data
        
        except Exception as e:
            logger.warning(f"⚠️ Erreur cache GINI: {e}")
        
        # 3. Fallback
        logger.info("🔄 Utilisation données GINI fallback")
        return self._get_fallback_data()
    
    def _fetch_from_eurostat(self) -> Optional[Dict[str, Any]]:
        """Récupère GINI depuis Eurostat API"""
        try:
            # Construire URL
            url = f"{self.EUROSTAT_URL}/{self.GINI_DATASET}"
            
            # Paramètres : France, dernière année
            params = {
                'format': 'JSON',
                'lang': 'FR',
                'geo': 'FR',
                'lastTimePeriod': 1
            }
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_eurostat_response(data)
            else:
                logger.warning(f"⚠️ Eurostat status {response.status_code}")
                return None
        
        except Exception as e:
            logger.error(f"❌ Erreur fetch Eurostat: {e}")
            return None
    
    def _parse_eurostat_response(self, data: Dict) -> Optional[Dict[str, Any]]:
        """Parse la réponse Eurostat"""
        try:
            if 'value' not in data or not data['value']:
                return None
            
            values = data['value']
            dimensions = data.get('dimension', {})
            time_dim = dimensions.get('time', {}).get('category', {}).get('index', {})
            
            if not values or not time_dim:
                return None
            
            # Récupérer dernière valeur
            sorted_times = sorted(time_dim.keys(), key=lambda x: time_dim[x])
            
            if not sorted_times:
                return None
            
            latest_time = sorted_times[-1]
            latest_value = float(values.get(str(time_dim[latest_time]), 0))
            
            # Valeur précédente pour variation
            previous_value = latest_value
            if len(sorted_times) > 1:
                previous_time = sorted_times[-2]
                previous_value = float(values.get(str(time_dim[previous_time]), latest_value))
            
            change = latest_value - previous_value
            change_percent = (change / previous_value * 100) if previous_value != 0 else 0
            
            return {
                'success': True,
                'id': 'eurostat_gini',
                'name': 'Indice GINI (inégalités)',
                'value': round(latest_value, 1),
                'previous_value': round(previous_value, 1),
                'change': round(change, 1),
                'change_percent': round(change_percent, 2),
                'unit': 'Points (0-100)',
                'period': latest_time,
                'source': 'Eurostat (officiel)',
                'dataset': self.GINI_DATASET,
                'description': 'Coefficient de GINI - Mesure des inégalités de revenus',
                'category': 'inequality',
                'reliability': 'official',
                'last_update': datetime.now().isoformat(),
                'interpretation': self._interpret_gini(latest_value)
            }
        
        except Exception as e:
            logger.error(f"❌ Erreur parsing Eurostat: {e}")
            return None
    
    def _interpret_gini(self, value: float) -> str:
        """Interprète la valeur du GINI"""
        if value < 25:
            return "Inégalités très faibles"
        elif value < 30:
            return "Inégalités faibles à modérées"
        elif value < 35:
            return "Inégalités modérées"
        elif value < 40:
            return "Inégalités élevées"
        else:
            return "Inégalités très élevées"
    
    def _load_from_cache(self) -> Optional[Dict]:
        """Charge depuis le cache JSON"""
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None
    
    def _save_to_cache(self, data: Dict):
        """Sauvegarde dans le cache"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info("💾 Cache GINI sauvegardé")
        except Exception as e:
            logger.error(f"Erreur sauvegarde cache: {e}")
    
    def _get_fallback_data(self) -> Dict[str, Any]:
        """Retourne les données de secours"""
        fb = self.FALLBACK_DATA
        
        return {
            'success': True,
            'id': 'eurostat_gini',
            'name': fb['name'],
            'value': fb['value'],
            'previous_value': fb['value'],
            'change': 0,
            'change_percent': 0,
            'unit': fb['unit'],
            'period': fb['period'],
            'source': 'Données de référence',
            'dataset': self.GINI_DATASET,
            'description': fb['description'],
            'category': 'inequality',
            'reliability': 'fallback',
            'last_update': datetime.now().isoformat(),
            'interpretation': self._interpret_gini(fb['value']),
            'note': 'Données de référence - API temporairement indisponible'
        }
    
    def force_refresh(self) -> Dict[str, Any]:
        """Force le rafraîchissement (ignore cache)"""
        logger.info("🔄 Rafraîchissement forcé GINI")
        return self._fetch_from_eurostat() or self._get_fallback_data()


# Test du module
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    scraper = GINIScraper()
    data = scraper.get_gini_data()
    
    print("=" * 60)
    print("📊 INDICE GINI (Inégalités)")
    print("=" * 60)
    
    if data.get('success'):
        print(f"\n{data['name']}: {data['value']} {data['unit']}")
        print(f"Période: {data['period']}")
        print(f"Source: {data['source']}")
        print(f"Interprétation: {data.get('interpretation', 'N/A')}")
        print(f"Fiabilité: {data['reliability']}")
    else:
        print("❌ Erreur récupération données")
