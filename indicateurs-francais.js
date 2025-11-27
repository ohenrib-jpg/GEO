// static/js/indicateurs-francais.js (VERSION COMPLÈTE ET CORRIGÉE)
class IndicateursFrancaisManager {
    constructor() {
        this.charts = {};
        this.currentData = null;
        this.qualityMetrics = null;
        this.apiSources = new Set();
        this.validSeries = {};
        this.init();
    }

    init() {
        console.log("🎯 IndicateursFrancaisManager Amélioré initialisé");
        this.loadData();
        this.setupEventListeners();
        this.loadValidSeries();
        this.setupDiagnostic();
        // Rafraîchissement toutes les 10 minutes
        setInterval(() => this.loadData(), 600000);
    }

    setupEventListeners() {
        const refreshBtn = document.getElementById('refreshData');
        const periodSelect = document.getElementById('periodSelect');
        const exploreBtn = document.getElementById('exploreSeries');
        const categorySelect = document.getElementById('categorySelect');

        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadData());
        }

        if (periodSelect) {
            periodSelect.addEventListener('change', () => this.loadHistoricalData());
        }

        if (exploreBtn) {
            exploreBtn.addEventListener('click', () => this.exploreSeries());
        }

        if (categorySelect) {
            categorySelect.addEventListener('change', () => this.filterIndicators());
        }
    }

    setupDiagnostic() {
        const diagnosticBtn = document.getElementById('diagnosticBtn');
        if (diagnosticBtn) {
            diagnosticBtn.addEventListener('click', () => this.runDiagnostic());
        }
    }

    async runDiagnostic() {
        try {
            this.showNotification('🔧 Diagnostic API INSEE en cours...', 'info');

            const response = await fetch('/indicateurs/api/explore-insee');
            const data = await response.json();

            const resultsElement = document.getElementById('diagnosticResults');
            if (resultsElement) {
                if (data.success) {
                    let html = '<div class="space-y-2">';
                    html += `<p class="text-sm text-green-700">✅ ${data.valid_count} séries valides trouvées</p>`;

                    Object.entries(data.results).forEach(([name, result]) => {
                        const status = result.success ? '✅' : '❌';
                        const value = result.success ? `Valeur: ${result.value} (${result.period})` : 'Échec';
                        html += `<div class="text-xs font-mono p-2 bg-white rounded border">
                            ${status} ${name}: ${result.series_id} - ${value}
                        </div>`;
                    });

                    html += '</div>';
                    resultsElement.innerHTML = html;
                    resultsElement.classList.remove('hidden');
                    this.showNotification('✅ Diagnostic terminé', 'success');
                } else {
                    resultsElement.innerHTML = `<p class="text-red-700">❌ Erreur diagnostic: ${data.error}</p>`;
                    resultsElement.classList.remove('hidden');
                    this.showNotification('❌ Erreur lors du diagnostic', 'error');
                }
            }
        } catch (error) {
            console.error('❌ Erreur diagnostic:', error);
            this.showNotification('❌ Erreur lors du diagnostic', 'error');
        }
    }

    async loadValidSeries() {
        try {
            const response = await fetch('/indicateurs/api/valid-series');
            const data = await response.json();

            if (data.success) {
                this.validSeries = data.valid_series;
                this.updateSeriesInfo(data);
            }
        } catch (error) {
            console.log('ℹ️ Route valid-series non disponible');
        }
    }

    updateSeriesInfo(data) {
        const seriesElement = document.getElementById('seriesInfo');
        if (!seriesElement) return;

        const validCount = Object.values(data.valid_series).filter(v => v).length;
        const totalCount = Object.keys(data.valid_series).length;

        seriesElement.innerHTML = `
            <div class="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                <span class="text-sm text-blue-700">
                    📊 ${validCount}/${totalCount} séries INSEE configurées
                </span>
                <button id="exploreSeries" class="text-xs bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded transition duration-200">
                    🔍 Explorer
                </button>
            </div>
        `;

        // Re-attacher l'event listener
        const exploreBtn = document.getElementById('exploreSeries');
        if (exploreBtn) {
            exploreBtn.addEventListener('click', () => this.exploreSeries());
        }
    }

    async exploreSeries() {
        try {
            this.showNotification('🔍 Exploration des APIs en cours...', 'info');

            // CORRECTION : Utiliser la bonne route et gérer l'absence de données
            const response = await fetch('/indicateurs/api/explore-apis');
            const data = await response.json();

            if (data.success) {
                // CORRECTION : Vérifier que data.results existe
                const results = data.results || {};
                const validCount = data.valid_count || 0;

                this.showNotification(`✅ Exploration terminée - ${validCount} APIs disponibles`, 'success');

                // Afficher les résultats du diagnostic
                const resultsElement = document.getElementById('diagnosticResults');
                if (resultsElement) {
                    let html = '<div class="space-y-2">';
                    html += `<p class="text-sm text-green-700">✅ ${validCount} APIs disponibles</p>`;

                    Object.entries(results).forEach(([name, result]) => {
                        const status = result.success ? '✅' : '❌';
                        const details = result.details || 'Non disponible';
                        html += `<div class="text-xs font-mono p-2 bg-white rounded border">
                        ${status} ${name}: ${details}
                    </div>`;
                    });

                    html += '</div>';
                    resultsElement.innerHTML = html;
                    resultsElement.classList.remove('hidden');
                }

                await this.loadData();
            } else {
                this.showNotification('❌ Erreur lors de l\'exploration: ' + (data.error || 'Inconnue'), 'error');
            }
        } catch (error) {
            console.error('❌ Erreur exploration:', error);
            this.showNotification('❌ Erreur lors de l\'exploration', 'error');
        }
    }

    async checkApiStatus() {
        try {
            const response = await fetch('/indicateurs/api/status');
            const data = await response.json();

            if (data.success) {
                this.updateStatusDisplay(data);
            }
        } catch (error) {
            console.log('ℹ️ Route status non disponible');
        }
    }

    updateStatusDisplay(statusData) {
        const statusElement = document.getElementById('apiStatus');
        if (!statusElement) return;

        let statusHtml = '';
        if (statusData.system_status === 'operational') {
            statusHtml = '<span class="text-green-600 font-semibold">✅ Système opérationnel</span>';

            if (statusData.exploration) {
                const validCount = statusData.exploration.valid_series_count;
                const totalCount = statusData.exploration.total_series;
                statusHtml += `<div class="text-xs text-green-700 mt-1">${validCount}/${totalCount} séries INSEE valides</div>`;
            }
        } else {
            statusHtml = '<span class="text-yellow-600 font-semibold">⚠️ Système dégradé</span>';
        }

        statusElement.innerHTML = statusHtml;
    }

    async loadData() {
        try {
            this.showLoading();

            const response = await fetch('/indicateurs/api/indicators');
            const data = await response.json();

            if (data.success) {
                this.currentData = data.indicators;
                this.displayIndicators(data.indicators);
                this.updateLastUpdate(data.timestamp);

                // Charger les données historiques
                await this.loadHistoricalData();
            } else {
                throw new Error(data.error || 'Erreur de chargement des données');
            }

        } catch (error) {
            console.error('❌ Erreur chargement indicateurs:', error);
            this.showError('Données temporairement indisponibles');
            // Charger des données de démo
            this.loadDemoData();
        }
    }

    // Méthode de démonstration en cas d'erreur
    loadDemoData() {
        const demoData = {
            'pib': {
                'success': true,
                'indicator': 'Produit Intérieur Brut',
                'value': 695.2,
                'unit': 'Milliards €',
                'period': '2024-T3',
                'trend': 'stable',
                'source': 'INSEE - Données de démonstration'
            },
            'chomage': {
                'success': true,
                'indicator': 'Taux de chômage',
                'value': 7.1,
                'unit': '%',
                'period': '2024-T3',
                'trend': 'stable',
                'source': 'INSEE - Données de démonstration'
            },
            'inflation': {
                'success': true,
                'indicator': "Taux d'inflation",
                'value': 2.2,
                'unit': '%',
                'period': '2024-10',
                'trend': 'down',
                'source': 'INSEE - Données de démonstration'
            }
        };

        this.displayIndicators(demoData);
        this.updateLastUpdate(new Date().toISOString());

        this.showNotification('Mode démonstration activé', 'info');
    }

    displayApiSources() {
        const sourcesElement = document.getElementById('apiSources');
        if (!sourcesElement) return;

        const sourceIcons = {
            'insee_direct': '📈',
            'insee_explored': '🔍',
            'ministere_economie': '🏛️',
            'yahoo_finance': '💰',
            'fallback': '📊',
            'unknown': '🔗'
        };

        const sourceNames = {
            'insee_direct': 'INSEE Direct',
            'insee_explored': 'INSEE Exploré',
            'ministere_economie': 'Ministère Économie',
            'yahoo_finance': 'Yahoo Finance',
            'fallback': 'Données de Référence',
            'unknown': 'Source inconnue'
        };

        let html = '<div class="flex flex-wrap gap-2 mt-3">';
        this.apiSources.forEach(source => {
            if (source) {
                html += `
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 border border-blue-200">
                        ${sourceIcons[source] || '🔗'} ${sourceNames[source] || source}
                    </span>
                `;
            }
        });
        html += '</div>';

        sourcesElement.innerHTML = html;
    }

    displayQualityMetrics(metrics) {
        const metricsElement = document.getElementById('qualityMetrics');
        if (!metricsElement || !metrics) return;

        metricsElement.innerHTML = `
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                <div class="bg-green-50 rounded-lg p-4 border border-green-200 shadow-sm">
                    <div class="text-2xl font-bold text-green-600">${metrics.availability_rate}</div>
                    <div class="text-xs text-green-800 font-medium">Disponibilité</div>
                </div>
                <div class="bg-blue-50 rounded-lg p-4 border border-blue-200 shadow-sm">
                    <div class="text-2xl font-bold text-blue-600">${metrics.high_confidence_data}</div>
                    <div class="text-xs text-blue-800 font-medium">Confiance élevée</div>
                </div>
                <div class="bg-purple-50 rounded-lg p-4 border border-purple-200 shadow-sm">
                    <div class="text-2xl font-bold text-purple-600">${metrics.insee_direct_data || '--%'}</div>
                    <div class="text-xs text-purple-800 font-medium">INSEE Direct</div>
                </div>
                <div class="bg-orange-50 rounded-lg p-4 border border-orange-200 shadow-sm">
                    <div class="text-sm font-bold text-orange-600">${metrics.available_indicators}/${metrics.total_indicators}</div>
                    <div class="text-xs text-orange-800 font-medium">Indicateurs</div>
                </div>
            </div>
            <div id="apiSources" class="mt-4"></div>
        `;
    }

    displayIndicators(indicators) {
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
            } else if (data.unit === '% PIB') {
                displayValue = data.value.toFixed(1) + '% PIB';
            } else {
                displayValue = data.value.toLocaleString('fr-FR');
            }

            valueElement.textContent = displayValue;
        }

        if (changeElement && data.change !== undefined) {
            const changeText = data.change > 0 ? `+${data.change.toFixed(1)}` : data.change.toFixed(1);
            const trendIcon = data.trend === 'up' ? '📈' :
                data.trend === 'down' ? '📉' : '➡️';

            changeElement.textContent = `${changeText}${data.unit === '' ? '' : data.unit} ${trendIcon}`;

            if (id === 'chomage' || id === 'deficit') {
                changeElement.className = data.trend === 'down' ? 'text-green-200 text-sm font-medium' :
                    data.trend === 'up' ? 'text-red-200 text-sm font-medium' : 'text-gray-200 text-sm';
            } else {
                changeElement.className = data.trend === 'up' ? 'text-green-200 text-sm font-medium' :
                    data.trend === 'down' ? 'text-red-200 text-sm font-medium' : 'text-gray-200 text-sm';
            }
        }

        if (sourceElement) {
            let sourceHtml = data.source || 'N/A';
            const apiIcons = {
                'insee_direct': '📈',
                'insee_explored': '🔍',
                'yahoo_finance': '💰',
                'ministere_economie': '🏛️',
                'fallback': '📊',
                'unknown': '🔗'
            };

            const icon = apiIcons[data.api_source] || '🔗';
            sourceHtml = `${icon} ${sourceHtml}`;

            if (data.confidence_level) {
                const confidenceConfig = this.getConfidenceConfig(data.confidence_level);
                sourceHtml += ` <span class="text-xs ${confidenceConfig.color}" title="${data.note || confidenceConfig.tooltip}">${confidenceConfig.icon}</span>`;
            }
            sourceElement.innerHTML = sourceHtml;
        }

        if (confidenceElement) {
            const confidenceConfig = this.getConfidenceConfig(data.confidence_level);
            confidenceElement.innerHTML = `
                <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${confidenceConfig.bgColor} ${confidenceConfig.textColor}">
                    ${confidenceConfig.icon} ${confidenceConfig.label}
                </span>
            `;
        }

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
                    (indicator.change > 0 ? `+${indicator.change.toFixed(1)}` : indicator.change.toFixed(1)) :
                    'N/A';

                const trendClass = !hasChange ? 'text-gray-600' :
                    indicator.trend === 'up' ? 'text-green-600 font-medium' :
                        indicator.trend === 'down' ? 'text-red-600 font-medium' : 'text-gray-600';

                const confidenceConfig = this.getConfidenceConfig(indicator.confidence_level);
                const apiIcons = {
                    'insee_direct': '📈',
                    'insee_explored': '🔍',
                    'yahoo_finance': '💰',
                    'ministere_economie': '🏛️',
                    'fallback': '📊',
                    'unknown': '🔗'
                };
                const apiIcon = apiIcons[indicator.api_source] || '🔗';

                html += `
                    <tr class="hover:bg-gray-50">
                        <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            ${indicator.indicator}
                            <span class="${confidenceConfig.color} ml-1" title="${indicator.note || confidenceConfig.tooltip}">
                                ${confidenceConfig.icon}
                            </span>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            ${this.formatValue(indicator.value, indicator.unit)}
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm ${trendClass}">
                            ${hasChange ? changeText + (indicator.unit === '' ? '' : ' ' + indicator.unit) : 'N/A'}
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            ${indicator.period || 'N/A'}
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            <span title="${indicator.api_source}">${apiIcon}</span> ${indicator.source}
                        </td>
                    </tr>
                `;
            } else {
                html += `
                    <tr class="hover:bg-gray-50">
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

    formatValue(value, unit) {
        if (unit === '%') {
            return value.toFixed(1) + '%';
        } else if (unit === 'Milliards €') {
            return value.toLocaleString('fr-FR') + ' Mds €';
        } else if (unit === 'points') {
            return value.toLocaleString('fr-FR') + ' pts';
        } else if (unit === 'Indice') {
            return value.toFixed(1);
        } else if (unit === '% PIB') {
            return value.toFixed(1) + '% PIB';
        } else {
            return value.toLocaleString('fr-FR');
        }
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
                this.displayCharts(data);
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
        if (!historicalData || !historicalData.data || historicalData.data.length === 0) {
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

        const dates = data.data.map(item => {
            const date = new Date(item.date);
            return date.toLocaleDateString('fr-FR', { month: 'short', day: 'numeric' });
        });
        const values = data.data.map(item => item.close);

        const movingAverage = this.calculateMovingAverage(values, 7);

        this.charts.main = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [
                    {
                        label: 'CAC 40',
                        data: values,
                        borderColor: '#3B82F6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 2,
                        pointHoverRadius: 5,
                        pointBackgroundColor: '#3B82F6'
                    },
                    {
                        label: 'Tendance (MM7)',
                        data: movingAverage,
                        borderColor: '#EF4444',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        fill: false,
                        tension: 0.4,
                        pointRadius: 0
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        ticks: {
                            callback: function (value) {
                                return value.toLocaleString('fr-FR') + ' pts';
                            }
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
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

        const dates = data.data.slice(-30).map(item => {
            const date = new Date(item.date);
            return date.toLocaleDateString('fr-FR', { month: 'short', day: 'numeric' });
        });
        const volumes = data.data.slice(-30).map(item => item.volume / 1000000);

        this.charts.volume = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: dates,
                datasets: [{
                    label: 'Volume (M)',
                    data: volumes,
                    backgroundColor: 'rgba(239, 68, 68, 0.7)',
                    borderColor: 'rgba(220, 38, 38, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.7)',
                        titleFont: {
                            size: 13
                        },
                        bodyFont: {
                            size: 12
                        },
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
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        ticks: {
                            callback: function (value) {
                                return value.toFixed(0) + 'M';
                            }
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            maxRotation: 45,
                            minRotation: 45
                        }
                    }
                }
            }
        });
    }

    calculateMovingAverage(data, period) {
        const result = [];
        for (let i = 0; i < data.length; i++) {
            if (i < period - 1) {
                result.push(null);
            } else {
                const sum = data.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0);
                result.push(sum / period);
            }
        }
        return result;
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${type === 'success' ? 'bg-green-500 text-white' :
            type === 'error' ? 'bg-red-500 text-white' :
                'bg-blue-500 text-white'
            }`;
        notification.textContent = message;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    filterIndicators() {
        const category = document.getElementById('categorySelect').value;
        const indicators = document.querySelectorAll('[id$="Card"]');

        indicators.forEach(card => {
            if (category === 'all') {
                card.style.display = 'block';
            } else {
                const isMacro = card.id.includes('pib') || card.id.includes('chomage') ||
                    card.id.includes('inflation') || card.id.includes('production') ||
                    card.id.includes('commerce') || card.id.includes('deficit') ||
                    card.id.includes('construction');
                const isFinance = card.id.includes('cac40');

                if ((category === 'macro' && isMacro) || (category === 'finance' && isFinance)) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
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
                valueElement.innerHTML = '<i class="fas fa-spinner fa-spin text-white text-lg"></i>';
            }
            if (confidenceElement) {
                confidenceElement.innerHTML = '<span class="text-xs text-gray-300">Chargement...</span>';
            }
        });

        const tableBody = document.getElementById('indicateursTable');
        if (tableBody) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="5" class="px-6 py-8 text-center text-gray-500">
                        <div class="flex items-center justify-center">
                            <i class="fas fa-spinner fa-spin mr-3 text-blue-500"></i>
                            <span>Chargement des données économiques...</span>
                        </div>
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
                    <td colspan="5" class="px-6 py-8 text-center text-red-500">
                        <div class="flex items-center justify-center">
                            <i class="fas fa-exclamation-triangle mr-3"></i>
                            <span>Erreur: ${message}</span>
                        </div>
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
    console.log("✅ IndicateursFrancaisManager Amélioré prêt");
});