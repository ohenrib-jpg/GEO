// static/js/sdr-surveillance-manager.js
class SDRSurveillanceManager {
    static async initialize() {
        console.log('📡 Initialisation SDR Surveillance Manager...');
        await this.loadDashboard();
        this.setupEventListeners();
    }

    static async loadDashboard() {
        try {
            const response = await fetch('/api/sdr-surveillance/dashboard');
            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error || 'Erreur serveur');
            }

            this.updateDashboard(data);
            this.updateGlobalStats(data);
            
        } catch (error) {
            console.error('❌ Erreur dashboard surveillance:', error);
            this.showError('Erreur chargement surveillance SDR');
        }
    }

    static updateDashboard(data) {
        const container = document.getElementById('sdr-surveillance-dashboard');
        if (!container) return;

        const { current_servers, recent_alerts, server_metrics, alert_stats } = data;

        container.innerHTML = `
            <!-- Métriques en temps réel -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div class="bg-white rounded-lg shadow p-4 text-center">
                    <div class="text-2xl font-bold text-blue-600">${current_servers.toFixed(0)}</div>
                    <div class="text-sm text-gray-600">Serveurs actifs</div>
                </div>
                <div class="bg-white rounded-lg shadow p-4 text-center">
                    <div class="text-2xl font-bold text-orange-600">${alert_stats.total_24h}</div>
                    <div class="text-sm text-gray-600">Alertes 24h</div>
                </div>
                <div class="bg-white rounded-lg shadow p-4 text-center">
                    <div class="text-2xl font-bold text-red-600">${alert_stats.critical_24h}</div>
                    <div class="text-sm text-gray-600">Critiques</div>
                </div>
                <div class="bg-white rounded-lg shadow p-4 text-center">
                    <div class="text-2xl font-bold text-purple-600">${alert_stats.blackout_24h}</div>
                    <div class="text-sm text-gray-600">Blackouts</div>
                </div>
            </div>

            <!-- Graphique serveurs -->
            <div class="bg-white rounded-lg shadow-md p-6 mb-6">
                <h3 class="text-lg font-semibold mb-4">📈 Serveurs KiwiSDR Actifs</h3>
                <canvas id="serversTrendChart" height="150"></canvas>
            </div>

            <!-- Alertes récentes -->
            <div class="bg-white rounded-lg shadow-md p-6">
                <h3 class="text-lg font-semibold mb-4">🚨 Alertes Récentes</h3>
                <div class="space-y-3">
                    ${this.renderRecentAlerts(recent_alerts)}
                </div>
            </div>
        `;

        // Initialiser les graphiques
        this.renderServersTrendChart(server_metrics);
    }

    static renderRecentAlerts(alerts) {
        if (!alerts || alerts.length === 0) {
            return '<p class="text-gray-500 text-center py-4">Aucune alerte récente</p>';
        }

        return alerts.map(alert => {
            const severityColor = {
                'low': 'blue',
                'medium': 'yellow', 
                'high': 'orange',
                'critical': 'red'
            }[alert.severity];

            return `
                <div class="border-l-4 border-${severityColor}-500 bg-${severityColor}-50 p-4 rounded">
                    <div class="flex justify-between items-start">
                        <div class="flex-1">
                            <h4 class="font-semibold text-${severityColor}-800">${alert.description}</h4>
                            <p class="text-sm text-${severityColor}-700 mt-1">
                                Type: ${alert.anomaly_type} • Confiance: ${(alert.confidence * 100).toFixed(1)}%
                            </p>
                        </div>
                        <span class="bg-${severityColor}-200 text-${severityColor}-800 px-2 py-1 rounded text-xs capitalize">
                            ${alert.severity}
                        </span>
                    </div>
                    <div class="text-xs text-${severityColor}-600 mt-2">
                        ${new Date(alert.timestamp).toLocaleString('fr-FR')}
                    </div>
                </div>
            `;
        }).join('');
    }

    static renderServersTrendChart(metrics) {
        const canvas = document.getElementById('serversTrendChart');
        if (!canvas || !metrics.length) return;

        const timestamps = metrics.map(m => 
            new Date(m.timestamp).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
        );
        const values = metrics.map(m => m.value);

        new Chart(canvas, {
            type: 'line',
            data: {
                labels: timestamps,
                datasets: [{
                    label: 'Serveurs actifs',
                    data: values,
                    borderColor: '#3B82F6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        ticks: { precision: 0 }
                    }
                }
            }
        });
    }

    static updateGlobalStats(data) {
        // Mettre à jour le compteur global d'anomalies
        const element = document.getElementById('sdr-anomalies-count');
        if (element && data.alert_stats) {
            element.textContent = data.alert_stats.total_24h;
        }
    }

    static async startMonitoring() {
        try {
            const response = await fetch('/api/sdr-surveillance/start', {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('✅ Surveillance SDR démarrée', 'success');
            } else {
                throw new Error(data.error || 'Erreur démarrage');
            }
        } catch (error) {
            console.error('❌ Erreur démarrage surveillance:', error);
            this.showNotification('Erreur démarrage: ' + error.message, 'error');
        }
    }

    static setupEventListeners() {
        // Actualisation automatique toutes les 2 minutes
        setInterval(() => {
            this.loadDashboard();
        }, 120000);
    }

    static showNotification(message, type = 'info') {
        // Implémentation existante de notification
        console.log(`[${type}] ${message}`);
    }
}

// Intégration avec l'existant
if (window.location.pathname.includes('/weak-indicators')) {
    document.addEventListener('DOMContentLoaded', () => {
        SDRSurveillanceManager.initialize();
    });
}