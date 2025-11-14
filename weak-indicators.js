// static/js/weak-indicators.js - VERSION CORRIGÉE COMPLÈTE
class WeakIndicatorsManager {
    static economicChart = null;
    static sdrStreams = new Map();
    static updateInterval = null;

    static async initialize() {
        console.log('🚀 Initialisation WeakIndicatorsManager...');

        try {
            await this.loadInitialData();
            this.setupEventListeners();
            this.startPeriodicUpdates();
            await this.initializeAlerts();

            console.log('✅ WeakIndicatorsManager initialisé');
        } catch (error) {
            console.error('❌ Erreur initialisation:', error);
            this.showError('Erreur lors de l\'initialisation des indicateurs faibles');
        }
    }

    static async loadInitialData() {
        try {
            // Charger le statut global
            const status = await this.fetchData('/api/weak-indicators/status');
            this.updateGlobalStats(status);

            // Charger les pays surveillés
            const countries = await this.fetchData('/api/weak-indicators/countries');
            this.updateCountriesList(countries);

            // Charger les flux SDR
            await this.loadSDRStreams();

            // Charger les statistiques SDR
            await this.loadSDRStats();

        } catch (error) {
            console.error('❌ Erreur chargement données initiales:', error);
            this.showErrorState();
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

    static updateCountriesList(countries) {
        const container = document.getElementById('countries-list');
        if (!container) return;

        container.innerHTML = countries.map(country => `
            <div class="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                <div class="flex items-center space-x-3">
                    <div class="w-3 h-3 rounded-full ${country.risk_level === 'high' ? 'bg-red-500' :
                country.risk_level === 'medium' ? 'bg-yellow-500' : 'bg-green-500'
            }"></div>
                    <div>
                        <p class="font-medium text-gray-800">${country.name}</p>
                        <p class="text-sm text-gray-600">${country.code}</p>
                    </div>
                </div>
                <div class="text-right">
                    <span class="px-2 py-1 text-xs rounded-full ${country.risk_level === 'high' ? 'bg-red-100 text-red-800' :
                country.risk_level === 'medium' ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'
            }">
                        ${country.risk_level}
                    </span>
                </div>
            </div>
        `).join('');
    }

    // === GESTION DES STATIONS SDR ===

    static async loadSDRStreams() {
        try {
            const streams = await this.fetchData('/api/sdr-streams');
            this.sdrStreams = new Map(streams.map(s => [s.id, s]));
            this.updateSDRDisplay();
        } catch (error) {
            console.warn('⚠️ Aucun flux SDR chargé:', error.message);
            this.showSDRSetupInterface();
        }
    }

    static async loadSDRStats() {
        try {
            const stats = await this.fetchData('/api/sdr-streams/stats');
            this.displaySDRStats(stats);
        } catch (error) {
            console.warn('⚠️ Erreur statistiques SDR:', error.message);
        }
    }

    static showSDRSetupInterface() {
        const container = document.getElementById('sdr-management');
        if (!container) return;

        container.innerHTML = `
            <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-6 mb-6">
                <div class="flex items-center mb-4">
                    <i class="fas fa-satellite-dish text-yellow-600 text-xl mr-3"></i>
                    <h3 class="text-lg font-semibold text-yellow-800">Configuration SDR Requise</h3>
                </div>
                <p class="text-yellow-700 mb-4">Aucune station SDR configurée. Ajoutez vos premières stations pour commencer la surveillance.</p>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <!-- Formulaire d'ajout manuel -->
                    <div class="bg-white p-4 rounded-lg border">
                        <h4 class="font-semibold mb-3">➕ Ajouter une Station</h4>
                        <form id="add-sdr-form" class="space-y-3">
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-1">Nom de la station</label>
                                <input type="text" name="name" class="w-full px-3 py-2 border border-gray-300 rounded-md" 
                                       placeholder="ex: WebSDR Twente" required>
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-1">URL WebSDR</label>
                                <input type="url" name="url" class="w-full px-3 py-2 border border-gray-300 rounded-md"
                                       placeholder="http://websdr.ewi.utwente.nl:8901/" required>
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-1">Fréquence (kHz)</label>
                                <input type="number" name="frequency_khz" class="w-full px-3 py-2 border border-gray-300 rounded-md"
                                       placeholder="ex: 14300" required>
                            </div>
                            <button type="submit" class="w-full bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded-md">
                                <i class="fas fa-plus mr-2"></i>Ajouter la Station
                            </button>
                        </form>
                    </div>

                    <!-- Configuration rapide -->
                    <div class="bg-white p-4 rounded-lg border">
                        <h4 class="font-semibold mb-3">⚡ Configuration Rapide</h4>
                        <p class="text-sm text-gray-600 mb-3">Ajouter des fréquences géopolitiques importantes :</p>
                        
                        <div class="space-y-2">
                            <button onclick="WeakIndicatorsManager.addGeopoliticalFrequencies()" 
                                    class="w-full bg-green-500 hover:bg-green-600 text-white py-2 px-4 rounded-md text-sm">
                                <i class="fas fa-bolt mr-2"></i>Ajouter les Fréquences Stratégiques
                            </button>
                            
                            <div class="text-xs text-gray-500">
                                Inclut: Aviation (121.5 MHz), Maritime, Diplomatique, Militaire
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Écouteur pour le formulaire
        const form = document.getElementById('add-sdr-form');
        if (form) {
            form.addEventListener('submit', (e) => this.handleAddSDRForm(e));
        }
    }

    static async handleAddSDRForm(e) {
        e.preventDefault();
        const formData = new FormData(e.target);

        const streamData = {
            name: formData.get('name'),
            url: formData.get('url'),
            frequency_khz: parseInt(formData.get('frequency_khz'))
        };

        try {
            const response = await fetch('/api/sdr-streams', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(streamData)
            });

            if (response.ok) {
                this.showNotification('Station SDR ajoutée avec succès', 'success');
                await this.loadSDRStreams();
                e.target.reset();
            } else {
                const error = await response.json();
                throw new Error(error.error || 'Erreur serveur');
            }
        } catch (error) {
            console.error('❌ Erreur ajout station:', error);
            this.showNotification(`Erreur: ${error.message}`, 'error');
        }
    }

    static async addGeopoliticalFrequencies() {
        const frequencies = [
            { name: "Emergency Aviation", freq: 121500 },
            { name: "Maritime MF", freq: 2182000 },
            { name: "Diplomatic HF", freq: 5732000 },
            { name: "Government Comm", freq: 8992000 },
            { name: "Foreign Service", freq: 11175000 },
            { name: "Military LF", freq: 4500000 }
        ];

        const websdrUrl = "http://websdr.ewi.utwente.nl:8901/";
        let added = 0;

        for (const freq of frequencies) {
            try {
                const response = await fetch('/api/sdr-streams', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        name: freq.name,
                        url: websdrUrl,
                        frequency_khz: freq.freq
                    })
                });

                if (response.ok) {
                    added++;
                }
            } catch (error) {
                console.warn(`Erreur ajout ${freq.name}:`, error);
            }
        }

        this.showNotification(`${added} stations stratégiques ajoutées`, 'success');
        await this.loadSDRStreams();
    }

    static updateSDRDisplay() {
        this.updateSDRStats();
        this.updateSDRStreamsList();
    }

    static displaySDRStats(stats) {
        const container = document.getElementById('sdr-global-stats');
        if (!container) return;

        container.innerHTML = `
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div class="bg-white p-4 rounded-lg border text-center">
                    <div class="text-2xl font-bold text-blue-600">${stats.total_streams}</div>
                    <div class="text-sm text-gray-600">Stations</div>
                </div>
                <div class="bg-white p-4 rounded-lg border text-center">
                    <div class="text-2xl font-bold text-green-600">${stats.today_activity}</div>
                    <div class="text-sm text-gray-600">Activité Aujourd'hui</div>
                </div>
                <div class="bg-white p-4 rounded-lg border text-center">
                    <div class="text-2xl font-bold text-purple-600">${stats.avg_daily_activity}</div>
                    <div class="text-sm text-gray-600">Moyenne/Jour</div>
                </div>
                <div class="bg-white p-4 rounded-lg border text-center">
                    <div class="text-2xl font-bold text-orange-600">${stats.top_streams.length}</div>
                    <div class="text-sm text-gray-600">Stations Actives</div>
                </div>
            </div>
        `;
    }

    static updateSDRStreamsList() {
        const container = document.getElementById('sdr-streams-list');
        if (!container) return;

        if (this.sdrStreams.size === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <i class="fas fa-satellite-dish text-3xl mb-3"></i>
                    <p>Aucune station SDR configurée</p>
                    <p class="text-sm mt-2">Utilisez le formulaire ci-dessus pour ajouter vos premières stations</p>
                </div>
            `;
            return;
        }

        container.innerHTML = Array.from(this.sdrStreams.values()).map(stream => `
            <div class="border border-gray-200 rounded-lg p-4 mb-3">
                <div class="flex justify-between items-start mb-3">
                    <div class="flex items-center">
                        <div class="w-3 h-3 rounded-full bg-green-500 mr-2"></div>
                        <div>
                            <h4 class="font-semibold text-gray-800">${stream.name}</h4>
                            <p class="text-sm text-gray-600">${(stream.frequency_khz / 1000).toFixed(3)} MHz</p>
                        </div>
                    </div>
                    <div class="flex space-x-2">
                        <button onclick="WeakIndicatorsManager.viewStreamActivity(${stream.id})" 
                                class="text-blue-500 hover:text-blue-700 text-sm">
                            <i class="fas fa-chart-bar mr-1"></i>Stats
                        </button>
                        <button onclick="WeakIndicatorsManager.deleteSDRStream(${stream.id})" 
                                class="text-red-500 hover:text-red-700 text-sm">
                            <i class="fas fa-trash mr-1"></i>Supprimer
                        </button>
                    </div>
                </div>
                
                <div class="grid grid-cols-2 gap-4 text-sm">
                    <div>
                        <span class="text-gray-600">URL:</span>
                        <div class="truncate">${stream.url}</div>
                    </div>
                    <div>
                        <span class="text-gray-600">Activité totale:</span>
                        <div class="font-medium">${stream.total_activity || 0}</div>
                    </div>
                </div>
                
                ${stream.last_activity ? `
                    <div class="text-xs text-gray-500 mt-2">
                        Dernière activité: ${new Date(stream.last_activity).toLocaleDateString()}
                    </div>
                ` : ''}
            </div>
        `).join('');
    }

    static async viewStreamActivity(streamId) {
        try {
            const activity = await this.fetchData(`/api/sdr-streams/${streamId}/activity`);
            this.showStreamActivityModal(streamId, activity);
        } catch (error) {
            console.error('❌ Erreur activité stream:', error);
            this.showNotification('Erreur chargement des statistiques', 'error');
        }
    }

    static showStreamActivityModal(streamId, activityData) {
        const stream = this.sdrStreams.get(streamId);
        if (!stream) return;

        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="bg-white rounded-lg shadow-xl w-11/12 max-w-2xl max-h-90vh overflow-hidden">
                <div class="flex justify-between items-center p-4 border-b">
                    <h3 class="text-lg font-semibold">📊 Activité - ${stream.name}</h3>
                    <button onclick="this.parentElement.parentElement.parentElement.remove()" 
                            class="text-gray-500 hover:text-gray-700">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                
                <div class="p-4">
                    <!-- Statistiques -->
                    <div class="grid grid-cols-3 gap-4 mb-6">
                        <div class="text-center p-3 bg-blue-50 rounded">
                            <div class="text-xl font-bold text-blue-600">${activityData.stats.avg_activity}</div>
                            <div class="text-sm text-blue-800">Moyenne/Jour</div>
                        </div>
                        <div class="text-center p-3 bg-green-50 rounded">
                            <div class="text-xl font-bold text-green-600">${activityData.stats.max_activity}</div>
                            <div class="text-sm text-green-800">Maximum</div>
                        </div>
                        <div class="text-center p-3 bg-purple-50 rounded">
                            <div class="text-xl font-bold text-purple-600">${activityData.stats.total_activity}</div>
                            <div class="text-sm text-purple-800">Total 30j</div>
                        </div>
                    </div>

                    <!-- Graphique d'activité -->
                    <div class="mb-4">
                        <canvas id="activityChart" height="150"></canvas>
                    </div>

                    <!-- Dernières activités -->
                    <div>
                        <h4 class="font-semibold mb-2">Dernières Activités</h4>
                        <div class="space-y-2 max-h-40 overflow-y-auto">
                            ${activityData.activity.slice(-10).map(day => `
                                <div class="flex justify-between items-center p-2 bg-gray-50 rounded text-sm">
                                    <span>${new Date(day.date).toLocaleDateString()}</span>
                                    <span class="font-medium ${day.activity_count > 50 ? 'text-red-600' : day.activity_count > 20 ? 'text-yellow-600' : 'text-green-600'}">
                                        ${day.activity_count} émissions
                                    </span>
                                </div>
                            `).reverse().join('')}
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Créer le graphique
        this.createActivityChart(activityData);
    }

    static createActivityChart(activityData) {
        const canvas = document.getElementById('activityChart');
        if (!canvas) return;

        const dates = activityData.activity.map(a => new Date(a.date).toLocaleDateString());
        const counts = activityData.activity.map(a => a.activity_count);

        new Chart(canvas, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [{
                    label: 'Émissions par jour',
                    data: counts,
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
                        beginAtZero: true,
                        title: { display: true, text: 'Nombre d\'émissions' }
                    }
                }
            }
        });
    }

    static async deleteSDRStream(streamId) {
        if (!confirm('Supprimer cette station SDR ?')) return;

        try {
            const response = await fetch(`/api/sdr-streams/${streamId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.showNotification('Station supprimée', 'success');
                await this.loadSDRStreams();
            } else {
                throw new Error('Erreur suppression');
            }
        } catch (error) {
            console.error('❌ Erreur suppression:', error);
            this.showNotification('Erreur lors de la suppression', 'error');
        }
    }

    // === CONSEILS AUX VOYAGEURS ===

    static async scanTravelAdvice() {
        console.log('🔍 Scan des conseils aux voyageurs...');

        const button = document.querySelector('[onclick*="scanTravelAdvice"]');
        const originalText = button?.innerHTML;

        if (button) {
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Scan en cours...';
        }

        try {
            const response = await fetch('/api/travel-advice/scan', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();

            if (result.success) {
                this.displayTravelAdviceResults(result.results);
                this.showNotification(`Scan terminé: ${result.summary.changes} changements détectés`, 'success');
            } else {
                throw new Error(result.error || 'Erreur inconnue');
            }

        } catch (error) {
            console.error('❌ Erreur scan conseils voyageurs:', error);
            this.showNotification('Erreur lors du scan des conseils aux voyageurs', 'error');
        } finally {
            if (button) {
                button.disabled = false;
                button.innerHTML = originalText;
            }
        }
    }

    static displayTravelAdviceResults(results) {
        const container = document.getElementById('travel-advice-results');
        if (!container) return;

        const { sources_checked, changes_detected, alerts } = results;

        let html = `
            <div class="mb-6">
                <h3 class="text-lg font-semibold mb-4">📊 Résultats du Scan</h3>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <div class="bg-blue-50 p-4 rounded-lg">
                        <div class="text-2xl font-bold text-blue-600">${sources_checked.length}</div>
                        <div class="text-sm text-blue-800">Sources vérifiées</div>
                    </div>
                    <div class="bg-yellow-50 p-4 rounded-lg">
                        <div class="text-2xl font-bold text-yellow-600">${changes_detected.length}</div>
                        <div class="text-sm text-yellow-800">Changements détectés</div>
                    </div>
                    <div class="bg-red-50 p-4 rounded-lg">
                        <div class="text-2xl font-bold text-red-600">${alerts.length}</div>
                        <div class="text-sm text-red-800">Alertes générées</div>
                    </div>
                </div>
            </div>
        `;

        // Afficher les changements détectés
        if (changes_detected.length > 0) {
            html += `
                <div class="mb-6">
                    <h4 class="font-semibold text-red-600 mb-2">🚨 Changements Détectés</h4>
                    <div class="space-y-2">
            `;

            changes_detected.forEach(change => {
                html += `
                    <div class="bg-red-50 border border-red-200 p-3 rounded">
                        <div class="font-medium">${change.country}</div>
                        <div class="text-sm">
                            ${change.previous_level} → ${change.new_level}
                        </div>
                    </div>
                `;
            });

            html += `</div></div>`;
        }

        // Afficher les sources vérifiées
        html += `
            <div>
                <h4 class="font-semibold mb-2">🌍 Sources Vérifiées</h4>
                <div class="space-y-2">
        `;

        sources_checked.forEach(source => {
            const statusColor = source.status === 'changed' ? 'text-yellow-600' :
                source.status === 'stable' ? 'text-green-600' : 'text-red-600';
            const statusIcon = source.status === 'changed' ? '🔄' :
                source.status === 'stable' ? '✅' : '❌';

            html += `
                <div class="bg-white border border-gray-200 p-3 rounded">
                    <div class="flex justify-between items-center">
                        <div>
                            <span class="font-medium">${source.country}</span>
                            <span class="text-sm text-gray-500 ml-2">${source.level || 'N/A'}</span>
                        </div>
                        <div class="${statusColor}">
                            ${statusIcon} ${source.status}
                        </div>
                    </div>
                    <div class="text-xs text-gray-500 mt-1">${source.url}</div>
                </div>
            `;
        });

        html += `</div></div>`;

        container.innerHTML = html;
    }

    // === WEBSDR MONITORING ===

    static async setupWebSDRMonitoring() {
        const url = document.getElementById('websdr-url')?.value?.trim();
        if (!url) {
            alert("Veuillez saisir l'URL du WebSDR");
            return;
        }

        try {
            const response = await fetch('/api/sdr-streams/websdr-monitor', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    websdr_url: url
                })
            });

            const result = await response.json();

            if (result.success) {
                this.showNotification(`Surveillance WebSDR démarrée: ${result.message}`, 'success');
                await this.loadSDRStreams();
            } else {
                throw new Error(result.error || 'Erreur inconnue');
            }

        } catch (error) {
            console.error('❌ Erreur configuration WebSDR:', error);
            this.showNotification('Erreur configuration WebSDR', 'error');
        }
    }

    // === MÉTHODES UTILITAIRES ===

    static async initializeAlerts() {
        if (typeof AlertsManager !== 'undefined') {
            await AlertsManager.initialize();
        }
    }

    static setupEventListeners() {
        // Recherche de pays
        const searchInput = document.getElementById('countrySearch');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.filterCountries(e.target.value);
            });
        }
    }

    static filterCountries(searchTerm) {
        const countries = document.querySelectorAll('#countries-list > div');
        countries.forEach(country => {
            const text = country.textContent.toLowerCase();
            const shouldShow = text.includes(searchTerm.toLowerCase());
            country.style.display = shouldShow ? 'block' : 'none';
        });
    }

    static startPeriodicUpdates() {
        setInterval(() => {
            this.loadInitialData();
        }, 5 * 60 * 1000); // 5 minutes
    }

    static async fetchData(endpoint) {
        const response = await fetch(endpoint);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
    }

    static showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${type === 'success' ? 'bg-green-500 text-white' :
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

    static showError(message) {
        console.error('🚨', message);
        this.showNotification(message, 'error');
    }

    static showErrorState() {
        const containers = ['travel-advice-results', 'sdr-stats', 'economic-indicators'];
        containers.forEach(id => {
            const container = document.getElementById(id);
            if (container) {
                container.innerHTML = `
                    <div class="text-center py-8 text-gray-500">
                        <i class="fas fa-exclamation-triangle text-3xl mb-3"></i>
                        <p>Erreur de chargement des données</p>
                    </div>
                `;
            }
        });
    }

    // Nettoyage
    static destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
        if (this.economicChart) {
            this.economicChart.destroy();
        }
    }
}

// Initialisation automatique
if (window.location.pathname.includes('/weak-indicators')) {
    document.addEventListener('DOMContentLoaded', function () {
        console.log('🎯 Page indicateurs faibles détectée');
        WeakIndicatorsManager.initialize();
    });
}

// Exposer globalement
window.WeakIndicatorsManager = WeakIndicatorsManager;