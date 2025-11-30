# Flask/eurostat_connector.py
"""
Connecteur Eurostat pour indicateurs économiques
Sources : https://ec.europa.eu/eurostat/web/main/data/web-services
Utilisation : Éducation et Recherche
"""

import logging
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class IndicatorCategory(Enum):
    """Catégories d'indicateurs"""
    MACRO = "macro"
    EMPLOYMENT = "employment"
    PRICES = "prices"
    TRADE = "trade"
    FINANCE = "finance"
    PRODUCTION = "production"


@dataclass
class EurostatIndicator:
    """Définition d'un indicateur Eurostat"""
    id: str
    name: str
    category: IndicatorCategory
    dataset: str
    filters: Dict[str, str]
    unit: str
    description: str
    frequency: str


class EurostatConnector:
    """Connecteur pour l'API Eurostat"""
    
    BASE_URL = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"
    
    # === INDICATEURS DISPONIBLES (15 indicateurs) ===
    AVAILABLE_INDICATORS = {
        # DÉFAUT (4 indicateurs)
        'gdp': EurostatIndicator(
            id='gdp',
            name='PIB (Produit Intérieur Brut)',
            category=IndicatorCategory.MACRO,
            dataset='namq_10_gdp',
            filters={'geo': 'FR', 'unit': 'CP_MEUR', 'na_item': 'B1GQ', 's_adj': 'SCA'},
            unit='Milliards €',
            description='PIB en prix courants désaisonnalisé',
            frequency='Q'
        ),
        'unemployment': EurostatIndicator(
            id='unemployment',
            name='Taux de chômage',
            category=IndicatorCategory.EMPLOYMENT,
            dataset='une_rt_m',
            filters={'geo': 'FR', 's_adj': 'SA', 'age': 'TOTAL', 'sex': 'T'},
            unit='%',
            description='Taux de chômage désaisonnalisé',
            frequency='M'
        ),
        'hicp': EurostatIndicator(
            id='hicp',
            name='Inflation (IPCH)',
            category=IndicatorCategory.PRICES,
            dataset='prc_hicp_manr',
            filters={'geo': 'FR', 'coicop': 'CP00', 'unit': 'RCH_A'},
            unit='%',
            description='Variation annuelle des prix à la consommation',
            frequency='M'
        ),
        'trade_balance': EurostatIndicator(
            id='trade_balance',
            name='Balance commerciale',
            category=IndicatorCategory.TRADE,
            dataset='ext_lt_intratrd',
            filters={'geo': 'FR', 'partner': 'EXT_EU27_2020', 'sitc06': 'TOTAL', 'stk_flow': 'BAL'},
            unit='Millions €',
            description='Solde commercial (exports - imports)',
            frequency='M'
        ),
        
        # SUPPLÉMENTAIRES (11 indicateurs sélectionnables)
        'industrial_production': EurostatIndicator(
            id='industrial_production',
            name='Production industrielle',
            category=IndicatorCategory.PRODUCTION,
            dataset='sts_inpr_m',
            filters={'geo': 'FR', 'nace_r2': 'B-D', 's_adj': 'SCA', 'unit': 'I15'},
            unit='Indice (2015=100)',
            description='Production industrielle désaisonnalisée',
            frequency='M'
        ),
        'government_debt': EurostatIndicator(
            id='government_debt',
            name='Dette publique',
            category=IndicatorCategory.FINANCE,
            dataset='gov_10dd_edpt1',
            filters={'geo': 'FR', 'na_item': 'GD', 'sector': 'S13', 'unit': 'PC_GDP'},
            unit='% PIB',
            description='Dette publique en % du PIB',
            frequency='A'
        ),
        'government_deficit': EurostatIndicator(
            id='government_deficit',
            name='Déficit public',
            category=IndicatorCategory.FINANCE,
            dataset='gov_10dd_edpt1',
            filters={'geo': 'FR', 'na_item': 'B9', 'sector': 'S13', 'unit': 'PC_GDP'},
            unit='% PIB',
            description='Déficit/excédent public en % du PIB',
            frequency='A'
        ),
        'retail_trade': EurostatIndicator(
            id='retail_trade',
            name='Ventes au détail',
            category=IndicatorCategory.TRADE,
            dataset='sts_trtu_m',
            filters={'geo': 'FR', 'nace_r2': 'G47', 's_adj': 'SCA', 'indic_bt': 'TOVT', 'unit': 'I15'},
            unit='Indice (2015=100)',
            description='Volume ventes au détail désaisonnalisé',
            frequency='M'
        ),
        'construction_production': EurostatIndicator(
            id='construction_production',
            name='Production du bâtiment',
            category=IndicatorCategory.PRODUCTION,
            dataset='sts_copr_m',
            filters={'geo': 'FR', 'nace_r2': 'F', 's_adj': 'SCA', 'indic_bt': 'PROD', 'unit': 'I15'},
            unit='Indice (2015=100)',
            description='Production dans la construction',
            frequency='M'
        ),
        'labour_cost': EurostatIndicator(
            id='labour_cost',
            name='Coût du travail',
            category=IndicatorCategory.EMPLOYMENT,
            dataset='lc_lci_r2_q',
            filters={'geo': 'FR', 'nace_r2': 'B-S', 'lcstruct': 'D1_D4_MD5', 's_adj': 'SCA', 'unit': 'I16'},
            unit='Indice (2016=100)',
            description='Coût du travail désaisonnalisé',
            frequency='Q'
        ),
        'house_prices': EurostatIndicator(
            id='house_prices',
            name='Prix de l\'immobilier',
            category=IndicatorCategory.PRICES,
            dataset='prc_hpi_q',
            filters={'geo': 'FR', 'purchase': 'TOTAL', 'unit': 'I15_Q'},
            unit='Indice (2015=100)',
            description='Prix des logements',
            frequency='Q'
        ),
        'exports': EurostatIndicator(
            id='exports',
            name='Exportations',
            category=IndicatorCategory.TRADE,
            dataset='ext_lt_intratrd',
            filters={'geo': 'FR', 'partner': 'EXT_EU27_2020', 'sitc06': 'TOTAL', 'stk_flow': 'EXP'},
            unit='Millions €',
            description='Exportations hors UE',
            frequency='M'
        ),
        'imports': EurostatIndicator(
            id='imports',
            name='Importations',
            category=IndicatorCategory.TRADE,
            dataset='ext_lt_intratrd',
            filters={'geo': 'FR', 'partner': 'EXT_EU27_2020', 'sitc06': 'TOTAL', 'stk_flow': 'IMP'},
            unit='Millions €',
            description='Importations hors UE',
            frequency='M'
        ),
        'consumer_confidence': EurostatIndicator(
            id='consumer_confidence',
            name='Confiance des consommateurs',
            category=IndicatorCategory.MACRO,
            dataset='ei_bsco_m',
            filters={'geo': 'FR', 's_adj': 'SA', 'indic': 'BS-CSMCI-BAL'},
            unit='Solde',
            description='Confiance des consommateurs',
            frequency='M'
        ),
        'business_confidence': EurostatIndicator(
            id='business_confidence',
            name='Confiance des entreprises',
            category=IndicatorCategory.MACRO,
            dataset='ei_bsin_m_r2',
            filters={'geo': 'FR', 's_adj': 'SA', 'indic': 'BS-ICI-BAL', 'nace_r2': 'B-E'},
            unit='Solde',
            description='Confiance dans l\'industrie',
            frequency='M'
        )
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GEO-Educational-Research/1.0',
            'Accept': 'application/json'
        })
        logger.info("✅ Connecteur Eurostat initialisé")
    
    def get_indicator_data(self, indicator_id: str, last_n: int = 12) -> Dict[str, Any]:
        """Récupère les données d'un indicateur"""
        if indicator_id not in self.AVAILABLE_INDICATORS:
            return {'success': False, 'error': f'Indicateur {indicator_id} inconnu'}
        
        indicator = self.AVAILABLE_INDICATORS[indicator_id]
        
        try:
            url = f"{self.BASE_URL}/{indicator.dataset}"
            params = {
                'format': 'JSON',
                'lang': 'FR',
                **indicator.filters,
                'lastTimePeriod': last_n
            }
            
            logger.info(f"📊 Requête: {indicator.name}")
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                parsed = self._parse_response(data, indicator)
                
                if parsed['success']:
                    logger.info(f"✅ {indicator.name}: {parsed['current_value']} {indicator.unit}")
                    return parsed
            
            logger.warning(f"⚠️ Fallback pour {indicator.name}")
            return self._get_fallback(indicator)
                
        except Exception as e:
            logger.error(f"❌ Erreur {indicator_id}: {e}")
            return self._get_fallback(indicator)
    
    def _parse_response(self, data: Dict, indicator: EurostatIndicator) -> Dict[str, Any]:
        """Parse la réponse Eurostat"""
        try:
            if 'value' not in data or not data['value']:
                return {'success': False}
            
            values = data['value']
            dimensions = data.get('dimension', {})
            time_dim = dimensions.get('time', {}).get('category', {}).get('index', {})
            
            if not values or not time_dim:
                return {'success': False}
            
            sorted_times = sorted(time_dim.keys(), key=lambda x: time_dim[x])
            
            if not sorted_times:
                return {'success': False}
            
            # Dernière valeur
            latest_time = sorted_times[-1]
            latest_value = float(values.get(str(time_dim[latest_time]), 0))
            
            # Valeur précédente
            previous_value = latest_value
            if len(sorted_times) > 1:
                previous_time = sorted_times[-2]
                previous_value = float(values.get(str(time_dim[previous_time]), latest_value))
            
            # Variation
            change = latest_value - previous_value
            change_percent = (change / previous_value * 100) if previous_value != 0 else 0
            
            # Historique
            historical = []
            for time_key in sorted_times[-12:]:
                val_index = str(time_dim[time_key])
                if val_index in values:
                    historical.append({
                        'period': time_key,
                        'value': float(values[val_index])
                    })
            
            return {
                'success': True,
                'indicator_id': indicator.id,
                'indicator_name': indicator.name,
                'current_value': round(latest_value, 2),
                'previous_value': round(previous_value, 2),
                'change': round(change, 2),
                'change_percent': round(change_percent, 2),
                'unit': indicator.unit,
                'period': latest_time,
                'source': 'Eurostat',
                'dataset': indicator.dataset,
                'description': indicator.description,
                'frequency': indicator.frequency,
                'category': indicator.category.value,
                'last_update': datetime.now().isoformat(),
                'historical': historical
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur parsing: {e}")
            return {'success': False}
    
    def _get_fallback(self, indicator: EurostatIndicator) -> Dict[str, Any]:
        """Données de référence"""
        fallbacks = {
            'gdp': {'value': 695.2, 'period': '2024-Q3'},
            'unemployment': {'value': 7.1, 'period': '2024-10'},
            'hicp': {'value': 2.2, 'period': '2024-10'},
            'trade_balance': {'value': -4.8, 'period': '2024-09'},
            'industrial_production': {'value': 102.5, 'period': '2024-09'},
            'government_debt': {'value': 112.0, 'period': '2023'},
            'government_deficit': {'value': -4.9, 'period': '2023'},
            'retail_trade': {'value': 105.3, 'period': '2024-09'},
            'construction_production': {'value': 98.7, 'period': '2024-09'},
            'labour_cost': {'value': 118.5, 'period': '2024-Q2'},
            'house_prices': {'value': 128.4, 'period': '2024-Q2'},
            'exports': {'value': 45200, 'period': '2024-09'},
            'imports': {'value': 50000, 'period': '2024-09'},
            'consumer_confidence': {'value': -20, 'period': '2024-10'},
            'business_confidence': {'value': 99, 'period': '2024-10'}
        }
        
        fb = fallbacks.get(indicator.id, {'value': 0, 'period': '2024'})
        
        return {
            'success': True,
            'indicator_id': indicator.id,
            'indicator_name': indicator.name,
            'current_value': fb['value'],
            'previous_value': fb['value'],
            'change': 0,
            'change_percent': 0,
            'unit': indicator.unit,
            'period': fb['period'],
            'source': 'Données de référence',
            'dataset': indicator.dataset,
            'description': indicator.description,
            'frequency': indicator.frequency,
            'category': indicator.category.value,
            'last_update': datetime.now().isoformat(),
            'note': 'Données de référence - API temporairement indisponible',
            'historical': []
        }
    
    def get_multiple_indicators(self, indicator_ids: List[str]) -> Dict[str, Any]:
        """Récupère plusieurs indicateurs"""
        results = {}
        
        for indicator_id in indicator_ids:
            results[indicator_id] = self.get_indicator_data(indicator_id)
        
        successful = sum(1 for r in results.values() if r.get('success'))
        
        return {
            'success': True,
            'indicators': results,
            'stats': {
                'total': len(indicator_ids),
                'successful': successful,
                'failed': len(indicator_ids) - successful
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def get_available_indicators(self) -> Dict[str, Any]:
        """Liste des indicateurs disponibles"""
        indicators_list = []
        
        for indicator_id, indicator in self.AVAILABLE_INDICATORS.items():
            indicators_list.append({
                'id': indicator_id,
                'name': indicator.name,
                'category': indicator.category.value,
                'unit': indicator.unit,
                'description': indicator.description,
                'frequency': indicator.frequency,
                'dataset': indicator.dataset
            })
        
        # Grouper par catégorie
        by_category = {}
        for ind in indicators_list:
            category = ind['category']
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(ind)
        
        return {
            'success': True,
            'total_indicators': len(indicators_list),
            'indicators': indicators_list,
            'by_category': by_category,
            'default_indicators': ['gdp', 'unemployment', 'hicp', 'trade_balance']
        }