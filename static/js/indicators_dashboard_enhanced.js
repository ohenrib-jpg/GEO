// static/js/indicators_dashboard_enhanced.js - VERSION ENTIÈREMENT CORRIGÉE

class EnhancedIndicatorsDashboard {
    constructor() {
        this.currentData = {};
        this.currentChart = null;
        this.refreshInterval = null;
        this.init();
    }

    async init() {
        console.log('🚀 Initialisation Enhanced Dashboard...');

        try {
            await this.loadAllData();
            this.setupEventListeners();
            this.startAutoRefresh();
            console.log('✅ Dashboard Enhanced initialisé');
        } catch (error) {
            console.error('❌ Erreur initialisation:', error);
            this.showError('Erreur initialisation dashboard');
        }
    }

    setupEventListeners() {
        // Délégation d'événements pour les boutons dynamiques
        document.addEventListener('click', (e) => {
            if (e.target.id === 'refreshDataBtn' || e.target.closest('#refreshDataBtn')) {
                e.preventDefault();
                this.forceRefresh();
            }
            if (e.target.id === 'settingsBtn' || e.target.closest('#settingsBtn')) {
                e.preventDefault();
                this.openSettings();
            }
        });

        // Sélection période
        const periodSelect = document.getElementById('periodSelect');
        if (periodSelect) {
            periodSelect.addEventListener('change', (e) => {
                this.loadHistoricalChart('^FCHI', e.target.value);
            });
        }
    }

    async loadAllData() {
        try {
            this.showLoading();

            // Récupérer toutes les données via l'endpoint unifié
            const response = await fetch('/indicators/api/dashboard');
            const data = await response.json();

            if (data.success) {
                this.currentData = data;
                console.log('📊 Données reçues:', data);
                this.renderAllComponents();
                this.updateSystemStatus(data);
            } else {
                throw new Error(data.error || 'Erreur chargement données');
            }

        } catch (error) {
            console.error('❌ Erreur chargement données:', error);
            this.showError('Erreur de connexion');
        }
    }

    renderAllComponents() {
        // 1. Indicateurs principaux
        this.renderMainIndicators();

        // 2. Indicateurs complémentaires (INSEE)
        this.renderSupplementaryIndicators();

        // 3. Indices internationaux
        this.renderInternationalIndices();

        // 4. Tableau détaillé
        this.renderDetailedTable();

        // 5. Graphique CAC 40
        this.loadHistoricalChart('^FCHI', '6mo');

        // 6. Mise à jour timestamp
        this.updateTimestamp();
    }

    renderMainIndicators() {
        const grid = document.getElementById('indicatorsGrid');
        if (!grid) return;

        // ✅ CORRECTION : Sélection stricte des 4 indicateurs principaux
        const indicators = this.currentData.indicators || {};

        // Créer un Set pour éviter les doublons
        const selectedIds = new Set();
        const mainIndicators = [];

        // Ordre prioritaire : PIB, IPCH, Commerce, GINI
        const priority = [
            'eurostat_gdp',
            'eurostat_hicp',
            'eurostat_trade_balance',
            'eurostat_gini'
        ];

        // Ajouter dans l'ordre de priorité (sans doublons)
        for (const id of priority) {
            if (indicators[id] && !selectedIds.has(id)) {
                selectedIds.add(id);
                mainIndicators.push([id, indicators[id]]);
            }
        }

        // Si moins de 4, compléter avec d'autres indicateurs Eurostat
        if (mainIndicators.length < 4) {
            for (const [id, indicator] of Object.entries(indicators)) {
                if (id.startsWith('eurostat_') &&
                    !selectedIds.has(id) &&
                    id !== 'eurostat_unemployment') {
                    selectedIds.add(id);
                    mainIndicators.push([id, indicator]);
                    if (mainIndicators.length >= 4) break;
                }
            }
        }

        console.log('📊 Indicateurs principaux:', mainIndicators.map(([id]) => id));

        if (mainIndicators.length === 0) {
            grid.innerHTML = '<div class="col-span-4 text-center text-gray-500">Aucun indicateur disponible</div>';
            return;
        }

        grid.innerHTML = mainIndicators.map(([id, indicator]) =>
            this.createIndicatorCard(indicator, false)
        ).join('');
    }

    renderSupplementaryIndicators() {
        const section = document.getElementById('supplementaryIndicatorsSection');
        const grid = document.getElementById('supplementaryIndicatorsGrid');

        if (!section || !grid) return;

        // ✅ CORRECTION : Filtrer uniquement INSEE (pas de doublon GINI)
        const inseeIndicators = Object.entries(this.currentData.indicators || {})
            .filter(([id, _]) => id.startsWith('insee_'));

        console.log('🇫🇷 Indicateurs INSEE:', inseeIndicators.map(([id]) => id));

        if (inseeIndicators.length === 0) {
            section.classList.add('hidden');
            return;
        }

        section.classList.remove('hidden');
        grid.innerHTML = inseeIndicators.map(([id, indicator]) =>
            this.createIndicatorCard(indicator, true)
        ).join('');
    }

    createIndicatorCard(indicator, isSupplementary = false) {
        const trendIcon = indicator.change_percent > 0 ? '📈' :
            indicator.change_percent < 0 ? '📉' : '➡️';
        const trendColor = indicator.change_percent > 0 ? 'text-green-600' :
            indicator.change_percent < 0 ? 'text-red-600' : 'text-gray-600';

        // ✅ CORRECTION : Couleurs très contrastées pour TOUS les widgets==>erreru transparecne maj 3011
        const categoryColors = {
            'macro': 'from-blue-600 to-blue-800',           // PIB - Bleu foncé
            'employment': 'from-red-600 to-red-800',        // Emploi - Rouge foncé
            'prices': 'from-purple-600 to-purple-800',      // IPCH - Orange foncé
            'trade': 'from-purple-600 to-purple-800',       // Commerce - Violet foncé
            'finance': 'from-green-600 to-green-800',       // Finance - Vert foncé
            'production': 'from-indigo-600 to-indigo-800',  // Production - Indigo foncé
            'inequality': 'from-pink-600 to-pink-800'       // GINI - Rose foncé
        };

        const gradient = categoryColors[indicator.category] || 'from-gray-600 to-gray-800';

        // Badge de fiabilité
        const reliabilityBadge = {
            'official': '<span class="text-xs bg-white bg-opacity-30 px-2 py-1 rounded-full">🔵 Officiel</span>',
            'scraped': '<span class="text-xs bg-white bg-opacity-30 px-2 py-1 rounded-full">🟢 Temps réel</span>',
            'fallback': '<span class="text-xs bg-white bg-opacity-30 px-2 py-1 rounded-full">🟡 Cache</span>'
        };

        return `
            <div class="bg-gradient-to-br ${gradient} rounded-xl shadow-lg p-6 text-white border-2 border-white border-opacity-20 transform hover:scale-105 transition duration-200">
                <div class="flex items-center justify-between mb-3">
                    <h3 class="text-lg font-semibold text-white">${this.truncateName(indicator.name)}</h3>
                    ${isSupplementary ? '<i class="fas fa-star text-yellow-300"></i>' : ''}
                </div>
                
                <div class="text-3xl font-bold mb-2 text-white">
                    ${indicator.value} ${indicator.unit}
                </div>
                
                <div class="flex justify-between items-center text-sm mb-2">
                    <span class="font-medium text-white opacity-90">
                        ${trendIcon} ${indicator.change_percent >= 0 ? '+' : ''}${indicator.change_percent.toFixed(2)}%
                    </span>
                    <span class="text-white opacity-90">${indicator.period}</span>
                </div>
                
                <div class="text-xs opacity-75 mb-2 text-white">
                    <span title="${indicator.description}">
                        ${indicator.source}
                    </span>
                </div>
                
                <div class="mt-2">
                    ${reliabilityBadge[indicator.reliability] || ''}
                </div>
            </div>
        `;
    }

    renderInternationalIndices() {
        const container = document.getElementById('internationalIndices');
        if (!container) return;

        const markets = this.currentData.financial_markets?.indices || {};

        if (Object.keys(markets).length === 0) {
            container.innerHTML = '<div class="col-span-5 text-center text-gray-500">Chargement indices...</div>';
            return;
        }

        container.innerHTML = Object.values(markets).map(index => {
            const trendColor = index.trend === 'up' ? 'text-green-600' : 'text-red-600';
            const trendIcon = index.trend === 'up' ? '↑' : '↓';

            return `
                <div class="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition">
                    <div class="text-sm font-medium text-gray-600 mb-1">${index.name}</div>
                    <div class="text-2xl font-bold text-gray-900 mb-1">${index.current_price}</div>
                    <div class="${trendColor} text-sm font-medium">
                        ${trendIcon} ${index.change_percent >= 0 ? '+' : ''}${index.change_percent.toFixed(2)}%
                    </div>
                </div>
            `;
        }).join('');
    }

    renderDetailedTable() {
        const tbody = document.getElementById('detailedTableBody');
        if (!tbody) return;

        const allIndicators = Object.values(this.currentData.indicators || {});

        if (allIndicators.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="px-6 py-8 text-center text-gray-500">
                        Aucune donnée disponible
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = allIndicators.map(indicator => {
            const trendClass = indicator.change_percent > 0 ? 'text-green-600 font-medium' :
                indicator.change_percent < 0 ? 'text-red-600 font-medium' : 'text-gray-600';

            const reliabilityIcon = indicator.reliability_icon || '⚪';

            return `
                <tr class="hover:bg-gray-50">
                    <td class="px-6 py-4 text-sm">
                        <span class="text-lg mr-2">${reliabilityIcon}</span>
                        <span class="font-medium text-gray-900">${indicator.name}</span>
                    </td>
                    <td class="px-6 py-4 text-sm text-gray-500">${indicator.value} ${indicator.unit}</td>
                    <td class="px-6 py-4 text-sm ${trendClass}">
                        ${indicator.change_percent >= 0 ? '+' : ''}${indicator.change_percent.toFixed(2)}%
                    </td>
                    <td class="px-6 py-4 text-sm text-gray-500">${indicator.period}</td>
                    <td class="px-6 py-4 text-sm text-gray-500">${indicator.source}</td>
                    <td class="px-6 py-4 text-xs">
                        <span class="px-2 py-1 rounded-full ${indicator.reliability === 'official' ? 'bg-blue-100 text-blue-800' :
                    indicator.reliability === 'scraped' ? 'bg-green-100 text-green-800' :
                        'bg-yellow-100 text-yellow-800'
                }">
                            ${indicator.reliability}
                        </span>
                    </td>
                </tr>
            `;
        }).join('');
    }

    async loadHistoricalChart(symbol, period) {
        try {
            const response = await fetch(`/indicators/api/historical/${symbol}?period=${period}`);
            const data = await response.json();

            if (data.success) {
                this.renderChart(data.data);

                const info = document.getElementById('cac40Info');
                if (info && data.data.length > 0) {
                    const latest = data.data[data.data.length - 1];
                    info.textContent = `Dernière valeur: ${latest.close} pts (${latest.date})`;
                }
            }
        } catch (error) {
            console.error('❌ Erreur graphique:', error);
        }
    }

    renderChart(data) {
        const ctx = document.getElementById('mainChart');
        if (!ctx) return;

        if (this.currentChart) {
            this.currentChart.destroy();
        }

        const dates = data.map(item => item.date);
        const values = data.map(item => item.close);

        this.currentChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [{
                    label: 'CAC 40',
                    data: values,
                    borderColor: '#3B82F6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 3,
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
                    legend: { display: true, position: 'top' },
                    tooltip: { mode: 'index', intersect: false }
                },
                scales: {
                    y: { beginAtZero: false, grid: { color: 'rgba(0, 0, 0, 0.05)' } },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    updateSystemStatus(data) {
        const statusDiv = document.getElementById('systemStatus');
        if (!statusDiv) return;

        const quality = data.summary?.data_quality || 'acceptable';
        const qualityInfo = {
            'excellent': { icon: '🟢', text: 'Excellente', color: 'green' },
            'good': { icon: '🟡', text: 'Bonne', color: 'yellow' },
            'acceptable': { icon: '🟠', text: 'Acceptable', color: 'orange' },
            'limited': { icon: '🔴', text: 'Limité', color: 'red' }
        };

        const info = qualityInfo[quality] || qualityInfo['acceptable'];

        const sourcesHtml = Object.entries(data.sources_status || {})
            .map(([source, status]) => {
                const icon = status === 'operational' ? '✅' : '❌';
                return `<span class="text-sm">${icon} ${source}</span>`;
            })
            .join(' • ');

        // ✅ CORRECTION : Structure HTML simplifiée avec position relative
        statusDiv.innerHTML = `
            <div class="relative">
                <div class="flex items-center justify-between flex-wrap gap-4">
                    <div class="flex items-center">
                        <span class="text-2xl mr-3">${info.icon}</span>
                        <div>
                            <h4 class="font-semibold text-${info.color}-800">
                                Qualité des données: ${info.text}
                            </h4>
                            <p class="text-sm text-${info.color}-700">${sourcesHtml}</p>
                        </div>
                    </div>
                    <div class="flex flex-wrap gap-2 items-center">
                        <button id="refreshDataBtn" class="bg-${info.color}-600 hover:bg-${info.color}-700 text-white px-4 py-2 rounded-lg text-sm transition whitespace-nowrap flex items-center shadow-md">
                            <i class="fas fa-sync-alt mr-2"></i>Actualiser
                        </button>
                        <button id="settingsBtn" class="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg text-sm transition whitespace-nowrap flex items-center shadow-md">
                            <i class="fas fa-cog mr-2"></i>Paramètres
                        </button>
                        <a href="https://ec.europa.eu/eurostat/fr/data/database" target="_blank"
                           class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm transition whitespace-nowrap flex items-center shadow-md">
                            <i class="fas fa-external-link-alt mr-2"></i>Eurostat DB
                        </a>
                    </div>
                </div>
            </div>
        `;
    }

    async forceRefresh() {
        try {
            this.showNotification('🔄 Rafraîchissement en cours...', 'info');

            const response = await fetch('/indicators/api/refresh', { method: 'POST' });
            const data = await response.json();

            if (data.success) {
                this.currentData = data.data;
                this.renderAllComponents();
                this.showNotification('✅ Données rafraîchies', 'success');
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            console.error('❌ Erreur refresh:', error);
            this.showNotification('❌ Erreur rafraîchissement', 'error');
        }
    }

    startAutoRefresh() {
        // Auto-refresh toutes les 5 minutes
        this.refreshInterval = setInterval(() => {
            console.log('🔄 Auto-refresh...');
            this.loadAllData();
        }, 5 * 60 * 1000);
    }

    truncateName(name) {
        return name.length > 30 ? name.substring(0, 27) + '...' : name;
    }

    updateTimestamp() {
        const lastUpdate = document.getElementById('lastUpdate');
        if (lastUpdate) {
            const now = new Date();
            lastUpdate.textContent = now.toLocaleString('fr-FR', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        }
    }

    showLoading() {
        const tbody = document.getElementById('detailedTableBody');
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="px-6 py-8 text-center text-gray-500">
                        <i class="fas fa-spinner fa-spin mr-2"></i>Chargement des données...
                    </td>
                </tr>
            `;
        }
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        const colors = {
            'success': 'bg-green-500',
            'error': 'bg-red-500',
            'warning': 'bg-yellow-500',
            'info': 'bg-blue-500'
        };

        notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${colors[type]} text-white transform transition-all duration-300`;
        notification.textContent = message;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.transform = 'translateX(400px)';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    openSettings() {
        this.showNotification('Paramètres à venir...', 'info');
    }
}

// Initialisation automatique
document.addEventListener('DOMContentLoaded', () => {
    window.enhancedDashboard = new EnhancedIndicatorsDashboard();
    console.log('✅ Enhanced Dashboard chargé');
});