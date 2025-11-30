// static/js/kiwisdr-manager.js - VERSION RÉALISTE CORRIGÉE
/**
 * KiwiSDR Manager - Interface d'observation manuelle assistée
 * 
 * Philosophie :
 * - On NE PEUT PAS automatiser l'analyse spectrale KiwiSDR
 * - On fournit des outils pour faciliter l'observation manuelle
 * - L'utilisateur observe le waterfall et enregistre manuellement
 */

class KiwiSDRManager {
    static serverChart = null;
    static updateInterval = null;
    static monitoredFrequencies = [];
    static availableServers = [];

    static async initialize() {
        console.log('📡 Initialisation KiwiSDRManager (observation manuelle)...');

        try {
            await this.loadDashboardData();
            this.setupEventListeners();
            this.startPeriodicUpdates();

            console.log('✅ KiwiSDRManager initialisé');
        } catch (error) {
            console.error('❌ Erreur initialisation:', error);
            this.showError('Erreur lors de l\'initialisation KiwiSDR');
        }
    }

    static async loadDashboardData() {
        try {
            console.log('📊 Chargement données dashboard KiwiSDR...');

            const response = await fetch('/api/kiwisdr/dashboard');
            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error || 'Erreur serveur');
            }

            this.availableServers = data.servers.current.servers || [];

            this.displayServerStatus(data.servers);
            this.displayMonitoredFrequencies(data.frequencies);
            this.updateGlobalStats(data);

            console.log('✅ Dashboard KiwiSDR chargé');

        } catch (error) {
            console.error('❌ Erreur chargement dashboard:', error);
            this.showFallbackData();
        }
    }

    // ========= ANALYSES AUTOMATIQUES SPECTRUM=========== //

    static async analyzeFrequencyAuto(frequencyId) {
        try {
            this.showNotification('🔍 Analyse automatique en cours...', 'info');

            const response = await fetch(`/api/kiwisdr/frequencies/${frequencyId}/analyze-auto`, {
                method: 'POST'
            });

            const data = await response.json();

            if (data.success) {
                this.showAnalysisResults(data);
                this.showNotification(`✅ ${data.analysis.significant_emissions} émissions détectées`, 'success');
            } else {
                throw new Error(data.error || 'Erreur analyse');
            }
        } catch (error) {
            console.error('Erreur analyse auto:', error);
            this.showError('Erreur analyse automatique: ' + error.message);
        }
    }

    static showAnalysisResults(data) {
        const analysis = data.analysis;

        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4';
        modal.innerHTML = `
        <div class="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-screen overflow-hidden flex flex-col">
            <div class="flex justify-between items-center p-4 border-b">
                <h3 class="text-lg font-semibold">🤖 Analyse Automatique - ${data.name}</h3>
                <button onclick="this.closest('.fixed').remove()" class="text-gray-500 hover:text-gray-700">
                    <i class="fas fa-times text-xl"></i>
                </button>
            </div>
            
            <div class="p-6 overflow-y-auto flex-1">
                <!-- Résumé -->
                <div class="grid grid-cols-3 gap-4 mb-6">
                    <div class="text-center p-4 bg-blue-50 rounded-lg">
                        <div class="text-3xl font-bold text-blue-600">${analysis.significant_emissions}</div>
                        <div class="text-sm text-blue-800">Émissions significatives</div>
                    </div>
                    <div class="text-center p-4 bg-green-50 rounded-lg">
                        <div class="text-3xl font-bold text-green-600">${analysis.total_peaks}</div>
                        <div class="text-sm text-green-800">Pics détectés</div>
                    </div>
                    <div class="text-center p-4 bg-purple-50 rounded-lg">
                        <div class="text-3xl font-bold text-purple-600">${data.frequency_khz}</div>
                        <div class="text-sm text-purple-800">Fréquence (kHz)</div>
                    </div>
                </div>

                <!-- Pics détectés -->
                <div class="mb-6">
                    <h4 class="font-semibold mb-3">📊 Pics détectés (Top 5)</h4>
                    <div class="space-y-2">
                        ${analysis.peaks.map(peak => `
                            <div class="flex justify-between items-center p-3 bg-gray-50 rounded">
                                <div class="flex-1">
                                    <div class="font-medium">${peak.frequency_khz.toFixed(3)} kHz</div>
                                    <div class="text-xs text-gray-500">
                                        ${peak.type} • BW: ${peak.bandwidth_khz.toFixed(2)} kHz
                                    </div>
                                </div>
                                <div class="text-right">
                                    <div class="font-bold ${peak.power_db > -60 ? 'text-red-600' : peak.power_db > -70 ? 'text-orange-600' : 'text-green-600'}">
                                        ${peak.power_db.toFixed(1)} dB
                                    </div>
                                    <div class="text-xs text-gray-500">
                                        Score: ${(peak.significance * 100).toFixed(0)}%
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>

                <!-- Actions -->
                <div class="bg-blue-50 border border-blue-200 rounded p-4">
                    <h4 class="font-semibold text-blue-800 mb-2">🚀 Surveillance Automatique</h4>
                    <p class="text-blue-700 text-sm mb-3">
                        Activez la surveillance continue pour analyser automatiquement cette fréquence.
                    </p>
                    <div class="flex space-x-2">
                        <button onclick="KiwiSDRManager.startAutoMonitoring(${data.frequency_id})" 
                                class="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded text-sm">
                            <i class="fas fa-play mr-2"></i>Démarrer surveillance
                        </button>
                        <button onclick="KiwiSDRManager.recordAutoResults(${data.frequency_id}, ${analysis.significant_emissions})" 
                                class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-sm">
                            <i class="fas fa-save mr-2"></i>Enregistrer résultats
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;

        document.body.appendChild(modal);
    }

    static async startAutoMonitoring(frequencyId) {
        try {
            const response = await fetch(`/api/kiwisdr/frequencies/${frequencyId}/start-monitoring`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ interval_minutes: 5 })
            });

            const data = await response.json();

            if (data.success) {
                this.showNotification('✅ Surveillance automatique démarrée', 'success');
                document.querySelector('.fixed.inset-0.bg-black.bg-opacity-50')?.remove();
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            console.error('Erreur démarrage surveillance:', error);
            this.showError('Erreur: ' + error.message);
        }
    }

    static async recordAutoResults(frequencyId, emissionCount) {
        try {
            const response = await fetch(`/api/kiwisdr/frequencies/${frequencyId}/record-manual`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    emission_count: emissionCount,
                    duration_minutes: 1,
                    notes: 'Détection automatique par analyse spectrale',
                    observer: 'system'
                })
            });

            const data = await response.json();

            if (data.success) {
                this.showNotification('✅ Résultats enregistrés', 'success');
                document.querySelector('.fixed.inset-0.bg-black.bg-opacity-50')?.remove();
                await this.loadDashboardData();
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            console.error('Erreur enregistrement:', error);
            this.showError('Erreur: ' + error.message);
        }
    }

    // === AFFICHAGE SERVEURS ===

    static displayServerStatus(serversData) {
        const container = document.getElementById('kiwisdr-servers-status');
        if (!container) return;

        const current = serversData.current;
        const history = serversData.history;

        if (!current || !current.servers) {
            container.innerHTML = this.renderErrorState('Serveurs KiwiSDR non disponibles');
            return;
        }

        // Calculer variation 1h
        const variation1h = history.history.length > 0
            ? history.history[history.history.length - 1].variation_1h
            : 0;

        container.innerHTML = `
            <div class="bg-white rounded-lg shadow-md p-6 mb-6">
                <h3 class="text-lg font-semibold mb-4 flex items-center">
                    <i class="fas fa-broadcast-tower text-blue-600 mr-2"></i>
                    Réseau KiwiSDR Mondial
                </h3>
                
                <!-- Statistiques globales -->
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                    <div class="text-center p-4 bg-blue-50 rounded-lg">
                        <div class="text-3xl font-bold text-blue-600">${current.total}</div>
                        <div class="text-sm text-blue-800">Serveurs actifs</div>
                    </div>
                    <div class="text-center p-4 bg-green-50 rounded-lg">
                        <div class="text-3xl font-bold ${variation1h >= 0 ? 'text-green-600' : 'text-red-600'}">
                            ${variation1h > 0 ? '+' : ''}${variation1h}
                        </div>
                        <div class="text-sm text-green-800">Δ 1 heure</div>
                    </div>
                    <div class="text-center p-4 bg-purple-50 rounded-lg">
                        <div class="text-3xl font-bold text-purple-600">
                            ${current.servers.filter(s => s.status === 'online').length}
                        </div>
                        <div class="text-sm text-purple-800">Disponibles</div>
                    </div>
                    <div class="text-center p-4 bg-orange-50 rounded-lg">
                        <div class="text-3xl font-bold text-orange-600">${history.alerts.length}</div>
                        <div class="text-sm text-orange-800">Alertes</div>
                    </div>
                </div>

                <!-- Liste des serveurs -->
                <div class="mb-4">
                    <h4 class="font-semibold mb-2">🌍 Serveurs Disponibles</h4>
                    <div class="max-h-64 overflow-y-auto space-y-2">
                        ${this.renderServerList(current.servers)}
                    </div>
                </div>

                <!-- Graphique historique -->
                <div class="mb-4">
                    <canvas id="serversHistoryChart" height="120"></canvas>
                </div>

                <!-- Alertes -->
                ${this.renderServerAlerts(history.alerts)}
            </div>
        `;

        this.createServerHistoryChart(history.history);
    }

    static renderServerList(servers) {
        if (!servers || servers.length === 0) {
            return '<p class="text-gray-500 text-sm">Aucun serveur disponible</p>';
        }

        return servers.slice(0, 10).map(server => `
            <div class="flex items-center justify-between p-2 bg-gray-50 rounded hover:bg-gray-100">
                <div class="flex-1 min-w-0">
                    <div class="font-medium text-sm truncate">${server.name}</div>
                    <div class="text-xs text-gray-500">${server.location}</div>
                </div>
                <div class="flex items-center space-x-2">
                    <span class="text-xs ${server.status === 'online' ? 'text-green-600' : 'text-red-600'}">
                        ${server.users}/${server.users_max}
                    </span>
                    <button onclick="KiwiSDRManager.testServer('${server.url}')"
                            class="text-blue-600 hover:text-blue-800 text-xs"
                            title="Tester la connexion">
                        <i class="fas fa-vial"></i>
                    </button>
                    <button onclick="window.open('${server.url}', '_blank')"
                            class="text-green-600 hover:text-green-800 text-xs"
                            title="Ouvrir le serveur">
                        <i class="fas fa-external-link-alt"></i>
                    </button>
                </div>
            </div>
        `).join('');
    }

    static renderServerAlerts(alerts) {
        if (!alerts || alerts.length === 0) {
            return `
                <div class="bg-green-50 border border-green-200 rounded p-3 text-sm text-green-800">
                    ✅ Aucune variation anormale détectée
                </div>
            `;
        }

        return `
            <div class="space-y-2">
                <h4 class="font-semibold text-red-600">🚨 Alertes Réseau</h4>
                ${alerts.map(alert => `
                    <div class="bg-red-50 border border-red-200 rounded p-3 text-sm">
                        <strong>${alert.message}</strong>
                        <div class="text-xs text-gray-500 mt-1">
                            ${new Date(alert.timestamp).toLocaleString('fr-FR')}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    static createServerHistoryChart(history) {
        const canvas = document.getElementById('serversHistoryChart');
        if (!canvas) return;

        if (this.serverChart) {
            this.serverChart.destroy();
        }

        if (!history || history.length === 0) {
            canvas.parentElement.innerHTML = '<p class="text-gray-500 text-sm text-center py-4">Aucun historique disponible</p>';
            return;
        }

        const ctx = canvas.getContext('2d');

        const timestamps = history.map(h =>
            new Date(h.timestamp).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
        );
        const serverCounts = history.map(h => h.total_servers);

        this.serverChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: timestamps,
                datasets: [{
                    label: 'Serveurs actifs',
                    data: serverCounts,
                    borderColor: '#3B82F6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4,
                    fill: true,
                    pointRadius: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (context) => `${context.parsed.y} serveurs`
                        }
                    }
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

    // === GESTION FRÉQUENCES ===

    static displayMonitoredFrequencies(frequenciesData) {
        const container = document.getElementById('monitored-frequencies-list');
        if (!container) return;

        this.monitoredFrequencies = frequenciesData.monitored || [];
        const activity = frequenciesData.activity || [];

        if (this.monitoredFrequencies.length === 0) {
            container.innerHTML = this.renderEmptyFrequenciesState();
            return;
        }

        container.innerHTML = `
            <div class="space-y-4">
                ${this.monitoredFrequencies.map(freq => {
            const stats = activity.find(a => a.frequency.id === freq.id);
            return this.renderFrequencyCard(freq, stats);
        }).join('')}
            </div>
        `;
    }

    static renderEmptyFrequenciesState() {
        return `
            <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-8 text-center">
                <i class="fas fa-satellite-dish text-yellow-600 text-5xl mb-4"></i>
                <h4 class="font-semibold text-yellow-800 mb-2 text-lg">Aucune fréquence surveillée</h4>
                <p class="text-yellow-700 mb-6">
                    Ajoutez des fréquences pour commencer l'observation manuelle du spectre
                </p>
                <div class="space-x-3">
                    <button onclick="KiwiSDRManager.showAddFrequencyModal()" 
                            class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg inline-flex items-center">
                        <i class="fas fa-plus mr-2"></i>Ajouter une fréquence
                    </button>
                    <button onclick="KiwiSDRManager.addGeopoliticalFrequencies()" 
                            class="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg inline-flex items-center">
                        <i class="fas fa-bolt mr-2"></i>Presets géopolitiques
                    </button>
                </div>
            </div>
        `;
    }

    static renderFrequencyCard(frequency, statsData) {
        const stats = statsData?.stats || { average: 0, variation: 0, total: 0 };
        const frequencyMHz = (frequency.frequency_khz / 1000).toFixed(3);

        return `
        <div class="border border-gray-200 rounded-lg p-4 bg-white hover:shadow-md transition">
            <div class="flex justify-between items-start mb-3">
                <div class="flex-1">
                    <h4 class="font-semibold text-gray-800 text-lg">${frequency.name}</h4>
                    <p class="text-sm text-blue-600 font-mono">${frequencyMHz} MHz</p>
                    ${frequency.description ? `
                        <p class="text-xs text-gray-500 mt-1">${frequency.description}</p>
                    ` : ''}
                </div>
                <div class="flex items-center space-x-2">
                    <!-- Ajouter le bouton d'analyse automatique -->
                    <button onclick="KiwiSDRManager.analyzeFrequencyAuto(${frequency.id})" 
                            class="text-purple-600 hover:text-purple-800 p-2"
                            title="Analyse automatique">
                        <i class="fas fa-robot text-xl"></i>
                    </button>
                    
                    <button onclick="KiwiSDRManager.openWaterfall(${frequency.id})" 
                            class="text-blue-600 hover:text-blue-800 p-2"
                            title="Observer le waterfall">
                        <i class="fas fa-eye text-xl"></i>
                    </button>
                        <button onclick="KiwiSDRManager.recordManualCount(${frequency.id})" 
                                class="text-green-600 hover:text-green-800 p-2"
                                title="Enregistrer une observation">
                            <i class="fas fa-plus-circle text-xl"></i>
                        </button>
                        <button onclick="KiwiSDRManager.viewStats(${frequency.id})" 
                                class="text-purple-600 hover:text-purple-800 p-2"
                                title="Voir les statistiques">
                            <i class="fas fa-chart-bar text-xl"></i>
                        </button>
                        <button onclick="KiwiSDRManager.deleteFrequency(${frequency.id})" 
                                class="text-red-600 hover:text-red-800 p-2"
                                title="Supprimer">
                            <i class="fas fa-trash text-xl"></i>
                        </button>
                    </div>
                </div>

                <!-- Statistiques -->
                <div class="grid grid-cols-3 gap-3 text-center text-sm">
                    <div class="bg-blue-50 p-3 rounded">
                        <div class="font-bold text-blue-600 text-xl">${stats.average}</div>
                        <div class="text-xs text-blue-800">Moyenne/jour</div>
                    </div>
                    <div class="bg-${stats.variation >= 0 ? 'green' : 'red'}-50 p-3 rounded">
                        <div class="font-bold text-${stats.variation >= 0 ? 'green' : 'red'}-600 text-xl">
                            ${stats.variation >= 0 ? '+' : ''}${stats.variation}%
                        </div>
                        <div class="text-xs text-${stats.variation >= 0 ? 'green' : 'red'}-800">Variation</div>
                    </div>
                    <div class="bg-purple-50 p-3 rounded">
                        <div class="font-bold text-purple-600 text-xl">${stats.total}</div>
                        <div class="text-xs text-purple-800">Total 7j</div>
                    </div>
                </div>

                <!-- Mini graphique -->
                ${this.renderMiniChart(stats)}
            </div>
        `;
    }

    static renderMiniChart(stats) {
        if (!stats.daily_activity || stats.daily_activity.length === 0) {
            return '<div class="text-xs text-gray-500 text-center mt-3">Aucune donnée d\'activité</div>';
        }

        const maxCount = Math.max(...stats.daily_activity.map(d => d.emission_count), 1);

        return `
            <div class="mt-3">
                <div class="flex items-end space-x-1 h-16">
                    ${stats.daily_activity.map(day => {
            const height = (day.emission_count / maxCount * 100);
            const date = new Date(day.date).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' });
            return `
                            <div class="flex-1 bg-blue-400 rounded-t hover:bg-blue-500 transition" 
                                 style="height: ${height}%"
                                 title="${date}: ${day.emission_count} émissions">
                            </div>
                        `;
        }).join('')}
                </div>
                <div class="text-xs text-gray-500 text-center mt-1">Activité 7 derniers jours</div>
            </div>
        `;
    }

    // === ACTIONS ===

    static async openWaterfall(frequencyId) {
        try {
            const frequency = this.monitoredFrequencies.find(f => f.id === frequencyId);
            if (!frequency) {
                this.showError('Fréquence non trouvée');
                return;
            }

            // Afficher modal de sélection de serveur
            this.showServerSelectionModal(frequencyId, frequency);

        } catch (error) {
            console.error('Erreur ouverture waterfall:', error);
            this.showError('Erreur lors de l\'ouverture du waterfall');
        }
    }

    static showServerSelectionModal(frequencyId, frequency) {
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4';
        modal.innerHTML = `
            <div class="bg-white rounded-lg shadow-xl w-full max-w-2xl">
                <div class="flex justify-between items-center p-4 border-b">
                    <h3 class="text-lg font-semibold">🌐 Sélectionner un serveur KiwiSDR</h3>
                    <button onclick="this.closest('.fixed').remove()" class="text-gray-500 hover:text-gray-700">
                        <i class="fas fa-times text-xl"></i>
                    </button>
                </div>
                
                <div class="p-4">
                    <p class="text-sm text-gray-600 mb-4">
                        Fréquence : <strong>${frequency.name}</strong> (${(frequency.frequency_khz / 1000).toFixed(3)} MHz)
                    </p>
                    
                    <div class="max-h-96 overflow-y-auto space-y-2">
                        ${this.availableServers.length > 0 ?
                this.availableServers.map(server => `
                                <button onclick="KiwiSDRManager.openWaterfallOnServer(${frequencyId}, '${server.url}')"
                                        class="w-full text-left p-3 bg-gray-50 hover:bg-blue-50 rounded border border-gray-200 hover:border-blue-300 transition">
                                    <div class="flex justify-between items-center">
                                        <div>
                                            <div class="font-medium">${server.name}</div>
                                            <div class="text-sm text-gray-500">${server.location}</div>
                                        </div>
                                        <div class="text-xs ${server.status === 'online' ? 'text-green-600' : 'text-red-600'}">
                                            ${server.users}/${server.users_max} utilisateurs
                                        </div>
                                    </div>
                                </button>
                            `).join('')
                : '<p class="text-gray-500 text-center py-8">Aucun serveur disponible</p>'
            }
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
    }

    static async openWaterfallOnServer(frequencyId, serverUrl) {
        try {
            const response = await fetch(`/api/kiwisdr/frequencies/${frequencyId}/waterfall?server_url=${encodeURIComponent(serverUrl)}&zoom=10`);
            const data = await response.json();

            if (data.success) {
                // Ouvrir dans un nouvel onglet
                window.open(data.waterfall_url, '_blank', 'width=1400,height=900');

                // Fermer le modal
                document.querySelector('.fixed.inset-0.bg-black.bg-opacity-50')?.remove();

                this.showNotification(`Waterfall ouvert : ${data.name}`, 'success');

                // Afficher instructions
                setTimeout(() => {
                    if (confirm('💡 Observez le waterfall et comptez les émissions.\n\nVoulez-vous enregistrer une observation maintenant ?')) {
                        this.recordManualCount(frequencyId);
                    }
                }, 2000);
            } else {
                throw new Error(data.error || 'Erreur serveur');
            }
        } catch (error) {
            console.error('Erreur:', error);
            this.showError('Impossible d\'ouvrir le waterfall : ' + error.message);
        }
    }

    static recordManualCount(frequencyId) {
        const frequency = this.monitoredFrequencies.find(f => f.id === frequencyId);
        if (!frequency) return;

        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4';
        modal.innerHTML = `
            <div class="bg-white rounded-lg shadow-xl w-full max-w-md">
                <div class="flex justify-between items-center p-4 border-b">
                    <h3 class="text-lg font-semibold">📝 Enregistrer une observation</h3>
                    <button onclick="this.closest('.fixed').remove()" class="text-gray-500 hover:text-gray-700">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                
                <form id="manual-count-form" class="p-4 space-y-4">
                    <div class="bg-blue-50 border border-blue-200 rounded p-3">
                        <p class="text-sm"><strong>Fréquence :</strong> ${frequency.name}</p>
                        <p class="text-sm"><strong>MHz :</strong> ${(frequency.frequency_khz / 1000).toFixed(3)}</p>
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium mb-1">Nombre d'émissions observées *</label>
                        <input type="number" name="emission_count" min="0" required
                               class="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500" 
                               placeholder="ex: 15">
                        <p class="text-xs text-gray-500 mt-1">Comptez les traits verticaux dans le waterfall</p>
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium mb-1">Durée d'observation (minutes)</label>
                        <input type="number" name="duration_minutes" min="1" value="30"
                               class="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500">
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium mb-1">Notes (optionnel)</label>
                        <textarea name="notes" rows="3"
                                  class="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500"
                                  placeholder="ex: Forte activité entre 14h et 15h, signaux faibles"></textarea>
                    </div>
                    
                    <div class="flex justify-end space-x-2 pt-2">
                        <button type="button" onclick="this.closest('.fixed').remove()"
                                class="px-4 py-2 border rounded-md hover:bg-gray-50">
                            Annuler
                        </button>
                        <button type="submit"
                                class="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700">
                            <i class="fas fa-save mr-2"></i>Enregistrer
                        </button>
                    </div>
                </form>
            </div>
        `;

        document.body.appendChild(modal);

        modal.querySelector('#manual-count-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);

            try {
                const response = await fetch(`/api/kiwisdr/frequencies/${frequencyId}/record-manual`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        emission_count: parseInt(formData.get('emission_count')),
                        duration_minutes: parseInt(formData.get('duration_minutes')),
                        notes: formData.get('notes'),
                        observer: 'user'
                    })
                });

                const result = await response.json();

                if (result.success) {
                    this.showNotification(result.message, 'success');
                    modal.remove();
                    await this.loadDashboardData();
                } else {
                    throw new Error(result.error || 'Erreur serveur');
                }
            } catch (error) {
                console.error('Erreur enregistrement:', error);
                alert('Erreur : ' + error.message);
            }
        });
    }

    static async viewStats(frequencyId) {
        try {
            const response = await fetch(`/api/kiwisdr/frequencies/${frequencyId}?days=30`);
            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error || 'Erreur serveur');
            }

            const frequency = this.monitoredFrequencies.find(f => f.id === frequencyId);
            if (!frequency) return;

            const modal = document.createElement('div');
            modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4';
            modal.innerHTML = `
                <div class="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-screen overflow-hidden flex flex-col">
                    <div class="flex justify-between items-center p-4 border-b">
                        <h3 class="text-lg font-semibold">📊 Statistiques - ${frequency.name}</h3>
                        <button onclick="this.closest('.fixed').remove()" class="text-gray-500">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    
                    <div class="p-6 overflow-y-auto flex-1">
                        <div class="grid grid-cols-3 gap-4 mb-6">
                            <div class="text-center p-4 bg-blue-50 rounded-lg">
                                <div class="text-3xl font-bold text-blue-600">${data.average}</div>
                                <div class="text-sm text-blue-800">Moyenne/jour</div>
                            </div>
                            <div class="text-center p-4 bg-green-50 rounded-lg">
                                <div class="text-3xl font-bold text-green-600">${data.total}</div>
                                <div class="text-sm text-green-800">Total 30j</div>
                            </div>
                            <div class="text-center p-4 bg-purple-50 rounded-lg">
                                <div class="text-3xl font-bold text-purple-600">${data.variation >= 0 ? '+' : ''}${data.variation}%</div>
                                <div class="text-sm text-purple-800">Variation</div>
                            </div>
                        </div>

                        <div class="mb-6">
                            <canvas id="frequencyStatsChart" height="200"></canvas>
                        </div>

                        <div class="space-y-2">
                            <h4 class="font-semibold mb-2">📅 Historique détaillé</h4>
                            ${data.daily_activity.length > 0 ?
                    data.daily_activity.slice().reverse().map(day => `
                                    <div class="flex justify-between items-center p-3 bg-gray-50 rounded">
                                        <span class="text-sm">${new Date(day.date).toLocaleDateString('fr-FR')}</span>
                                        <div class="text-right">
                                            <span class="font-medium">${day.emission_count} émissions</span>
                                            ${day.notes ? `<p class="text-xs text-gray-500 mt-1">${day.notes}</p>` : ''}
                                        </div>
                                    </div>
                                `).join('')
                    : '<p class="text-gray-500 text-center py-4">Aucune observation enregistrée</p>'
                }
                        </div>
                    </div>
                </div>
            `;

            document.body.appendChild(modal);

            // Créer le graphique
            setTimeout(() => {
                const canvas = document.getElementById('frequencyStatsChart');
                if (canvas && data.daily_activity.length > 0) {
                    new Chart(canvas, {
                        type: 'bar',
                        data: {
                            labels: data.daily_activity.map(d =>
                                new Date(d.date).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' })
                            ),
                            datasets: [{
                                label: 'Émissions',
                                data: data.daily_activity.map(d => d.emission_count),
                                backgroundColor: 'rgba(59, 130, 246, 0.5)',
                                borderColor: '#3B82F6',
                                borderWidth: 1
                            }]
                        },
                        options: {
                            responsive: true,
                            plugins: {
                                legend: { display: false },
                                tooltip: {
                                    callbacks: {
                                        label: (context) => `${context.parsed.y} émissions`
                                    }
                                }
                            },
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    ticks: { precision: 0 }
                                }
                            }
                        }
                    });
                }
            }, 100);
        } catch (error) {
            console.error('Erreur stats:', error);
            this.showError('Erreur chargement statistiques : ' + error.message);
        }
    }

    static showAddFrequencyModal() {
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4';
        modal.innerHTML = `
            <div class="bg-white rounded-lg shadow-xl w-full max-w-md">
                <div class="flex justify-between items-center p-4 border-b">
                    <h3 class="text-lg font-semibold">➕ Ajouter une fréquence</h3>
                    <button onclick="this.closest('.fixed').remove()" class="text-gray-500 hover:text-gray-700">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                
                <form id="add-frequency-form" class="p-4 space-y-4">
                    <div>
                        <label class="block text-sm font-medium mb-1">Fréquence (kHz) *</label>
                        <input type="number" name="frequency_khz" required
                               class="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500" 
                               placeholder="ex: 14300">
                        <p class="text-xs text-gray-500 mt-1">Exemple : 14300 kHz = 14.3 MHz</p>
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium mb-1">Nom *</label>
                        <input type="text" name="name" required
                               class="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500" 
                               placeholder="ex: Maritime 14.3 MHz">
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium mb-1">Description</label>
                        <textarea name="description" rows="2"
                                  class="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500"
                                  placeholder="ex: Fréquence maritime pour communications internationales"></textarea>
                    </div>
                    
                    <div class="bg-blue-50 border border-blue-200 rounded p-3 text-sm">
                        <p class="font-medium text-blue-800 mb-1">💡 Conseil</p>
                        <p class="text-blue-700">Utilisez des fréquences HF (3-30 MHz) pour une meilleure couverture mondiale sur KiwiSDR</p>
                    </div>
                    
                    <div class="flex justify-end space-x-2 pt-2">
                        <button type="button" onclick="this.closest('.fixed').remove()"
                                class="px-4 py-2 border rounded-md hover:bg-gray-50">
                            Annuler
                        </button>
                        <button type="submit"
                                class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
                            <i class="fas fa-plus mr-2"></i>Ajouter
                        </button>
                    </div>
                </form>
            </div>
        `;

        document.body.appendChild(modal);

        modal.querySelector('#add-frequency-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);

            try {
                const response = await fetch('/api/kiwisdr/frequencies', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        frequency_khz: parseInt(formData.get('frequency_khz')),
                        name: formData.get('name'),
                        description: formData.get('description')
                    })
                });

                const result = await response.json();

                if (result.success) {
                    this.showNotification('Fréquence ajoutée avec succès', 'success');
                    modal.remove();
                    await this.loadDashboardData();
                } else {
                    throw new Error(result.error || 'Erreur serveur');
                }
            } catch (error) {
                console.error('Erreur:', error);
                alert('Erreur : ' + error.message);
            }
        });
    }

    static async addGeopoliticalFrequencies() {
        if (!confirm('Ajouter les 8 fréquences géopolitiques prédéfinies ?\n\nCes fréquences sont utilisées pour :\n- Communications diplomatiques\n- Urgences maritimes et aviation\n- Surveillance militaire (légale)')) {
            return;
        }

        try {
            const response = await fetch('/api/kiwisdr/frequencies/preset/geopolitical', {
                method: 'POST'
            });

            const result = await response.json();

            if (result.success) {
                this.showNotification(`✅ ${result.added} fréquences géopolitiques ajoutées`, 'success');

                if (result.errors.length > 0) {
                    console.warn('Erreurs lors de l\'ajout:', result.errors);
                }

                await this.loadDashboardData();
            } else {
                throw new Error(result.error || 'Erreur serveur');
            }
        } catch (error) {
            console.error('Erreur ajout presets:', error);
            this.showError('Erreur lors de l\'ajout des fréquences : ' + error.message);
        }
    }

    static async deleteFrequency(frequencyId) {
        const frequency = this.monitoredFrequencies.find(f => f.id === frequencyId);
        if (!frequency) return;

        if (!confirm(`Désactiver la fréquence "${frequency.name}" ?\n\nLes données historiques seront conservées.`)) {
            return;
        }

        try {
            const response = await fetch(`/api/kiwisdr/frequencies/${frequencyId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.showNotification('Fréquence désactivée', 'success');
                await this.loadDashboardData();
            } else {
                const data = await response.json();
                throw new Error(data.error || 'Erreur serveur');
            }
        } catch (error) {
            console.error('Erreur suppression:', error);
            this.showError('Erreur lors de la suppression : ' + error.message);
        }
    }

    static async testServer(serverUrl) {
        try {
            this.showNotification('Test de connexion en cours...', 'info');

            const response = await fetch(`/api/kiwisdr/servers/test/${encodeURIComponent(serverUrl)}`);
            const data = await response.json();

            if (data.success) {
                if (data.available) {
                    this.showNotification('✅ Serveur accessible', 'success');
                } else {
                    this.showNotification('❌ Serveur inaccessible', 'error');
                }
            } else {
                throw new Error(data.error || 'Erreur test');
            }
        } catch (error) {
            console.error('Erreur test serveur:', error);
            this.showError('Erreur lors du test : ' + error.message);
        }
    }

    // === SNAPSHOTS ===

    static async createManualSnapshot() {
        try {
            const button = document.getElementById('manual-snapshot-btn');
            const originalText = button?.innerHTML;

            if (button) {
                button.disabled = true;
                button.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Création...';
            }

            const response = await fetch('/api/kiwisdr/servers/snapshot', {
                method: 'POST'
            });

            const result = await response.json();

            if (result.success) {
                this.showNotification(`📸 Snapshot créé : ${result.total_servers} serveurs`, 'success');
                await this.loadDashboardData();
            } else {
                throw new Error(result.error || 'Erreur serveur');
            }

            if (button) {
                button.disabled = false;
                button.innerHTML = originalText;
            }
        } catch (error) {
            console.error('Erreur snapshot:', error);
            this.showError('Erreur création snapshot : ' + error.message);

            const button = document.getElementById('manual-snapshot-btn');
            if (button) {
                button.disabled = false;
                button.innerHTML = '<i class="fas fa-camera mr-2"></i>Snapshot Manuel';
            }
        }
    }

    // === UTILITAIRES ===

    static updateGlobalStats(data) {
        const activeServers = data.servers?.current?.total || 0;
        const monitoredFreqs = data.frequencies?.monitored?.filter(f => f.active).length || 0;

        this.updateCard('kiwisdr-active-servers', activeServers);
        this.updateCard('kiwisdr-monitored-frequencies', monitoredFreqs);
    }

    static updateCard(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value.toLocaleString('fr-FR');
        }
    }

    static setupEventListeners() {
        // Snapshot manuel
        const snapshotBtn = document.getElementById('manual-snapshot-btn');
        if (snapshotBtn) {
            snapshotBtn.addEventListener('click', () => this.createManualSnapshot());
        }
    }

    static startPeriodicUpdates() {
        // Actualisation toutes les 5 minutes
        this.updateInterval = setInterval(() => {
            console.log('🔄 Actualisation périodique KiwiSDR...');
            this.loadDashboardData();
        }, 5 * 60 * 1000);

        // Snapshot automatique toutes les heures
        setInterval(() => {
            console.log('📸 Snapshot automatique KiwiSDR...');
            this.createManualSnapshot();
        }, 60 * 60 * 1000);
    }

    static showNotification(message, type = 'info') {
        const notification = document.createElement('div');

        const colors = {
            success: 'bg-green-500',
            error: 'bg-red-500',
            info: 'bg-blue-500',
            warning: 'bg-yellow-500'
        };

        const icons = {
            success: 'check-circle',
            error: 'exclamation-triangle',
            info: 'info-circle',
            warning: 'exclamation-triangle'
        };

        notification.className = `fixed top-4 right-4 ${colors[type]} text-white p-4 rounded-lg shadow-lg z-50 max-w-md`;
        notification.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-${icons[type]} mr-3 text-xl"></i>
                <span>${message}</span>
            </div>
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transition = 'opacity 0.5s';
            setTimeout(() => notification.remove(), 500);
        }, 5000);
    }

    static showError(message) {
        console.error('🚨', message);
        this.showNotification(message, 'error');
    }

    static renderErrorState(message) {
        return `
            <div class="bg-red-50 border border-red-200 rounded-lg p-8 text-center">
                <i class="fas fa-exclamation-triangle text-red-600 text-5xl mb-4"></i>
                <h4 class="font-semibold text-red-800 text-lg mb-2">Erreur de connexion</h4>
                <p class="text-red-700 mb-4">${message}</p>
                <button onclick="KiwiSDRManager.loadDashboardData()" 
                        class="bg-red-600 hover:bg-red-700 text-white px-6 py-2 rounded-lg">
                    <i class="fas fa-redo mr-2"></i>Réessayer
                </button>
            </div>
        `;
    }

    static showFallbackData() {
        const container = document.getElementById('kiwisdr-servers-status');
        if (container) {
            container.innerHTML = `
                <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
                    <div class="flex items-center mb-4">
                        <i class="fas fa-exclamation-triangle text-yellow-600 text-2xl mr-3"></i>
                        <h4 class="font-semibold text-yellow-800 text-lg">Données KiwiSDR non disponibles</h4>
                    </div>
                    <p class="text-yellow-700 mb-4">
                        Impossible de se connecter au réseau KiwiSDR. Cela peut être dû à :
                    </p>
                    <ul class="text-yellow-700 text-sm space-y-1 ml-6 mb-4">
                        <li>• Problème de connexion internet</li>
                        <li>• Serveurs KiwiSDR temporairement indisponibles</li>
                        <li>• Pare-feu bloquant les requêtes</li>
                    </ul>
                    <div class="space-x-2">
                        <button onclick="KiwiSDRManager.loadDashboardData()" 
                                class="bg-yellow-600 hover:bg-yellow-700 text-white px-4 py-2 rounded-lg">
                            <i class="fas fa-redo mr-2"></i>Réessayer
                        </button>
                        <button onclick="window.open('http://kiwisdr.com/public/', '_blank')" 
                                class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg">
                            <i class="fas fa-external-link-alt mr-2"></i>Accéder manuellement
                        </button>
                    </div>
                </div>
            `;
        }

        // Stats par défaut
        this.updateCard('kiwisdr-active-servers', 0);
        this.updateCard('kiwisdr-monitored-frequencies', 0);
    }

    static destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
        if (this.serverChart) {
            this.serverChart.destroy();
        }
        console.log('🧹 KiwiSDRManager nettoyé');
    }
}

// === INITIALISATION AUTOMATIQUE ===

if (window.location.pathname.includes('/weak-indicators')) {
    document.addEventListener('DOMContentLoaded', () => {
        console.log('🎯 Page indicateurs faibles détectée - Initialisation KiwiSDR...');
        KiwiSDRManager.initialize();
    });

    // Nettoyage avant déchargement
    window.addEventListener('beforeunload', () => {
        KiwiSDRManager.destroy();
    });
}

// Exposer globalement pour accès externe
window.KiwiSDRManager = KiwiSDRManager;

console.log('✅ KiwiSDRManager chargé (version observation manuelle)')
