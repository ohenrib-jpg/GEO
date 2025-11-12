// static/js/feeds.js - Version corrigée

class FeedManager {
    static currentFeeds = [];
    static scrapingInProgress = false;

    static async init() {
        console.log('📊 Chargement des statistiques rapides...');
        await this.loadQuickStats();
        this.setupEventListeners();

        // Chargement périodique des stats
        setInterval(() => {
            this.loadQuickStats();
        }, 30000); // 30 secondes

        console.log('✅ FeedManager initialisé');
    }

    static setupEventListeners() {
        // Bouton lancer l'analyse
        const scrapeBtn = document.getElementById('scrapeFeedsBtn');
        if (scrapeBtn) {
            scrapeBtn.addEventListener('click', () => {
                this.startScraping();
            });
        }

        // Bouton mettre à jour les flux
        const updateBtn = document.getElementById('updateFeedsBtn');
        if (updateBtn) {
            updateBtn.addEventListener('click', () => {
                this.updateFeeds();
            });
        }

        // Bouton charger les flux par défaut
        const loadDefaultBtn = document.getElementById('loadDefaultFeedsBtn');
        if (loadDefaultBtn) {
            loadDefaultBtn.addEventListener('click', () => {
                this.loadDefaultFeeds();
            });
        }
    }

    static async startScraping() {
        const feedUrlsTextarea = document.getElementById('feedUrls');
        if (!feedUrlsTextarea) return;

        const feedUrls = feedUrlsTextarea.value.trim();
        if (!feedUrls) {
            alert('Veuillez entrer au moins une URL de flux RSS');
            return;
        }

        this.scrapingInProgress = true;
        const scrapeBtn = document.getElementById('scrapeFeedsBtn');
        const originalText = scrapeBtn.innerHTML;

        scrapeBtn.disabled = true;
        scrapeBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Analyse en cours...';

        try {
            // Essayer d'abord la nouvelle route
            let response = await fetch('/api/feeds/scrape', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ feed_urls: feedUrls })
            });

            // Si 404, essayer l'ancienne route
            if (!response.ok) {
                console.log('⚠️ Route /api/feeds/scrape non disponible, essai /api/update-feeds');
                response = await fetch('/api/update-feeds', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ feed_urls: feedUrls.split('\n').filter(url => url.trim()) })
                });
            }

            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }

            const data = await response.json();
            this.displayScrapingResult(data);

        } catch (error) {
            console.error('❌ Erreur lors de l\'analyse:', error);
            this.displayScrapingResult({
                error: 'Impossible de contacter le serveur. Vérifiez que le serveur Flask est en cours d\'exécution.'
            });
        } finally {
            scrapeBtn.disabled = false;
            scrapeBtn.innerHTML = originalText;
            this.scrapingInProgress = false;
        }
    }

    static async updateFeeds() {
        console.log('🔄 Mise à jour des flux...');

        const updateBtn = document.getElementById('updateFeedsBtn');
        const originalText = updateBtn.innerHTML;

        updateBtn.disabled = true;
        updateBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Mise à jour...';

        try {
            // Essayer d'abord la nouvelle route
            let response = await fetch('/api/feeds/update', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            // Si 404, essayer l'ancienne route
            if (!response.ok) {
                console.log('⚠️ Route /api/feeds/update non disponible, essai /api/update-feeds');
                response = await fetch('/api/update-feeds', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
            }

            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }

            const data = await response.json();
            this.displayScrapingResult(data);

        } catch (error) {
            console.error('❌ Erreur lors de l\'analyse:', error);
            this.displayScrapingResult({
                error: 'Impossible de mettre à jour les flux. Vérifiez la connexion au serveur.'
            });
        } finally {
            updateBtn.disabled = false;
            updateBtn.innerHTML = originalText;
        }
    }

    static displayScrapingResult(data) {
        const resultDiv = document.getElementById('updateResult');
        if (!resultDiv) return;

        if (data.error) {
            resultDiv.innerHTML = `
                <div class="bg-red-50 border border-red-200 rounded-lg p-4">
                    <div class="flex items-center">
                        <i class="fas fa-exclamation-triangle text-red-600 mr-3"></i>
                        <div>
                            <p class="font-semibold text-red-800">Erreur</p>
                            <p class="text-sm text-red-600">${data.error}</p>
                        </div>
                    </div>
                </div>
            `;
            return;
        }

        let html = '<div class="space-y-3">';

        if (data.success !== undefined) {
            html += `
                <div class="bg-green-50 border border-green-200 rounded-lg p-4">
                    <div class="flex items-center">
                        <i class="fas fa-check-circle text-green-600 mr-3"></i>
                        <div>
                            <p class="font-semibold text-green-800">Succès</p>
                            <p class="text-sm text-green-600">${data.message || 'Opération réussie'}</p>
                        </div>
                    </div>
                </div>
            `;
        }

        if (data.results) {
            html += '<div class="bg-blue-50 border border-blue-200 rounded-lg p-4">';
            html += '<p class="font-semibold text-blue-800 mb-2">Résultats détaillés:</p>';

            Object.entries(data.results).forEach(([feed, result]) => {
                const statusClass = result.success ? 'text-green-600' : 'text-red-600';
                const statusIcon = result.success ? 'fa-check-circle' : 'fa-times-circle';

                html += `
                    <div class="flex justify-between items-center py-1 border-b border-blue-100 last:border-b-0">
                        <span class="text-sm text-blue-700 truncate flex-1 mr-2">${feed}</span>
                        <div class="flex items-center space-x-2">
                            <i class="fas ${statusIcon} ${statusClass}"></i>
                            <span class="text-xs ${statusClass}">${result.articles || 0} articles</span>
                        </div>
                    </div>
                `;
            });

            html += '</div>';
        }

        if (data.total_articles !== undefined) {
            html += `
                <div class="bg-purple-50 border border-purple-200 rounded-lg p-4">
                    <div class="grid grid-cols-2 gap-4 text-center">
                        <div>
                            <p class="text-2xl font-bold text-purple-600">${data.total_articles || 0}</p>
                            <p class="text-xs text-purple-600">Articles totaux</p>
                        </div>
                        <div>
                            <p class="text-2xl font-bold text-green-600">${data.new_articles || 0}</p>
                            <p class="text-xs text-green-600">Nouveaux articles</p>
                        </div>
                    </div>
                </div>
            `;
        }

        html += '</div>';
        resultDiv.innerHTML = html;

        // Recharger les stats après une mise à jour
        setTimeout(() => {
            this.loadQuickStats();
        }, 1000);
    }

    static loadDefaultFeeds() {
        const defaultFeeds = [
            'https://feeds.bbci.co.uk/news/rss.xml',
            'https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml',
            'https://feeds.lemonde.fr/c/205/f/3050/index.rss',
            'https://www.lefigaro.fr/rss/figaro_actualites.xml',
            'https://www.theguardian.com/international/rss'
        ];

        const feedUrlsTextarea = document.getElementById('feedUrls');
        if (feedUrlsTextarea) {
            feedUrlsTextarea.value = defaultFeeds.join('\n');

            // Afficher un message de confirmation
            const resultDiv = document.getElementById('updateResult');
            if (resultDiv) {
                resultDiv.innerHTML = `
                    <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                        <div class="flex items-center">
                            <i class="fas fa-info-circle text-blue-600 mr-3"></i>
                            <div>
                                <p class="font-semibold text-blue-800">Flux par défaut chargés</p>
                                <p class="text-sm text-blue-600">${defaultFeeds.length} flux RSS chargés. Cliquez sur "Lancer l'analyse" pour commencer.</p>
                            </div>
                        </div>
                    </div>
                `;
            }
        }
    }

    static async loadQuickStats() {
        try {
            // Essayer d'abord /api/stats
            let response = await fetch('/api/stats');

            if (!response.ok) {
                // Fallback vers l'ancienne route
                response = await fetch('/api/themes/statistics');
            }

            if (response.ok) {
                const data = await response.json();
                this.updateQuickStats(data);
            } else {
                console.warn('⚠️ Réponse API stats non réussie:', response.status);
                // Utiliser des données par défaut
                this.updateQuickStats({
                    total_articles: 0,
                    sentiment_distribution: { positive: 0, negative: 0, neutral: 0 },
                    theme_stats: {}
                });
            }
        } catch (error) {
            console.error('❌ Erreur chargement stats:', error);
            // Données par défaut en cas d'erreur
            this.updateQuickStats({
                total_articles: 0,
                sentiment_distribution: { positive: 0, negative: 0, neutral: 0 },
                theme_stats: {}
            });
        }
    }

    static updateQuickStats(data) {
        // Mettre à jour les compteurs
        const totalArticles = document.getElementById('totalArticles');
        const positiveArticles = document.getElementById('positiveArticles');
        const totalThemes = document.getElementById('totalThemes');

        if (totalArticles) {
            this.animateCounter(totalArticles, data.total_articles || 0);
        }

        if (positiveArticles) {
            const positiveCount = data.sentiment_distribution?.positive || 0;
            this.animateCounter(positiveArticles, positiveCount);
        }

        if (totalThemes) {
            const themeCount = data.active_themes || Object.keys(data.theme_stats || {}).length;
            this.animateCounter(totalThemes, themeCount);
        }

        console.log('✅ Statistiques mises à jour:', data);
    }

    static animateCounter(element, targetValue, duration = 1000) {
        const startValue = parseInt(element.textContent) || 0;
        const startTime = performance.now();

        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // Easing function
            const easeOutQuart = 1 - Math.pow(1 - progress, 4);
            const currentValue = Math.floor(startValue + (targetValue - startValue) * easeOutQuart);

            element.textContent = currentValue.toLocaleString('fr-FR');

            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };

        requestAnimationFrame(animate);
    }
}

// Initialisation
document.addEventListener('DOMContentLoaded', function () {
    FeedManager.init();
});