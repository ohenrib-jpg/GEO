// static/js/indicateurs-francais.js (VERSION CORRIGÉE)
class IndicateursFrancaisManager {
    constructor() {
        this.charts = {};
        this.currentData = null;
        this.qualityMetrics = null;
        this.init();
    }

    init() {
        console.log("🎯 IndicateursFrancaisManager Production initialisé");
        this.loadData();
        this.setupEventListeners();

        // Rafraîchissement automatique toutes les 5 minutes
        setInterval(() => this.loadData(), 300000);
    }

    setupEventListeners() {
        const refreshBtn = document.getElementById('refreshData');
        const periodSelect = document.getElementById('periodSelect');
        const categorySelect = document.getElementById('categorySelect');

        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadData());
        }

        if (periodSelect) {
            periodSelect.addEventListener('change', () => this.loadHistoricalData());
        }

        if (categorySelect) {
            categorySelect.addEventListener('change', () => this.filterIndicators());
        }
    }

    async checkApiStatus() {
        try {
            // Utilisez la route /status qui existe
            const response = await fetch('/indicateurs/api/status');
            const data = await response.json();

            if (data.success) {
                this.updateStatusDisplay(data);
            }
        } catch (error) {
            console.log('ℹ️ Route detailed-status non disponible, utilisation de méthodes alternatives');
            // Ne pas afficher d'erreur, cette route est optionnelle
        }
    }

    updateStatusDisplay(statusData) {
        const statusElement = document.getElementById('apiStatus');
        if (!statusElement) return;

        if (statusData.system_status === 'operational') {
            statusElement.innerHTML = '<span class="text-green-600 font-semibold">✅ Système opérationnel</span>';
            statusElement.parentElement.className = 'rounded-lg p-3 border bg-green-50 border-green-200 mb-4';
        } else {
            statusElement.innerHTML = '<span class="text-yellow-600 font-semibold">⚠️ Système dégradé</span>';
            statusElement.parentElement.className = 'rounded-lg p-3 border bg-yellow-50 border-yellow-200 mb-4';
        }
    }

    async loadData() {
        try {
            this.showLoading();
            await this.checkApiStatus();

            // Récupérer les indicateurs principaux
            const response = await fetch('/indicateurs/api/indicators');
            const data = await response.json();

            if (data.success) {
                this.currentData = data.indicators;
                this.qualityMetrics = data.quality_metrics;
                this.displayIndicators(data.indicators);
                this.updateLastUpdate(data.timestamp);
                this.displayQualityMetrics(data.quality_metrics);

                await this.loadHistoricalData();
            } else {
                throw new Error(data.error || 'Erreur de chargement');
            }

        } catch (error) {
            console.error('❌ Erreur chargement indicateurs:', error);
            this.showError(error.message);
        }
    }

    displayQualityMetrics(metrics) {
        const metricsElement = document.getElementById('qualityMetrics');
        if (!metricsElement || !metrics) return;

        metricsElement.innerHTML = `
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                <div class="bg-green-50 rounded-lg p-3">
                    <div class="text-2xl font-bold text-green-600">${metrics.availability_rate}</div>
                    <div class="text-xs text-green-800">Disponibilité</div>
                </div>
                <div class="bg-blue-50 rounded-lg p-3">
                    <div class="text-2xl font-bold text-blue-600">${metrics.high_confidence_data}</div>
                    <div class="text-xs text-blue-800">Confiance élevée</div>
                </div>
                <div class="bg-purple-50 rounded-lg p-3">
                    <div class="text-sm font-bold text-purple-600">${metrics.data_freshness}</div>
                    <div class="text-xs text-purple-800">Fraîcheur</div>
                </div>
                <div class="bg-orange-50 rounded-lg p-3">
                    <div class="text-sm font-bold text-orange-600">${metrics.available_indicators}/${metrics.total_indicators}</div>
                    <div class="text-xs text-orange-800">Indicateurs</div>
                </div>
            </div>
        `;
    }

    displayIndicators(indicators) {
        // Afficher chaque indicateur disponible
        Object.keys(indicators).forEach(indicatorKey => {
            const indicator = indicators[indicatorKey];
            if (indicator?.success) {
                this.updateIndicatorCard(indicatorKey, indicator);
            } else {
                this.showIndicatorError(indicatorKey);
            }
        });

        this.updateTable(indicators);
    }

    updateIndicatorCard(id, data) {
        const card = document.getElementById(`${id}Card`);
        const valueElement = document.getElementById(`${id}Value`);
        const changeElement = document.getElementById(`${id}Change`);
        const sourceElement = document.getElementById(`${id}Source`);
        const confidenceElement = document.getElementById(`${id}Confidence`);

        if (!card) {
            console.log(`ℹ️ Carte ${id}Card non trouvée dans le HTML`);
            return;
        }

        // Mettre à jour la valeur
        if (valueElement) {
            let displayValue = '';

            if (data.unit === '%') {
                displayValue = data.value.toFixed(1) + '%';
            } else if (data.unit === 'Milliards €') {
                displayValue = data.value.toLocaleString('fr-FR') + ' Mds €';
            } else if (data.unit === 'points') {
                displayValue = data.value.toLocaleString('fr-FR') + ' pts';
            } else if (data.unit === 'Indice') {
                displayValue = data.value.toFixed(1);
            } else {
                displayValue = data.value.toLocaleString('fr-FR');
            }

            valueElement.textContent = displayValue;
        }

        // Mettre à jour le changement
        if (changeElement && data.change !== undefined) {
            const changeText = data.change > 0 ? `+${data.change}` : data.change.toString();
            const trendIcon = data.trend === 'up' ? '↗️' :
                data.trend === 'down' ? '↘️' : '➡️';

            changeElement.textContent = `${changeText}${data.unit === '' ? '' : data.unit} ${trendIcon}`;

            // Couleurs adaptées
            if (id === 'chomage' || id === 'deficit') {
                // Pour le chômage et déficit, une baisse est positive
                changeElement.className = data.trend === 'down' ? 'text-green-200 text-sm' :
                    data.trend === 'up' ? 'text-red-200 text-sm' : 'text-gray-200 text-sm';
            } else {
                changeElement.className = data.trend === 'up' ? 'text-green-200 text-sm' :
                    data.trend === 'down' ? 'text-red-200 text-sm' : 'text-gray-200 text-sm';
            }
        }

        // Mettre à jour la source
        if (sourceElement) {
            let sourceHtml = data.source || 'N/A';

            // Ajouter l'indicateur de confiance
            if (data.confidence_level) {
                const confidenceConfig = this.getConfidenceConfig(data.confidence_level);
                sourceHtml += ` <span class="text-xs ${confidenceConfig.color}" title="${data.note || confidenceConfig.tooltip}">${confidenceConfig.icon}</span>`;
            }

            sourceElement.innerHTML = sourceHtml;
        }

        // Indicateur de confiance visuel
        if (confidenceElement) {
            const confidenceConfig = this.getConfidenceConfig(data.confidence_level);
            confidenceElement.innerHTML = `
                <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${confidenceConfig.bgColor} ${confidenceConfig.textColor}">
                    ${confidenceConfig.icon} ${confidenceConfig.label}
                </span>
            `;
        }

        // Bordure de carte selon la confiance
        const confidenceConfig = this.getConfidenceConfig(data.confidence_level);
        card.className = card.className.replace(/border-\w+-\d+/, '');
        card.classList.add(confidenceConfig.borderColor);
    }

    getConfidenceConfig(level) {
        const configs = {
            'high': {
                icon: '✅',
                label: 'Direct',
                color: 'text-green-300',
                bgColor: 'bg-green-100',
                textColor: 'text-green-800',
                borderColor: 'border-green-300',
                tooltip: 'Donnée directe de la source officielle'
            },
            'medium': {
                icon: '🔄',
                label: 'Vérifiée',
                color: 'text-blue-300',
                bgColor: 'bg-blue-100',
                textColor: 'text-blue-800',
                borderColor: 'border-blue-300',
                tooltip: 'Dernière donnée officielle vérifiée'
            },
            'low': {
                icon: '📊',
                label: 'Référence',
                color: 'text-orange-300',
                bgColor: 'bg-orange-100',
                textColor: 'text-orange-800',
                borderColor: 'border-orange-300',
                tooltip: 'Donnée statistique de référence'
            }
        };
        return configs[level] || configs.low;
    }

    showIndicatorError(indicatorId) {
        const valueElement = document.getElementById(`${indicatorId}Value`);
        if (valueElement) {
            valueElement.innerHTML = '<span class="text-red-200 text-sm">Indisponible</span>';
        }
    }

    updateTable(indicators) {
        const tableBody = document.getElementById('indicateursTable');
        if (!tableBody) return;

        let html = '';
        Object.values(indicators).forEach(indicator => {
            if (indicator?.success) {
                const hasChange = indicator.change !== undefined;
                const changeText = hasChange ?
                    (indicator.change > 0 ? `+${indicator.change}` : indicator.change) :
                    'N/A';

                const trendClass = !hasChange ? 'text-gray-600' :
                    indicator.trend === 'up' ? 'text-green-600' :
                        indicator.trend === 'down' ? 'text-red-600' : 'text-gray-600';

                const confidenceConfig = this.getConfidenceConfig(indicator.confidence_level);

                html += `
                    <tr>
                        <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            ${indicator.indicator}
                            <span class="${confidenceConfig.color} ml-1" title="${indicator.note || confidenceConfig.tooltip}">
                                ${confidenceConfig.icon}
                            </span>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            ${indicator.value}${indicator.unit}
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm ${trendClass}">
                            ${hasChange ? changeText + indicator.unit : 'N/A'}
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            ${indicator.period || 'N/A'}
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            ${indicator.source}
                        </td>
                    </tr>
                `;
            } else {
                html += `
                    <tr>
                        <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            ${this.getIndicatorNameFromKey(indicator?.indicator)}
                        </td>
                        <td colspan="4" class="px-6 py-4 text-center text-red-500 text-sm">
                            <i class="fas fa-exclamation-triangle mr-1"></i>
                            Données temporairement indisponibles
                        </td>
                    </tr>
                `;
            }
        });

        tableBody.innerHTML = html || '<tr><td colspan="5" class="px-6 py-4 text-center text-gray-500">Aucune donnée disponible</td></tr>';
    }

    getIndicatorNameFromKey(key) {
        const names = {
            'Produit Intérieur Brut': 'PIB',
            'Taux de chômage': 'Chômage',
            "Taux d'inflation": 'Inflation',
            'Production industrielle': 'Production',
            'Solde commercial': 'Commerce',
            'Déficit public': 'Déficit',
            'Activité construction': 'Construction',
            'CAC 40': 'CAC 40'
        };
        return names[key] || key;
    }

    async loadHistoricalData() {
        try {
            const period = document.getElementById('periodSelect')?.value || '6M';
            const response = await fetch(`/indicateurs/api/historical?period=${period}`);
            const data = await response.json();

            if (data.success) {
                this.displayCharts(data.data);
            } else {
                this.showChartError('pibChart', 'Données historiques indisponibles');
                this.showChartError('chomageChart', 'Données historiques indisponibles');
            }
        } catch (error) {
            console.error('❌ Erreur chargement historique:', error);
            this.showChartError('pibChart', 'Erreur de chargement');
            this.showChartError('chomageChart', 'Erreur de chargement');
        }
    }

    displayCharts(historicalData) {
        if (!historicalData || historicalData.length === 0) {
            console.warn('Pas de données historiques disponibles');
            this.showChartError('pibChart', 'Données historiques indisponibles');
            this.showChartError('chomageChart', 'Données historiques indisponibles');
            return;
        }

        this.createMainChart(historicalData);
        this.createVolumeChart(historicalData);
    }

    showChartError(canvasId, message) {
        const ctx = document.getElementById(canvasId);
        if (ctx) {
            ctx.innerHTML = `
                <div class="flex items-center justify-center h-full text-gray-500">
                    <i class="fas fa-chart-line mr-2"></i>
                    ${message}
                </div>
            `;
        }
    }

    createMainChart(data) {
        const ctx = document.getElementById('pibChart');
        if (!ctx) return;

        if (this.charts.main) {
            this.charts.main.destroy();
        }

        const dates = data.map(item => {
            const date = new Date(item.date);
            return date.toLocaleDateString('fr-FR', { month: 'short', day: 'numeric' });
        });
        const values = data.map(item => item.close);

        this.charts.main = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [{
                    label: 'CAC 40',
                    data: values,
                    borderColor: '#3B82F6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 2,
                    pointHoverRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function (context) {
                                return `${context.dataset.label}: ${context.parsed.y.toFixed(2)} pts`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        ticks: {
                            callback: function (value) {
                                return value.toLocaleString('fr-FR') + ' pts';
                            }
                        }
                    },
                    x: {
                        ticks: {
                            maxRotation: 45,
                            minRotation: 45
                        }
                    }
                }
            }
        });
    }

    createVolumeChart(data) {
        const ctx = document.getElementById('chomageChart');
        if (!ctx) return;

        if (this.charts.volume) {
            this.charts.volume.destroy();
        }

        const dates = data.slice(-30).map(item => {
            const date = new Date(item.date);
            return date.toLocaleDateString('fr-FR', { month: 'short', day: 'numeric' });
        });
        const volumes = data.slice(-30).map(item => item.volume / 1000000);

        this.charts.volume = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: dates,
                datasets: [{
                    label: 'Volume (M)',
                    data: volumes,
                    backgroundColor: '#EF4444',
                    borderColor: '#DC2626',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                return `Volume: ${context.parsed.y.toFixed(2)}M`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function (value) {
                                return value.toFixed(0) + 'M';
                            }
                        }
                    },
                    x: {
                        ticks: {
                            maxRotation: 45,
                            minRotation: 45
                        }
                    }
                }
            }
        });
    }

    showLoading() {
        const cards = ['pib', 'chomage', 'inflation', 'production', 'commerce', 'deficit', 'construction', 'cac40'];
        cards.forEach(id => {
            const valueElement = document.getElementById(`${id}Value`);
            const confidenceElement = document.getElementById(`${id}Confidence`);

            if (valueElement) {
                valueElement.innerHTML = '<i class="fas fa-spinner fa-spin text-white"></i>';
            }
            if (confidenceElement) {
                confidenceElement.innerHTML = '<span class="text-xs text-gray-300">Chargement...</span>';
            }
        });

        const tableBody = document.getElementById('indicateursTable');
        if (tableBody) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="5" class="px-6 py-4 text-center text-gray-500">
                        <i class="fas fa-spinner fa-spin mr-2"></i>
                        Chargement des données...
                    </td>
                </tr>
            `;
        }

        this.showChartError('pibChart', 'Chargement des données...');
        this.showChartError('chomageChart', 'Chargement des données...');
    }

    showError(message) {
        console.error('Erreur indicateurs:', message);

        const tableBody = document.getElementById('indicateursTable');
        if (tableBody) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="5" class="px-6 py-4 text-center text-red-500">
                        <i class="fas fa-exclamation-triangle mr-2"></i>
                        Erreur: ${message}
                    </td>
                </tr>
            `;
        }

        this.showChartError('pibChart', 'Erreur de chargement');
        this.showChartError('chomageChart', 'Erreur de chargement');
    }

    updateLastUpdate(timestamp) {
        const lastUpdateElement = document.getElementById('lastUpdate');
        if (lastUpdateElement && timestamp) {
            const date = new Date(timestamp);
            lastUpdateElement.textContent = date.toLocaleString('fr-FR', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        }
    }
}

// Initialisation automatique
document.addEventListener('DOMContentLoaded', function () {
    window.IndicateursFrancaisManager = new IndicateursFrancaisManager();
    console.log("✅ IndicateursFrancaisManager Production prêt");
});