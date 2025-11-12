// static/js/dashboard.js - VERSION UNIFIÉE COMPLÈTE

class UnifiedDashboard {
    static currentView = 'themes';
    static autoRefreshInterval = null;
    static realTimeData = {
        themes: { count: 0, trends: [] },
        articles: { total: 0, recent: [] },
        sentiment: { average: 0, distribution: {} },
        social: { posts: 0, factorZ: 0, comparison: {} },
        archiviste: { analyses: 0, periods: [] },
        weakIndicators: { alerts: 0, countries: 0 }
    };

    // ===== INITIALISATION =====
    static async initialize() {
        console.log('🚀 Initialisation Dashboard Unifié GEOPOL - 4 Modules...');

        try {
            await this.loadInitialData();
            this.setupEventListeners();
            this.startRealTimeUpdates();
            this.initializeNavigation();

            console.log('✅ Dashboard unifié initialisé (4 modules)');
        } catch (error) {
            console.error('❌ Erreur initialisation dashboard:', error);
            this.showError('Erreur lors du chargement du dashboard');
        }
    }

    static async loadInitialData() {
        try {
            // Chargement parallèle de toutes les données des 4 modules
            await Promise.all([
                this.loadThemeStats(),
                this.loadArticleStats(),
                this.loadSentimentOverview(),
                this.loadSocialOverview(),
                this.loadArchivisteOverview(),
                this.loadWeakIndicatorsOverview()
            ]);

            this.updateAllDisplays();
        } catch (error) {
            console.error('Erreur chargement données initiales:', error);
        }
    }

    // ===== NAVIGATION UNIFIÉE - 4 MODULES =====
    static initializeNavigation() {
        // Navigation par hash URL
        window.addEventListener('hashchange', () => {
            this.handleRouteChange();
        });

        // Navigation initiale
        this.handleRouteChange();

        // Boutons de navigation rapide
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-nav]')) {
                e.preventDefault();
                const target = e.target.getAttribute('data-nav');
                this.navigateTo(target);
            }
        });
    }

    static handleRouteChange() {
        const hash = window.location.hash.replace('#', '') || 'themes';
        this.navigateTo(hash);
    }

    static navigateTo(view) {
        // Masquer toutes les sections
        document.querySelectorAll('.dashboard-section').forEach(section => {
            section.classList.add('hidden');
        });

        // Désactiver tous les boutons de navigation
        document.querySelectorAll('[data-nav]').forEach(btn => {
            btn.classList.remove('bg-blue-600', 'text-white');
            btn.classList.add('bg-gray-200', 'text-gray-700');
        });

        // Activer la section cible
        const targetSection = document.getElementById(`${view}-section`);
        const targetButton = document.querySelector(`[data-nav="${view}"]`);

        if (targetSection) {
            targetSection.classList.remove('hidden');
        }

        if (targetButton) {
            targetButton.classList.remove('bg-gray-200', 'text-gray-700');
            targetButton.classList.add('bg-blue-600', 'text-white');
        }

        this.currentView = view;

        // Actions spécifiques selon la vue
        this.onViewChange(view);
    }

    static onViewChange(view) {
        switch (view) {
            case 'social':
                SocialAggregatorManager.loadStatistics();
                break;
            case 'archiviste':
                ArchivisteManager.loadHistoricalAnalyses();
                break;
            case 'weak-indicators':
                WeakIndicatorsManager.loadInitialData();
                break;
            case 'themes':
                this.loadThemeStats();
                break;
        }
    }

    // ===== CHARGEMENT DES DONNÉES - 4 MODULES =====

    // 1. THÈMES ET ARTICLES
    static async loadThemeStats() {
        try {
            const response = await fetch('/api/themes/statistics');
            if (response.ok) {
                const data = await response.json();
                this.realTimeData.themes = data;
                this.updateThemeDisplay();
            } else {
                console.warn('⚠️ API themes/statistics non disponible');
                this.realTimeData.themes = { count: 0, trends: [] };
                this.updateThemeDisplay();
            }
        } catch (error) {
            console.error('Erreur chargement thèmes:', error);
            this.realTimeData.themes = { count: 0, trends: [] };
            this.updateThemeDisplay();
        }
    }

    static async loadArticleStats() {
        try {
            const response = await fetch('/api/articles?limit=5'); // Correction de l'URL
            if (response.ok) {
                const data = await response.json();
                this.realTimeData.articles = data;
                this.updateArticleDisplay();
            } else {
                console.warn('⚠️ API articles non disponible');
                this.realTimeData.articles = { total: 0, recent: [] };
                this.updateArticleDisplay();
            }
        } catch (error) {
            console.error('Erreur chargement articles:', error);
            this.realTimeData.articles = { total: 0, recent: [] };
            this.updateArticleDisplay();
        }
    }

    static async loadSentimentOverview() {
        try {
            const response = await fetch('/api/sentiment'); // URL alternative
            if (response.ok) {
                const data = await response.json();
                this.realTimeData.sentiment = data;
                this.updateSentimentDisplay();
            } else {
                console.warn('⚠️ API sentiment non disponible');
                this.realTimeData.sentiment = { average: 0, distribution: {} };
                this.updateSentimentDisplay();
            }
        } catch (error) {
            console.error('Erreur chargement sentiment:', error);
            this.realTimeData.sentiment = { average: 0, distribution: {} };
            this.updateSentimentDisplay();
        }
    }

    static async loadWeakIndicatorsOverview() {
        try {
            // Essayer plusieurs endpoints possibles
            const endpoints = [
                '/api/weak-indicators/countries',
                '/api/weak-indicators/status',
                '/api/countries'  // Fallback
            ];

            let data = null;
            for (const endpoint of endpoints) {
                try {
                    const response = await fetch(endpoint);
                    if (response.ok) {
                        data = await response.json();
                        break;
                    }
                } catch (e) {
                    continue;
                }
            }

            if (data && Array.isArray(data)) {
                this.realTimeData.weakIndicators.countries = data.length;
            } else {
                this.realTimeData.weakIndicators.countries = 20; // Valeur par défaut
            }

            this.updateWeakIndicatorsDisplay();
        } catch (error) {
            console.error('Erreur chargement indicateurs faibles:', error);
            this.realTimeData.weakIndicators.countries = 20;
            this.updateWeakIndicatorsDisplay();
        }
    }

    // ===== AFFICHAGE DES DONNÉES - 4 MODULES =====

    // 1. THÈMES ET ARTICLES
    static updateThemeDisplay() {
        // Cartes de statistiques
        this.updateCard('total-themes', this.realTimeData.themes.count || 0);
        this.updateCard('trending-themes', this.realTimeData.themes.trends?.length || 0);

        // Liste des thèmes tendance
        const trendingContainer = document.getElementById('trending-themes-list');
        if (trendingContainer && this.realTimeData.themes.trends) {
            trendingContainer.innerHTML = this.realTimeData.themes.trends
                .slice(0, 5)
                .map(theme => `
                    <div class="flex justify-between items-center p-2 hover:bg-gray-50 rounded">
                        <span class="text-sm">${theme.name}</span>
                        <span class="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                            ${theme.article_count} articles
                        </span>
                    </div>
                `).join('');
        }
    }

    static updateArticleDisplay() {
        this.updateCard('total-articles', this.realTimeData.articles.total || 0);

        const recentContainer = document.getElementById('recent-articles-list');
        if (recentContainer && this.realTimeData.articles.recent) {
            recentContainer.innerHTML = this.realTimeData.articles.recent
                .map(article => `
                    <div class="border-l-4 border-blue-500 pl-3 py-2">
                        <div class="text-sm font-medium truncate">${article.title}</div>
                        <div class="text-xs text-gray-500">
                            ${new Date(article.pub_date).toLocaleDateString()} • 
                            <span class="capitalize">${article.sentiment_type}</span>
                        </div>
                    </div>
                `).join('');
        }
    }

    static updateSentimentDisplay() {
        const sentiment = this.realTimeData.sentiment;
        this.updateCard('avg-sentiment', sentiment.average ? sentiment.average.toFixed(3) : '0.000');

        // Distribution des sentiments
        const distContainer = document.getElementById('sentiment-distribution');
        if (distContainer && sentiment.distribution) {
            const dist = sentiment.distribution;
            distContainer.innerHTML = `
                <div class="flex justify-between text-sm mb-1">
                    <span>Positif</span>
                    <span>${dist.positive || 0} (${dist.positive_percent || 0}%)</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-2 mb-2">
                    <div class="bg-green-600 h-2 rounded-full" style="width: ${dist.positive_percent || 0}%"></div>
                </div>
                
                <div class="flex justify-between text-sm mb-1">
                    <span>Négatif</span>
                    <span>${dist.negative || 0} (${dist.negative_percent || 0}%)</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-2 mb-2">
                    <div class="bg-red-600 h-2 rounded-full" style="width: ${dist.negative_percent || 0}%"></div>
                </div>
                
                <div class="flex justify-between text-sm mb-1">
                    <span>Neutre</span>
                    <span>${dist.neutral || 0} (${dist.neutral_percent || 0}%)</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-2">
                    <div class="bg-gray-600 h-2 rounded-full" style="width: ${dist.neutral_percent || 0}%"></div>
                </div>
            `;
        }
    }

    // 2. RÉSEAUX SOCIAUX
    static updateSocialDisplay() {
        const social = this.realTimeData.social;

        this.updateCard('social-posts', social.total_posts || 0);
        this.updateCard('social-positive', social.sentiment_distribution?.positive || 0);
        this.updateCard('social-negative', social.sentiment_distribution?.negative || 0);

        // Facteur Z
        const factorZElement = document.getElementById('social-factor-z');
        if (factorZElement) {
            const factorZ = social.factorZ || 0;
            factorZElement.textContent = factorZ.toFixed(3);

            // Couleur selon l'intensité
            if (Math.abs(factorZ) > 2.5) {
                factorZElement.className = 'text-2xl font-bold text-red-600';
            } else if (Math.abs(factorZ) > 1.5) {
                factorZElement.className = 'text-2xl font-bold text-orange-600';
            } else {
                factorZElement.className = 'text-2xl font-bold text-green-600';
            }
        }
    }

    // 3. ARCHIVISTE
    static updateArchivisteDisplay() {
        const archiviste = this.realTimeData.archiviste;

        this.updateCard('historical-analyses', archiviste.analyses || 0);

        // Dernières analyses
        const recentContainer = document.getElementById('recent-historical-analyses');
        if (recentContainer && archiviste.periods) {
            if (archiviste.periods.length === 0) {
                recentContainer.innerHTML = '<p class="text-gray-500 text-sm">Aucune analyse récente</p>';
            } else {
                recentContainer.innerHTML = archiviste.periods
                    .map(analysis => `
                        <div class="border-l-4 border-amber-500 pl-3 py-2">
                            <div class="text-sm font-medium">${analysis.period_name}</div>
                            <div class="text-xs text-gray-500">
                                Score: ${analysis.avg_sentiment_score?.toFixed(3) || '0.000'} • 
                                ${analysis.total_items} articles
                            </div>
                        </div>
                    `).join('');
            }
        }
    }

    // 4. INDICATEURS FAIBLES
    static updateWeakIndicatorsDisplay() {
        const indicators = this.realTimeData.weakIndicators;

        this.updateCard('monitored-countries', indicators.countries || 0);
        this.updateCard('weak-indicator-alerts', indicators.alerts || 0);

        // Statut global
        const statusContainer = document.getElementById('weak-indicators-status');
        if (statusContainer) {
            if (indicators.alerts > 0) {
                statusContainer.innerHTML = `
                    <div class="bg-red-50 border border-red-200 rounded p-3">
                        <div class="flex items-center">
                            <i class="fas fa-exclamation-triangle text-red-600 mr-2"></i>
                            <span class="text-red-800 font-medium">${indicators.alerts} alertes actives</span>
                        </div>
                    </div>
                `;
            } else {
                statusContainer.innerHTML = `
                    <div class="bg-green-50 border border-green-200 rounded p-3">
                        <div class="flex items-center">
                            <i class="fas fa-check-circle text-green-600 mr-2"></i>
                            <span class="text-green-800">Situation normale</span>
                        </div>
                    </div>
                `;
            }
        }
    }

    // ===== COMPOSANTS DASHBOARD UNIFIÉS =====

    static updateAllDisplays() {
        this.updateThemeDisplay();
        this.updateArticleDisplay();
        this.updateSentimentDisplay();
        this.updateSocialDisplay();
        this.updateArchivisteDisplay();
        this.updateWeakIndicatorsDisplay();
    }

    static updateCard(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            // Animation de compteur
            const current = parseInt(element.textContent) || 0;
            this.animateCount(element, current, value);
        }
    }

    static animateCount(element, start, end, duration = 500) {
        const range = end - start;
        const startTime = performance.now();

        function updateCount(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // Easing function
            const easeOutQuart = 1 - Math.pow(1 - progress, 4);
            const currentValue = Math.floor(start + range * easeOutQuart);

            element.textContent = currentValue.toLocaleString('fr-FR');

            if (progress < 1) {
                requestAnimationFrame(updateCount);
            } else {
                element.textContent = end.toLocaleString('fr-FR');
            }
        }

        requestAnimationFrame(updateCount);
    }

    // ===== ACTIONS RAPIDES - 4 MODULES =====

    static setupEventListeners() {
        // Actions rapides sociales
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-action="fetch-social-posts"]')) {
                e.preventDefault();
                SocialAggregatorManager.fetchRecentPosts();
            }

            if (e.target.matches('[data-action="compare-social-rss"]')) {
                e.preventDefault();
                SocialAggregatorManager.compareWithRSS();
            }

            if (e.target.matches('[data-action="manage-social-instances"]')) {
                e.preventDefault();
                InstanceManager.showInstancePanel();
            }
        });

        // Actions rapides archiviste
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-action="analyze-historical-period"]')) {
                e.preventDefault();
                ArchivisteManager.showPeriodAnalysis();
            }

            if (e.target.matches('[data-action="compare-with-history"]')) {
                e.preventDefault();
                ArchivisteManager.compareWithHistory();
            }
        });

        // Actions rapides indicateurs faibles
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-action="scan-travel-advice"]')) {
                e.preventDefault();
                WeakIndicatorsManager.scanTravelAdvice();
            }

            if (e.target.matches('[data-action="update-economic-data"]')) {
                e.preventDefault();
                WeakIndicatorsManager.updateEconomicData();
            }
        });

        // Rafraîchissement manuel
        const refreshBtn = document.getElementById('refresh-dashboard');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadInitialData();
            });
        }
    }

    // ===== MISE À JOUR TEMPS RÉEL =====

    static startRealTimeUpdates() {
        // Arrêter l'intervalle existant
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
        }

        // Nouvel intervalle (toutes les 2 minutes)
        this.autoRefreshInterval = setInterval(() => {
            this.loadInitialData();
        }, 2 * 60 * 1000);

        console.log('🔄 Mise à jour temps réel activée (2min)');
    }

    static stopRealTimeUpdates() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
            this.autoRefreshInterval = null;
        }
    }

    // ===== UTILITAIRES =====

    static showError(message) {
        // Afficher une notification d'erreur
        const notification = document.createElement('div');
        notification.className = 'fixed top-4 right-4 bg-red-500 text-white p-4 rounded-lg shadow-lg z-50';
        notification.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-exclamation-triangle mr-2"></i>
                <span>${message}</span>
            </div>
        `;

        document.body.appendChild(notification);

        // Supprimer après 5 secondes
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    static showSuccess(message) {
        // Afficher une notification de succès
        const notification = document.createElement('div');
        notification.className = 'fixed top-4 right-4 bg-green-500 text-white p-4 rounded-lg shadow-lg z-50';
        notification.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-check-circle mr-2"></i>
                <span>${message}</span>
            </div>
        `;

        document.body.appendChild(notification);

        // Supprimer après 3 secondes
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    // ===== GESTION DES MODALES =====

    static showModal(modalId) {
        const modal = document.getElementById(modalId);
        const overlay = document.getElementById('modal-overlay');

        if (modal) {
            modal.classList.remove('hidden');
        }
        if (overlay) {
            overlay.classList.remove('hidden');
        }
    }

    static hideModal(modalId) {
        const modal = document.getElementById(modalId);
        const overlay = document.getElementById('modal-overlay');

        if (modal) {
            modal.classList.add('hidden');
        }
        if (overlay) {
            overlay.classList.add('hidden');
        }
    }
}

// ===== INITIALISATION AUTOMATIQUE =====

document.addEventListener('DOMContentLoaded', function () {
    // Initialiser le dashboard unifié
    UnifiedDashboard.initialize();

    // Exposer les managers globaux pour les boutons inline
    window.UnifiedDashboard = UnifiedDashboard;

    console.log('🎯 Dashboard GEOPOL 4-Modules prêt');
});

// ===== COMPATIBILITÉ AVEC L'EXISTANT =====

// Alias pour la compatibilité avec l'ancien code
window.DashboardManager = UnifiedDashboard;