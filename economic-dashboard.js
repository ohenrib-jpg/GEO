// static/js/economic-dashboard.js
class EconomicDashboard {
    constructor() {
        this.baseUrl = '/economic-dashboard/api';
        this.currentConfig = {};
        this.elements = {};
        this.init();
    }

    init() {
        this.cacheElements();
        if (this.areRequiredElementsPresent()) {
            this.loadAllData();
            this.setupEventListeners();
            this.setupWidgetControls();
            console.log('🚀 Economic Dashboard initialisé');
        } else {
            console.error('❌ Éléments manquants dans le DOM');
            this.retryInitialization();
        }
    }

    cacheElements() {
        this.elements = {
            refreshData: document.getElementById('refreshData'),
            configPanelBtn: document.getElementById('configPanelBtn'),
            closeConfig: document.getElementById('closeConfig'),
            configPanel: document.getElementById('configPanel'),
            baseCountry: document.getElementById('baseCountry'),
            sectorFilter: document.getElementById('sectorFilter'),
            configContent: document.getElementById('configContent'),
            lastUpdateTime: document.getElementById('lastUpdateTime'),
            frenchIndicatorsContent: document.getElementById('frenchIndicatorsContent'),
            europeComparisonContent: document.getElementById('europeComparisonContent'),
            sectorAnalysisContent: document.getElementById('sectorAnalysisContent')
        };
    }

    areRequiredElementsPresent() {
        const required = [
            'frenchIndicatorsContent',
            'europeComparisonContent',
            'sectorAnalysisContent'
        ];

        return required.every(key => {
            const exists = this.elements[key] !== null;
            if (!exists) {
                console.warn(`❌ Élément manquant: ${key}`);
            }
            return exists;
        });
    }

    retryInitialization() {
        console.log('🔄 Nouvelle tentative d\'initialisation dans 1s...');
        setTimeout(() => {
            this.cacheElements();
            if (this.areRequiredElementsPresent()) {
                this.loadAllData();
                this.setupEventListeners();
                this.setupWidgetControls();
                console.log('✅ Economic Dashboard initialisé après retry');
            } else {
                console.error('❌ Échec de l\'initialisation après retry');
                this.showCriticalError();
            }
        }, 1000);
    }

    showCriticalError() {
        const container = document.querySelector('.max-w-7xl.mx-auto');
        if (container) {
            container.innerHTML = `
                <div class="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
                    <i class="fas fa-exclamation-triangle text-red-500 text-4xl mb-4"></i>
                    <h2 class="text-xl font-bold text-red-800 mb-2">Erreur d'initialisation</h2>
                    <p class="text-red-600 mb-4">Le dashboard économique n'a pas pu se charger correctement.</p>
                    <button onclick="location.reload()" class="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg">
                        <i class="fas fa-redo mr-2"></i>Recharger la page
                    </button>
                </div>
            `;
        }
    }

    setupEventListeners() {
        // Bouton d'actualisation
        if (this.elements.refreshData) {
            this.elements.refreshData.addEventListener('click', () => {
                this.loadAllData();
            });
        }

        // Configuration du panneau
        if (this.elements.configPanelBtn) {
            this.elements.configPanelBtn.addEventListener('click', () => {
                this.openConfigPanel();
            });
        }

        if (this.elements.closeConfig) {
            this.elements.closeConfig.addEventListener('click', () => {
                this.closeConfigPanel();
            });
        }

        // Fermer le panneau en cliquant à l'extérieur
        if (this.elements.configPanel) {
            this.elements.configPanel.addEventListener('click', (e) => {
                if (e.target.id === 'configPanel') {
                    this.closeConfigPanel();
                }
            });
        }

        // Filtres
        if (this.elements.baseCountry) {
            this.elements.baseCountry.addEventListener('change', (e) => {
                this.loadCountryComparison(e.target.value);
            });
        }

        if (this.elements.sectorFilter) {
            this.elements.sectorFilter.addEventListener('change', (e) => {
                this.filterSectors(e.target.value);
            });
        }
    }

    setupWidgetControls() {
        // Configuration des widgets
        document.querySelectorAll('.widget-config-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const widget = e.target.closest('.widget');
                if (widget) {
                    const widgetType = widget.dataset.widgetType;
                    this.configureWidget(widgetType);
                }
            });
        });

        // Expansion des widgets
        document.querySelectorAll('.widget-expand-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const widget = e.target.closest('.widget');
                if (widget) {
                    this.toggleWidgetExpand(widget);
                }
            });
        });
    }

    async loadAllData() {
        try {
            this.showLoadingStates();

            // Charger en parallèle
            await Promise.all([
                this.loadFrenchIndicators(),
                this.loadCountryComparison(),
                this.loadSectorAnalysis(),
                this.updateLastUpdateTime()
            ]);

            console.log('✅ Toutes les données chargées avec succès');

        } catch (error) {
            console.error('❌ Erreur chargement données:', error);
            this.showErrorStates();
        }
    }

    async loadFrenchIndicators() {
        try {
            console.log('📊 Chargement des indicateurs français...');
            const response = await fetch(`${this.baseUrl}/strategic-indicators`);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                this.renderFrenchIndicators(data.indicators);
            } else {
                throw new Error(data.error || 'Erreur inconnue');
            }
        } catch (error) {
            console.error('❌ Erreur indicateurs français:', error);
            this.renderFrenchIndicatorsError();
        }
    }

    renderFrenchIndicators(indicators) {
        if (!this.elements.frenchIndicatorsContent) {
            console.error('❌ Container indicateurs français non trouvé');
            return;
        }

        if (!indicators || Object.keys(indicators).length === 0) {
            this.elements.frenchIndicatorsContent.innerHTML = this.getNoDataTemplate('Indicateurs français');
            return;
        }

        let html = '<div class="space-y-4">';

        Object.entries(indicators).forEach(([key, indicator]) => {
            if (!indicator || !indicator.value) return;

            const trendIcon = this.getTrendIcon(indicator.trend);
            const confidenceBadge = this.getConfidenceBadge(indicator.confidence);

            html += `
                <div class="bg-gradient-to-r from-blue-50 to-white p-4 rounded-lg border border-blue-100">
                    <div class="flex justify-between items-start mb-2">
                        <div>
                            <h4 class="font-bold text-blue-800 capitalize">${this.formatIndicatorName(key)}</h4>
                            <p class="text-sm text-gray-600">${indicator.period || 'N/A'} • ${indicator.source || 'INSEE'}</p>
                        </div>
                        ${confidenceBadge}
                    </div>
                    <div class="flex justify-between items-center">
                        <span class="text-2xl font-bold text-gray-900">${indicator.value} ${indicator.unit || ''}</span>
                        <span class="text-xl ${this.getTrendColor(indicator.trend)}">${trendIcon}</span>
                    </div>
                </div>
            `;
        });

        html += '</div>';
        this.elements.frenchIndicatorsContent.innerHTML = html;
    }

    async loadCountryComparison(baseCountry = 'FR') {
        try {
            console.log('🌍 Chargement des comparaisons pays...');
            const response = await fetch(`${this.baseUrl}/country-comparison?base=${baseCountry}`);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                this.renderCountryComparison(data.comparisons, baseCountry);
            } else {
                throw new Error(data.error || 'Erreur inconnue');
            }
        } catch (error) {
            console.error('❌ Erreur comparaisons pays:', error);
            this.renderCountryComparisonError();
        }
    }

    renderCountryComparison(comparisons, baseCountry) {
        if (!this.elements.europeComparisonContent) {
            console.error('❌ Container comparaisons européennes non trouvé');
            return;
        }

        if (!comparisons || Object.keys(comparisons).length === 0) {
            this.elements.europeComparisonContent.innerHTML = this.getNoDataTemplate('Comparaisons européennes');
            return;
        }

        let html = `
            <div class="mb-4 text-center">
                <span class="text-sm text-gray-600">Pays de référence: <strong>${this.getCountryName(baseCountry)}</strong></span>
            </div>
            <div class="space-y-3">
        `;

        Object.entries(comparisons).forEach(([code, country]) => {
            if (!country) return;

            const statusColor = country.status === 'better' ? 'text-green-600' : 'text-red-600';
            const statusIcon = country.status === 'better' ? '📈' : '📉';

            html += `
                <div class="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                    <div class="flex justify-between items-center mb-2">
                        <div class="flex items-center">
                            <span class="text-lg mr-2">${this.getCountryFlag(code)}</span>
                            <h4 class="font-bold text-gray-800">${country.name || code}</h4>
                        </div>
                        <span class="${statusColor} font-semibold">${statusIcon} ${country.difference_pib || 'N/A'}</span>
                    </div>
                    
                    <div class="grid grid-cols-2 gap-2 text-sm">
                        <div class="text-center p-2 bg-gray-50 rounded">
                            <div class="text-gray-600">PIB</div>
                            <div class="font-bold">${country.pib || 'N/A'} ${country.pib ? 'Md€' : ''}</div>
                        </div>
                        <div class="text-center p-2 bg-gray-50 rounded">
                            <div class="text-gray-600">Chômage</div>
                            <div class="font-bold ${country.chomage > 7 ? 'text-red-600' : 'text-green-600'}">${country.chomage || 'N/A'}%</div>
                        </div>
                        <div class="text-center p-2 bg-gray-50 rounded">
                            <div class="text-gray-600">Inflation</div>
                            <div class="font-bold">${country.inflation || 'N/A'}%</div>
                        </div>
                        <div class="text-center p-2 bg-gray-50 rounded">
                            <div class="text-gray-600">Commerce</div>
                            <div class="font-bold ${country.commerce > 0 ? 'text-green-600' : 'text-red-600'}">${country.commerce || 'N/A'}%</div>
                        </div>
                    </div>
                </div>
            `;
        });

        html += '</div>';
        this.elements.europeComparisonContent.innerHTML = html;
    }

    async loadSectorAnalysis() {
        try {
            console.log('🏭 Chargement de l\'analyse sectorielle...');
            const response = await fetch(`${this.baseUrl}/sector-analysis`);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                this.renderSectorAnalysis(data.sectors);
            } else {
                throw new Error(data.error || 'Erreur inconnue');
            }
        } catch (error) {
            console.error('❌ Erreur analyse sectorielle:', error);
            this.renderSectorAnalysisError();
        }
    }

    renderSectorAnalysis(sectors) {
        if (!this.elements.sectorAnalysisContent) {
            console.error('❌ Container analyse sectorielle non trouvé');
            return;
        }

        if (!sectors || Object.keys(sectors).length === 0) {
            this.elements.sectorAnalysisContent.innerHTML = this.getNoDataTemplate('Analyse sectorielle');
            return;
        }

        let html = '<div class="space-y-4">';

        Object.entries(sectors).forEach(([sector, data]) => {
            if (!data) return;

            const trendIcon = data.trend === 'up' ? '📈' : '📉';
            const trendColor = data.trend === 'up' ? 'text-green-600' : 'text-red-600';
            const sentimentIcon = data.news_sentiment === 'positive' ? '😊' :
                data.news_sentiment === 'negative' ? '😟' : '😐';

            html += `
                <div class="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                    <div class="flex justify-between items-center mb-3">
                        <h4 class="font-bold text-gray-800 capitalize">${this.formatSectorName(sector)}</h4>
                        <div class="flex items-center space-x-2">
                            <span class="text-sm text-gray-500">${sentimentIcon}</span>
                            <span class="${trendColor} font-bold">${trendIcon} ${data.performance || 'N/A'}%</span>
                        </div>
                    </div>
                    
                    <div class="flex justify-between items-center text-sm text-gray-600">
                        <span>Volume: ${data.volume || 'N/A'}</span>
                        <span class="px-2 py-1 rounded-full ${this.getSentimentColor(data.news_sentiment)} text-white text-xs">
                            ${data.news_sentiment || 'neutral'}
                        </span>
                    </div>
                    
                    ${data.symbols ? `
                        <div class="mt-2 text-xs text-gray-500">
                            Symboles: ${data.symbols.join(', ')}
                        </div>
                    ` : ''}
                </div>
            `;
        });

        html += '</div>';
        this.elements.sectorAnalysisContent.innerHTML = html;
    }

    // Méthodes utilitaires
    formatIndicatorName(key) {
        const names = {
            'pib': 'Produit Intérieur Brut',
            'chomage': 'Taux de Chômage',
            'inflation': 'Taux d\'Inflation',
            'production': 'Production Industrielle',
            'commerce': 'Balance Commerciale',
            'deficit': 'Déficit Public',
            'construction': 'Secteur Construction'
        };
        return names[key] || key;
    }

    formatSectorName(sector) {
        const names = {
            'defense': 'Défense & Aérospatial',
            'sante': 'Santé & Pharma',
            'energie': 'Énergie',
            'technologie': 'Technologie',
            'finance': 'Finance & Banque'
        };
        return names[sector] || sector;
    }

    getCountryName(code) {
        const countries = {
            'FR': 'France',
            'DE': 'Allemagne',
            'IT': 'Italie',
            'ES': 'Espagne',
            'NL': 'Pays-Bas'
        };
        return countries[code] || code;
    }

    getCountryFlag(code) {
        const flags = {
            'FR': '🇫🇷',
            'DE': '🇩🇪',
            'IT': '🇮🇹',
            'ES': '🇪🇸',
            'NL': '🇳🇱'
        };
        return flags[code] || '🏳️';
    }

    getTrendIcon(trend) {
        const icons = {
            'up': '📈',
            'down': '📉',
            'stable': '➡️'
        };
        return icons[trend] || '➡️';
    }

    getTrendColor(trend) {
        const colors = {
            'up': 'text-green-600',
            'down': 'text-red-600',
            'stable': 'text-blue-600'
        };
        return colors[trend] || 'text-gray-600';
    }

    getSentimentColor(sentiment) {
        const colors = {
            'positive': 'bg-green-500',
            'negative': 'bg-red-500',
            'neutral': 'bg-gray-500'
        };
        return colors[sentiment] || 'bg-gray-500';
    }

    getConfidenceBadge(confidence) {
        const colors = {
            'high': 'bg-green-100 text-green-800',
            'medium': 'bg-yellow-100 text-yellow-800',
            'low': 'bg-red-100 text-red-800'
        };
        const color = colors[confidence] || 'bg-gray-100 text-gray-800';
        return `<span class="px-2 py-1 rounded-full text-xs font-medium ${color}">${confidence}</span>`;
    }

    getNoDataTemplate(widgetName) {
        return `
            <div class="text-center py-8 text-gray-500">
                <i class="fas fa-exclamation-triangle text-2xl mb-2"></i>
                <p>Données non disponibles pour ${widgetName}</p>
                <button class="mt-2 text-blue-600 hover:text-blue-800 text-sm" onclick="economicDashboard.loadAllData()">
                    <i class="fas fa-redo mr-1"></i> Réessayer
                </button>
            </div>
        `;
    }

    // États d'interface
    showLoadingStates() {
        const containers = [
            this.elements.frenchIndicatorsContent,
            this.elements.europeComparisonContent,
            this.elements.sectorAnalysisContent
        ];

        containers.forEach(container => {
            if (container) {
                container.innerHTML = `
                    <div class="text-center py-8 text-gray-500">
                        <i class="fas fa-spinner fa-spin text-2xl mb-2"></i>
                        <p>Chargement en cours...</p>
                    </div>
                `;
            }
        });
    }

    showErrorStates() {
        const containers = [
            this.elements.frenchIndicatorsContent,
            this.elements.europeComparisonContent,
            this.elements.sectorAnalysisContent
        ];

        containers.forEach(container => {
            if (container) {
                container.innerHTML = `
                    <div class="text-center py-8 text-red-500">
                        <i class="fas fa-exclamation-circle text-2xl mb-2"></i>
                        <p>Erreur de chargement</p>
                        <button class="mt-2 text-blue-600 hover:text-blue-800 text-sm" onclick="economicDashboard.loadAllData()">
                            <i class="fas fa-redo mr-1"></i> Réessayer
                        </button>
                    </div>
                `;
            }
        });
    }

    renderFrenchIndicatorsError() {
        if (this.elements.frenchIndicatorsContent) {
            this.elements.frenchIndicatorsContent.innerHTML = this.getNoDataTemplate('les indicateurs français');
        }
    }

    renderCountryComparisonError() {
        if (this.elements.europeComparisonContent) {
            this.elements.europeComparisonContent.innerHTML = this.getNoDataTemplate('les comparaisons européennes');
        }
    }

    renderSectorAnalysisError() {
        if (this.elements.sectorAnalysisContent) {
            this.elements.sectorAnalysisContent.innerHTML = this.getNoDataTemplate('l\'analyse sectorielle');
        }
    }

    // Gestion du panneau de configuration
    openConfigPanel() {
        if (this.elements.configPanel) {
            this.elements.configPanel.classList.remove('hidden');
            this.loadConfigContent();
        }
    }

    closeConfigPanel() {
        if (this.elements.configPanel) {
            this.elements.configPanel.classList.add('hidden');
        }
    }

    loadConfigContent() {
        if (!this.elements.configContent) return;

        this.elements.configContent.innerHTML = `
            <div class="space-y-6">
                <div>
                    <h4 class="font-bold text-gray-800 mb-3">📊 Widgets</h4>
                    <div class="space-y-3">
                        <div class="flex justify-between items-center p-3 bg-gray-50 rounded">
                            <span>Indicateurs France</span>
                            <input type="checkbox" checked class="rounded text-blue-600">
                        </div>
                        <div class="flex justify-between items-center p-3 bg-gray-50 rounded">
                            <span>Comparaisons Europe</span>
                            <input type="checkbox" checked class="rounded text-blue-600">
                        </div>
                        <div class="flex justify-between items-center p-3 bg-gray-50 rounded">
                            <span>Analyse Sectorielle</span>
                            <input type="checkbox" checked class="rounded text-blue-600">
                        </div>
                    </div>
                </div>
                
                <div>
                    <h4 class="font-bold text-gray-800 mb-3">🔄 Actualisation</h4>
                    <select class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm">
                        <option value="5">5 minutes</option>
                        <option value="15" selected>15 minutes</option>
                        <option value="30">30 minutes</option>
                        <option value="60">1 heure</option>
                    </select>
                </div>
                
                <div>
                    <h4 class="font-bold text-gray-800 mb-3">🌍 Sources</h4>
                    <div class="space-y-2 text-sm">
                        <div class="flex justify-between">
                            <span>INSEE</span>
                            <span class="text-green-600">✅ Active</span>
                        </div>
                        <div class="flex justify-between">
                            <span>Eurostat</span>
                            <span class="text-green-600">✅ Active</span>
                        </div>
                        <div class="flex justify-between">
                            <span>Yahoo Finance</span>
                            <span class="text-green-600">✅ Active</span>
                        </div>
                    </div>
                </div>
                
                <button class="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition">
                    <i class="fas fa-save mr-2"></i>Sauvegarder
                </button>
            </div>
        `;
    }

    configureWidget(widgetType) {
        this.openConfigPanel();
        console.log('Configuration du widget:', widgetType);
    }

    toggleWidgetExpand(widget) {
        if (widget) {
            widget.classList.toggle('col-span-2');
            widget.classList.toggle('row-span-2');
        }
    }

    filterSectors(sector) {
        const sectorWidget = document.querySelector('[data-widget-type="sector-analysis"]');
        if (!sectorWidget) return;

        const sectors = sectorWidget.querySelectorAll('.widget-content > div > div');
        sectors.forEach(item => {
            if (sector === 'all' || item.querySelector('h4').textContent.toLowerCase().includes(sector)) {
                item.style.display = 'block';
            } else {
                item.style.display = 'none';
            }
        });
    }

    async updateLastUpdateTime() {
        if (this.elements.lastUpdateTime) {
            this.elements.lastUpdateTime.textContent = new Date().toLocaleString('fr-FR');
        }
    }
}

// Initialisation globale avec gestion d'erreur
let economicDashboard;

document.addEventListener('DOMContentLoaded', function () {
    try {
        economicDashboard = new EconomicDashboard();
        window.economicDashboard = economicDashboard;
    } catch (error) {
        console.error('❌ Erreur critique lors de l\'initialisation:', error);
    }
});