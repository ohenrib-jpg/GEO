// static/js/weak-indicators.js - GESTIONNAIRE DES INDICATEURS FAIBLES

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
            console.log('✅ WeakIndicatorsManager initialisé');
        } catch (error) {
            console.error('❌ Erreur initialisation:', error);
        }
    }

    // Dans weak-indicators.js - Ajouter après initialize()

    static async loadInitialData() {
        try {
            // Données par défaut si les APIs ne répondent pas
            this.monitoredCountries = [
                { code: 'FR', name: 'France', slug: 'france' },
                { code: 'US', name: 'United States', slug: 'united-states' },
                { code: 'CN', name: 'China', slug: 'china' },
                { code: 'DE', name: 'Germany', slug: 'germany' },
                { code: 'GB', name: 'United Kingdom', slug: 'united-kingdom' },
                { code: 'JP', name: 'Japan', slug: 'japan' },
                { code: 'RU', name: 'Russia', slug: 'russia' }
            ];

            // Statut global par défaut
            const defaultStatus = {
                monitored_countries: this.monitoredCountries.length,
                active_alerts: 0,
                active_sdr_streams: 0
            };

            this.updateGlobalStats(defaultStatus);

            console.log('✅ Données par défaut chargées pour indicateurs faibles');

        } catch (error) {
            console.error('❌ Erreur chargement données initiales:', error);
            this.showErrorState();
        }
    }

    // Modifier scanAllCountries pour utiliser les données par défaut
    static async scanAllCountries() {
        if (!this.monitoredCountries || this.monitoredCountries.length === 0) {
            // Utiliser les données par défaut
            this.monitoredCountries = [
                { code: 'FR', name: 'France', slug: 'france' },
                { code: 'US', name: 'United States', slug: 'united-states' },
                // ... autres pays
            ];
        }

        const results = [];
        for (const country of this.monitoredCountries) {
            try {
                // Générer des données simulées
                const mockAdvice = this.generateMockTravelAdvice(country.slug || country.code.toLowerCase());
                results.push({
                    country: country.name || country.code,
                    code: country.code,
                    advice: mockAdvice,
                    status: this.analyzeTravelAdvice(mockAdvice)
                });

                // Pause pour éviter la surcharge
                await this.delay(100);

            } catch (error) {
                console.warn(`⚠️ Erreur pour ${country.code}:`, error);
                results.push({
                    country: country.name || country.code,
                    code: country.code,
                    error: error.message,
                    status: 'error'
                });
            }
        }

        return results;
    }

    // Modifier updateEconomicData pour gérer les erreurs
    static async updateEconomicData(buttonElement = null) {
        const button = buttonElement;
        const country = document.getElementById('economic-country')?.value || 'US';
        const indicator = document.getElementById('economic-indicator')?.value || 'GDP';
        const period = document.getElementById('economic-period')?.value || '1y';

        try {
            // Données simulées si l'API n'est pas disponible
            const mockData = this.generateMockEconomicData(country, indicator, period);
            this.displayEconomicChart(mockData);
            this.analyzeEconomicTrends(mockData);

        } catch (error) {
            console.error('❌ Erreur données économiques:', error);
            // Afficher un message d'erreur
            const container = document.getElementById('economic-data');
            if (container) {
                container.innerHTML = `
                <div class="bg-red-50 border border-red-200 rounded p-3">
                    <p class="text-red-800 text-sm">API économique non disponible</p>
                    <p class="text-red-600 text-xs">Utilisation de données simulées</p>
                </div>
            `;
            }
        }
    }

    static generateMockEconomicData(country, indicator, period) {
        // Générer des données économiques simulées
        const dataPoints = [];
        const now = new Date();

        for (let i = 0; i < 12; i++) {
            const date = new Date(now);
            date.setMonth(now.getMonth() - i);

            dataPoints.push({
                date: date.toISOString().split('T')[0],
                value: this.getRandomValue(indicator)
            });
        }

        return {
            country: country,
            indicator: indicator,
            data: dataPoints.reverse(),
            current: this.getRandomValue(indicator),
            trend: Math.random() > 0.5 ? 'up' : 'down'
        };
    }

    static getRandomValue(indicator) {
        const ranges = {
            'GDP': { min: 1.5, max: 4.5 },
            'INFLATION': { min: 1.0, max: 8.0 },
            'UNEMPLOYMENT': { min: 3.0, max: 12.0 },
            'TRADE_BALANCE': { min: -50, max: 50 }
        };

        const range = ranges[indicator] || { min: 0, max: 100 };
        return Number((Math.random() * (range.max - range.min) + range.min).toFixed(2));
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

    static updateGlobalStats(status) {
        // Mettre à jour les cartes de statistiques
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

    // 1. CONSEILS AUX VOYAGEURS
    static async scanTravelAdvice(buttonElement = null) {
        const button = buttonElement || document.querySelector('[onclick*="scanTravelAdvice"]');
        if (!button) {
            console.error('❌ Bouton scanTravelAdvice non trouvé');
            return;
        }

        const originalText = button.innerHTML;

        try {
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Scan en cours...';

            const results = await this.scanAllCountries();
            this.displayTravelAdviceResults(results);
            this.checkForAlerts(results);

            button.innerHTML = '<i class="fas fa-check mr-2"></i>Scan terminé';

        } catch (error) {
            console.error('❌ Erreur scan:', error);
            button.innerHTML = '<i class="fas fa-times mr-2"></i>Erreur';
        } finally {
            setTimeout(() => {
                button.disabled = false;
                button.innerHTML = originalText;
            }, 2000);
        }
    }

    static async scanAllCountries() {
        if (!this.monitoredCountries || this.monitoredCountries.length === 0) {
            await this.loadInitialData();
        }

        const results = [];
        for (const country of this.monitoredCountries) {
            try {
                const advice = await this.fetchTravelAdvice(country.slug || country.code.toLowerCase());
                results.push({
                    country: country.name || country.code,
                    code: country.code,
                    advice: advice,
                    status: this.analyzeTravelAdvice(advice)
                });

                // Pause pour éviter la surcharge
                await this.delay(100);

            } catch (error) {
                console.warn(`⚠️ Erreur pour ${country.code}:`, error);
                results.push({
                    country: country.name || country.code,
                    code: country.code,
                    error: error.message,
                    status: 'error'
                });
            }
        }

        return results;
    }

    static async fetchTravelAdvice(countryCode) {
        try {
            return await this.fetchData(`/api/travel-advice/${countryCode}`);
        } catch (error) {
            // Fallback vers des données simulées
            return this.generateMockTravelAdvice(countryCode);
        }
    }

    static generateMockTravelAdvice(countryCode) {
        const statuses = ['normal', 'vigilance', 'deconseille', 'formellement_deconseille'];
        const weights = [0.7, 0.2, 0.08, 0.02];
        const status = this.weightedRandom(statuses, weights);

        return {
            country: countryCode,
            status: status,
            lastUpdate: new Date().toISOString(),
            details: {
                security: `Situation ${status === 'normal' ? 'calme' : 'tendue'}`,
                recommendations: this.getRecommendations(status)
            }
        };
    }

    static weightedRandom(items, weights) {
        const total = weights.reduce((sum, weight) => sum + weight, 0);
        let random = Math.random() * total;

        for (let i = 0; i < items.length; i++) {
            random -= weights[i];
            if (random <= 0) return items[i];
        }
        return items[0];
    }

    static analyzeTravelAdvice(advice) {
        if (!advice || !advice.status) return { level: 1, risk: 'very_low' };

        const levels = {
            'normal': 1,
            'vigilance': 2,
            'deconseille': 3,
            'formellement_deconseille': 4
        };

        const risks = {
            1: 'very_low',
            2: 'low',
            3: 'medium',
            4: 'high'
        };

        const level = levels[advice.status] || 1;
        return {
            level: level,
            risk: risks[level],
            hasChanges: advice.changes && advice.changes.length > 0
        };
    }

    static getRecommendations(status) {
        const recommendations = {
            normal: ['Vigilance normale dans les lieux touristiques'],
            vigilance: ['Éviter les rassemblements', 'Rester informé'],
            deconseille: ['Voyage essentiel uniquement', 'Éviter certaines régions'],
            formellement_deconseille: ['Ne pas se rendre dans le pays', 'Évacuation recommandée']
        };
        return recommendations[status] || ['Aucune recommandation spécifique'];
    }

    static displayTravelAdviceResults(results) {
        const container = document.getElementById('travel-advice-results');
        if (!container) return;

        if (!results || results.length === 0) {
            container.innerHTML = '<p class="text-gray-500">Aucun résultat</p>';
            return;
        }

        container.innerHTML = results.map(result => `
            <div class="border rounded-lg p-4 ${this.getStatusColor(result.status.level)}">
                <div class="flex justify-between items-start">
                    <div>
                        <h4 class="font-semibold text-gray-800">${result.country}</h4>
                        <p class="text-sm text-gray-600">Statut: ${this.getStatusText(result.status.level)}</p>
                    </div>
                    <span class="px-2 py-1 rounded-full text-xs font-medium ${this.getRiskBadgeClass(result.status.risk)}">
                        ${this.getRiskText(result.status.risk)}
                    </span>
                </div>
                ${result.advice?.details?.recommendations ? `
                    <div class="mt-2">
                        <p class="text-sm text-gray-700">Recommandations:</p>
                        <ul class="text-sm text-gray-600 list-disc list-inside">
                            ${result.advice.details.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>
        `).join('');
    }

    static getStatusColor(level) {
        const colors = {
            1: 'bg-green-50 border-green-200',
            2: 'bg-yellow-50 border-yellow-200',
            3: 'bg-orange-50 border-orange-200',
            4: 'bg-red-50 border-red-200'
        };
        return colors[level] || 'bg-gray-50 border-gray-200';
    }

    static getStatusText(level) {
        const texts = { 1: 'Normal', 2: 'Vigilance', 3: 'Déconseillé', 4: 'Formellement déconseillé' };
        return texts[level] || 'Inconnu';
    }

    static getRiskBadgeClass(risk) {
        const classes = {
            'very_low': 'bg-green-100 text-green-800',
            'low': 'bg-blue-100 text-blue-800',
            'medium': 'bg-yellow-100 text-yellow-800',
            'high': 'bg-red-100 text-red-800'
        };
        return classes[risk] || 'bg-gray-100 text-gray-800';
    }

    static getRiskText(risk) {
        const texts = {
            'very_low': 'Très faible',
            'low': 'Faible',
            'medium': 'Moyen',
            'high': 'Élevé'
        };
        return texts[risk] || 'Inconnu';
    }

    static checkForAlerts(results) {
        const alerts = results.filter(result =>
            result.status.hasChanges || result.status.level >= 3
        );
        this.displayTravelAlerts(alerts);
    }

    static displayTravelAlerts(alerts) {
        const container = document.getElementById('travel-alerts');
        if (!container) return;

        if (alerts.length === 0) {
            container.innerHTML = '<p class="text-yellow-700 text-sm">Aucune alerte récente</p>';
            return;
        }

        container.innerHTML = alerts.map(alert => `
            <div class="flex items-start space-x-2 p-2 bg-white rounded border border-yellow-300">
                <i class="fas fa-exclamation-triangle text-yellow-600 mt-1"></i>
                <div>
                    <p class="text-sm font-medium text-yellow-800">${alert.country}</p>
                    <p class="text-xs text-yellow-700">
                        ${alert.status.hasChanges ? 'Changements détectés' : 'Niveau d\'alerte élevé'}
                    </p>
                </div>
            </div>
        `).join('');
    }

    // 2. SURVEILLANCE SDR
    static async addSDRStream() {
        const url = document.getElementById('sdr-url')?.value;
        const frequency = document.getElementById('sdr-frequency')?.value;

        if (!url || !frequency) {
            alert('Veuillez remplir l\'URL et la fréquence');
            return;
        }

        try {
            const stream = {
                url: url,
                frequency: frequency,
                description: `Flux ${frequency}MHz`
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
        const totalActivity = Array.from(this.sdrStreams.values()).reduce((sum, s) => sum + (s.activity_count || 0), 0);

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
                    <div class="text-xs text-gray-600">Activité totale</div>
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
                        <p class="font-medium text-gray-800">${stream.frequency_mhz || stream.frequency} MHz</p>
                        <p class="text-sm text-gray-600">${stream.stream_url || stream.url}</p>
                    </div>
                </div>
                <div class="text-right">
                    <p class="text-sm text-gray-800">${stream.activity_count || 0} activités</p>
                </div>
            </div>
        `).join('');
    }

    static clearSDRForm() {
        const urlInput = document.getElementById('sdr-url');
        const freqInput = document.getElementById('sdr-frequency');
        if (urlInput) urlInput.value = '';
        if (freqInput) freqInput.value = '';
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
        }
    }

    static displayEconomicChart(data) {
        const canvas = document.getElementById('economic-chart');
        if (!canvas) return;

        // Détruire l'ancien graphique
        if (this.economicChart) {
            this.economicChart.destroy();
        }

        if (!data.data || data.data.length === 0) {
            canvas.parentElement.innerHTML = '<p class="text-gray-500">Aucune donnée disponible</p>';
            return;
        }

        const labels = data.data.map(d => new Date(d.date).toLocaleDateString('fr-FR'));
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
            'GDP': 'PIB', 'INFLATION': 'Inflation',
            'UNEMPLOYMENT': 'Chômage', 'TRADE_BALANCE': 'Balance commerciale'
        };
        return names[indicator] || indicator;
    }

    static getCountryName(code) {
        const names = {
            'US': 'États-Unis', 'CN': 'Chine', 'DE': 'Allemagne',
            'FR': 'France', 'JP': 'Japon'
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
        if (data.current > 8 && data.indicator === 'INFLATION') {
            alerts.push('🚨 Inflation élevée');
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
                this.filterCountries(e.target.value);
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

    static filterCountries(searchTerm) {
        console.log('Filtrage pays:', searchTerm);
        // Implémentation de la filtration
    }

    static startPeriodicUpdates() {
        // Actualisation automatique
        setInterval(() => {
            this.loadInitialData();
        }, 5 * 60 * 1000); // 5 minutes
    }

    static delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    static showErrorState() {
        console.error('📛 État d\'erreur affiché');
        // Afficher un message d'erreur à l'utilisateur
    }
}

// Initialisation automatique
if (window.location.pathname.includes('/weak-indicators')) {
    document.addEventListener('DOMContentLoaded', function () {
        console.log('🎯 Page indicateurs faibles détectée');
        WeakIndicatorsManager.initialize();
    });
}

window.WeakIndicatorsManager = WeakIndicatorsManager;