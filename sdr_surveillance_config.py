# Flask/sdr_surveillance_config.py
"""
Configuration de la surveillance SDR
"""

# Fréquences géopolitiques prioritaires pour surveillance
GEOPOLITICAL_PRIORITY_FREQUENCIES = {
    'diplomatic': [5732, 8992, 11175],
    'military': [4625, 6998, 8131, 11175],
    'maritime': [2182, 14313, 15680],
    'aviation': [121500, 123100],
    'emergency': [2182, 121500, 15680]
}

# Serveurs KiwiSDR critiques (régions stratégiques)
CRITICAL_SERVERS = [
    'http://kiwisdr.com/public/',
    'http://websdr.ewi.utwente.nl:8901/',
    'http://oh3ac.dy.fi:8073/',  # Finlande
    'http://vk2dds.com:8073/',   # Australie
    'http://ja2ykz.com:8073/',   # Japon
]

# Seuils d'alertes par région
REGIONAL_THRESHOLDS = {
    'europe': {'blackout': 0.4, 'peak_std': 2.5},
    'asia': {'blackout': 0.6, 'peak_std': 3.0},
    'americas': {'blackout': 0.5, 'peak_std': 2.8},
    'global': {'blackout': 0.5, 'peak_std': 2.5}
}