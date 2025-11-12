// static/js/feeds.js - Gestion des flux RSS et analyse

class FeedManager {
    static defaultFeeds = [
        'https://feeds.bbci.co.uk/news/rss.xml',
        'https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml',
        'https://feeds.lemonde.fr/c/205/f/3050/index.rss',
        'https://www.lefigaro.fr/rss/figaro_actualites.xml',
        'https://www.liberation.fr/arc/outboundfeeds/rss-all/',
        'https://www.francetvinfo.fr/titres.rss',
        'https://www.20minutes.fr/feeds/rss-une.xml'
    ];

    constructor() {
        this.currentFeeds = [];
        this.isUpdating = false;
    }

    static init() {
        this.setupEventListeners();
        this.loadSavedFeeds();
        this.loadQuickStats(); // Charger les stats au démarrage
    }

    static setupEventListeners() {
        // Bouton de scraping (analyse)
        const scrapeBtn = document.getElementById('scrapeFeedsBtn');
        if (scrapeBtn) {
            scrapeBtn.addEventListener('click', () => this.startScraping());
        }

        // Bouton de mise à jour classique
        const updateBtn = document.getElementById('updateFeedsBtn');
        if (updateBtn) {
            updateBtn.addEventListener('click', () => this.updateFeeds());
        }

        // Bouton de chargement des flux par défaut
        const loadDefaultBtn = document.getElementById('loadDefaultFeedsBtn');
        if (loadDefaultBtn) {
            loadDefaultBtn.addEventListener('click', () => this.loadDefaultFeeds());
        }

        // Sauvegarde automatique lors de la modification des URLs
        const feedsTextarea = document.getElementById('feedUrls');
        if (feedsTextarea) {
            feedsTextarea.addEventListener('input', () => this.saveFeeds());
        }
    }

    static loadSavedFeeds() {
        const savedFeeds = localStorage.getItem('savedFeeds');
        if (savedFeeds) {
            const feedsTextarea = document.getElementById('feedUrls');
            if (feedsTextarea) {
                feedsTextarea.value = savedFeeds;
            }
        }
    }

    static saveFeeds() {
        const feedsTextarea = document.getElementById('feedUrls');
        if (feedsTextarea) {
            localStorage.setItem('savedFeeds', feedsTextarea.value);
        }
    }

    static loadDefaultFeeds() {
        const feedsTextarea = document.getElementById('feedUrls');
        if (feedsTextarea) {
            feedsTextarea.value = this.defaultFeeds.join('\n');
            this.showResult('Flux par défaut chargés avec succès!', 'success');
            this.saveFeeds();
        }
    }

    static async startScraping() {
        const feedUrls = this.getFeedUrls();
        if (feedUrls.length === 0) {
            this.showResult('Veuillez entrer au moins un flux RSS', 'error');
            return;
        }

        this.saveFeeds();
        await this.updateFeeds();
    }

    static async updateFeeds() {
        const feedUrls = this.getFeedUrls();

        if (feedUrls.length === 0) {
            this.showResult('Veuillez entrer au moins un flux RSS', 'error');
            return;
        }

        const resultDiv = document.getElementById('updateResult');
        const scrapeBtn = document.getElementById('scrapeFeedsBtn');
        const updateBtn = document.getElementById('updateFeedsBtn');

        // Désactiver les boutons pendant l'analyse
        if (scrapeBtn) scrapeBtn.disabled = true;
        if (updateBtn) updateBtn.disabled = true;

        if (scrapeBtn) scrapeBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Analyse en cours...';
        if (updateBtn) updateBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Traitement...';

        resultDiv.innerHTML = `
            <div class="flex items-center text-blue-600">
                <i class="fas fa-spinner fa-spin mr-2"></i>
                <div>
                    <p class="font-medium">Analyse des flux RSS en cours...</p>
                    <p class="text-xs">Traitement de ${feedUrls.length} flux</p>
                </div>
            </div>
        `;

        try {
            const response = await fetch('/api/update-feeds', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ feeds: feedUrls })
            });

            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }

            const data = await response.json();

            if (data.results) {
                const result = data.results;
                let resultHTML = '';

                if (result.new_articles > 0) {
                    resultHTML = `
                        <div class="text-green-600">
                            <div class="flex items-center mb-2">
                                <i class="fas fa-check-circle mr-2"></i>
                                <span class="font-medium">Analyse terminée avec succès!</span>
                            </div>
                            <div class="text-sm space-y-1">
                                <p>📊 ${result.total_articles || 0} articles traités</p>
                                <p>🆕 ${result.new_articles || 0} nouveaux articles analysés</p>
                                <p>📰 ${feedUrls.length} flux RSS analysés</p>
                                ${result.analyzed_count ? `<p>🔍 ${result.analyzed_count} articles analysés pour les thèmes</p>` : ''}
                            </div>
                        </div>
                    `;
                } else {
                    resultHTML = `
                        <div class="text-blue-600">
                            <div class="flex items-center mb-2">
                                <i class="fas fa-info-circle mr-2"></i>
                                <span class="font-medium">Analyse terminée</span>
                            </div>
                            <div class="text-sm">
                                <p>Aucun nouvel article trouvé dans les flux RSS</p>
                                <p>${result.total_articles || 0} articles déjà en base de données</p>
                            </div>
                        </div>
                    `;
                }

                if (result.errors && result.errors.length > 0) {
                    resultHTML += `
                        <div class="mt-3 text-orange-600">
                            <div class="flex items-center mb-1">
                                <i class="fas fa-exclamation-triangle mr-2"></i>
                                <span class="font-medium">Avertissements:</span>
                            </div>
                            <div class="text-sm max-h-20 overflow-y-auto">
                                ${result.errors.slice(0, 3).map(error => `<p class="truncate">${error}</p>`).join('')}
                                ${result.errors.length > 3 ? `<p>... et ${result.errors.length - 3} autres erreurs</p>` : ''}
                            </div>
                        </div>
                    `;
                }

                resultDiv.innerHTML = resultHTML;

                // Recharger les données affichées
                this.refreshDisplayedData();

            } else if (data.error) {
                throw new Error(data.error);
            } else {
                throw new Error('Réponse invalide du serveur');
            }
        } catch (error) {
            console.error('❌ Erreur lors de l\'analyse:', error);
            resultDiv.innerHTML = `
                <div class="text-red-600">
                    <div class="flex items-center mb-2">
                        <i class="fas fa-exclamation-triangle mr-2"></i>
                        <span class="font-medium">Erreur lors de l'analyse</span>
                    </div>
                    <p class="text-sm">${error.message}</p>
                </div>
            `;
        } finally {
            // Réactiver les boutons
            if (scrapeBtn) {
                scrapeBtn.disabled = false;
                scrapeBtn.innerHTML = '<i class="fas fa-play mr-2"></i>Lancer l\'analyse';
            }
            if (updateBtn) {
                updateBtn.disabled = false;
                updateBtn.innerHTML = '<i class="fas fa-sync-alt mr-2"></i>Mettre à jour les flux';
            }
        }
    }

    static getFeedUrls() {
        const feedsTextarea = document.getElementById('feedUrls');
        if (!feedsTextarea) return [];

        return feedsTextarea.value
            .split('\n')
            .map(url => url.trim())
            .filter(url => url.length > 0 && this.isValidUrl(url));
    }

    static isValidUrl(string) {
        try {
            new URL(string);
            return true;
        } catch (_) {
            return false;
        }
    }

    static async refreshDisplayedData() {
        try {
            // Recharger les articles récents
            if (typeof ArticleManager !== 'undefined' && ArticleManager.loadRecentArticles) {
                await ArticleManager.loadRecentArticles();
            }

            // Recharger les statistiques
            if (typeof DashboardManager !== 'undefined' && DashboardManager.loadDashboardData) {
                await DashboardManager.loadDashboardData();
            }

            // Recharger les quick stats sur la page d'accueil
            await this.loadQuickStats();

            console.log('✅ Données rafraîchies avec succès');
        } catch (error) {
            console.error('❌ Erreur lors du rafraîchissement des données:', error);
        }
    }

    static async loadQuickStats() {
        try {
            console.log('📊 Chargement des statistiques rapides...');

            const response = await fetch('/api/stats');

            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                this.updateStatsDisplay(data);
                return data;
            } else {
                console.warn('⚠️ Réponse API stats non réussie:', data);
                // Utiliser les données de fallback
                const fallbackData = data.fallback_data || {
                    total_articles: 0,
                    sentiment_distribution: {
                        positive: 0,
                        neutral_positive: 0,
                        neutral_negative: 0,
                        negative: 0
                    },
                    theme_stats: {}
                };
                this.updateStatsDisplay(fallbackData);
                return fallbackData;
            }
        } catch (error) {
            console.error('❌ Erreur chargement stats:', error);
            // Données par défaut en cas d'erreur
            const fallbackData = {
                total_articles: 0,
                sentiment_distribution: {
                    positive: 0,
                    neutral_positive: 0,
                    neutral_negative: 0,
                    negative: 0
                },
                theme_stats: {}
            };
            this.updateStatsDisplay(fallbackData);
            return fallbackData;
        }
    }

    static updateStatsDisplay(stats) {
        try {
            // Mettre à jour l'affichage des statistiques sur la page d'accueil
            const totalArticlesEl = document.getElementById('totalArticles');
            const positiveArticlesEl = document.getElementById('positiveArticles');
            const totalThemesEl = document.getElementById('totalThemes');

            if (totalArticlesEl) {
                totalArticlesEl.textContent = stats.total_articles || 0;
                totalArticlesEl.classList.add('pulse-animation');
                setTimeout(() => totalArticlesEl.classList.remove('pulse-animation'), 1000);
            }

            if (positiveArticlesEl) {
                positiveArticlesEl.textContent = stats.sentiment_distribution?.positive || 0;
                positiveArticlesEl.classList.add('pulse-animation');
                setTimeout(() => positiveArticlesEl.classList.remove('pulse-animation'), 1000);
            }

            if (totalThemesEl) {
                totalThemesEl.textContent = Object.keys(stats.theme_stats || {}).length;
                totalThemesEl.classList.add('pulse-animation');
                setTimeout(() => totalThemesEl.classList.remove('pulse-animation'), 1000);
            }

            // Mettre à jour les statistiques détaillées si présentes
            const totalArticlesCountEl = document.getElementById('total-articles-count');
            const positiveCountEl = document.getElementById('positive-count');
            const neutralPositiveCountEl = document.getElementById('neutral-positive-count');
            const neutralNegativeCountEl = document.getElementById('neutral-negative-count');
            const negativeCountEl = document.getElementById('negative-count');

            if (totalArticlesCountEl) totalArticlesCountEl.textContent = stats.total_articles || 0;
            if (positiveCountEl) positiveCountEl.textContent = stats.sentiment_distribution?.positive || 0;
            if (neutralPositiveCountEl) neutralPositiveCountEl.textContent = stats.sentiment_distribution?.neutral_positive || 0;
            if (neutralNegativeCountEl) neutralNegativeCountEl.textContent = stats.sentiment_distribution?.neutral_negative || 0;
            if (negativeCountEl) negativeCountEl.textContent = stats.sentiment_distribution?.negative || 0;

            console.log('✅ Statistiques mises à jour:', stats);
        } catch (error) {
            console.error('❌ Erreur mise à jour affichage stats:', error);
        }
    }

    static showResult(message, type = 'info') {
        const resultDiv = document.getElementById('updateResult');
        if (!resultDiv) return;

        const bgColor = type === 'success' ? 'bg-green-100 text-green-800 border-green-300' :
            type === 'error' ? 'bg-red-100 text-red-800 border-red-300' :
                'bg-blue-100 text-blue-800 border-blue-300';

        resultDiv.innerHTML = `
            <div class="p-3 rounded border ${bgColor}">
                <div class="flex items-center">
                    <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-triangle' : 'info-circle'} mr-2"></i>
                    <span>${message}</span>
                </div>
            </div>
        `;

        // Auto-dismiss après 5 secondes pour les succès
        if (type === 'success') {
            setTimeout(() => {
                if (resultDiv.innerHTML.includes(message)) {
                    resultDiv.innerHTML = '';
                }
            }, 5000);
        }
    }

    // Méthode pour analyser un flux spécifique
    static async analyzeSingleFeed(feedUrl) {
        try {
            const response = await fetch('/api/update-feeds', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ feeds: [feedUrl] })
            });

            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Erreur analyse flux:', error);
            throw error;
        }
    }

    // Méthode pour tester un flux
    static async testFeed(feedUrl) {
        try {
            const response = await fetch(`/api/test-feed?url=${encodeURIComponent(feedUrl)}`);

            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Erreur test flux:', error);
            throw error;
        }
    }

    // Méthode pour obtenir les sources disponibles
    static async getSources() {
        try {
            const response = await fetch('/api/sources');

            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }

            const data = await response.json();
            return data.sources || [];
        } catch (error) {
            console.error('Erreur récupération sources:', error);
            return [];
        }
    }

    // Méthode pour exporter les articles
    static async exportArticles(filters = {}) {
        try {
            const params = new URLSearchParams();
            Object.keys(filters).forEach(key => {
                if (filters[key]) params.append(key, filters[key]);
            });

            const response = await fetch(`/api/articles/export?${params}`);

            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }

            return await response.blob();
        } catch (error) {
            console.error('Erreur export articles:', error);
            throw error;
        }
    }
}

// Styles CSS pour les animations
const style = document.createElement('style');
style.textContent = `
    .pulse-animation {
        animation: pulse 0.5s ease-in-out;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    .fade-in {
        animation: fadeIn 0.3s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }
`;
document.head.appendChild(style);

// Initialisation
document.addEventListener('DOMContentLoaded', function () {
    // Vérifier si on est sur une page qui utilise FeedManager
    const feedsContainer = document.getElementById('feedUrls');
    const updateResult = document.getElementById('updateResult');

    if (feedsContainer || updateResult) {
        window.FeedManager = FeedManager;
        FeedManager.init();
        console.log('✅ FeedManager initialisé');

        // Charger les stats immédiatement
        setTimeout(() => FeedManager.loadQuickStats(), 1000);
    }
});

// Export pour les modules ES6
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { FeedManager };
}
