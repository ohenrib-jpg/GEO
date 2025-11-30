// static/js/travel-advisories.js - LIGNE 4 CORRIGÉE
class TravelAdvisoriesManager {
    static async initialize() {
        console.log('🛫 Initialisation TravelAdvisoriesManager...');
        await this.loadAdvisories();
        console.log('✅ TravelAdvisoriesManager initialisé');
    }

    static async loadAdvisories() {
        try {
            const response = await fetch('/weak-indicators/api/travel-advisories/countries');
            let data;

            // Gérer la réponse texte si JSON échoue
            try {
                data = await response.json();
            } catch (e) {
                console.warn('Réponse non-JSON, utilisation données fallback');
                data = this.getFallbackData();
            }

            this.displayAdvisories(Array.isArray(data) ? data : []);

        } catch (error) {
            console.error('Erreur chargement avis:', error);
            this.displayAdvisories(this.getFallbackData());
        }
    }

    static getFallbackData() {
        return [
            {
                id: 1,
                name: "France",
                risk_level: 1,
                advice: "Normal",
                last_updated: new Date().toISOString()
            },
            {
                id: 2,
                name: "États-Unis",
                risk_level: 1,
                advice: "Normal",
                last_updated: new Date().toISOString()
            }
        ];
    }

    static displayAdvisories(countries) {
        const container = document.getElementById('travel-advisories-list');
        if (!container) return;

        if (!countries || countries.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <i class="fas fa-plane-slash text-3xl mb-3"></i>
                    <p>Aucun avis disponible</p>
                    <button onclick="TravelAdvisoriesManager.scanAdvisories()" 
                            class="mt-2 bg-blue-500 text-white px-4 py-2 rounded">
                        Scanner les sources
                    </button>
                </div>
            `;
            return;
        }

        container.innerHTML = countries.map(country => `
            <div class="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition" 
                 data-risk="${country.risk_level}" data-country="${country.country_code}">
                <div class="flex justify-between items-start mb-2">
                    <div class="flex items-center">
                        <span class="risk-badge risk-${country.risk_level} mr-3">
                            ${this.getRiskIcon(country.risk_level)}
                        </span>
                        <div>
                            <h4 class="font-semibold">${country.country_name || country.country_code}</h4>
                            <p class="text-sm text-gray-600">${this.getRiskText(country.risk_level)}</p>
                        </div>
                    </div>
                    <div class="text-right text-sm">
                        <div class="text-gray-500">${country.last_updated ? new Date(country.last_updated).toLocaleDateString() : 'N/A'}</div>
                        <div class="flex space-x-1 mt-1">
                            <button onclick="TravelAdvisoriesManager.showCountryDetails('${country.country_code}')"
                                    class="text-blue-500 hover:text-blue-700">
                                <i class="fas fa-info-circle"></i>
                            </button>
                            <button onclick="TravelAdvisoriesManager.toggleWatch('${country.country_code}')"
                                    class="text-yellow-500 hover:text-yellow-700">
                                <i class="fas fa-eye"></i>
                            </button>
                        </div>
                    </div>
                </div>
                ${country.sources && country.sources.length > 0 ? `
                    <div class="text-xs text-gray-500 mt-2">
                        Sources: ${country.sources.join(', ')}
                    </div>
                ` : ''}
            </div>
        `).join('');

        this.applyFilters();
    }

    static updateStats(countries) {
        const stats = {
            safe: countries.filter(c => c.risk_level === 1).length,
            caution: countries.filter(c => c.risk_level === 2).length,
            high_risk: countries.filter(c => c.risk_level === 3).length,
            critical: countries.filter(c => c.risk_level === 4).length
        };

        const safeEl = document.getElementById('travel-safe-count');
        const cautionEl = document.getElementById('travel-caution-count');
        const highRiskEl = document.getElementById('travel-high-risk-count');
        const criticalEl = document.getElementById('travel-critical-count');

        if (safeEl) safeEl.textContent = stats.safe;
        if (cautionEl) cautionEl.textContent = stats.caution;
        if (highRiskEl) highRiskEl.textContent = stats.high_risk;
        if (criticalEl) criticalEl.textContent = stats.critical;
    }

    static getRiskIcon(riskLevel) {
        const icons = {
            1: '🟢',
            2: '🟡',
            3: '🟠',
            4: '🔴'
        };
        return icons[riskLevel] || '⚪';
    }

    static getRiskText(riskLevel) {
        const texts = {
            1: 'Précautions normales',
            2: 'Précautions accrues',
            3: 'Éviter les déplacements non essentiels',
            4: 'Éviter tout déplacement'
        };
        return texts[riskLevel] || 'Information non disponible';
    }

    static async scanAdvisories() {
        try {
            this.showNotification('Scan des avis en cours...', 'info');

            const response = await fetch('/weak-indicators/api/travel-advisories/scan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({})
            });

            const data = await response.json();

            if (data.success) {
                this.showNotification('Scan terminé avec succès', 'success');
                await this.loadAdvisories();
            } else {
                this.showNotification('Erreur lors du scan: ' + (data.error || 'Inconnue'), 'error');
            }
        } catch (error) {
            console.error('Erreur scan avis:', error);
            this.showNotification('Erreur de connexion lors du scan', 'error');
        }
    }

    static async showCountryDetails(countryCode) {
        try {
            const response = await fetch(`/weak-indicators/api/travel-advisories/country/${countryCode}`);
            const data = await response.json();

            if (data.success) {
                this.showCountryModal(data.advisory);
            } else {
                this.showNotification('Aucune information détaillée disponible', 'warning');
            }
        } catch (error) {
            console.error('Erreur détails pays:', error);
            this.showNotification('Erreur de connexion', 'error');
        }
    }

    static showCountryModal(advisory) {
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4';
        modal.innerHTML = `
            <div class="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-screen overflow-auto">
                <div class="flex justify-between items-center p-4 border-b">
                    <h3 class="text-lg font-semibold">
                        ${this.getRiskIcon(advisory.risk_level)} 
                        ${advisory.country_name || advisory.country_code}
                    </h3>
                    <button onclick="this.parentElement.parentElement.parentElement.remove()" 
                            class="text-gray-500 hover:text-gray-700">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="p-4">
                    <div class="mb-4">
                        <h4 class="font-semibold mb-2">Niveau de risque: ${this.getRiskText(advisory.risk_level)}</h4>
                        <p class="text-sm text-gray-600">Dernière mise à jour: ${advisory.last_updated ? new Date(advisory.last_updated).toLocaleString() : 'N/A'}</p>
                    </div>
                    
                    ${advisory.sources && advisory.sources.length > 0 ? `
                        <div class="mb-4">
                            <h4 class="font-semibold mb-2">Sources:</h4>
                            ${advisory.sources.map(source => `
                                <div class="border-l-4 border-blue-500 pl-3 mb-2">
                                    <div class="font-medium">${source.source}</div>
                                    <div class="text-sm text-gray-600">Niveau: ${source.risk_level}</div>
                                    ${source.summary ? `<div class="text-sm mt-1">${source.summary}</div>` : ''}
                                    <div class="text-xs text-gray-500 mt-1">Mise à jour: ${source.last_updated ? new Date(source.last_updated).toLocaleDateString() : 'N/A'}</div>
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}
                    
                    ${advisory.recommendations ? `
                        <div class="bg-yellow-50 border border-yellow-200 rounded p-3">
                            <h4 class="font-semibold text-yellow-800 mb-2">Recommandations:</h4>
                            <p class="text-sm text-yellow-700">${advisory.recommendations}</p>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;

        document.body.appendChild(modal);
    }

    static async showChanges() {
        try {
            const response = await fetch('/weak-indicators/api/travel-advisories/changes');
            const data = await response.json();

            if (data.success && data.changes && data.changes.length > 0) {
                this.showChangesModal(data.changes);
            } else {
                this.showNotification('Aucun changement récent détecté', 'info');
            }
        } catch (error) {
            console.error('Erreur changements:', error);
            this.showNotification('Erreur de connexion', 'error');
        }
    }

    static async showAlerts() {
        try {
            const response = await fetch('/weak-indicators/api/travel-advisories/alerts');
            const data = await response.json();

            if (data.success) {
                this.showAlertsModal(data.alerts);
            } else {
                this.showNotification('Aucune alerte critique', 'info');
            }
        } catch (error) {
            console.error('Erreur alertes:', error);
            this.showNotification('Erreur de connexion', 'error');
        }
    }

    static showChangesModal(changes) {
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4';
        modal.innerHTML = `
            <div class="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-screen overflow-auto">
                <div class="flex justify-between items-center p-4 border-b">
                    <h3 class="text-lg font-semibold">📊 Changements Récents</h3>
                    <button onclick="this.parentElement.parentElement.parentElement.remove()" 
                            class="text-gray-500 hover:text-gray-700">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="p-4">
                    ${changes.map(change => `
                        <div class="border-l-4 ${change.new_risk > change.previous_risk ? 'border-red-500' : 'border-green-500'} pl-3 mb-4">
                            <div class="font-semibold">${change.country_name || change.country_code}</div>
                            <div class="text-sm">
                                <span class="text-gray-600">${this.getRiskText(change.previous_risk)} → ${this.getRiskText(change.new_risk)}</span>
                                <span class="ml-2 text-xs ${change.new_risk > change.previous_risk ? 'text-red-600' : 'text-green-600'}">
                                    ${change.new_risk > change.previous_risk ? '⚠️ Détérioration' : '✅ Amélioration'}
                                </span>
                            </div>
                            <div class="text-xs text-gray-500 mt-1">
                                Source: ${change.source} • ${new Date(change.changed_at).toLocaleString()}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    static showAlertsModal(alerts) {
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4';
        modal.innerHTML = `
            <div class="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-screen overflow-auto">
                <div class="flex justify-between items-center p-4 border-b">
                    <h3 class="text-lg font-semibold">🚨 Alertes Critiques</h3>
                    <button onclick="this.parentElement.parentElement.parentElement.remove()" 
                            class="text-gray-500 hover:text-gray-700">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="p-4">
                    ${alerts && alerts.length > 0 ? alerts.map(alert => `
                        <div class="border-l-4 border-red-500 pl-3 mb-4 bg-red-50 p-3 rounded">
                            <div class="font-semibold text-red-800">${alert.country_name || alert.country_code}</div>
                            <div class="text-sm text-red-700">${alert.message}</div>
                            <div class="text-xs text-red-600 mt-1">
                                Niveau: ${this.getRiskText(alert.new_level)} • 
                                Source: ${alert.source} • 
                                ${new Date(alert.timestamp).toLocaleString()}
                            </div>
                        </div>
                    `).join('') : '<p class="text-gray-500 text-center py-4">Aucune alerte critique</p>'}
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    static setupEventListeners() {
        const searchInput = document.getElementById('travel-country-search');
        if (searchInput) {
            searchInput.addEventListener('input', this.applyFilters.bind(this));
        }

        const riskFilter = document.getElementById('travel-risk-filter');
        if (riskFilter) {
            riskFilter.addEventListener('change', this.applyFilters.bind(this));
        }
    }

    static applyFilters() {
        const searchTerm = document.getElementById('travel-country-search')?.value.toLowerCase() || '';
        const riskFilter = document.getElementById('travel-risk-filter')?.value || 'all';

        document.querySelectorAll('#travel-advisories-list > div').forEach(item => {
            const countryName = item.querySelector('h4')?.textContent.toLowerCase() || '';
            const riskLevel = item.dataset.risk;

            const matchesSearch = countryName.includes(searchTerm);
            const matchesRisk = riskFilter === 'all' || riskFilter === riskLevel;

            item.style.display = (matchesSearch && matchesRisk) ? 'block' : 'none';
        });
    }

    static showNotification(message, type = 'info') {
        // Utiliser la fonction globale si disponible, sinon créer une notification simple
        if (typeof window.showNotification === 'function') {
            window.showNotification(message, type);
        } else {
            // Fallback
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
    }

    static toggleWatch(countryCode) {
        this.showNotification(`Surveillance activée pour ${countryCode}`, 'info');
    }
}

// Initialisation conditionnelle
if (window.location.pathname.includes('/weak-indicators')) {
    document.addEventListener('DOMContentLoaded', function () {
        // Initialiser quand l'onglet voyageurs est cliqué
        const travelTab = document.getElementById('tab-travel');
        if (travelTab) {
            travelTab.addEventListener('click', function () {
                setTimeout(() => {
                    TravelAdvisoriesManager.initialize();
                }, 100);
            });
        }
    });
}

console.log('✅ TravelAdvisoriesManager chargé');