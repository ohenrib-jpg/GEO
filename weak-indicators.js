// static/js/weak-indicators.js - VERSION CORRIGÉE
class WeakIndicatorsManager {
    static economicChart = null;
    static sdrStreams = new Map();
    static travelAdviceCache = new Map();

    static async initialize() {
        console.log('🚀 Initialisation WeakIndicatorsManager...');

        try {
            await this.loadInitialData();
            this.setupEventListeners();
            this.startPeriodicUpdates();
            await this.initializeAlerts(); // Ajouté
            console.log('✅ WeakIndicatorsManager initialisé');
        } catch (error) {
            console.error('❌ Erreur initialisation:', error);
        }
    }

    static async loadInitialData() {
        try {
            // Charger le statut global
            const status = await this.fetchData('/api/weak-indicators/status');
            this.updateGlobalStats(status);

            // Charger les pays surveillés
            const countries = await this.fetchData('/api/weak-indicators/countries');
            this.monitoredCountries = countries;

        } catch (error) {
            console.error('❌ Erreur chargement données initiales:', error);
            this.showErrorState();
        }
    }

    // AJOUTER CETTE MÉTHODE
    static async initializeAlerts() {
        // Charger et initialiser le gestionnaire d'alertes
        if (typeof AlertsManager !== 'undefined') {
            await AlertsManager.initialize();
        } else {
            // Charger le script dynamiquement si pas encore chargé
            const script = document.createElement('script');
            script.src = '/static/js/alerts-management.js';
            script.onload = async () => {
                if (typeof AlertsManager !== 'undefined') {
                    await AlertsManager.initialize();
                }
            };
            script.onerror = () => {
                console.warn('⚠️ Impossible de charger alerts-management.js');
            };
            document.head.appendChild(script);
        }
    }

    static updateGlobalStats(status) {
        this.updateCard('monitored-countries', status.monitored_countries || 0);
        this.updateCard('active-alerts', status.active_alerts || 0);
        this.updateCard('active-radios', status.active_sdr_streams || 0);
    }

    static updateCard(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value.toLocaleString('fr-FR');
        }
    }

    static async fetchData(endpoint) {
        try {
            const response = await fetch(endpoint);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error(`❌ Erreur fetch ${endpoint}:`, error);
            throw error;
        }
    }

    // 1. CONSEILS AUX VOYAGEURS - Version simplifiée
    static async scanTravelAdvice() {
        console.log('🔍 Scan des conseils aux voyageurs...');
        const button = document.querySelector('[onclick*="scanTravelAdvice"]');
        if (button) {
            const originalText = button.innerHTML;
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Scan en cours...';

            setTimeout(() => {
                button.disabled = false;
                button.innerHTML = originalText;
                console.log('✅ Scan terminé');
            }, 2000);
        }
    }

    // 2. SURVEILLANCE SDR
    static async addSDRStream() {
        const url = document.getElementById('sdr-url')?.value;
        const frequency = document.getElementById('sdr-frequency')?.value;
        const name = document.getElementById('sdr-name')?.value;

        if (!url || !frequency) {
            alert('Veuillez remplir l\'URL et la fréquence');
            return;
        }

        try {
            const stream = {
                url: url,
                frequency_khz: parseInt(frequency),
                name: name || `Flux ${frequency} kHz`
            };

            const response = await fetch('/api/sdr-streams', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(stream)
            });

            if (response.ok) {
                await this.loadSDRStreams();
                this.clearSDRForm();
            } else {
                throw new Error('Erreur serveur');
            }
        } catch (error) {
            console.error('❌ Erreur ajout flux SDR:', error);
            alert('Erreur lors de l\'ajout du flux');
        }
    }

    static async addDefaultBands() {
        const url = document.getElementById('sdr-url')?.value?.trim();
        if (!url) {
            alert("Veuillez saisir l'URL du WebSDR d'abord.");
            return;
        }

        const presets_khz = [14300, 14205, 14235, 14285, 14320, 7085, 7105, 7115, 7125, 7135];
        let added = 0;

        for (const f of presets_khz) {
            try {
                const res = await fetch('/api/sdr-streams', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        url,
                        frequency_khz: f,
                        name: `HF ${f} kHz`
                    })
                });
                if (res.ok) added++;
            } catch (e) {
                console.warn("Erreur ajout preset", f, e);
            }
        }

        alert(`${added} flux ajoutés sur ${presets_khz.length}`);
        await this.loadSDRStreams();
    }

    static clearSDRForm() {
        const urlInput = document.getElementById('sdr-url');
        const freqInput = document.getElementById('sdr-frequency');
        const nameInput = document.getElementById('sdr-name');

        if (urlInput) urlInput.value = '';
        if (freqInput) freqInput.value = '';
        if (nameInput) nameInput.value = '';
    }

    static async loadSDRStreams() {
        try {
            const streams = await this.fetchData('/api/sdr-streams');
            this.sdrStreams = new Map(streams.map(s => [s.id, s]));
            this.updateSDRDisplay();
        } catch (error) {
            console.warn('⚠️ Aucun flux SDR chargé');
        }
    }

    static updateSDRDisplay() {
        this.updateSDRStats();
        this.updateSDRStreamsList();
    }

    static updateSDRStats() {
        const container = document.getElementById('sdr-stats');
        if (!container) return;

        const total = this.sdrStreams.size;
        const active = Array.from(this.sdrStreams.values()).filter(s => s.active).length;
        const totalActivity = Array.from(this.sdrStreams.values()).reduce((sum, s) => sum + (s.total_activity || 0), 0);

        container.innerHTML = `
            <div class="grid grid-cols-2 gap-4">
                <div class="text-center p-3 bg-gray-50 rounded-lg">
                    <div class="text-2xl font-bold text-blue-600">${total}</div>
                    <div class="text-xs text-gray-600">Flux configurés</div>
                </div>
                <div class="text-center p-3 bg-gray-50 rounded-lg">
                    <div class="text-2xl font-bold text-green-600">${active}</div>
                    <div class="text-xs text-gray-600">Flux actifs</div>
                </div>
                <div class="text-center p-3 bg-gray-50 rounded-lg">
                    <div class="text-2xl font-bold text-purple-600">${totalActivity}</div>
                    <div class="text-xs text-gray-600">Activités totales</div>
                </div>
            </div>
        `;
    }

    static updateSDRStreamsList() {
        const container = document.getElementById('sdr-streams-list');
        if (!container) return;

        if (this.sdrStreams.size === 0) {
            container.innerHTML = '<p class="text-gray-500 text-sm">Aucun flux configuré</p>';
            return;
        }

        container.innerHTML = Array.from(this.sdrStreams.values()).map(stream => `
            <div class="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                <div class="flex items-center space-x-3">
                    <div class="w-3 h-3 rounded-full ${stream.active ? 'bg-green-500' : 'bg-gray-300'}"></div>
                    <div>
                        <p class="font-medium text-gray-800">${stream.name || (stream.frequency_khz + ' kHz')}</p>
                        <p class="text-sm text-gray-600">${stream.url}</p>
                    </div>
                </div>
                <div class="flex items-center space-x-3">
                    <div class="text-right">
                        <p class="text-sm text-gray-800">${stream.total_activity || 0} activités</p>
                        <p class="text-xs text-gray-500">${stream.frequency_khz} kHz</p>
                    </div>
                    <button class="text-red-500 hover:text-red-700" title="Supprimer" onclick="WeakIndicatorsManager.deleteSDRStream(${stream.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `).join('');
    }

    static async deleteSDRStream(id) {
        if (!confirm("Supprimer ce flux ?")) return;
        try {
            const res = await fetch(`/api/sdr-streams/${id}`, { method: 'DELETE' });
            if (!res.ok) throw new Error(await res.text());
            await this.loadSDRStreams();
        } catch (error) {
            console.error(error);
            alert("Erreur suppression");
        }
    }

    // 3. INDICATEURS ÉCONOMIQUES
    static async updateEconomicData() {
        const country = document.getElementById('economic-country')?.value || 'US';
        const indicator = document.getElementById('economic-indicator')?.value || 'GDP';
        const period = document.getElementById('economic-period')?.value || '1y';

        try {
            const data = await this.fetchData(`/api/economic-data/${country}/${indicator}?period=${period}`);
            this.displayEconomicChart(data);
            this.analyzeEconomicTrends(data);
        } catch (error) {
            console.error('❌ Erreur données économiques:', error);
            const container = document.getElementById('economic-alerts');
            if (container) {
                container.innerHTML = `<div class="p-2 bg-red-50 border border-red-200 rounded text-sm text-red-800">Erreur: ${error.message}</div>`;
            }
        }
    }

    static displayEconomicChart(data) {
        const canvas = document.getElementById('economic-chart');
        if (!canvas) return;

        if (this.economicChart) {
            this.economicChart.destroy();
        }

        if (!data.data || data.data.length === 0) {
            canvas.parentElement.innerHTML = '<p class="text-gray-500">Aucune donnée disponible</p>';
            return;
        }

        const labels = data.data.map(d => d.date);
        const values = data.data.map(d => d.value);

        this.economicChart = new Chart(canvas, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: `${this.getIndicatorName(data.indicator)} - ${this.getCountryName(data.country)}`,
                    data: values,
                    borderColor: '#3B82F6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }

    static getIndicatorName(indicator) {
        const names = {
            'GDP': 'PIB',
            'INFLATION': 'Inflation',
            'UNEMPLOYMENT': 'Chômage',
            'TRADE_BALANCE': 'Balance commerciale',
            'VIX': 'VIX'
        };
        return names[indicator] || indicator;
    }

    static getCountryName(code) {
        const names = {
            'US': 'États-Unis',
            'CN': 'Chine',
            'DE': 'Allemagne',
            'FR': 'France',
            'JP': 'Japon'

        };
        return names[code] || code;
    }

    static analyzeEconomicTrends(data) {
        const container = document.getElementById('economic-alerts');
        if (!container) return;

        const alerts = [];
        if (data.trend === 'down') {
            alerts.push('⚠️ Tendance à la baisse détectée');
        }
        if (data.indicator?.toUpperCase() === 'VIX' && data.current > 30) {
            alerts.push('🚨 VIX élevé (volatilité forte)');
        }

        container.innerHTML = alerts.length > 0
            ? alerts.map(alert => `<div class="p-2 bg-yellow-50 border border-yellow-200 rounded text-sm text-yellow-800">${alert}</div>`).join('')
            : '<div class="text-sm text-green-600">✅ Aucune anomalie détectée</div>';
    }

    // MÉTHODES UTILITAIRES
    static setupEventListeners() {
        // Recherche de pays
        const searchInput = document.getElementById('countrySearch');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                console.log('Filtrage pays:', e.target.value);
            });
        }

        // Changements des sélecteurs économiques
        const economicSelects = ['economic-country', 'economic-indicator', 'economic-period'];
        economicSelects.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('change', () => this.updateEconomicData());
            }
        });
    }

    static startPeriodicUpdates() {
        setInterval(() => {
            this.loadInitialData();
        }, 5 * 60 * 1000); // 5 minutes
    }

    static delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    static showErrorState() {
        console.error('📛 État d\'erreur affiché');
    }
}

// Initialisation automatique
if (window.location.pathname.includes('/weak-indicators')) {
    document.addEventListener('DOMContentLoaded', function () {
        console.log('🎯 Page indicateurs faibles détectée');
        if (typeof WeakIndicatorsManager !== 'undefined') {
            WeakIndicatorsManager.initialize();
        } else {
            console.error('❌ WeakIndicatorsManager non défini');
        }
    });
}

// Exposer globalement
window.WeakIndicatorsManager = WeakIndicatorsManager;
