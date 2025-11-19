// static/js/archiviste-enhanced.js - VERSION CORRIGÉE AVEC GESTION D'ERREURS

class EnhancedArchivisteManager {
    constructor() {
        console.log("🎯 EnhancedArchivisteManager initialisé");
        this.initialized = false;
        this.init();
    }

    init() {
        console.log("📚 Initialisation EnhancedArchivisteManager...");

        // Attendre que le DOM soit prêt pour les sélecteurs
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.initializeComponents();
            });
        } else {
            this.initializeComponents();
        }
    }

    initializeComponents() {
        console.log("🔧 Initialisation des composants...");
        this.loadPeriods();
        this.loadThemes();
        this.loadStats();
        this.initialized = true;
    }

    loadPeriods() {
        console.log("📅 Enhanced - Chargement des périodes historiques...");

        // Périodes prédéfinies
        const periods = [
            { key: '1945-1950', name: 'Après-guerre (1945-1950)' },
            { key: '1950-1960', name: 'Guerre froide débuts (1950-1960)' },
            { key: '1960-1970', name: 'Décolonisation (1960-1970)' },
            { key: '1970-1980', name: 'Détente (1970-1980)' },
            { key: '1980-1990', name: 'Fin guerre froide (1980-1990)' },
            { key: '1990-2000', name: 'Nouvel ordre mondial (1990-2000)' },
            { key: '2000-2010', name: 'Post-11/09 (2000-2010)' },
            { key: '2010-2020', name: 'Printemps arabes/Crise (2010-2020)' },
            { key: '2020-2025', name: 'Pandémie/IA (2020-2025)' }
        ];

        // Peupler le selecteur de périodes
        this.populatePeriodSelect(periods);
        console.log("✅ Périodes chargées:", periods.length);
        return periods;
    }

    populatePeriodSelect(periods) {
        try {
            const select = document.getElementById('archiviste-period-select');
            if (select) {
                select.innerHTML = '<option value="">Sélectionnez une période...</option>';
                periods.forEach(period => {
                    const option = document.createElement('option');
                    option.value = period.key;
                    option.textContent = period.name;
                    select.appendChild(option);
                });
                console.log("✅ Selecteur de périodes peuplé");
            } else {
                console.log("ℹ️ Element archiviste-period-select non trouvé (peut être normal si pas sur la page archiviste)");
            }
        } catch (error) {
            console.error("❌ Erreur populatePeriodSelect:", error);
        }
    }

    loadThemes() {
        console.log("🎨 Enhanced - Chargement des thèmes...");

        // Essayer l'API d'abord
        if (typeof ApiClient !== 'undefined' && ApiClient.get) {
            ApiClient.get('/archiviste/api/themes')
                .then(response => {
                    if (response && response.success) {
                        console.log("✅ Thèmes chargés via API:", response.themes.length);
                        this.populateThemeSelect(response.themes);
                    } else {
                        throw new Error('Réponse API invalide');
                    }
                })
                .catch(error => {
                    console.warn("⚠️ API non disponible, utilisation du fallback:", error);
                    this.loadThemesFallback();
                });
        } else {
            console.warn("⚠️ ApiClient non disponible, utilisation du fallback");
            this.loadThemesFallback();
        }
    }

    loadThemesFallback() {
        console.log("🔄 Chargement fallback des thèmes...");
        // Données de fallback
        const fallbackThemes = [
            { id: 1, name: 'Géopolitique', keywords: ['politique', 'international', 'diplomatie'] },
            { id: 2, name: 'Conflits', keywords: ['guerre', 'conflit', 'tensions'] },
            { id: 3, name: 'Économie', keywords: ['économie', 'commerce', 'finance'] }
        ];
        this.populateThemeSelect(fallbackThemes);
    }

    populateThemeSelect(themes) {
        try {
            const select = document.getElementById('archiviste-theme-select');
            if (select) {
                select.innerHTML = '<option value="">Sélectionnez un thème...</option>';
                themes.forEach(theme => {
                    const option = document.createElement('option');
                    // ✅ S'assurer que l'ID est bien un nombre
                    option.value = theme.id.toString();  // Convertir en string pour le HTML
                    option.textContent = theme.name;
                    option.dataset.themeId = theme.id;   // Stocker l'ID numérique
                    select.appendChild(option);
                });
                console.log("✅ Selecteur de thèmes peuplé");
            } else {
                console.log("ℹ️ Element archiviste-theme-select non trouvé");
            }
        } catch (error) {
            console.error("❌ Erreur populateThemeSelect:", error);
        }
    }

    loadStats() {
        console.log("📊 Enhanced - Chargement des statistiques...");

        if (typeof ApiClient !== 'undefined' && ApiClient.get) {
            ApiClient.get('/archiviste/api/stats')
                .then(response => {
                    if (response && response.success) {
                        console.log("✅ Stats chargées via API");
                        this.displayStats(response.stats || {});
                    } else {
                        throw new Error('Réponse API invalide');
                    }
                })
                .catch(error => {
                    console.warn("⚠️ API stats non disponible, utilisation des stats par défaut:", error);
                    this.displayStats({
                        total_analyses: 0,
                        available_periods: 9,
                        available_themes: 3,
                        recent_analyses: []
                    });
                });
        } else {
            console.warn("⚠️ ApiClient non disponible pour les stats");
            this.displayStats({
                total_analyses: 0,
                available_periods: 9,
                available_themes: 3,
                recent_analyses: []
            });
        }
    }

    displayStats(stats) {
        try {
            const statsElement = document.getElementById('stats-content');
            if (statsElement) {
                statsElement.innerHTML = `
                    <div class="grid grid-cols-2 gap-4">
                        <div class="bg-blue-500/20 p-3 rounded-lg text-center border border-blue-400/30">
                            <div class="text-xl font-bold text-blue-300">${stats.total_analyses || 0}</div>
                            <div class="text-sm text-blue-200">Analyses</div>
                        </div>
                        <div class="bg-green-500/20 p-3 rounded-lg text-center border border-green-400/30">
                            <div class="text-xl font-bold text-green-300">${stats.available_periods || 9}</div>
                            <div class="text-sm text-green-200">Périodes</div>
                        </div>
                        <div class="bg-purple-500/20 p-3 rounded-lg text-center border border-purple-400/30">
                            <div class="text-xl font-bold text-purple-300">${stats.available_themes || 3}</div>
                            <div class="text-sm text-purple-200">Thèmes</div>
                        </div>
                        <div class="bg-orange-500/20 p-3 rounded-lg text-center border border-orange-400/30">
                            <div class="text-xl font-bold text-orange-300">${stats.recent_analyses ? stats.recent_analyses.length : 0}</div>
                            <div class="text-sm text-orange-200">Récentes</div>
                        </div>
                    </div>
                    ${stats.total_analyses === 0 ?
                        '<p class="text-center text-blue-300 mt-4">🎯 Aucune analyse effectuée yet</p>' :
                        ''
                    }
                `;
            }
        } catch (error) {
            console.error("❌ Erreur displayStats:", error);
        }
    }

    // MÉTHODES STATIQUES
    static showArchivistePanel() {
        console.log("🎯 EnhancedArchivisteManager.showArchivistePanel() appelé");
        window.location.href = '/archiviste';
    }

    static analyzePeriod(periodKey, themeId) {
        console.log(`🔍 Enhanced - Analyse période: ${periodKey}, thème ID: ${themeId}`);

        // ✅ CORRECTION : Gérer les IDs qui peuvent être des chaînes ou des nombres
        let numericThemeId;
        if (typeof themeId === 'string') {
            // Si c'est une chaîne qui représente un nombre
            if (!isNaN(themeId) && !isNaN(parseFloat(themeId))) {
                numericThemeId = parseInt(themeId);
            } else {
                // Si c'est un slug ou un nom, il faut le convertir
                console.warn("⚠️ Theme ID est une chaîne, tentative de conversion...");
                // Pour l'instant, on retourne une erreur claire
                this.displayAnalysisResult({
                    success: false,
                    error: `ID de thème invalide: ${themeId} (doit être un nombre)`
                });
                return;
            }
        } else {
            numericThemeId = parseInt(themeId);
        }

        if (isNaN(numericThemeId)) {
            console.error("❌ Theme ID invalide:", themeId);
            this.displayAnalysisResult({
                success: false,
                error: 'ID de thème invalide'
            });
            return;
        }

        if (typeof ApiClient !== 'undefined' && ApiClient.post) {
            ApiClient.post('/archiviste/api/analyze-period', {
                period_key: periodKey,
                theme_id: numericThemeId  // ✅ Maintenant un nombre valide
            })
                .then(result => {
                    console.log("✅ Analyse terminée:", result);
                    this.displayAnalysisResult(result);
                })
                .catch(error => {
                    console.error("❌ Erreur analyse:", error);
                    this.displayAnalysisResult({
                        success: false,
                        error: 'Erreur lors de l\'analyse: ' + (error.message || 'Erreur inconnue')
                    });
                });
        } else {
            this.displayAnalysisResult({
                success: false,
                error: 'Fonctionnalité d\'analyse non disponible (ApiClient manquant)'
            });
        }
    }


    static displayAnalysisResult(result) {
        try {
            const resultsElement = document.getElementById('analysis-results');
            const contentElement = document.getElementById('results-content');

            if (resultsElement && contentElement) {
                if (result.success) {
                    contentElement.innerHTML = `
                        <div class="bg-green-500/20 border border-green-400/30 rounded-xl p-6 mb-6">
                            <h3 class="text-xl font-bold text-green-300 mb-2">✅ Analyse réussie</h3>
                            <p class="text-green-200 text-lg">${result.period?.name || 'Période'} - ${result.theme?.name || 'Thème'}</p>
                            <p class="text-green-100">${result.items_analyzed || 0} items analysés</p>
                        </div>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div class="bg-white/10 border border-white/20 rounded-xl p-4">
                                <h4 class="font-semibold text-white mb-3">📊 Métriques</h4>
                                <p class="text-blue-200">Items analysés: ${result.statistics?.total_items || 0}</p>
                                <p class="text-blue-200">Pertinence: ${result.statistics?.relevance_metrics?.average_relevance || 'N/A'}</p>
                            </div>
                            <div class="bg-white/10 border border-white/20 rounded-xl p-4">
                                <h4 class="font-semibold text-white mb-3">🎯 Couverture</h4>
                                <p class="text-purple-200">Mots-clés: ${result.theme_coverage?.covered_keywords || 'N/A'}/${result.theme_coverage?.total_keywords || 'N/A'}</p>
                                <p class="text-purple-200">Couverture: ${result.theme_coverage?.coverage_percent || 'N/A'}%</p>
                            </div>
                        </div>
                    `;
                } else {
                    contentElement.innerHTML = `
                        <div class="bg-red-500/20 border border-red-400/30 rounded-xl p-6">
                            <h3 class="text-xl font-bold text-red-300 mb-2">❌ Erreur d'analyse</h3>
                            <p class="text-red-200">${result.error || 'Erreur inconnue lors de l\'analyse'}</p>
                        </div>
                    `;
                }

                resultsElement.classList.remove('hidden');
                resultsElement.scrollIntoView({ behavior: 'smooth' });
            }
        } catch (error) {
            console.error("❌ Erreur displayAnalysisResult:", error);
        }
    }

    // Méthodes proxy pour compatibilité
    static getInstance() {
        if (!window._enhancedArchivisteInstance) {
            window._enhancedArchivisteInstance = new EnhancedArchivisteManager();
        }
        return window._enhancedArchivisteInstance;
    }

    static loadPeriods() {
        const instance = this.getInstance();
        return instance.loadPeriods();
    }

    static loadThemes() {
        const instance = this.getInstance();
        return instance.loadThemes();
    }

    static loadStats() {
        const instance = this.getInstance();
        return instance.loadStats();
    }
}

// Initialisation automatique
document.addEventListener('DOMContentLoaded', function () {
    window.EnhancedArchivisteManager = EnhancedArchivisteManager;
    window.EnhancedArchivisteManager.getInstance();
    console.log("✅ EnhancedArchivisteManager initialisé et prêt");
});