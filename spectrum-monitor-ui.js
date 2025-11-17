// static/js/spectrum-monitor-ui.js
/**
 * Interface pour le monitoring automatique du spectre
 * Version simplifiée
 */

class SpectrumMonitorUI {
    static async initialize() {
        console.log('📡 Initialisation Spectrum Monitor UI...');
        
        try {
            this.setupEventListeners();
            console.log('✅ Spectrum Monitor UI initialisé');
        } catch (error) {
            console.error('❌ Erreur initialisation:', error);
        }
    }

    static setupEventListeners() {
        // Événements pour les boutons spectrum
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('spectrum-analyze-btn')) {
                const frequency = e.target.dataset.frequency;
                this.analyzeFrequency(frequency);
            }
        });
    }

    static async analyzeFrequency(frequencyKhz) {
        try {
            const response = await fetch('/api/weak-indicators/sdr/rtlsdr/analyze', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    frequency_khz: parseInt(frequencyKhz),
                    duration_seconds: 60
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification(`Analyse terminée: ${data.emissions_detected} émissions`, 'success');
            } else {
                this.showNotification('Erreur lors de l\'analyse', 'error');
            }
        } catch (error) {
            console.error('Erreur analyse spectrum:', error);
            this.showNotification('Erreur de connexion', 'error');
        }
    }

    static showNotification(message, type = 'info') {
        // Implémentation simple de notification
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${
            type === 'success' ? 'bg-green-500' : 
            type === 'error' ? 'bg-red-500' : 'bg-blue-500'
        } text-white`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
}

// Initialisation conditionnelle
if (window.location.pathname.includes('/weak-indicators')) {
    document.addEventListener('DOMContentLoaded', () => {
        SpectrumMonitorUI.initialize();
    });
}

console.log('✅ Spectrum Monitor UI chargé');