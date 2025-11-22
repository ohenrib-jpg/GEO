// static/js/rtlsdr-manager.js
class RTLSDRAnalyzer {
    static async initialize() {
        console.log('📡 Initialisation RTL-SDR Manager...');
        this.setupEventListeners();
    }

    static async loadWaterfall(frequencyKhz, canvasId) {
        try {
            const response = await fetch(`/api/sdr/rtlsdr/waterfall/${frequencyKhz}`);
            const data = await response.json();
            
            if (data.success) {
                this.renderWaterfall(canvasId, data.waterfall_data);
                return true;
            }
        } catch (error) {
            console.error('Erreur chargement waterfall:', error);
        }
        return false;
    }

    static renderWaterfall(canvasId, waterfallData) {
        const canvas = document.getElementById(canvasId);
        if (!canvas || !waterfallData) return;
        
        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;
        
        const frequencies = waterfallData.frequencies;
        const waterfall = waterfallData.waterfall;
        
        if (!waterfall || waterfall.length === 0) return;
        
        // Effacer le canvas
        ctx.clearRect(0, 0, width, height);
        
        // Rendu du waterfall
        const timeSlices = waterfall.length;
        const freqBins = waterfall[0].length;
        
        for (let t = 0; t < timeSlices; t++) {
            for (let f = 0; f < freqBins; f++) {
                const power = waterfall[t][f];
                const intensity = this.powerToIntensity(power);
                
                ctx.fillStyle = intensity;
                ctx.fillRect(
                    (f / freqBins) * width,
                    (t / timeSlices) * height,
                    Math.ceil(width / freqBins),
                    Math.ceil(height / timeSlices)
                );
            }
        }
    }

    static powerToIntensity(power) {
        // Convertir puissance dB en couleur
        if (power > -60) return '#ff0000'; // Rouge - fort
        if (power > -70) return '#ffff00'; // Jaune - moyen
        if (power > -80) return '#00ff00'; // Vert - faible
        if (power > -90) return '#0000ff'; // Bleu - très faible
        return '#000000'; // Noir - bruit
    }

    static setupEventListeners() {
        // Événements pour les contrôles RTL-SDR
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('rtlsdr-analyze-btn')) {
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
                this.displayAnalysisResults(data.analysis);
            }
        } catch (error) {
            console.error('Erreur analyse:', error);
        }
    }

    static displayAnalysisResults(analysis) {
        const modal = document.createElement('div');
        modal.className = 'analysis-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <h3>📊 Analyse RTL-SDR</h3>
                <p>Niveau d'activité: <strong>${analysis.activity_level}</strong></p>
                <p>Confiance: <strong>${(analysis.confidence * 100).toFixed(1)}%</strong></p>
                
                ${analysis.anomalies.length > 0 ? `
                    <div class="anomalies">
                        <h4>🚨 Anomalies détectées:</h4>
                        <ul>
                            ${analysis.anomalies.map(a => `<li>${a}</li>`).join('')}
                        </ul>
                    </div>
                ` : '<p>✅ Aucune anomalie détectée</p>'}
                
                ${analysis.recommendations.length > 0 ? `
                    <div class="recommendations">
                        <h4>💡 Recommandations:</h4>
                        <ul>
                            ${analysis.recommendations.map(r => `<li>${r}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>
        `;
        
        document.body.appendChild(modal);
    }
}

// Initialisation automatique
if (window.location.pathname.includes('/weak-indicators')) {
    document.addEventListener('DOMContentLoaded', () => {
        RTLSDRAnalyzer.initialize();
    });
}