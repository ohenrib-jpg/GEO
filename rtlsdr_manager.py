# Flask/rtlsdr_manager.py
"""
Manager RTL-SDR unifié pour l'analyse waterfall
"""

import logging
import numpy as np
from datetime import datetime, timedelta
import subprocess
import tempfile
import os
import json

logger = logging.getLogger(__name__)

class RTLSDRAnalyzer:
    """Analyseur RTL-SDR pour données waterfall et spectrale"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.rtl_power_available = self._check_rtl_power()
        
    def _check_rtl_power(self):
        """Vérifie si rtl_power est disponible"""
        try:
            result = subprocess.run(['which', 'rtl_power'], 
                                  capture_output=True, timeout=2)
            return result.returncode == 0
        except:
            logger.warning("rtl_power non disponible")
            return False
    
    def capture_waterfall_data(self, frequency_khz, duration_seconds=30):
        """
        Capture les données waterfall via RTL-SDR
        """
        if not self.rtl_power_available:
            return self._get_simulated_waterfall(frequency_khz, duration_seconds)
        
        try:
            # Utiliser rtl_power pour capturer le spectre
            freq_start = frequency_khz - 500  # ±500 kHz
            freq_end = frequency_khz + 500
            integration_time = min(duration_seconds, 10)  # Max 10s pour rtl_power
            
            with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
                output_file = f.name
            
            # Commande rtl_power
            cmd = [
                'rtl_power',
                '-f', f'{freq_start}k:{freq_end}k:1k',
                '-i', str(integration_time),
                '-1',
                output_file
            ]
            
            # Exécuter
            result = subprocess.run(cmd, capture_output=True, timeout=integration_time + 5)
            
            if result.returncode == 0:
                waterfall_data = self._parse_rtl_power_waterfall(output_file)
                os.unlink(output_file)
                return waterfall_data
            else:
                logger.error(f"rtl_power error: {result.stderr.decode()}")
                return self._get_simulated_waterfall(frequency_khz, duration_seconds)
                
        except Exception as e:
            logger.error(f"Erreur capture RTL-SDR: {e}")
            return self._get_simulated_waterfall(frequency_khz, duration_seconds)
    
    def _parse_rtl_power_waterfall(self, filename):
        """Parse la sortie CSV de rtl_power pour waterfall"""
        try:
            import csv
            frequencies = []
            power_matrix = []
            
            with open(filename, 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) > 6:
                        # Extraire fréquences et puissances
                        freq_low = float(row[2])
                        freq_high = float(row[3])
                        power_values = [float(x) for x in row[6:] if x.strip()]
                        
                        # Ajouter aux données
                        freqs = np.linspace(freq_low, freq_high, len(power_values))
                        frequencies.extend(freqs)
                        power_matrix.append(power_values)
            
            # Convertir en format waterfall
            if power_matrix:
                # Transposer pour avoir temps en lignes
                waterfall = np.array(power_matrix).T
                return {
                    "frequencies": [f/1000 for f in frequencies[:len(waterfall[0])]],  # kHz
                    "waterfall": waterfall.tolist(),
                    "type": "rtlsdr_real"
                }
            else:
                raise ValueError("Aucune donnée dans le fichier")
                
        except Exception as e:
            logger.error(f"Erreur parsing waterfall: {e}")
            raise
    
    def _get_simulated_waterfall(self, frequency_khz, duration_seconds):
        """Données waterfall simulées pour tests"""
        # Générer des données réalistes
        num_freqs = 1000
        num_times = min(int(duration_seconds * 2), 100)  # 2 échantillons par seconde
        
        frequencies = np.linspace(frequency_khz - 500, frequency_khz + 500, num_freqs)
        
        # Générer le waterfall avec quelques émissions
        waterfall = np.random.normal(-100, 5, (num_times, num_freqs))
        
        # Ajouter quelques émissions simulées
        for _ in range(np.random.randint(3, 8)):
            center_idx = np.random.randint(100, 900)
            width = np.random.randint(10, 50)
            strength = np.random.uniform(-70, -50)
            duration = np.random.randint(5, 20)
            start_time = np.random.randint(0, num_times - duration)
            
            for t in range(start_time, start_time + duration):
                for f in range(center_idx - width, center_idx + width):
                    if 0 <= f < num_freqs:
                        distance = abs(f - center_idx)
                        waterfall[t, f] = strength * np.exp(-(distance ** 2) / (width / 2) ** 2)
        
        return {
            "frequencies": frequencies.tolist(),
            "waterfall": waterfall.tolist(),
            "type": "rtlsdr_simulated",
            "note": "Données simulées - RTL-SDR non disponible"
        }
    
    def get_spectrum_data(self, center_freq_khz, span_khz=1000):
        """Récupère les données spectrales"""
        waterfall_data = self.capture_waterfall_data(center_freq_khz, 1)
        
        # Moyenner le waterfall pour avoir un spectre
        if waterfall_data and "waterfall" in waterfall_data:
            waterfall_array = np.array(waterfall_data["waterfall"])
            spectrum = np.mean(waterfall_array, axis=0)
            
            return {
                "frequencies": waterfall_data["frequencies"],
                "powers": spectrum.tolist(),
                "center_freq_khz": center_freq_khz,
                "span_khz": span_khz
            }
        
        return None
    
    def detect_emissions(self, frequency_khz, threshold_db=-70):
        """Détecte les émissions autour d'une fréquence"""
        spectrum_data = self.get_spectrum_data(frequency_khz)
        
        if not spectrum_data:
            return []
        
        frequencies = np.array(spectrum_data["frequencies"])
        powers = np.array(spectrum_data["powers"])
        
        # Détecter les pics
        from scipy.signal import find_peaks
        peaks, properties = find_peaks(powers, height=threshold_db, distance=10)
        
        emissions = []
        for i, peak_idx in enumerate(peaks):
            emissions.append({
                "frequency_khz": float(frequencies[peak_idx]),
                "power_db": float(powers[peak_idx]),
                "bandwidth_khz": 1.0,  # Estimation
                "distance_from_target": abs(frequencies[peak_idx] - frequency_khz)
            })
        
        return emissions