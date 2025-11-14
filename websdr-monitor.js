// static/js/websdr-monitor.js
class WebSDRMonitor {
    static spectrumCharts = new Map();
    static activeMonitors = new Map();
    static wsConnection = null;
    static updateInterval = null;

    static async initialize() {
        console.log('📡 Initialisation WebSDR Monitor...');
        
        try {
            await this.loadWebSDRServers();
            this.setupEventListeners();
            this.initializeWebSocket();
            this.startPeriodicUpdates();
            
            console.log('✅ WebSDR Monitor initialisé');
        } catch (error) {
            console.error('❌ Erreur initialisation WebSDR:', error);
        }
    }

    static async loadWebSDRServers() {
        try {
            const response = await this.fetchData('/api/websdr/servers');
            this.displayServersList(response.servers);
        } catch (error) {
            console.error('❌ Erreur chargement serveurs:', error);
        }
    }

    static displayServersList(servers) {
        const container = document.getElementById('websdr-servers');
        if (!container) return;

        container.innerHTML = servers.map(server => `
            <div class="border border-gray-200 rounded-lg p-4 mb-3">
                <div class="flex justify-between items-center mb-2">
                    <div class="flex items-center">
                        <div class="w-3 h-3 rounded-full mr-2 ${server.status === 'online' ? 'bg-green-500' : 'bg-red-500'}"></div>
                        <h3 class="font-semibold text-gray-800">${server.name}</h3>
                    </div>
                    <span class="px-2 py-1 text-xs rounded-full ${server.status === 'online' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">
                        ${server.status === 'online' ? '🟢 En ligne' : '🔴 Hors ligne'}
                    </span>
                </div>
                <div class="text-sm text-gray-600 mb-2">
                    <div>📍 ${server.location}</div>
                    <div>📶 Bandes: ${server.bands.join(', ')}</div>
                    <div class="text-xs text-gray-500">Dernière vérification: ${new Date(server.last_checked).toLocaleTimeString()}</div>
                </div>
                <div class="flex space-x-2">
                    <button onclick="WebSDRMonitor.viewServerSpectrum('${server.url}')" 
                            class="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm ${server.status !== 'online' ? 'opacity-50 cursor-not-allowed' : ''}"
                            ${server.status !== 'online' ? 'disabled' : ''}>
                        <i class="fas fa-chart-line mr-1"></i>Spectrum
                    </button>
                    <button onclick="WebSDRMonitor.monitorServer('${server.url}')"
                            class="bg-green-500 hover:bg-green-600 text-white px-3 py-1 rounded text-sm ${server.status !== 'online' ? 'opacity-50 cursor-not-allowed' : ''}"
                            ${server.status !== 'online' ? 'disabled' : ''}>
                        <i class="fas fa-play mr-1"></i>Surveiller
                    </button>
                </div>
            </div>
        `).join('');
    }

    static async viewServerSpectrum(serverUrl) {
        try {
            const serverId = this.getServerIdFromUrl(serverUrl);
            const spectrumData = await this.fetchData(`/api/websdr/spectrum/${serverId}`);
            
            this.displayRealtimeSpectrum(serverUrl, spectrumData);
        } catch (error) {
            console.error('❌ Erreur affichage spectrum:', error);
            this.showNotification('Erreur lors du chargement du spectrum', 'error');
        }
    }

    static displayRealtimeSpectrum(serverUrl, spectrumData) {
        const modal = this.createSpectrumModal(serverUrl, spectrumData);
        document.body.appendChild(modal);
        
        // Créer le graphique spectrum
        this.createSpectrumChart(modal, spectrumData);
        
        // Démarrer les mises à jour temps réel
        this.startSpectrumUpdates(serverUrl, modal);
    }

    static createSpectrumModal(serverUrl, spectrumData) {
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="bg-white rounded-lg shadow-xl w-11/12 max-w-4xl max-h-90vh overflow-hidden">
                <div class="flex justify-between items-center p-4 border-b">
                    <h3 class="text-lg font-semibold">📊 Spectrum Temps Réel - ${spectrumData.server}</h3>
                    <button onclick="this.parentElement.parentElement.parentElement.remove()" 
                            class="text-gray-500 hover:text-gray-700">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="p-4">
                    <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-4">
                        <div class="bg-blue-50 p-3 rounded">
                            <div class="text-sm text-blue-800">Émissions actives</div>
                            <div class="text-xl font-bold">${spectrumData.emissions.length}</div>
                        </div>
                        <div class="bg-green-50 p-3 rounded">
                            <div class="text-sm text-green-800">Bande HF</div>
                            <div class="text-xl font-bold">${spectrumData.band_activity.HF || 0}</div>
                        </div>
                        <div class="bg-yellow-50 p-3 rounded">
                            <div class="text-sm text-yellow-800">Anomalies</div>
                            <div class="text-xl font-bold">${spectrumData.analysis.anomalies.length}</div>
                        </div>
                    </div>
                    
                    <div class="mb-4">
                        <canvas id="spectrumChart" height="200"></canvas>
                    </div>
                    
                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
                        <div>
                            <h4 class="font-semibold mb-2">📡 Émissions Détectées</h4>
                            <div id="emissionsList" class="space-y-2 max-h-40 overflow-y-auto">
                                ${this.renderEmissionsList(spectrumData.emissions)}
                            </div>
                        </div>
                        <div>
                            <h4 class="font-semibold mb-2">⚠️ Analyse</h4>
                            <div id="spectrumAnalysis" class="space-y-2">
                                ${this.renderAnalysis(spectrumData.analysis)}
                            </div>
                        </div>
                    </div>
                </div>
                <div class="p-4 border-t bg-gray-50">
                    <div class="flex justify-between items-center text-sm text-gray-600">
                        <span>Dernière mise à jour: ${new Date(spectrumData.timestamp).toLocaleTimeString()}</span>
                        <button onclick="WebSDRMonitor.startServerMonitoring('${serverUrl}')" 
                                class="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded text-sm">
                            <i class="fas fa-satellite-dish mr-1"></i>Surveillance Continue
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        return modal;
    }

    static createSpectrumChart(modal, spectrumData) {
        const canvas = modal.querySelector('#spectrumChart');
        const ctx = canvas.getContext('2d');
        
        const frequencies = spectrumData.spectrum.map(s => s.frequency / 1000); // Convert to kHz
        const amplitudes = spectrumData.spectrum.map(s => s.amplitude * 100); // Scale for visibility
        
        // Créer un gradient pour le spectrum
        const gradient = ctx.createLinearGradient(0, 0, 0, 200);
        gradient.addColorStop(0, 'rgba(59, 130, 246, 0.8)');
        gradient.addColorStop(1, 'rgba(59, 130, 246, 0.1)');
        
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: frequencies,
                datasets: [{
                    label: 'Amplitude du Signal',
                    data: amplitudes,
                    borderColor: '#3B82F6',
                    backgroundColor: gradient,
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (context) => `Freq: ${context.label} kHz - Amplitude: ${context.parsed.y.toFixed(1)}%`
                        }
                    }
                },
                scales: {
                    x: {
                        title: { display: true, text: 'Fréquence (kHz)' },
                        grid: { display: false }
                    },
                    y: {
                        title: { display: true, text: 'Amplitude (%)' },
                        min: 0,
                        max: 100
                    }
                }
            }
        });
        
        this.spectrumCharts.set(modal, chart);
    }

    static renderEmissionsList(emissions) {
        if (emissions.length === 0) {
            return '<div class="text-gray-500 text-sm">Aucune émission détectée</div>';
        }
        
        return emissions.slice(0, 5).map(emission => `
            <div class="flex justify-between items-center p-2 bg-gray-50 rounded text-sm">
                <div>
                    <span class="font-medium">${(emission.frequency / 1000).toFixed(1)} kHz</span>
                    <span class="text-xs text-gray-500 ml-2">${emission.type}</span>
                </div>
                <div class="flex items-center">
                    <div class="w-16 bg-gray-200 rounded-full h-2 mr-2">
                        <div class="bg-green-500 h-2 rounded-full" style="width: ${emission.strength * 100}%"></div>
                    </div>
                    <span class="text-xs font-medium">${Math.round(emission.strength * 100)}%</span>
                </div>
            </div>
        `).join('');
    }

    static renderAnalysis(analysis) {
        let html = '';
        
        html += `<div class="text-sm"><strong>Émissions totales:</strong> ${analysis.total_emissions}</div>`;
        html += `<div class="text-sm"><strong>Émissions fortes:</strong> ${analysis.strong_emissions}</div>`;
        
        if (analysis.anomalies.length > 0) {
            html += `<div class="mt-2"><strong>Anomalies détectées:</strong></div>`;
            analysis.anomalies.forEach(anomaly => {
                html += `<div class="text-xs bg-yellow-50 border border-yellow-200 p-2 rounded">⚠️ ${anomaly}</div>`;
            });
        } else {
            html += `<div class="text-sm text-green-600">✅ Aucune anomalie détectée</div>`;
        }
        
        return html;
    }

    static async startServerMonitoring(serverUrl) {
        try {
            // Surveiller les fréquences géopolitiques importantes
            const geopoliticalFreqs = [121500, 5732000, 8992000, 11175000, 4500000];
            
            for (const freq of geopoliticalFreqs) {
                await this.monitorFrequency(serverUrl, freq, 5000);
            }
            
            this.showNotification(`Surveillance démarrée sur ${geopoliticalFreqs.length} fréquences`, 'success');
        } catch (error) {
            console.error('❌ Erreur démarrage surveillance:', error);
            this.showNotification('Erreur démarrage surveillance', 'error');
        }
    }

    static async monitorFrequency(serverUrl, frequency, bandwidth = 5000) {
        try {
            const response = await fetch('/api/websdr/monitor-frequency', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    frequency: frequency,
                    bandwidth: bandwidth,
                    server_url: serverUrl
                })
            });
            
            const result = await response.json();
            
            if (result.status === 'started') {
                this.activeMonitors.set(result.monitoring_id, {
                    frequency: frequency,
                    server: serverUrl,
                    started: result.started_at
                });
                
                this.showNotification(`Surveillance ${frequency/1000} kHz démarrée`, 'success');
            }
            
        } catch (error) {
            console.error('❌ Erreur surveillance fréquence:', error);
            this.showNotification('Erreur surveillance fréquence', 'error');
        }
    }

    static initializeWebSocket() {
        // Connexion WebSocket pour données temps réel
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/websdr`;
            
            this.wsConnection = new WebSocket(wsUrl);
            
            this.wsConnection.onopen = () => {
                console.log('🔌 WebSocket WebSDR connecté');
                this.showNotification('Connexion temps réel établie', 'success');
            };
            
            this.wsConnection.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleRealtimeData(data);
            };
            
            this.wsConnection.onclose = () => {
                console.log('🔌 WebSocket WebSDR déconnecté');
                // Reconnexion automatique
                setTimeout(() => this.initializeWebSocket(), 5000);
            };
            
        } catch (error) {
            console.warn('WebSocket non disponible:', error);
        }
    }

    static handleRealtimeData(data) {
        // Traiter les données temps réel du WebSDR
        switch (data.type) {
            case 'spectrum_update':
                this.updateSpectrumDisplay(data.spectrum);
                break;
            case 'emission_detected':
                this.handleNewEmission(data.emission);
                break;
            case 'anomaly_alert':
                this.handleAnomalyAlert(data.alert);
                break;
        }
    }

    static handleNewEmission(emission) {
        // Afficher notification pour nouvelle émission
        if (emission.strength > 0.7) {
            this.showRealTimeAlert(
                `Nouvelle émission forte: ${(emission.frequency/1000).toFixed(1)} kHz (${emission.type})`,
                'sdr'
            );
        }
        
        // Mettre à jour l'interface
        this.updateEmissionsDisplay();
    }

    static handleAnomalyAlert(alert) {
        this.showRealTimeAlert(`🚨 ALERTE SDR: ${alert.message}`, 'warning');
        
        // Enregistrer l'alerte dans le système
        if (typeof AlertsManager !== 'undefined') {
            AlertsManager.createAlert({
                name: `Anomalie SDR - ${alert.type}`,
                description: alert.message,
                severity: 'high',
                category: 'sdr'
            });
        }
    }

    static updateSpectrumDisplay(spectrumData) {
        // Mettre à jour tous les graphiques spectrum ouverts
        this.spectrumCharts.forEach((chart, modal) => {
            if (document.body.contains(modal)) {
                chart.data.datasets[0].data = spectrumData.map(s => s.amplitude * 100);
                chart.update('none');
            }
        });
    }

    static async updateEmissionsDisplay() {
        try {
            const recentEmissions = await this.fetchData('/api/websdr/emissions/recent?hours=1');
            this.displayRecentEmissions(recentEmissions);
        } catch (error) {
            console.warn('Erreur mise à jour émissions:', error);
        }
    }

    static displayRecentEmissions(emissionsData) {
        const container = document.getElementById('recent-emissions');
        if (!container) return;

        container.innerHTML = `
            <h4 class="font-semibold mb-3">📡 Émissions Récentes (${emissionsData.total})</h4>
            <div class="space-y-2 max-h-60 overflow-y-auto">
                ${emissionsData.emissions.slice(0, 10).map(emission => `
                    <div class="flex justify-between items-center p-2 bg-white border border-gray-200 rounded text-sm">
                        <div>
                            <span class="font-medium">${(emission.frequency / 1000).toFixed(1)} kHz</span>
                            <div class="text-xs text-gray-500">
                                ${emission.type} • ${new Date(emission.timestamp).toLocaleTimeString()}
                            </div>
                        </div>
                        <div class="text-right">
                            <div class="text-xs font-medium ${emission.strength > 0.7 ? 'text-red-600' : emission.strength > 0.4 ? 'text-yellow-600' : 'text-green-600'}">
                                ${Math.round(emission.strength * 100)}%
                            </div>
                            <div class="text-xs text-gray-500">${emission.bandwidth} Hz</div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    static startPeriodicUpdates() {
        // Mettre à jour les données toutes les 30 secondes
        this.updateInterval = setInterval(() => {
            this.loadWebSDRServers();
            this.updateEmissionsDisplay();
        }, 30000);
    }

    static setupEventListeners() {
        // Écouteur pour la recherche de fréquences
        const freqSearch = document.getElementById('frequency-search');
        if (freqSearch) {
            freqSearch.addEventListener('input', (e) => {
                this.filterFrequencies(e.target.value);
            });
        }

        // Écouteur pour le monitoring manuel
        const monitorForm = document.getElementById('manual-monitor-form');
        if (monitorForm) {
            monitorForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleManualMonitoring(e);
            });
        }
    }

    static async handleManualMonitoring(e) {
        const formData = new FormData(e.target);
        const frequency = parseInt(formData.get('frequency'));
        const bandwidth = parseInt(formData.get('bandwidth') || '5000');
        const server = formData.get('server');

        if (frequency) {
            await this.monitorFrequency(server, frequency, bandwidth);
        }
    }

    // Méthodes utilitaires
    static getServerIdFromUrl(url) {
        return WEBSDR_SERVERS.findIndex(server => server.url === url);
    }

    static async fetchData(endpoint) {
        const response = await fetch(endpoint);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
    }

    static showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${
            type === 'success' ? 'bg-green-500 text-white' :
            type === 'error' ? 'bg-red-500 text-white' :
            'bg-blue-500 text-white'
        }`;
        notification.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'exclamation-triangle' : 'info'} mr-2"></i>
                <span>${message}</span>
            </div>
        `;
        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 5000);
    }

    static showRealTimeAlert(message, category) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `fixed top-4 left-1/2 transform -translate-x-1/2 z-50 px-6 py-3 rounded-lg shadow-lg border-l-4 ${
            category === 'sdr' ? 'bg-blue-50 border-blue-500 text-blue-700' :
            category === 'warning' ? 'bg-red-50 border-red-500 text-red-700' :
            'bg-gray-50 border-gray-500 text-gray-700'
        }`;
        
        alertDiv.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-satellite-dish mr-2"></i>
                <span class="font-medium">${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-gray-500 hover:text-gray-700">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        document.body.appendChild(alertDiv);
        setTimeout(() => alertDiv.remove(), 8000);
    }

    // Nettoyage
    static destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
        if (this.wsConnection) {
            this.wsConnection.close();
        }
        this.spectrumCharts.forEach(chart => chart.destroy());
    }
}

// Initialisation automatique
if (window.location.pathname.includes('/weak-indicators')) {
    document.addEventListener('DOMContentLoaded', function() {
        WebSDRMonitor.initialize();
    });

    window.addEventListener('beforeunload', () => {
        WebSDRMonitor.destroy();
    });
}

// Exposer globalement
window.WebSDRMonitor = WebSDRMonitor;