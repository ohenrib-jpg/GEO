# Flask/spectrum_analyzer.py
"""
Analyseur automatique de spectre pour comptage de pics
Compatible avec WebSDR et RTL-SDR local
"""

import logging
import numpy as np
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from scipy import signal
from scipy.ndimage import maximum_filter
import json

logger = logging.getLogger(__name__)


class SpectrumAnalyzer:
    """
    Analyse automatique du spectre pour compter les pics d'émission
    """
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GeoPolMonitor/1.0'
        })
        
    def detect_peaks_in_spectrum(self, frequencies: np.ndarray, 
                                 power_spectrum: np.ndarray,
                                 threshold_db: float = -80,
                                 min_distance: float = 1.0) -> List[Dict[str, float]]:
        """
        Détecte les pics dans un spectre de puissance
        
        Args:
            frequencies: Array des fréquences (en kHz)
            power_spectrum: Array des puissances (en dB)
            threshold_db: Seuil minimum de détection (dB)
            min_distance: Distance minimale entre pics (kHz)
        
        Returns:
            Liste des pics détectés avec {frequency, power, bandwidth}
        """
        try:
            # Convertir min_distance en indices
            freq_step = frequencies[1] - frequencies[0]
            min_distance_idx = int(min_distance / freq_step)
            
            # Filtrage pour réduire le bruit
            filtered_spectrum = signal.savgol_filter(power_spectrum, 11, 3)
            
            # Trouver les maxima locaux
            local_max = maximum_filter(filtered_spectrum, size=min_distance_idx)
            peaks_mask = (filtered_spectrum == local_max) & (filtered_spectrum > threshold_db)
            
            peak_indices = np.where(peaks_mask)[0]
            
            peaks = []
            for idx in peak_indices:
                # Estimer la largeur du pic (bandwidth)
                bandwidth = self._estimate_peak_bandwidth(
                    filtered_spectrum, idx, threshold_db - 3
                )
                
                peaks.append({
                    'frequency_khz': float(frequencies[idx]),
                    'power_db': float(filtered_spectrum[idx]),
                    'bandwidth_khz': float(bandwidth * freq_step),
                    'index': int(idx)
                })
            
            # Trier par puissance décroissante
            peaks.sort(key=lambda x: x['power_db'], reverse=True)
            
            return peaks
            
        except Exception as e:
            logger.error(f"Erreur détection pics: {e}")
            return []
    
    def _estimate_peak_bandwidth(self, spectrum: np.ndarray, 
                                 peak_idx: int, 
                                 threshold_db: float) -> int:
        """Estime la largeur d'un pic (en nombre d'indices)"""
        try:
            # Chercher vers la gauche
            left_idx = peak_idx
            while left_idx > 0 and spectrum[left_idx] > threshold_db:
                left_idx -= 1
            
            # Chercher vers la droite
            right_idx = peak_idx
            while right_idx < len(spectrum) - 1 and spectrum[right_idx] > threshold_db:
                right_idx += 1
            
            return right_idx - left_idx
            
        except:
            return 1


class WebSDRClient:
    """
    Client pour récupérer les données spectrales depuis WebSDR
    
    WebSDR de l'Université de Twente expose des données FFT publiques
    """
    
    WEBSDR_BASE_URL = "http://websdr.ewi.utwente.nl:8901"
    
    def __init__(self):
        self.session = requests.Session()
        self.session_id = None
        
    def get_spectrum_data(self, center_freq_khz: int, 
                         span_khz: int = 10) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """
        Récupère les données spectrales depuis WebSDR
        
        Args:
            center_freq_khz: Fréquence centrale (kHz)
            span_khz: Largeur spectrale (kHz)
        
        Returns:
            (frequencies, power_spectrum) ou None si échec
        """
        try:
            # WebSDR utilise une API spécifique pour récupérer le spectre
            # Format: /~~fft?f=14300&b=10000
            
            url = f"{self.WEBSDR_BASE_URL}/~~fft"
            params = {
                'f': center_freq_khz,
                'b': span_khz * 1000  # WebSDR attend en Hz
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            # Parser la réponse FFT (format spécifique WebSDR)
            fft_data = self._parse_websdr_fft(response.content)
            
            if fft_data is None:
                return None
            
            # Créer l'array de fréquences
            num_points = len(fft_data)
            freq_start = center_freq_khz - span_khz / 2
            freq_end = center_freq_khz + span_khz / 2
            frequencies = np.linspace(freq_start, freq_end, num_points)
            
            return frequencies, fft_data
            
        except Exception as e:
            logger.error(f"Erreur récupération WebSDR: {e}")
            return None
    
    def _parse_websdr_fft(self, data: bytes) -> Optional[np.ndarray]:
        """
        Parse les données FFT de WebSDR
        Format propriétaire, adapté selon la réponse réelle
        """
        try:
            # WebSDR retourne généralement du binaire ou du JSON
            # Exemple de parsing (à adapter selon la vraie API)
            
            if data.startswith(b'{'):
                # Format JSON
                json_data = json.loads(data)
                return np.array(json_data.get('spectrum', []))
            else:
                # Format binaire (int16 ou float32)
                # Tenter int16 en premier
                spectrum = np.frombuffer(data, dtype=np.int16)
                # Convertir en dB
                spectrum_db = 20 * np.log10(np.abs(spectrum) + 1e-10)
                return spectrum_db
                
        except Exception as e:
            logger.error(f"Erreur parsing FFT: {e}")
            return None


class RTLSDRClient:
    """
    Client pour RTL-SDR local (si disponible)
    Utilise rtl_power pour scanner le spectre
    """
    
    def __init__(self):
        self.rtl_power_available = self._check_rtl_power()
    
    def _check_rtl_power(self) -> bool:
        """Vérifie si rtl_power est installé"""
        try:
            import subprocess
            result = subprocess.run(['which', 'rtl_power'], 
                                  capture_output=True, 
                                  timeout=2)
            return result.returncode == 0
        except:
            return False
    
    def get_spectrum_data(self, center_freq_khz: int,
                         span_khz: int = 10,
                         integration_time: int = 1) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """
        Scanne le spectre avec RTL-SDR local
        
        Args:
            center_freq_khz: Fréquence centrale
            span_khz: Largeur spectrale
            integration_time: Temps d'intégration (secondes)
        
        Returns:
            (frequencies, power_spectrum) ou None
        """
        if not self.rtl_power_available:
            logger.warning("rtl_power non disponible")
            return None
        
        try:
            import subprocess
            import tempfile
            import os
            
            # Créer un fichier temporaire pour les résultats
            with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
                output_file = f.name
            
            # Calculer les paramètres
            freq_start = (center_freq_khz - span_khz / 2) * 1000  # Hz
            freq_end = (center_freq_khz + span_khz / 2) * 1000    # Hz
            
            # Commande rtl_power
            cmd = [
                'rtl_power',
                '-f', f'{int(freq_start)}:{int(freq_end)}:1k',  # start:end:step
                '-i', str(integration_time),
                '-1',  # Single shot
                output_file
            ]
            
            # Exécuter rtl_power
            result = subprocess.run(cmd, 
                                  capture_output=True, 
                                  timeout=integration_time + 5)
            
            if result.returncode != 0:
                logger.error(f"rtl_power error: {result.stderr.decode()}")
                return None
            
            # Lire les résultats
            frequencies, power_spectrum = self._parse_rtl_power_output(output_file)
            
            # Nettoyer
            os.unlink(output_file)
            
            return frequencies / 1000, power_spectrum  # Convertir en kHz
            
        except Exception as e:
            logger.error(f"Erreur RTL-SDR: {e}")
            return None
    
    def _parse_rtl_power_output(self, filename: str) -> Tuple[np.ndarray, np.ndarray]:
        """Parse la sortie CSV de rtl_power"""
        import csv
        
        frequencies = []
        powers = []
        
        with open(filename, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                # Format rtl_power: date, time, freq_low, freq_high, step, samples, power...
                if len(row) > 6:
                    freq_low = float(row[2])
                    freq_high = float(row[3])
                    center = (freq_low + freq_high) / 2
                    
                    # Les puissances sont après la colonne 6
                    power_values = [float(x) for x in row[6:]]
                    
                    frequencies.extend(
                        np.linspace(freq_low, freq_high, len(power_values))
                    )
                    powers.extend(power_values)
        
        return np.array(frequencies), np.array(powers)


class AutomatedSpectrumMonitor:
    """
    Système de monitoring automatique du spectre
    Compte automatiquement les pics sur les fréquences surveillées
    """
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.analyzer = SpectrumAnalyzer(db_manager)
        
        # Essayer différentes sources de données
        self.websdr = WebSDRClient()
        self.rtlsdr = RTLSDRClient()
        
        self.default_source = 'websdr'  # ou 'rtlsdr' si disponible
        
        if self.rtlsdr.rtl_power_available:
            logger.info("✅ RTL-SDR disponible - Mode local activé")
            self.default_source = 'rtlsdr'
        else:
            logger.info("ℹ️ RTL-SDR non disponible - Mode WebSDR")
    
    def monitor_frequency(self, frequency_id: int, 
                         frequency_khz: int,
                         duration_minutes: int = 60,
                         scan_interval_seconds: int = 300) -> Dict[str, Any]:
        """
        Surveille automatiquement une fréquence
        
        Args:
            frequency_id: ID de la fréquence dans la DB
            frequency_khz: Fréquence en kHz
            duration_minutes: Durée totale de surveillance
            scan_interval_seconds: Intervalle entre chaque scan
        
        Returns:
            Statistiques de surveillance
        """
        logger.info(f"🔍 Début surveillance automatique {frequency_khz} kHz")
        
        import time
        start_time = time.time()
        end_time = start_time + duration_minutes * 60
        
        total_peaks = 0
        peak_history = []
        scan_count = 0
        
        while time.time() < end_time:
            try:
                # Récupérer le spectre
                spectrum_data = self._get_spectrum_data(
                    frequency_khz,
                    span_khz=10
                )
                
                if spectrum_data is not None:
                    frequencies, power_spectrum = spectrum_data
                    
                    # Détecter les pics
                    peaks = self.analyzer.detect_peaks_in_spectrum(
                        frequencies,
                        power_spectrum,
                        threshold_db=-80,
                        min_distance=1.0
                    )
                    
                    # Filtrer les pics proches de la fréquence cible
                    # (±5 kHz autour de la fréquence)
                    relevant_peaks = [
                        p for p in peaks
                        if abs(p['frequency_khz'] - frequency_khz) <= 5
                    ]
                    
                    num_peaks = len(relevant_peaks)
                    total_peaks += num_peaks
                    scan_count += 1
                    
                    peak_history.append({
                        'timestamp': datetime.utcnow().isoformat(),
                        'peak_count': num_peaks,
                        'peaks': relevant_peaks
                    })
                    
                    if num_peaks > 0:
                        logger.info(f"📡 {num_peaks} pics détectés à {frequency_khz} kHz")
                
                # Attendre avant le prochain scan
                time.sleep(scan_interval_seconds)
                
            except Exception as e:
                logger.error(f"Erreur durant scan: {e}")
                time.sleep(scan_interval_seconds)
        
        # Enregistrer les résultats
        avg_peaks_per_scan = total_peaks / scan_count if scan_count > 0 else 0
        
        result = {
            'frequency_id': frequency_id,
            'frequency_khz': frequency_khz,
            'duration_minutes': duration_minutes,
            'total_scans': scan_count,
            'total_peaks_detected': total_peaks,
            'average_peaks_per_scan': round(avg_peaks_per_scan, 2),
            'peak_history': peak_history
        }
        
        # Sauvegarder dans la DB
        self._save_monitoring_results(result)
        
        logger.info(f"✅ Surveillance terminée: {total_peaks} pics au total")
        
        return result
    
    def _get_spectrum_data(self, center_freq_khz: int, 
                          span_khz: int = 10) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """
        Récupère les données spectrales depuis la meilleure source disponible
        """
        if self.default_source == 'rtlsdr':
            data = self.rtlsdr.get_spectrum_data(center_freq_khz, span_khz)
            if data is not None:
                return data
        
        # Fallback sur WebSDR
        return self.websdr.get_spectrum_data(center_freq_khz, span_khz)
    
    def _save_monitoring_results(self, result: Dict[str, Any]):
        """Enregistre les résultats dans la base de données"""
        try:
            conn = self.db_manager.get_connection()
            cur = conn.cursor()
            
            today = datetime.utcnow().date()
            
            # Mettre à jour l'activité quotidienne
            cur.execute("""
                INSERT INTO kiwisdr_frequency_activity 
                (frequency_id, date, emission_count, observation_duration)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(frequency_id, date) 
                DO UPDATE SET 
                    emission_count = emission_count + ?,
                    observation_duration = observation_duration + ?
            """, (
                result['frequency_id'],
                today,
                result['total_peaks_detected'],
                result['duration_minutes'] * 60,
                result['total_peaks_detected'],
                result['duration_minutes'] * 60
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"💾 Résultats sauvegardés pour fréquence {result['frequency_id']}")
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde résultats: {e}")
    
    def get_available_sources(self) -> Dict[str, bool]:
        """Retourne les sources de données disponibles"""
        return {
            'websdr': True,  # Toujours disponible (public)
            'rtlsdr': self.rtlsdr.rtl_power_available,
            'default': self.default_source
        }


# Fonction de simulation pour tests
def simulate_spectrum_data(center_freq_khz: int, 
                          span_khz: int = 10,
                          num_emissions: int = 3) -> Tuple[np.ndarray, np.ndarray]:
    """
    Génère des données spectrales simulées pour tests
    
    Utile quand aucune source réelle n'est disponible
    """
    num_points = 1024
    freq_start = center_freq_khz - span_khz / 2
    freq_end = center_freq_khz + span_khz / 2
    
    frequencies = np.linspace(freq_start, freq_end, num_points)
    
    # Bruit de fond
    noise_floor = -100
    noise = noise_floor + np.random.normal(0, 3, num_points)
    
    # Ajouter des émissions simulées
    spectrum = noise.copy()
    
    for _ in range(num_emissions):
        # Position aléatoire
        emission_freq = np.random.uniform(freq_start, freq_end)
        emission_idx = np.argmin(np.abs(frequencies - emission_freq))
        
        # Largeur et puissance de l'émission
        bandwidth_points = np.random.randint(5, 20)
        peak_power = np.random.uniform(-70, -50)
        
        # Créer un pic gaussien
        for i in range(max(0, emission_idx - bandwidth_points),
                      min(num_points, emission_idx + bandwidth_points)):
            distance = abs(i - emission_idx)
            spectrum[i] += peak_power * np.exp(-(distance ** 2) / (bandwidth_points / 2) ** 2)
    
    return frequencies, spectrum
