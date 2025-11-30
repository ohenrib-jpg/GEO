# Flask/insee_scraper.py
"""
Scraper léger et respectueux pour les indicateurs clés INSEE
Récupère inflation, chômage et croissance depuis la page d'accueil
Usage éducatif - 1 requête par jour maximum
"""

import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import json
import re

logger = logging.getLogger(__name__)


class INSEEScraper:
    """Scraper pour les indicateurs clés INSEE"""
    
    INSEE_URL = "https://www.insee.fr/fr/accueil"
    CACHE_DURATION_HOURS = 24  # Cache 24h
    
    # Fallback values (dernières données connues - novembre 2024)
    FALLBACK_DATA = {
        'inflation': {
            'value': 1.2,
            'period': '2024-10',
            'name': 'Inflation (glissement annuel)',
            'unit': '%'
        },
        'unemployment': {
            'value': 7.4,
            'period': '2024-Q3',
            'name': 'Taux de chômage',
            'unit': '%'
        },
        'growth': {
            'value': 1.1,
            'period': '2024-Q3',
            'name': 'Croissance du PIB',
            'unit': '% (variation annuelle)'
        }
    }
    
    def __init__(self, cache_file: str = 'instance/insee_cache.json'):
        self.cache_file = cache_file
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GEO-Educational-Research/1.0 (Educational Purpose)',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'fr-FR,fr;q=0.9'
        })
        logger.info("✅ INSEEScraper initialisé")
    
    def get_indicators(self) -> Dict[str, Any]:
        """
        Récupère les 3 indicateurs clés INSEE
        Avec système de cache intelligent
        """
        # Vérifier le cache d'abord
        cached_data = self._load_from_cache()
        if cached_data and self._is_cache_valid(cached_data):
            logger.info("📦 Utilisation données INSEE depuis cache")
            return cached_data
        
        # Tenter de scraper les nouvelles données
        try:
            logger.info("🌐 Récupération données INSEE depuis le site...")
            fresh_data = self._scrape_insee_homepage()
            
            if fresh_data and self._validate_data(fresh_data):
                self._save_to_cache(fresh_data)
                logger.info("✅ Données INSEE fraîches récupérées")
                return fresh_data
            else:
                logger.warning("⚠️ Données scrapées invalides, utilisation fallback")
                return self._get_fallback_data()
        
        except Exception as e:
            logger.error(f"❌ Erreur scraping INSEE: {e}")
            # Retourner le cache même expiré ou fallback
            if cached_data:
                logger.info("📦 Utilisation cache expiré en secours")
                return cached_data
            else:
                logger.info("🔄 Utilisation données fallback")
                return self._get_fallback_data()
    
    def _scrape_insee_homepage(self) -> Optional[Dict[str, Any]]:
        """
        Scrape la page d'accueil INSEE pour extraire les indicateurs
        Méthode respectueuse : 1 seule requête, timeout court
        """
        try:
            response = self.session.get(
                self.INSEE_URL,
                timeout=10,
                allow_redirects=True
            )
            
            if response.status_code != 200:
                logger.warning(f"⚠️ Status code INSEE: {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Chercher les indicateurs dans la section "Indicateurs clés"
            indicators = {}
            
            # Stratégie 1: Chercher dans les éléments de la page d'accueil
            # Les indicateurs sont souvent dans des divs ou spans spécifiques
            
            # Exemple de pattern pour inflation
            inflation_value = self._extract_indicator_value(
                soup, 
                keywords=['inflation', 'prix', 'consommation'],
                pattern=r'(\d+[,\.]\d+)\s*%'
            )
            
            if inflation_value:
                indicators['inflation'] = {
                    'value': inflation_value,
                    'period': self._extract_period(soup, 'inflation'),
                    'name': 'Inflation (glissement annuel)',
                    'unit': '%',
                    'source': 'INSEE (scraping)',
                    'last_update': datetime.now().isoformat()
                }
            
            # Chômage
            unemployment_value = self._extract_indicator_value(
                soup,
                keywords=['chômage', 'chomage', 'emploi'],
                pattern=r'(\d+[,\.]\d+)\s*%'
            )
            
            if unemployment_value:
                indicators['unemployment'] = {
                    'value': unemployment_value,
                    'period': self._extract_period(soup, 'chomage'),
                    'name': 'Taux de chômage',
                    'unit': '%',
                    'source': 'INSEE (scraping)',
                    'last_update': datetime.now().isoformat()
                }
            
            # Croissance
            growth_value = self._extract_indicator_value(
                soup,
                keywords=['croissance', 'pib', 'PIB'],
                pattern=r'([+-]?\d+[,\.]\d+)\s*%'
            )
            
            if growth_value:
                indicators['growth'] = {
                    'value': growth_value,
                    'period': self._extract_period(soup, 'pib'),
                    'name': 'Croissance du PIB',
                    'unit': '% (variation annuelle)',
                    'source': 'INSEE (scraping)',
                    'last_update': datetime.now().isoformat()
                }
            
            return {
                'success': True,
                'indicators': indicators,
                'timestamp': datetime.now().isoformat(),
                'source': 'INSEE scraping'
            } if indicators else None
            
        except Exception as e:
            logger.error(f"❌ Erreur scraping: {e}")
            return None
    
    def _extract_indicator_value(
        self, 
        soup: BeautifulSoup, 
        keywords: list, 
        pattern: str
    ) -> Optional[float]:
        """
        Extrait une valeur d'indicateur depuis le HTML
        """
        try:
            # Chercher dans tous les éléments textuels
            for elem in soup.find_all(['div', 'span', 'p', 'td', 'strong']):
                text = elem.get_text(strip=True).lower()
                
                # Vérifier si un mot-clé est présent
                if any(keyword in text for keyword in keywords):
                    # Chercher une valeur numérique avec le pattern
                    match = re.search(pattern, elem.get_text())
                    if match:
                        value_str = match.group(1).replace(',', '.')
                        return float(value_str)
            
            return None
        except Exception as e:
            logger.error(f"Erreur extraction valeur: {e}")
            return None
    
    def _extract_period(self, soup: BeautifulSoup, indicator_type: str) -> str:
        """
        Tente d'extraire la période de référence
        """
        try:
            # Chercher des patterns de date
            date_patterns = [
                r'(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})',
                r'T(\d)\s+(\d{4})',  # Trimestre
                r'(\d{4})\s*[-–]\s*T(\d)',
                r'(\d{2})/(\d{4})'
            ]
            
            text = soup.get_text()
            
            for pattern in date_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return match.group(0)
            
            # Par défaut, retourner période actuelle
            now = datetime.now()
            return f"{now.year}-{now.month:02d}"
            
        except Exception:
            return datetime.now().strftime('%Y-%m')
    
    def _validate_data(self, data: Dict) -> bool:
        """Valide que les données récupérées sont cohérentes"""
        if not data or not data.get('success'):
            return False
        
        indicators = data.get('indicators', {})
        
        # Vérifier qu'au moins 2 indicateurs sur 3 sont présents
        valid_count = sum(
            1 for key in ['inflation', 'unemployment', 'growth']
            if key in indicators and indicators[key].get('value') is not None
        )
        
        return valid_count >= 2
    
    def _load_from_cache(self) -> Optional[Dict]:
        """Charge les données depuis le cache JSON"""
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None
    
    def _save_to_cache(self, data: Dict):
        """Sauvegarde les données dans le cache"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info("💾 Cache INSEE sauvegardé")
        except Exception as e:
            logger.error(f"Erreur sauvegarde cache: {e}")
    
    def _is_cache_valid(self, cached_data: Dict) -> bool:
        """Vérifie si le cache est encore valide (< 24h)"""
        try:
            timestamp = datetime.fromisoformat(cached_data['timestamp'])
            age = datetime.now() - timestamp
            return age < timedelta(hours=self.CACHE_DURATION_HOURS)
        except (KeyError, ValueError):
            return False
    
    def _get_fallback_data(self) -> Dict[str, Any]:
        """Retourne les données de secours"""
        logger.info("🔄 Utilisation données INSEE fallback")
        return {
            'success': True,
            'indicators': self.FALLBACK_DATA,
            'timestamp': datetime.now().isoformat(),
            'source': 'Fallback data',
            'note': 'Données de référence - source temporairement indisponible'
        }
    
    def force_refresh(self) -> Dict[str, Any]:
        """Force un rafraîchissement des données (ignore le cache)"""
        logger.info("🔄 Rafraîchissement forcé INSEE")
        return self._scrape_insee_homepage() or self._get_fallback_data()


# Fonction d'intégration avec Eurostat
def get_combined_french_indicators(
    eurostat_connector,
    insee_scraper: INSEEScraper
) -> Dict[str, Any]:
    """
    Combine les données Eurostat et INSEE pour la France
    Eurostat = données officielles UE (PIB, chômage, etc.)
    INSEE scraping = indicateurs clés page d'accueil
    """
    results = {
        'success': True,
        'timestamp': datetime.now().isoformat(),
        'sources': {
            'eurostat': 'official',
            'insee': 'scraping'
        },
        'indicators': {}
    }
    
    # 1. Récupérer les indicateurs Eurostat (prioritaires)
    try:
        eurostat_data = eurostat_connector.get_multiple_indicators([
            'gdp', 'unemployment', 'hicp', 'trade_balance'
        ])
        
        if eurostat_data.get('success'):
            for key, indicator in eurostat_data['indicators'].items():
                if indicator.get('success'):
                    results['indicators'][f'eurostat_{key}'] = indicator
    except Exception as e:
        logger.error(f"Erreur Eurostat: {e}")
    
    # 2. Ajouter les indicateurs INSEE (complémentaires)
    try:
        insee_data = insee_scraper.get_indicators()
        
        if insee_data.get('success'):
            for key, indicator in insee_data['indicators'].items():
                results['indicators'][f'insee_{key}'] = indicator
    except Exception as e:
        logger.error(f"Erreur INSEE: {e}")
    
    return results


# Exemple d'utilisation
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    scraper = INSEEScraper()
    data = scraper.get_indicators()
    
    print("=" * 60)
    print("📊 Indicateurs INSEE")
    print("=" * 60)
    
    if data.get('success'):
        for key, indicator in data['indicators'].items():
            print(f"\n{indicator['name']}: {indicator['value']} {indicator['unit']}")
            print(f"  Période: {indicator['period']}")
            print(f"  Source: {indicator.get('source', 'N/A')}")
    else:
        print("❌ Erreur récupération données")