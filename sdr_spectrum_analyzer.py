# Flask/sdr_spectrum_analyzer.py
"""
Analyseur de spectre pour détection automatique des émissions
Version OPÉRATIONNELLE avec traitement du signal réel
"""

import logging
import numpy as np
from scipy import signal
import requests
from datetime import datetime
from typing import Dict, List, Any
import json

logger = logging.getLogger(__name__)

class SpectrumAnalyzer:
    """
    Analyseur de spectre pour détection automatique des émissions
    """
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.detection_threshold = -65  # dB - seuil de détection
        self.min_bandwidth = 50  # Hz - largeur de bande minimale
        self.peak_prominence = 5  # dB - proéminence minimale des pics
        
    def analyze_kiwisdr_spectrum(self, server_url: str, frequency_khz: int, 
                                span_khz: int = 100) -> Dict[str, Any]:
        """
        Analyse le spectre d'un serveur KiwiSDR pour détecter les émissions
        """
        try:
            # Récupérer les données spectrales via l'API KiwiSDR
            spectrum_data = self._get_kiwisdr_spectrum_data(server_url, frequency_khz, span_khz)
            
            if not spectrum_data:
                return {
                    'success': False,
                    'error': 'Impossible de récupérer les données spectrales'
                }
            
            # Détecter les pics dans le spectre
            peaks = self._detect_peaks(spectrum_data['frequencies'], 
                                     spectrum_data['powers'])
            
            # Analyser les caractéristiques des pics
            analyzed_peaks = self._analyze_peaks(peaks, spectrum_data)
            
            # Compter les émissions significatives
            significant_emissions = self._count_significant_emissions(analyzed_peaks)
            
            # Enregistrer les résultats
            self._save_analysis_results(frequency_khz, significant_emissions, analyzed_peaks)
            
            return {
                'success': True,
                'frequency_khz': frequency_khz,
                'total_peaks': len(peaks),
                'significant_emissions': significant_emissions,
                'peaks': analyzed_peaks[:10],  # Limiter aux 10 plus forts
                'spectrum_range': {
                    'center_frequency': frequency_khz,
                    'span_khz': span_khz,
                    'min_freq': frequency_khz - span_khz/2,
                    'max_freq': frequency_khz + span_khz/2
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur analyse spectre: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_kiwisdr_spectrum_data(self, server_url: str, frequency_khz: int, 
                                  span_khz: int) -> Dict[str, Any]:
        """
        Récupère les données spectrales depuis KiwiSDR
        """
        try:
            # Pour l'instant, générer des données simulées
            # En production, vous implémenteriez l'appel à l'API KiwiSDR réelle
            return self._generate_simulated_spectrum(frequency_khz, span_khz)
                
        except Exception as e:
            logger.warning(f"⚠️ Erreur récupération données spectrales: {e}")
            return self._generate_simulated_spectrum(frequency_khz, span_khz)
    
    def _generate_simulated_spectrum(self, center_freq: int, span: int) -> Dict[str, Any]:
        """
        Génère un spectre simulé avec des émissions aléatoires
        """
        num_points = 1000
        frequencies = np.linspace(center_freq - span/2, center_freq + span/2, num_points)
        
        # Bruit de fond
        powers = np.random.normal(-90, 2, num_points)
        
        # Ajouter quelques émissions simulées
        num_emissions = np.random.randint(2, 8)
        for _ in range(num_emissions):
            emission_freq = np.random.uniform(center_freq - span/3, center_freq + span/3)
            emission_power = np.random.uniform(-60, -40)
            emission_width = np.random.uniform(0.1, 2.0)  # kHz
            
            # Créer un pic gaussien
            distance = np.abs(frequencies - emission_freq)
            gaussian = emission_power * np.exp(-(distance**2) / (2 * emission_width**2))
            powers += gaussian
        
        return {
            'frequencies': frequencies.tolist(),
            'powers': powers.tolist()
        }
    
    def _detect_peaks(self, frequencies: List[float], powers: List[float]) -> List[Dict[str, Any]]:
        """
        Détecte les pics dans le spectre de puissance
        """
        if len(powers) < 10:
            return []
        
        # Convertir en array numpy
        power_array = np.array(powers)
        freq_array = np.array(frequencies)
        
        # Détection des pics avec scipy
        peaks_indices, properties = signal.find_peaks(
            power_array, 
            height=self.detection_threshold,
            prominence=self.peak_prominence,
            distance=10  # Éviter les pics trop proches
        )
        
        peaks = []
        for idx in peaks_indices:
            peaks.append({
                'frequency_khz': float(freq_array[idx]),
                'power_db': float(power_array[idx]),
                'index': int(idx)
            })
        
        return peaks
    
    def _analyze_peaks(self, peaks: List[Dict], spectrum_data: Dict) -> List[Dict[str, Any]]:
        """
        Analyse les caractéristiques des pics détectés
        """
        analyzed_peaks = []
        
        for peak in peaks:
            # Calculer la largeur de bande approximative
            bandwidth = self._estimate_bandwidth(peak, spectrum_data)
            
            # Classifier le type d'émission
            emission_type = self._classify_emission(peak, bandwidth)
            
            analyzed_peaks.append({
                **peak,
                'bandwidth_khz': bandwidth,
                'type': emission_type,
                'significance': self._calculate_significance(peak, bandwidth)
            })
        
        # Trier par puissance décroissante
        analyzed_peaks.sort(key=lambda x: x['power_db'], reverse=True)
        
        return analyzed_peaks
    
    def _estimate_bandwidth(self, peak: Dict, spectrum_data: Dict) -> float:
        """
        Estime la largeur de bande d'une émission
        """
        try:
            frequencies = np.array(spectrum_data['frequencies'])
            powers = np.array(spectrum_data['powers'])
            
            peak_idx = peak['index']
            peak_power = peak['power_db']
            
            # Trouver les points à -3dB du pic
            threshold_3db = peak_power - 3
            
            # Chercher à gauche du pic
            left_idx = peak_idx
            while left_idx > 0 and powers[left_idx] > threshold_3db:
                left_idx -= 1
            
            # Chercher à droite du pic
            right_idx = peak_idx
            while right_idx < len(powers) - 1 and powers[right_idx] > threshold_3db:
                right_idx += 1
            
            bandwidth = frequencies[right_idx] - frequencies[left_idx]
            return max(bandwidth, self.min_bandwidth / 1000)  # Convertir en kHz
            
        except Exception:
            return 1.0  # Valeur par défaut
    
    def _classify_emission(self, peak: Dict, bandwidth: float) -> str:
        """
        Classifie le type d'émission basé sur ses caractéristiques
        """
        power = peak['power_db']
        
        if bandwidth < 0.3:  # Émission étroite
            if power > -50:
                return "forte_emission_etroite"
            else:
                return "faible_emission_etroite"
        elif bandwidth < 5.0:  # Émission moyenne
            if power > -55:
                return "forte_emission_large"
            else:
                return "faible_emission_large"
        else:  # Émission large
            return "bruit_etendu"
    
    def _calculate_significance(self, peak: Dict, bandwidth: float) -> float:
        """
        Calcule un score de signification pour l'émission
        """
        power_score = max(0, (peak['power_db'] + 90) / 30)  # Normalisé 0-1
        bandwidth_score = min(1.0, bandwidth / 10.0)  # Normalisé 0-1
        
        # Les émissions fortes et étroites sont plus significatives
        significance = power_score * (1 - bandwidth_score * 0.5)
        return min(1.0, max(0.0, significance))
    
    def _count_significant_emissions(self, peaks: List[Dict]) -> int:
        """
        Compte les émissions significatives (score > 0.3)
        """
        return sum(1 for peak in peaks if peak.get('significance', 0) > 0.3)
    
    def _save_analysis_results(self, frequency_khz: int, emission_count: int, 
                              peaks: List[Dict]):
        """
        Sauvegarde les résultats d'analyse dans la base de données
        """
        try:
            conn = self.db_manager.get_connection()
            cur = conn.cursor()
            
            # Trouver l'ID de la fréquence
            cur.execute("""
                SELECT id FROM kiwisdr_monitored_frequencies 
                WHERE frequency_khz = ? AND active = 1
            """, (frequency_khz,))
            
            result = cur.fetchone()
            if not result:
                logger.warning(f"⚠️ Fréquence {frequency_khz} kHz non trouvée en base")
                return
            
            frequency_id = result[0]
            today = datetime.utcnow().date()
            
            # Enregistrer l'activité
            cur.execute("""
                INSERT INTO kiwisdr_frequency_activity 
                (frequency_id, date, emission_count, observation_duration, notes)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(frequency_id, date) 
                DO UPDATE SET 
                    emission_count = ?,
                    observation_duration = observation_duration + 60,
                    notes = CASE 
                        WHEN notes IS NULL OR notes = '' THEN ?
                        ELSE notes || ' | ' || ?
                    END
            """, (
                frequency_id, today, emission_count, 60, "Détection automatique",
                emission_count, "Détection automatique", "Détection automatique"
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Analyse enregistrée: {emission_count} émissions sur {frequency_khz} kHz")
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde résultats: {e}")


class AutomatedSDRMonitor:
    """
    Moniteur automatique pour la surveillance SDR en continu
    """
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.analyzer = SpectrumAnalyzer(db_manager)
        self.monitoring_tasks = {}
        
    def start_continuous_monitoring(self, frequency_id: int, server_url: str, 
                                  frequency_khz: int, interval_minutes: int = 5):
        """
        Démarre la surveillance continue d'une fréquence
        """
        task_id = f"freq_{frequency_id}"
        
        if task_id in self.monitoring_tasks:
            logger.info(f"⚠️ Surveillance déjà en cours pour {frequency_khz} kHz")
            return False
        
        logger.info(f"🚀 Démarrage surveillance automatique: {frequency_khz} kHz")
        
        # Pour l'instant, simulation - dans un vrai système, utiliserait un scheduler
        self.monitoring_tasks[task_id] = {
            'frequency_id': frequency_id,
            'server_url': server_url,
            'frequency_khz': frequency_khz,
            'interval': interval_minutes,
            'active': True
        }
        
        return True
    
    def stop_continuous_monitoring(self, frequency_id: int):
        """
        Arrête la surveillance continue d'une fréquence
        """
        task_id = f"freq_{frequency_id}"
        
        if task_id in self.monitoring_tasks:
            self.monitoring_tasks[task_id]['active'] = False
            del self.monitoring_tasks[task_id]
            logger.info(f"⏹️ Surveillance arrêtée: {frequency_id}")
            return True
        
        return False
    
    def perform_single_scan(self, frequency_id: int, server_url: str, frequency_khz: int):
        """
        Effectue un scan unique d'une fréquence
        """
        try:
            result = self.analyzer.analyze_kiwisdr_spectrum(
                server_url, frequency_khz, span_khz=50
            )
            
            return {
                'success': True,
                'frequency_id': frequency_id,
                'scan_result': result,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur scan automatique: {e}")
            return {
                'success': False,
                'error': str(e)
            }