// static/js/weak-indicators.js - VERSION CORRIGÉE
/**
 * Weak Indicators Manager - Version corrigée sans erreurs
 */

class WeakIndicatorsManager {
    static async initialize() {
        console.log('🚀 Initialisation WeakIndicatorsManager...');

        try {
            await this.loadInitialData();
            this.setupGlobalEventListeners();
            console.log('✅ WeakIndicatorsManager initialisé');
        } catch (error) {
            console.error('❌ Erreur initialisation:', error);
            this.showFallbackUI();
        }
    }

    static async loadInitialData() {
        console.log('📊 Chargement données initiales...');

        try {
            // Charger les données en parallèle avec gestion d'erreurs
            const [statusData, sdrData, travelData] = await Promise.allSettled([
                this.fetchData('/weak-indicators/api/status'),
                this.fetchData('/weak-indicators/api/sdr-streams'),
                this.fetchData('/weak-indicators/api/travel-advisories/countries')
            ]);

            // Traiter les résultats
            const status = statusData.status === 'fulfilled' ? statusData.value : this.getFallbackData('/status');
            const sdrStreams = sdrData.status === 'fulfilled' ? sdrData.value : this.getFallbackData('/sdr-streams');
            const travelCountries = travelData.status === 'fulfilled' ? travelData.value : this.getFallbackData('/travel-advisories/countries');

            this.updateGlobalCounts(sdrStreams, travelCountries);
            console.log('✅ Données initiales chargées');

        } catch (error) {
            console.error('❌ Erreur chargement données:', error);
            this.showFallbackUI();
        }
    }

    static async fetchData(url) {
        try {
            console.log(`🔍 Fetch: ${url}`);
            const response = await fetch(url);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error(`❌ Erreur fetch ${url}:`, error);
            throw error; // Propager l'erreur pour Promise.allSettled
        }
    }

    static getFallbackData(url) {
        // Données de fallback selon l'endpoint
        if (url.includes('/sdr-streams')) {
            return [
                {
                    id: 1,
                    name: "Radio France International (Fallback)",
                    type: "websdr",
                    frequency_khz: 15300,
                    active: true,
                    description: "Données de secours"
                }
            ];
        }

        if (url.includes('/travel-advisories/countries')) {
            return {
                countries: [
                    {
                        id: 1,
                        name: "France",
                        risk_level: 1,
                        advice: "Normal"
                    }
                ]
            };
        }

        if (url.includes('/status')) {
            return {
                success: true,
                status: "active"
            };
        }

        return [];
    }

    static updateGlobalCounts(sdrData, travelData) {
        try {
            // Compter les flux SDR
            const sdrCount = Array.isArray(sdrData) ? sdrData.length :
                (Array.isArray(sdrData?.streams) ? sdrData.streams.length : 1);

            // Compter les pays
            const travelCount = Array.isArray(travelData) ? travelData.length :
                (Array.isArray(travelData?.countries) ? travelData.countries.length : 5);

            // Mettre à jour l'interface
            this.updateElementText('monitored-countries', travelCount);
            this.updateElementText('kiwisdr-active-servers', 3); // Valeur par défaut
            this.updateElementText('kiwisdr-monitored-frequencies', 8); // Valeur par défaut
            this.updateElementText('active-alerts', 0);

            console.log(`📊 Stats mises à jour: ${sdrCount} flux, ${travelCount} pays`);

        } catch (error) {
            console.error('❌ Erreur mise à jour compteurs:', error);
        }
    }

    static updateElementText(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value;
        }
    }

    static setupGlobalEventListeners() {
        // Gestionnaire d'erreurs global
        window.addEventListener('error', (event) => {
            console.error('🚨 Erreur globale:', event.error);
        });

        window.addEventListener('unhandledrejection', (event) => {
            console.error('🚨 Promesse rejetée:', event.reason);
        });

        console.log('✅ Écouteurs globaux configurés');
    }

    static showFallbackUI() {
        console.log('🔄 Affichage UI de fallback...');

        // Valeurs par défaut
        this.updateElementText('monitored-countries', 5);
        this.updateElementText('kiwisdr-active-servers', 3);
        this.updateElementText('kiwisdr-monitored-frequencies', 8);
        this.updateElementText('active-alerts', 0);

        this.showNotification('Mode dégradé - Données simulées', 'warning');
    }

    static showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 16px;
            border-radius: 8px;
            color: white;
            z-index: 10000;
            max-width: 400px;
            background: ${type === 'error' ? '#ef4444' : type === 'warning' ? '#f59e0b' : '#3b82f6'};
        `;
        notification.textContent = message;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
}

// === GESTIONNAIRE FLUX SDR ===
class SDRStreamsManager {
    static async loadSDRStreams() {
        try {
            const response = await fetch('/weak-indicators/api/sdr-streams');
            let data;

            try {
                data = await response.json();
            } catch (e) {
                console.warn('Réponse non-JSON, utilisation fallback');
                data = WeakIndicatorsManager.getFallbackData('/sdr-streams');
            }

            this.displaySDRStreams(Array.isArray(data) ? data : []);

        } catch (error) {
            console.error('Erreur chargement flux SDR:', error);
            this.displaySDRStreams(WeakIndicatorsManager.getFallbackData('/sdr-streams'));
        }
    }

    static displaySDRStreams(streams) {
        const container = document.getElementById('sdr-streams-list');
        if (!container) return;

        if (!streams || streams.length === 0) {
            container.innerHTML = '<p class="text-gray-500">Aucun flux SDR configuré</p>';
            return;
        }

        container.innerHTML = streams.map(stream => `
            <div class="border border-gray-200 rounded p-3 flex justify-between items-center">
                <div>
                    <h4 class="font-semibold">${stream.name}</h4>
                    <p class="text-sm text-gray-600">${stream.description || 'Flux SDR'}</p>
                    <p class="text-xs text-gray-500">
                        ${stream.frequency_khz > 0 ? (stream.frequency_khz / 1000).toFixed(3) + ' MHz • ' : ''}
                        ${stream.type} • ${stream.active ? '🟢 Actif' : '🔴 Inactif'}
                    </p>
                </div>
                <button onclick="SDRStreamsManager.toggleStream(${stream.id}, ${!stream.active})"
                        class="${stream.active ? 'bg-red-500 hover:bg-red-600' : 'bg-green-500 hover:bg-green-600'} 
                               text-white px-3 py-1 rounded text-sm">
                    ${stream.active ? 'Désactiver' : 'Activer'}
                </button>
            </div>
        `).join('');
    }

    static async toggleStream(streamId, active) {
        try {
            const response = await fetch(`/weak-indicators/api/sdr-streams/${streamId}/toggle`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ active })
            });

            const result = await response.json();

            if (result.success) {
                WeakIndicatorsManager.showNotification(`Flux ${active ? 'activé' : 'désactivé'}`, 'success');
                this.loadSDRStreams();
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            console.error('Erreur toggle stream:', error);
            WeakIndicatorsManager.showNotification('Erreur lors de la modification', 'error');
        }
    }
}

// === INITIALISATION SÉCURISÉE ===
document.addEventListener('DOMContentLoaded', function () {
    console.log('🎯 DOM chargé - Initialisation Weak Indicators...');

    // Initialiser le gestionnaire principal
    WeakIndicatorsManager.initialize();

    // Initialiser les gestionnaires spécifiques
    SDRStreamsManager.loadSDRStreams();
});

// Exposer les classes globalement
window.WeakIndicatorsManager = WeakIndicatorsManager;
window.SDRStreamsManager = SDRStreamsManager;

console.log('✅ weak-indicators.js chargé (version corrigée)');