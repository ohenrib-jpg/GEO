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

    static init() {
        this.setupEventListeners();
        this.loadSavedFeeds();
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
            const data = await ApiClient.post('/api/update-feeds', { feeds: feedUrls });

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
                                <p>📊 ${result.total_articles} articles traités</p>
                                <p>🆕 ${result.new_articles} nouveaux articles analysés</p>
                                <p>📰 ${feedUrls.length} flux RSS analysés</p>
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
                                <p>${result.total_articles} articles déjà en base de données</p>
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

            } else {
                throw new Error(data.error || 'Erreur inconnue lors de l\'analyse');
            }
        } catch (error) {
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

    static refreshDisplayedData() {
        // Recharger les articles récents
        if (typeof ArticleManager !== 'undefined') {
            ArticleManager.loadRecentArticles();
        }

        // Recharger les statistiques
        if (typeof DashboardManager !== 'undefined') {
            DashboardManager.loadDashboardData();
        }

        // Recharger les quick stats sur la page d'accueil
        this.loadQuickStats();
    }

    static loadQuickStats() {
        // Mettre à jour les statistiques rapides sur la page d'accueil
        const totalArticlesEl = document.getElementById('totalArticles');
        const positiveArticlesEl = document.getElementById('positiveArticles');
        const totalThemesEl = document.getElementById('totalThemes');

        if (totalArticlesEl || positiveArticlesEl || totalThemesEl) {
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    if (totalArticlesEl) totalArticlesEl.textContent = data.total_articles || 0;
                    if (positiveArticlesEl) positiveArticlesEl.textContent = data.sentiment_distribution?.positive || 0;
                    if (totalThemesEl) totalThemesEl.textContent = Object.keys(data.theme_stats || {}).length;
                })
                .catch(error => console.error('Erreur chargement stats:', error));
        }
    }

    static showResult(message, type = 'info') {
        const resultDiv = document.getElementById('updateResult');
        if (!resultDiv) return;

        const bgColor = type === 'success' ? 'text-green-600' :
            type === 'error' ? 'text-red-600' : 'text-blue-600';

        resultDiv.innerHTML = `<p class="${bgColor}">${message}</p>`;
    }

    // Méthode pour analyser un flux spécifique
    static async analyzeSingleFeed(feedUrl) {
        try {
            const data = await ApiClient.post('/api/update-feeds', { feeds: [feedUrl] });
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
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Erreur test flux:', error);
            throw error;
        }
    }
}

// Initialisation
document.addEventListener('DOMContentLoaded', function () {
    window.FeedManager = FeedManager;
    FeedManager.init();
    console.log('✅ FeedManager initialisé');
});