// static/js/weak-indicators.js - VERSION AVEC PROTECTION CONTRE LES DÉCLARATIONS MULTIPLES


// ============================================
// CONFIGURATION DES URLs - SECTION À AJOUTER EN HAUT
// ============================================

// ✅ URLs correctes des API
const WEAK_INDICATORS_API = {
    STATUS: '/weak-indicators/api/status',
    TRAVEL_SCAN: '/weak-indicators/api/travel-advisories/scan',
    TRAVEL_COUNTRIES: '/weak-indicators/api/travel-advisories/countries',
    TRAVEL_COUNTRY: '/weak-indicators/api/travel-advisories/country',
    KIWISDR_SERVERS: '/weak-indicators/api/kiwisdr/servers',
    KIWISDR_FREQUENCIES: '/weak-indicators/api/kiwisdr/frequencies',
    STOCK_REAL_DATA: '/weak-indicators/api/stock/real-data',
    STOCK_CACHED: '/weak-indicators/api/stock/cached',
    UPDATE_ALL: '/weak-indicators/api/update-all'
};

// Fonction de notification globale
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${type === 'success' ? 'bg-green-500' :
        type === 'error' ? 'bg-red-500' :
            type === 'warning' ? 'bg-yellow-500' : 'bg-blue-500'
        } text-white`;
    notification.innerHTML = `
        <div class="flex items-center">
            <i class="fas fa-${type === 'success' ? 'check' :
            type === 'error' ? 'exclamation-triangle' :
                type === 'warning' ? 'exclamation' : 'info'
        } mr-2"></i>
            <span>${message}</span>
        </div>
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.remove();
    }, 5000);
}
// Vérifier si WeakIndicatorsManager est déjà défini
if (typeof WeakIndicatorsManager === 'undefined') {

    class WeakIndicatorsManager {
        static async initialize() {
            console.log('🚀 Initialisation WeakIndicatorsManager...');

            try {
                await this.loadInitialData();
                this.setupEventListeners();
                console.log('✅ WeakIndicatorsManager initialisé');
            } catch (error) {
                console.error('❌ Erreur initialisation:', error);
            }
        }

        static async loadInitialData() {
            try {
                // ✅ CORRECTION : Utiliser les bonnes URLs
                const [streams, status] = await Promise.all([
                    this.fetchData('/weak-indicators/api/sdr-streams'),
                    this.fetchData('/weak-indicators/api/status')
                ]);

                this.displaySDRStreams(streams);
                this.updateSystemStatus(status);

            } catch (error) {
                console.error('❌ Erreur chargement données initiales:', error);
            }
        }

        static async fetchData(url) {
            try {
                const response = await fetch(url);
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                return await response.json();
            } catch (error) {
                console.error(`Erreur fetch ${url}:`, error);
                throw error;
            }
        }

        static displaySDRStreams(streams) {
            const container = document.getElementById('sdr-streams-container');
            if (!container) return;

            if (!streams || streams.length === 0) {
                container.innerHTML = `
                <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
                    <i class="fas fa-satellite-dish text-yellow-600 text-3xl mb-3"></i>
                    <p class="text-yellow-800">Aucun flux SDR configuré</p>
                </div>
            `;
                return;
            }

            container.innerHTML = streams.map(stream => `
            <div class="border border-gray-200 rounded-lg p-4 mb-3">
                <div class="flex justify-between items-center mb-2">
                    <h3 class="font-semibold text-gray-800">${stream.name}</h3>
                    <span class="px-2 py-1 text-xs rounded-full ${stream.active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                }">
                        ${stream.active ? '🟢 Actif' : '⚪ Inactif'}
                    </span>
                </div>
                <div class="text-sm text-gray-600 mb-2">
                    <p>📡 ${stream.frequency_khz ? (stream.frequency_khz / 1000).toFixed(3) + ' MHz' : 'Fréquence non définie'}</p>
                    <p>🔧 ${stream.type || 'rtlsdr'}</p>
                    ${stream.description ? `<p class="text-xs text-gray-500 mt-1">${stream.description}</p>` : ''}
                </div>
                <div class="flex space-x-2">
                    <button onclick="WeakIndicatorsManager.analyzeStream(${stream.id})" 
                            class="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm">
                        <i class="fas fa-chart-line mr-1"></i>Analyser
                    </button>
                    <button onclick="WeakIndicatorsManager.viewWaterfall(${stream.frequency_khz || 0})"
                            class="bg-green-500 hover:bg-green-600 text-white px-3 py-1 rounded text-sm">
                        <i class="fas fa-water mr-1"></i>Waterfall
                    </button>
                </div>
            </div>
        `).join('');
        }

        static updateSystemStatus(status) {
            const statusElement = document.getElementById('system-status');
            if (!statusElement || !status) return;

            statusElement.innerHTML = `
            <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div class="flex items-center">
                    <i class="fas fa-circle text-green-500 mr-2"></i>
                    <span class="font-semibold">Système ${status.status || 'actif'}</span>
                </div>
                <div class="text-sm text-gray-600 mt-2">
                    <p>📡 RTL-SDR: ${status.rtlsdr_available ? '✅ Disponible' : '❌ Indisponible'}</p>
                    <p>🕒 Dernière analyse: ${status.last_analysis ? new Date(status.last_analysis).toLocaleString() : 'N/A'}</p>
                </div>
            </div>
        `;
        }

        static async analyzeStream(streamId) {
            try {
                const response = await fetch(`/weak-indicators/api/sdr/rtlsdr/analyze`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        stream_id: streamId,
                        duration_seconds: 60
                    })
                });

                const data = await response.json();

                if (data.success) {
                    this.showNotification(`Analyse terminée: ${data.emissions_detected} émissions détectées`, 'success');
                } else {
                    this.showNotification('Erreur lors de l\'analyse', 'error');
                }
            } catch (error) {
                console.error('Erreur analyse stream:', error);
                this.showNotification('Erreur de connexion', 'error');
            }
        }

        static async viewWaterfall(frequencyKhz) {
            try {
                if (!frequencyKhz || frequencyKhz === 0) {
                    this.showNotification('Fréquence non définie', 'warning');
                    return;
                }

                const response = await fetch(`/weak-indicators/api/sdr/rtlsdr/waterfall/embed?frequency_khz=${frequencyKhz}`);
                const data = await response.json();

                if (data.html) {
                    this.showWaterfallModal(data.html);
                }
            } catch (error) {
                console.error('Erreur chargement waterfall:', error);
                this.showNotification('Erreur chargement waterfall', 'error');
            }
        }

        static showWaterfallModal(htmlContent) {
            const modal = document.createElement('div');
            modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4';
            modal.innerHTML = `
            <div class="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-screen overflow-auto">
                <div class="flex justify-between items-center p-4 border-b">
                    <h3 class="text-lg font-semibold">🌊 Waterfall RTL-SDR</h3>
                    <button onclick="this.parentElement.parentElement.parentElement.remove()" 
                            class="text-gray-500 hover:text-gray-700">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="p-4">
                    ${htmlContent}
                </div>
            </div>
        `;

            document.body.appendChild(modal);
        }

        static showNotification(message, type = 'info') {
            const notification = document.createElement('div');
            notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${type === 'success' ? 'bg-green-500' :
                type === 'error' ? 'bg-red-500' :
                    type === 'warning' ? 'bg-yellow-500' : 'bg-blue-500'
                } text-white`;
            notification.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'exclamation-triangle' : type === 'warning' ? 'exclamation' : 'info'} mr-2"></i>
                <span>${message}</span>
            </div>
        `;

            document.body.appendChild(notification);

            setTimeout(() => {
                notification.remove();
            }, 5000);
        }

        static setupEventListeners() {
            // Événements pour les boutons d'analyse globale
            document.addEventListener('click', (e) => {
                if (e.target.classList.contains('global-analyze-btn')) {
                    this.startGlobalAnalysis();
                }
            });
        }

        static async startGlobalAnalysis() {
            try {
                const response = await fetch('/weak-indicators/api/analysis/patterns', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        frequencies: '14300,6998,121500,2182'
                    })
                });

                const data = await response.json();

                if (data.success) {
                    this.showNotification('Analyse globale terminée', 'success');
                    console.log('Patterns détectés:', data.patterns);
                }
            } catch (error) {
                console.error('Erreur analyse globale:', error);
                this.showNotification('Erreur analyse globale', 'error');
            }
        }
    }


    // Initialisation automatique
    if (window.location.pathname.includes('/weak-indicators')) {
        document.addEventListener('DOMContentLoaded', () => {
            WeakIndicatorsManager.initialize();
        });
    }

    console.log('✅ WeakIndicatorsManager chargé');

} else {
    console.log('ℹ️ WeakIndicatorsManager déjà chargé');
}

// MAJ true data 
async function updateAllRealData() {
    try {
        showNotification('Mise à jour des données réelles en cours...', 'info');

        const response = await fetch('/weak-indicators/api/real-data/update-all', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const data = await response.json();

        if (data.success) {
            showNotification('Données réelles mises à jour avec succès', 'success');
            console.log('Résultats mise à jour:', data.results);

            // Recharger les données affichées
            if (typeof WeakIndicatorsManager !== 'undefined') {
                WeakIndicatorsManager.initialize();
            }
            if (typeof TravelAdvisoriesManager !== 'undefined') {
                TravelAdvisoriesManager.initialize();
            }
        } else {
            showNotification('Erreur lors de la mise à jour', 'error');
        }
    } catch (error) {
        console.error('Erreur mise à jour données réelles:', error);
        showNotification('Erreur de connexion', 'error');
    }
}

// ============================================
// FONCTION loadRealStockData - CORRIGER
// ============================================

async function loadRealStockData() {
    try {
        showNotification('Chargement données boursières...', 'info');

        // ✅ CORRECTION : Utiliser la bonne URL
        const response = await fetch(WEAK_INDICATORS_API.STOCK_REAL_DATA);
        const data = await response.json();

        if (data.success) {
            displayRealStockData(data);
            showNotification('Données boursières chargées', 'success');
        } else {
            throw new Error(data.error || 'Erreur serveur');
        }
    } catch (error) {
        console.error('Erreur données boursières:', error);
        showNotification('Erreur chargement données boursières', 'error');
    }
}

// ============================================
// FONCTION displayRealStockData - CORRIGER
// ============================================

function displayRealStockData(data) {
    const container = document.getElementById('stock-data-content');
    const stockSection = document.getElementById('real-stock-data');

    if (!container || !stockSection) return;

    stockSection.classList.remove('hidden');

    let html = '';

    // Indices boursiers
    if (data.indices && Object.keys(data.indices).length > 0) {
        html += '<h4 class="font-semibold mb-3">📈 Indices Internationaux</h4>';
        html += '<div class="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">';

        Object.entries(data.indices).forEach(([symbol, info]) => {
            if (!info.error && info.current_price > 0) {
                const changeClass = info.change_direction === 'up' ? 'text-green-600' : 'text-red-600';
                const changeIcon = info.change_direction === 'up' ? '📈' : '📉';

                html += `
                    <div class="border border-gray-200 rounded p-3">
                        <div class="flex justify-between items-center">
                            <div>
                                <strong>${info.name}</strong>
                                <div class="text-sm text-gray-600">${info.country} • ${symbol}</div>
                            </div>
                            <div class="text-right">
                                <div class="font-bold">${info.current_price.toFixed(2)}</div>
                                <div class="text-sm ${changeClass}">
                                    ${changeIcon} ${info.change_percent >= 0 ? '+' : ''}${info.change_percent.toFixed(2)}%
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            }
        });

        html += '</div>';
    }

    // Matières premières
    if (data.commodities && Object.keys(data.commodities).length > 0) {
        html += '<h4 class="font-semibold mb-3">⛽ Matières Premières</h4>';
        html += '<div class="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">';

        Object.entries(data.commodities).forEach(([symbol, info]) => {
            if (!info.error && info.current_price > 0) {
                const changeClass = info.change_direction === 'up' ? 'text-green-600' : 'text-red-600';
                const changeIcon = info.change_direction === 'up' ? '📈' : '📉';

                html += `
                    <div class="border border-gray-200 rounded p-3">
                        <div class="flex justify-between items-center">
                            <div>
                                <strong>${info.name}</strong>
                                <div class="text-sm text-gray-600">${info.unit || ''}</div>
                            </div>
                            <div class="text-right">
                                <div class="font-bold">${info.current_price.toFixed(2)}</div>
                                <div class="text-sm ${changeClass}">
                                    ${changeIcon} ${info.change_percent >= 0 ? '+' : ''}${info.change_percent.toFixed(2)}%
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            }
        });

        html += '</div>';
    }

    // Cryptos
    if (data.cryptos && Object.keys(data.cryptos).length > 0) {
        html += '<h4 class="font-semibold mb-3">₿ Cryptomonnaies</h4>';
        html += '<div class="grid grid-cols-1 md:grid-cols-2 gap-3">';

        Object.entries(data.cryptos).forEach(([symbol, info]) => {
            if (!info.error && info.current_price > 0) {
                const changeClass = info.change_direction === 'up' ? 'text-green-600' : 'text-red-600';
                const changeIcon = info.change_direction === 'up' ? '📈' : '📉';

                html += `
                    <div class="border border-gray-200 rounded p-3">
                        <div class="flex justify-between items-center">
                            <div>
                                <strong>${info.name}</strong>
                            </div>
                            <div class="text-right">
                                <div class="font-bold">${info.current_price.toFixed(2)}</div>
                                <div class="text-sm ${changeClass}">
                                    ${changeIcon} ${info.change_percent >= 0 ? '+' : ''}${info.change_percent.toFixed(2)}%
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            }
        });

        html += '</div>';
    }

    if (!html) {
        html = '<p class="text-gray-500">Aucune donnée disponible</p>';
    }

    container.innerHTML = html;
}

// ============================================
// FONCTION updateAllRealData - CORRIGER
// ============================================

async function updateAllRealData() {
    try {
        showNotification('Mise à jour des données en cours...', 'info');

        // ✅ CORRECTION : Utiliser la bonne URL
        const response = await fetch(WEAK_INDICATORS_API.UPDATE_ALL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const data = await response.json();

        if (data.success) {
            showNotification('Données mises à jour avec succès', 'success');
            console.log('Résultats mise à jour:', data.results);

            // Recharger les données affichées
            if (typeof WeakIndicatorsManager !== 'undefined') {
                WeakIndicatorsManager.initialize();
            }
            if (typeof TravelAdvisoriesManager !== 'undefined') {
                TravelAdvisoriesManager.initialize();
            }

            // Recharger les données boursières
            loadRealStockData();
        } else {
            showNotification('Erreur lors de la mise à jour', 'error');
        }
    } catch (error) {
        console.error('Erreur mise à jour données réelles:', error);
        showNotification('Erreur de connexion', 'error');
    }
}

// ============================================
// CORRECTION FONCTION showNotification - SI MANQUANTE
// ============================================

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${type === 'success' ? 'bg-green-500' :
        type === 'error' ? 'bg-red-500' :
            type === 'warning' ? 'bg-yellow-500' : 'bg-blue-500'
        } text-white`;

    notification.innerHTML = `
        <div class="flex items-center">
            <i class="fas fa-${type === 'success' ? 'check' :
            type === 'error' ? 'exclamation-triangle' :
                type === 'warning' ? 'exclamation' : 'info'
        } mr-2"></i>
            <span>${message}</span>
        </div>
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.remove();
    }, 5000);
}

// ============================================
// INITIALISATION AU CHARGEMENT - CORRIGER
// ============================================

// VÃ©rifier si WeakIndicatorsManager est déjà défini
if (typeof WeakIndicatorsManager === 'undefined') {
    class WeakIndicatorsManager {
        static async initialize() {
            console.log('🚀 Initialisation WeakIndicatorsManager...');

            try {
                await this.loadInitialData();
                this.setupEventListeners();
                console.log('✅ WeakIndicatorsManager initialisé');
            } catch (error) {
                console.error('❌ Erreur initialisation:', error);
            }
        }

        static async loadInitialData() {
            try {
                // Charger statut
                const statusResponse = await fetch(WEAK_INDICATORS_API.STATUS);
                const statusData = await statusResponse.json();

                if (statusData.success) {
                    console.log('✅ Services disponibles:', statusData.services);
                }

                // Charger données boursières
                await loadRealStockData();

            } catch (error) {
                console.error('❌ Erreur chargement données:', error);
            }
        }

        static setupEventListeners() {
            // Bouton "Actualiser toutes les données"
            const updateBtn = document.getElementById('update-all-data-btn');
            if (updateBtn) {
                updateBtn.addEventListener('click', updateAllRealData);
            }
        }
    }
}

// Initialisation automatique
if (window.location.pathname.includes('/weak-indicators')) {
    document.addEventListener('DOMContentLoaded', () => {
        WeakIndicatorsManager.initialize();
    });
}

console.log('✅ weak-indicators.js chargé (URLs corrigées)');