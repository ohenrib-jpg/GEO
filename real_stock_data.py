# Flask/real_stock_data.py - VERSION CORRIGÉE
import logging
import yfinance as yf
from datetime import datetime, timedelta
import requests

logger = logging.getLogger(__name__)

class RealStockData:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        
    def get_geopolitical_indices(self):
        """Récupère les indices boursiers géopolitiques importants - SYMBOLES CORRIGÉS"""
        indices = {
            'RSX': {'name': 'Russia ETF', 'country': 'Russia'},  # ETF Russie au lieu de RTSI
            '^GSPC': {'name': 'S&P 500', 'country': 'USA'},     # ^ pour les indices
            '^FTSE': {'name': 'FTSE 100', 'country': 'UK'},     # ^ pour les indices
            '^GDAXI': {'name': 'DAX Performance', 'country': 'Germany'},
            '^FCHI': {'name': 'CAC 40', 'country': 'France'},
            '^N225': {'name': 'Nikkei 225', 'country': 'Japan'},
            '^HSI': {'name': 'Hang Seng', 'country': 'Hong Kong'},
            '000001.SS': {'name': 'Shanghai Composite', 'country': 'China'},
        }
        
        results = {}
        for symbol, info in indices.items():
            try:
                stock = yf.Ticker(symbol)
                hist = stock.history(period="5d")
                
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    previous_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
                    change_percent = ((current_price - previous_price) / previous_price) * 100
                    
                    results[symbol] = {
                        'name': info['name'],
                        'country': info['country'],
                        'current_price': round(current_price, 2),
                        'change_percent': round(change_percent, 2),
                        'change_direction': 'up' if change_percent > 0 else 'down',
                        'last_updated': datetime.utcnow().isoformat()
                    }
                else:
                    # Données de secours si pas de données
                    results[symbol] = {
                        'name': info['name'],
                        'country': info['country'],
                        'current_price': 0,
                        'change_percent': 0,
                        'change_direction': 'stable',
                        'note': 'Données non disponibles',
                        'last_updated': datetime.utcnow().isoformat()
                    }
                    
            except Exception as e:
                logger.error(f"Erreur récupération {symbol}: {e}")
                results[symbol] = {
                    'name': info['name'],
                    'country': info['country'],
                    'error': str(e),
                    'current_price': 0,
                    'change_percent': 0,
                    'change_direction': 'stable',
                    'last_updated': datetime.utcnow().isoformat()
                }
        
        return results
    
    def get_commodity_prices(self):
        """Récupère les prix des matières premières géopolitiques - SYMBOLES CORRIGÉS"""
        commodities = {
            'CL=F': {'name': 'Oil Crude', 'unit': 'USD/barrel'},
            'NG=F': {'name': 'Natural Gas', 'unit': 'USD/MMBtu'},
            'GC=F': {'name': 'Gold', 'unit': 'USD/ounce'},
            'SI=F': {'name': 'Silver', 'unit': 'USD/ounce'},
            'ZC=F': {'name': 'Corn', 'unit': 'USD/bushel'},
            'ZW=F': {'name': 'Wheat', 'unit': 'USD/bushel'},
            'HG=F': {'name': 'Copper', 'unit': 'USD/pound'}
        }
        
        results = {}
        for symbol, info in commodities.items():
            try:
                stock = yf.Ticker(symbol)
                hist = stock.history(period="2d")
                
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    previous_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
                    change_percent = ((current_price - previous_price) / previous_price) * 100
                    
                    results[symbol] = {
                        'name': info['name'],
                        'unit': info['unit'],
                        'current_price': round(current_price, 2),
                        'change_percent': round(change_percent, 2),
                        'change_direction': 'up' if change_percent > 0 else 'down',
                        'last_updated': datetime.utcnow().isoformat()
                    }
                else:
                    results[symbol] = {
                        'name': info['name'],
                        'unit': info['unit'],
                        'current_price': 0,
                        'change_percent': 0,
                        'change_direction': 'stable',
                        'note': 'Données non disponibles',
                        'last_updated': datetime.utcnow().isoformat()
                    }
                    
            except Exception as e:
                logger.error(f"Erreur récupération {symbol}: {e}")
                results[symbol] = {
                    'name': info['name'],
                    'unit': info['unit'],
                    'error': str(e),
                    'current_price': 0,
                    'change_percent': 0,
                    'change_direction': 'stable',
                    'last_updated': datetime.utcnow().isoformat()
                }
        
        return results
    
    def get_crypto_prices(self):
        """Récupère les prix des cryptomonnaies (indicateurs de risque)"""
        cryptos = {
            'BTC-USD': 'Bitcoin',
            'ETH-USD': 'Ethereum',
            'USDT-USD': 'Tether',
            'BNB-USD': 'Binance Coin'
        }
        
        results = {}
        for symbol, name in cryptos.items():
            try:
                stock = yf.Ticker(symbol)
                hist = stock.history(period="2d")
                
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    previous_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
                    change_percent = ((current_price - previous_price) / previous_price) * 100
                    
                    results[symbol] = {
                        'name': name,
                        'current_price': round(current_price, 2),
                        'change_percent': round(change_percent, 2),
                        'change_direction': 'up' if change_percent > 0 else 'down',
                        'last_updated': datetime.utcnow().isoformat()
                    }
                    
            except Exception as e:
                logger.error(f"Erreur récupération crypto {symbol}: {e}")
        
        return results