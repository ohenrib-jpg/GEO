// static/js/alerts-management.js - VERSION CORRIGÉE

class AlertsManager {
    static currentAlerts = [];
    static triggeredAlerts = [];
    static editingAlert = null;

    // === CHARGEMENT INITIAL ===
    static async initialize() {
        console.log('🔔 Initialisation AlertsManager...');
        try {
            await this.loadAlerts();
            await this.loadTriggeredAlerts();
            this.setupEventListeners();
            this.startPeriodicAnalysis();
            console.log('✅ AlertsManager initialisé');
        } catch (error) {
            console.error('❌ Erreur init AlertsManager:', error);
        }
    }

    static async loadAlerts() {
        try {
            const response = await fetch('/api/alerts');
            if (response.ok) {
                this.currentAlerts = await response.json();
                this.renderAlertsList();
            }
        } catch (error) {
            console.error('Erreur chargement alertes:', error);
        }
    }

    static async loadTriggeredAlerts() {
        try {
            const response = await fetch('/api/alerts/triggered?hours=24');
            if (response.ok) {
                this.triggeredAlerts = await response.json();
                this.renderTriggeredAlerts();
                this.updateActiveAlertsCount();
            }
        } catch (error) {
            console.error('Erreur chargement alertes déclenchées:', error);
        }
    }

    // === GESTION DE L'INTERFACE ===

    static showAlertsModal() {
        const modal = document.getElementById('alertsModal');
        if (modal) {
            modal.classList.remove('hidden');
            this.loadAlerts();
        } else {
            console.error('Modal alertes non trouvé');
        }
    }

    static hideAlertsModal() {
        const modal = document.getElementById('alertsModal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    static renderAlertsList() {
        const container = document.getElementById('alertsList');
        if (!container) return;

        if (this.currentAlerts.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <i class="fas fa-bell text-4xl mb-3 opacity-50"></i>
                    <p>Aucune alerte configurée</p>
                    <button onclick="AlertsManager.showCreateAlertForm()" 
                            class="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                        Créer une alerte
                    </button>
                </div>
            `;
            return;
        }

        container.innerHTML = this.currentAlerts.map(alert => `
            <div class="border rounded-lg p-4 ${alert.active ? 'border-green-200 bg-green-50' : 'border-gray-200 bg-gray-50'}">
                <div class="flex justify-between items-start">
                    <div class="flex-1">
                        <h4 class="font-semibold text-gray-800">${alert.name}</h4>
                        ${alert.description ? `<p class="text-sm text-gray-600 mt-1">${alert.description}</p>` : ''}
                        <div class="flex flex-wrap gap-2 mt-2">
                            ${alert.keywords.map(keyword => `
                                <span class="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">${keyword}</span>
                            `).join('')}
                        </div>
                        <div class="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                            <span>Seuil: ${alert.threshold_count} articles</span>
                            <span>Période: ${alert.threshold_time_hours}h</span>
                            <span>Sensibilité: ${alert.sensitivity}</span>
                        </div>
                    </div>
                    <div class="flex items-center space-x-2">
                        <span class="px-2 py-1 rounded-full text-xs ${alert.active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}">
                            ${alert.active ? 'Active' : 'Inactive'}
                        </span>
                        <button onclick="AlertsManager.editAlert(${alert.id})" 
                                class="text-blue-600 hover:text-blue-800" title="Modifier">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button onclick="AlertsManager.toggleAlert(${alert.id}, ${!alert.active})" 
                                class="text-yellow-600 hover:text-yellow-800" title="${alert.active ? 'Désactiver' : 'Activer'}">
                            <i class="fas fa-${alert.active ? 'pause' : 'play'}"></i>
                        </button>
                        <button onclick="AlertsManager.deleteAlert(${alert.id})" 
                                class="text-red-600 hover:text-red-800" title="Supprimer">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `).join('');

        // Ajouter le bouton "Créer une alerte" si pas déjà présent
        if (!container.querySelector('.create-alert-btn')) {
            const createBtn = document.createElement('button');
            createBtn.className = 'create-alert-btn w-full mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700';
            createBtn.innerHTML = '<i class="fas fa-plus mr-2"></i>Créer une nouvelle alerte';
            createBtn.onclick = () => this.showCreateAlertForm();
            container.appendChild(createBtn);
        }
    }

    static renderTriggeredAlerts() {
        const container = document.getElementById('activeAlerts');
        if (!container) return;

        if (this.triggeredAlerts.length === 0) {
            container.innerHTML = '<p class="text-gray-500 text-sm">Aucune alerte déclenchée</p>';
            return;
        }

        container.innerHTML = this.triggeredAlerts.map(alert => `
            <div class="p-3 border-l-4 ${alert.severity === 'high' ? 'border-red-500 bg-red-50' :
                alert.severity === 'medium' ? 'border-yellow-500 bg-yellow-50' :
                    'border-blue-500 bg-blue-50'
            } rounded-r-lg">
                <div class="flex justify-between items-start">
                    <div>
                        <p class="font-medium text-gray-800">${alert.alert_name}</p>
                        <p class="text-sm text-gray-600 mt-1">${alert.article_count} articles trouvés (${alert.time_window_hours}h)</p>
                        <div class="flex flex-wrap gap-1 mt-2">
                            ${Object.entries(alert.keyword_counts || {}).map(([keyword, count]) => `
                                <span class="px-2 py-1 bg-white text-gray-700 text-xs rounded border">
                                    ${keyword}: ${count}
                                </span>
                            `).join('')}
                        </div>
                    </div>
                    <div class="text-right">
                        <span class="px-2 py-1 rounded-full text-xs font-medium ${alert.severity === 'high' ? 'bg-red-100 text-red-800' :
                alert.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-blue-100 text-blue-800'
            }">
                            ${alert.severity.toUpperCase()}
                        </span>
                        <p class="text-xs text-gray-500 mt-1">
                            ${new Date(alert.created_at).toLocaleString('fr-FR')}
                        </p>
                    </div>
                </div>
            </div>
        `).join('');
    }

    static updateActiveAlertsCount() {
        const count = this.triggeredAlerts.length;
        const element = document.getElementById('active-alerts');
        if (element) {
            element.textContent = count.toLocaleString('fr-FR');
        }
    }

    // === GESTION DES ALERTES ===

    static showCreateAlertForm() {
        const form = document.getElementById('alertForm');
        const modal = document.getElementById('alertsModal');
        if (form && modal) {
            form.reset();
            this.editingAlert = null;
            modal.querySelector('.modal-header h3').textContent = 'Créer une alerte';
            modal.classList.remove('hidden');
        }
    }

    static editAlert(alertId) {
        const alert = this.currentAlerts.find(a => a.id === alertId);
        if (!alert) return;

        const form = document.getElementById('alertForm');
        const modal = document.getElementById('alertsModal');
        if (form && modal) {
            // Remplir le formulaire
            form.querySelector('#alertName').value = alert.name;
            form.querySelector('#alertDescription').value = alert.description || '';
            form.querySelector('#alertKeywords').value = alert.keywords.join(', ');
            form.querySelector('#alertThreshold').value = alert.threshold_count;
            form.querySelector('#alertTimeWindow').value = alert.threshold_time_hours;
            form.querySelector('#alertSensitivity').value = alert.sensitivity;

            this.editingAlert = alertId;
            modal.querySelector('.modal-header h3').textContent = 'Modifier l\'alerte';
            modal.classList.remove('hidden');
        }
    }

    static async saveAlert(event) {
        event.preventDefault();

        const form = event.target;
        const formData = new FormData(form);

        const alertData = {
            name: formData.get('name'),
            description: formData.get('description'),
            keywords: formData.get('keywords').split(',').map(k => k.trim()).filter(k => k),
            threshold_count: parseInt(formData.get('threshold_count')),
            threshold_time_hours: parseInt(formData.get('threshold_time_hours')),
            sensitivity: formData.get('sensitivity'),
            categories: []
        };

        if (!alertData.name || alertData.keywords.length === 0) {
            alert('Le nom et au moins un mot-clé sont requis');
            return;
        }

        try {
            const url = this.editingAlert ? `/api/alerts/${this.editingAlert}` : '/api/alerts';
            const method = this.editingAlert ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(alertData)
            });

            if (response.ok) {
                this.hideAlertsModal();
                await this.loadAlerts();
                alert(this.editingAlert ? 'Alerte modifiée avec succès' : 'Alerte créée avec succès');
            } else {
                const error = await response.json();
                alert('Erreur: ' + (error.error || 'Erreur inconnue'));
            }
        } catch (error) {
            console.error('Erreur sauvegarde alerte:', error);
            alert('Erreur lors de la sauvegarde');
        }
    }

    static async toggleAlert(alertId, active) {
        try {
            const response = await fetch(`/api/alerts/${alertId}/toggle`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ active })
            });

            if (response.ok) {
                await this.loadAlerts();
            } else {
                alert('Erreur lors de la modification');
            }
        } catch (error) {
            console.error('Erreur toggle alerte:', error);
        }
    }

    static async deleteAlert(alertId) {
        if (!confirm('Êtes-vous sûr de vouloir supprimer cette alerte ?')) return;

        try {
            const response = await fetch(`/api/alerts/${alertId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                await this.loadAlerts();
                alert('Alerte supprimée avec succès');
            } else {
                alert('Erreur lors de la suppression');
            }
        } catch (error) {
            console.error('Erreur suppression alerte:', error);
        }
    }

    // === ANALYSE ===

    static async runAnalysis() {
        const button = document.querySelector('[onclick*="runAnalysis"]');
        if (!button) return;

        const originalText = button.innerHTML;
        try {
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Analyse en cours...';

            const response = await fetch('/api/alerts/analyze');
            if (response.ok) {
                const result = await response.json();
                this.triggeredAlerts = result.triggered_alerts;
                this.renderTriggeredAlerts();
                this.updateActiveAlertsCount();

                if (result.triggered_alerts.length > 0) {
                    alert(`${result.triggered_alerts.length} alerte(s) déclenchée(s) sur ${result.total_analyzed} articles`);
                } else {
                    alert('Aucune alerte déclenchée');
                }
            }
        } catch (error) {
            console.error('Erreur analyse:', error);
            alert('Erreur lors de l\'analyse');
        } finally {
            button.disabled = false;
            button.innerHTML = originalText;
        }
    }

    // === UTILITAIRES ===

    static setupEventListeners() {
        // Modal
        const modal = document.getElementById('alertsModal');
        if (modal) {
            const closeBtn = modal.querySelector('[data-close]');
            if (closeBtn) {
                closeBtn.addEventListener('click', () => this.hideAlertsModal());
            }
        }

        // Formulaire
        const form = document.getElementById('alertForm');
        if (form) {
            form.addEventListener('submit', (e) => this.saveAlert(e));
        }
    }

    static startPeriodicAnalysis() {
        // Analyse automatique toutes les 15 minutes
        setInterval(() => {
            this.runAnalysis();
        }, 15 * 60 * 1000);
    }
}

// Exposer globalement
window.AlertsManager = AlertsManager;
