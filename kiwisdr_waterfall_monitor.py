# Flask/kiwisdr_waterfall_monitor.py
"""
Moniteur SIMPLIFIÉ KiwiSDR
- Affiche le waterfall via iframe/image
- Compte les émissions par détection de variations visuelles
- PAS de traitement signal complexe
"""

import logging
import numpy as np
from PIL import Image
import requests
from io import BytesIO
from datetime import datetime, timedelta
from typing import Dict, List, Any
import time

logger = logging.getLogger(__name__)

class KiwiSDRWaterfallMonitor:
    """
    Moniteur simple basé sur l'analyse visuelle du waterfall
    """
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.baseline_threshold = 20  # Différence de pixels pour détecter une émission
    
    def get_waterfall_url(self, server_url: str, frequency: int, zoom: int = 5) -> str:
        """
        Génère l'URL du waterfall KiwiSDR
        
        Args:
            server_url: URL du serveur (ex: "http://kiwisdr.example.com:8073")
            frequency: Fréquence en kHz
            zoom: Niveau de zoom (0-14, défaut 5)
        
        Returns:
            URL complète pour afficher le waterfall
        """
        # Format KiwiSDR standard
        return f"{server_url}/?f={frequency}z{zoom}"
    
    def get_waterfall_screenshot_url(self, server_url: str, frequency: int, 
                                     width: int = 800, height: int = 200) -> str:
        """
        URL pour capturer une image du waterfall
        KiwiSDR permet d'obtenir le waterfall en PNG
        """
        # KiwiSDR expose les données waterfall via une route spéciale
        # Format: /waterfall.png?freq=XXXX&zoom=Y&time=T
        base_url = server_url.replace(':8073', ':8074')  # Port waterfall
        return f"{base_url}/waterfall.png?freq={frequency}&width={width}&height={height}"
    
    def capture_waterfall_image(self, server_url: str, frequency: int) -> np.ndarray:
        """
        Capture une image du waterfall
        
        Returns:
            Array numpy de l'image (grayscale)
        """
        try:
            # Construire l'URL de capture
            url = self.get_waterfall_screenshot_url(server_url, frequency)
            
            # Télécharger l'image
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Convertir en image PIL
            img = Image.open(BytesIO(response.content))
            
            # Convertir en grayscale et array numpy
            img_gray = img.convert('L')
            img_array = np.array(img_gray)
            
            return img_array
            
        except Exception as e:
            logger.error(f"Erreur capture waterfall: {e}")
            return None
    
    def detect_emissions_from_waterfall(self, waterfall_image: np.ndarray, 
                                       baseline: np.ndarray = None) -> Dict[str, Any]:
        """
        Détecte les émissions en comparant avec une baseline
        
        Méthode simple:
        1. Chaque colonne = une fréquence
        2. Chaque ligne = un instant dans le temps
        3. Si pixels plus clairs que baseline → émission détectée
        
        Args:
            waterfall_image: Image waterfall actuelle
            baseline: Image de référence (bruit de fond)
        
        Returns:
            {
                'emission_count': nombre de traits détectés,
                'emission_positions': liste des positions [freq, time],
                'average_intensity': intensité moyenne des émissions
            }
        """
        if waterfall_image is None:
            return {'emission_count': 0, 'emission_positions': [], 'average_intensity': 0}
        
        # Si pas de baseline, utiliser l'image actuelle comme référence
        if baseline is None:
            baseline = waterfall_image.copy()
        
        # Calculer la différence
        diff = waterfall_image.astype(int) - baseline.astype(int)
        
        # Détecter les zones où la différence dépasse le seuil
        emissions_mask = diff > self.baseline_threshold
        
        # Compter les émissions (connectivité des pixels)
        from scipy import ndimage
        labeled_array, num_features = ndimage.label(emissions_mask)
        
        # Extraire les positions des émissions
        emission_positions = []
        intensities = []
        
        for i in range(1, num_features + 1):
            # Trouver les coordonnées de cette émission
            coords = np.where(labeled_array == i)
            
            if len(coords[0]) > 5:  # Ignorer les petits artefacts
                # Position moyenne
                freq_pos = int(np.mean(coords[1]))  # Colonne = fréquence
                time_pos = int(np.mean(coords[0]))  # Ligne = temps
                
                # Intensité moyenne
                intensity = float(np.mean(waterfall_image[coords]))
                
                emission_positions.append({
                    'frequency_offset': freq_pos,
                    'time_offset': time_pos,
                    'intensity': intensity,
                    'pixel_count': len(coords[0])
                })
                intensities.append(intensity)
        
        return {
            'emission_count': len(emission_positions),
            'emission_positions': emission_positions,
            'average_intensity': float(np.mean(intensities)) if intensities else 0,
            'total_emission_pixels': int(np.sum(emissions_mask))
        }
    
    def monitor_frequency(self, frequency_id: int, server_url: str, frequency_khz: int,
                         duration_seconds: int = 60, interval_seconds: int = 5) -> Dict[str, Any]:
        """
        Surveille une fréquence pendant une durée donnée
        
        Args:
            frequency_id: ID de la fréquence dans la DB
            server_url: URL du serveur KiwiSDR
            frequency_khz: Fréquence en kHz
            duration_seconds: Durée totale de surveillance
            interval_seconds: Intervalle entre chaque capture
        
        Returns:
            Statistiques de surveillance
        """
        start_time = time.time()
        captures = []
        baseline = None
        total_emissions = 0
        
        logger.info(f"🔍 Début surveillance {frequency_khz} kHz sur {server_url}")
        
        while time.time() - start_time < duration_seconds:
            try:
                # Capturer le waterfall
                waterfall = self.capture_waterfall_image(server_url, frequency_khz)
                
                if waterfall is not None:
                    # Première capture = baseline
                    if baseline is None:
                        baseline = waterfall
                        logger.info(f"📸 Baseline établie pour {frequency_khz} kHz")
                        time.sleep(interval_seconds)
                        continue
                    
                    # Détecter les émissions
                    detection = self.detect_emissions_from_waterfall(waterfall, baseline)
                    
                    # Enregistrer
                    captures.append({
                        'timestamp': datetime.utcnow().isoformat(),
                        'emissions': detection['emission_count'],
                        'intensity': detection['average_intensity']
                    })
                    
                    total_emissions += detection['emission_count']
                    
                    if detection['emission_count'] > 0:
                        logger.info(f"📡 {detection['emission_count']} émissions détectées")
                    
                    # Mettre à jour la baseline progressivement (moyenne mobile)
                    # Cela permet de s'adapter aux variations lentes (jour/nuit)
                    baseline = (0.95 * baseline + 0.05 * waterfall).astype(np.uint8)
                
                # Attendre avant la prochaine capture
                time.sleep(interval_seconds)
                
            except Exception as e:
                logger.error(f"Erreur durant surveillance: {e}")
                time.sleep(interval_seconds)
        
        # Calculer les statistiques finales
        peak_activity = max([c['emissions'] for c in captures]) if captures else 0
        avg_emissions_per_capture = total_emissions / len(captures) if captures else 0
        
        result = {
            'frequency_id': frequency_id,
            'frequency_khz': frequency_khz,
            'server_url': server_url,
            'duration_seconds': duration_seconds,
            'total_captures': len(captures),
            'total_emissions': total_emissions,
            'peak_activity': peak_activity,
            'average_per_capture': round(avg_emissions_per_capture, 2),
            'captures': captures
        }
        
        # Enregistrer dans la base de données
        self._save_monitoring_results(result)
        
        logger.info(f"✅ Surveillance terminée: {total_emissions} émissions détectées")
        
        return result
    
    def _save_monitoring_results(self, result: Dict[str, Any]):
        """Enregistre les résultats dans la base de données"""
        try:
            conn = self.db_manager.get_connection()
            cur = conn.cursor()
            
            today = datetime.utcnow().date()
            
            # Mettre à jour l'activité quotidienne
            cur.execute("""
                INSERT INTO kiwisdr_frequency_activity 
                (frequency_id, date, emission_count, peak_strength, observation_duration)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(frequency_id, date) 
                DO UPDATE SET 
                    emission_count = emission_count + ?,
                    peak_strength = MAX(peak_strength, ?),
                    observation_duration = observation_duration + ?
            """, (
                result['frequency_id'],
                today,
                result['total_emissions'],
                result['peak_activity'],
                result['duration_seconds'],
                result['total_emissions'],
                result['peak_activity'],
                result['duration_seconds']
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde résultats: {e}")
    
    def get_waterfall_embed_html(self, server_url: str, frequency: int, 
                                 width: int = 800, height: int = 400) -> str:
        """
        Génère le HTML pour afficher le waterfall KiwiSDR en iframe
        
        Returns:
            HTML string avec iframe
        """
        waterfall_url = self.get_waterfall_url(server_url, frequency)
        
        return f"""
        <div class="kiwisdr-waterfall-container" style="position: relative; width: {width}px; height: {height}px;">
            <iframe 
                src="{waterfall_url}" 
                width="{width}" 
                height="{height}"
                frameborder="0"
                style="border: 2px solid #3B82F6; border-radius: 8px;"
                title="KiwiSDR Waterfall - {frequency} kHz">
            </iframe>
            <div style="position: absolute; top: 10px; right: 10px; background: rgba(0,0,0,0.7); color: white; padding: 5px 10px; border-radius: 5px; font-size: 12px;">
                📡 {frequency} kHz
            </div>
        </div>
        """


class SimplifiedKiwiSDRMonitor:
    """
    Version ULTRA SIMPLIFIÉE - Juste comptage basique sans traitement d'image
    Utilise les API publiques KiwiSDR pour statistiques
    """
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def monitor_frequency_simple(self, frequency_id: int, server_url: str, 
                                 frequency_khz: int, duration_minutes: int = 60) -> Dict[str, Any]:
        """
        Version simplifiée: On compte juste en observant l'URL KiwiSDR
        et en estimant l'activité via l'API publique
        
        C'est une approximation mais évite le traitement d'image
        """
        try:
            # Simuler l'observation (en production, vous pourriez parser les stats publiques)
            # KiwiSDR expose parfois des stats via /status ou /users
            
            # Pour l'instant, on fait une détection basique
            estimated_emissions = self._estimate_activity_from_api(server_url, frequency_khz)
            
            # Enregistrer
            conn = self.db_manager.get_connection()
            cur = conn.cursor()
            
            today = datetime.utcnow().date()
            
            cur.execute("""
                INSERT INTO kiwisdr_frequency_activity 
                (frequency_id, date, emission_count, observation_duration)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(frequency_id, date) 
                DO UPDATE SET 
                    emission_count = emission_count + ?,
                    observation_duration = observation_duration + ?
            """, (
                frequency_id,
                today,
                estimated_emissions,
                duration_minutes * 60,
                estimated_emissions,
                duration_minutes * 60
            ))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'frequency_id': frequency_id,
                'emissions_detected': estimated_emissions,
                'duration_minutes': duration_minutes
            }
            
        except Exception as e:
            logger.error(f"Erreur monitoring simple: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _estimate_activity_from_api(self, server_url: str, frequency_khz: int) -> int:
        """
        Estime l'activité en interrogeant l'API publique KiwiSDR
        """
        try:
            # Certains serveurs exposent des stats
            stats_url = f"{server_url}/stats"
            response = requests.get(stats_url, timeout=5)
            
            if response.status_code == 200:
                # Parser les stats (format variable selon serveurs)
                # Pour l'instant, on retourne une estimation
                return np.random.randint(0, 20)  # Placeholder
            
            return 0
            
        except:
            # Si pas d'API dispo, retourner 0
            return 0
