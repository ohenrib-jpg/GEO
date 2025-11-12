// static/js/feeds.js - Gestion optimisée des flux RSS et analyse

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

    // Configuration pour le traitement par lots
    static BATCH_SIZE = 3; // Traiter 3 flux en parallèle maximum
    static RETRY_ATTEMPTS = 2;
    static TIMEOUT_MS = 15000; // 15 secondes par flux

    static init() {
        this.setupEventListeners();
        this.loadSavedFeeds();
        this.initProgressTracking();
    }

    static initProgressTracking() {
        // Créer un conteneur pour la barre de progression si nécessaire
        const resultDiv = document.getElementById('updateResult');
        if (resultDiv && !document.getElementById('feedProgressBar')) {
            const progressHTML = `
                <div id="feedProgressBar" class="hidden mb-4">
                    <div class="flex justify-between text-sm mb-1">
                        <span id="progressLabel">Préparation...</span>
                        <span id="progressCount">0/0</span>
                    </div>
                    <div class="w-full bg-gray-200 rounded-full h-2">
                        <div id="progressBarFill" class="bg-blue-600 h-2 rounded-full transition-all duration-300" style="width: 0%"></div>
                    </div>
                </div>
            `;
            resultDiv.insertAdjacentHTML('beforebegin', progressHTML);
        }
    }

    static setupEventListeners() {
        const scrapeBtn = document.getElementById('scrapeFeedsBtn');
        if (scrapeBtn) {
            scrapeBtn.addEventListener('click', () => this.startScraping());
        }

        const updateBtn = document.getElementById('updateFeedsBtn');
        if (updateBtn) {
            updateBtn.addEventListener('click', () => this.updateFeeds());
        }

        const loadDefaultBtn = document.getElementById('loadDefaultFeedsBtn');
        if (loadDefaultBtn) {
            loadDefaultBtn.addEventListener('click', () => this.loadDefaultFeeds());
        }

        // Sauvegarde automatique lors de la modification des flux
        const feedsTextarea = document.getElementById('feedUrls');
        if (feedsTextarea) {
            feedsTextarea.addEventListener('blur', () => this.saveFeeds());
        }
    }

    static loadSavedFeeds() {
        const savedFeeds = localStorage.getItem('savedFeeds');
        if (savedFeeds) {
            const feedsTextarea = document.getElementById('feedUrls');
            if (feedsTextarea && !feedsTextarea.value) {
                feedsTextarea.value = savedFeeds;
            }
        } else {
            // Si aucun flux sauvegardé, charger les flux par défaut
            this.loadDefaultFeeds();
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
            this.showResult('✓ Flux par défaut chargés avec succès!', 'success');
            this.saveFeeds();
        }
    }

    static async startScraping() {
        const feedUrls = this.getFeedUrls();
        if (feedUrls.length === 0) {
            this.showResult('⚠ Veuillez entrer au moins un flux RSS', 'error');
            return;
        }

        this.saveFeeds();
        await this.updateFeedsWithBatching();
    }

    static async updateFeeds() {
        await this.updateFeedsWithBatching();
    }

    /**
     * Traitement optimisé des flux par lots avec retry et timeout
     */
    static async updateFeedsWithBatching() {
        const feedUrls = this.getFeedUrls();

        if (feedUrls.length === 0) {
            this.showResult('⚠ Veuillez entrer au moins un flux RSS', 'error');
            return;
        }

        const resultDiv = document.getElementById('updateResult');
        const scrapeBtn = document.getElementById('scrapeFeedsBtn');
        const updateBtn = document.getElementById('updateFeedsBtn');

        // Désactiver les boutons
        this.setButtonsState(false);
        this.showProgressBar(true);

        // Initialiser les résultats globaux
        let totalArticles = 0;
        let newArticles = 0;
        let errors = [];
        let processedFeeds = 0;

        try {
            // Diviser les flux en lots
            for (let i = 0; i < feedUrls.length; i += this.BATCH_SIZE) {
                const batch = feedUrls.slice(i, i + this.BATCH_SIZE);
                
                // Mettre à jour la progression
                this.updateProgress(processedFeeds, feedUrls.length, 
                    `Traitement du lot ${Math.floor(i / this.BATCH_SIZE) + 1}...`);

                // Traiter le lot en parallèle avec retry
                const batchPromises = batch.map(url => 
                    this.processFeedWithRetry(url, this.RETRY_ATTEMPTS)
                );

                const batchResults = await Promise.allSettled(batchPromises);

                // Agréger les résultats
                batchResults.forEach((result, index) => {
                    processedFeeds++;
                    
                    if (result.status === 'fulfilled' && result.value.success) {
                        totalArticles += result.value.total_articles || 0;
                        newArticles += result.value.new_articles || 0;
                    } else {
                        const feedUrl = batch[index];
                        const errorMsg = result.reason?.message || 'Erreur inconnue';
                        errors.push(`${this.extractDomainName(feedUrl)}: ${errorMsg}`);
                    }

                    this.updateProgress(processedFeeds, feedUrls.length, 
                        `Traitement en cours...`);
                });

                // Pause entre les lots pour éviter la surcharge
                if (i + this.BATCH_SIZE < feedUrls.length) {
                    await this.sleep(500);
                }
            }

            // Afficher les résultats finaux
            this.displayResults({
                total_articles: totalArticles,
                new_articles: newArticles,
                errors: errors,
                processed_feeds: processedFeeds
            });

            // Recharger les données affichées si nouveaux articles
            if (newArticles > 0) {
                await this.refreshDisplayedData();
            }

        } catch (error) {
            this.showResult(`❌ Erreur critique: ${error.message}`, 'error');
        } finally {
            this.setButtonsState(true);
            this.showProgressBar(false);
        }
    }

    /**
     * Traite un flux avec tentatives de retry en cas d'échec
     */
    static async processFeedWithRetry(feedUrl, attemptsLeft) {
        try {
            return await this.processSingleFeedWithTimeout(feedUrl);
        } catch (error) {
            if (attemptsLeft > 1) {
                console.warn(`Retry pour ${feedUrl}, tentatives restantes: ${attemptsLeft - 1}`);
                await this.sleep(1000);
                return this.processFeedWithRetry(feedUrl, attemptsLeft - 1);
            }
            throw error;
        }
    }

    /**
     * Traite un flux unique avec timeout
     */
    static async processSingleFeedWithTimeout(feedUrl) {
        return Promise.race([
            ApiClient.post('/api/update-feeds', { feeds: [feedUrl] }),
            this.timeout(this.TIMEOUT_MS, `Timeout pour ${feedUrl}`)
        ]).then(data => {
            if (data.results) {
                return {
                    success: true,
                    total_articles: data.results.total_articles || 0,
                    new_articles: data.results.new_articles || 0
                };
            }
            throw new Error(data.error || 'Erreur inconnue');
        });
    }

    /**
     * Utilitaire pour créer un timeout Promise
     */
    static timeout(ms, message) {
        return new Promise((_, reject) => 
            setTimeout(() => reject(new Error(message)), ms)
        );
    }

    /**
     * Utilitaire pour pause
     */
    static sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Mise à jour de la barre de progression
     */
    static updateProgress(current, total, label) {
        const progressBar = document.getElementById('feedProgressBar');
        const progressLabel = document.getElementById('progressLabel');
        const progressCount = document.getElementById('progressCount');
        const progressBarFill = document.getElementById('progressBarFill');

        if (progressBar && progressLabel && progressCount && progressBarFill) {
            const percentage = Math.round((current / total) * 100);
            progressLabel.textContent = label;
            progressCount.textContent = `${current}/${total}`;
            progressBarFill.style.width = `${percentage}%`;
        }
    }

    /**
     * Afficher/masquer la barre de progression
     */
    static showProgressBar(show) {
        const progressBar = document.getElementById('feedProgressBar');
        if (progressBar) {
            progressBar.classList.toggle('hidden', !show);
            if (show) {
                this.updateProgress(0, 1, 'Préparation...');
            }
        }
    }

    /**
     * Activer/désactiver les boutons
     */
    static setButtonsState(enabled) {
        const scrapeBtn = document.getElementById('scrapeFeedsBtn');
        const updateBtn = document.getElementById('updateFeedsBtn');

        if (scrapeBtn) {
            scrapeBtn.disabled = !enabled;
            scrapeBtn.innerHTML = enabled 
                ? '<i class="fas fa-play mr-2"></i>Lancer l\'analyse'
                : '<i class="fas fa-spinner fa-spin mr-2"></i>Analyse en cours...';
        }

        if (updateBtn) {
            updateBtn.disabled = !enabled;
            updateBtn.innerHTML = enabled
                ? '<i class="fas fa-sync-alt mr-2"></i>Mettre à jour les flux'
                : '<i class="fas fa-spinner fa-spin mr-2"></i>Traitement...';
        }
    }

    /**
     * Affichage des résultats détaillés
     */
    static displayResults(result) {
        const resultDiv = document.getElementById('updateResult');
        if (!resultDiv) return;

        let resultHTML = '';

        if (result.new_articles > 0) {
            resultHTML = `
                <div class="text-green-600">
                    <div class="flex items-center mb-2">
                        <i class="fas fa-check-circle mr-2"></i>
                        <span class="font-medium">✓ Analyse terminée avec succès!</span>
                    </div>
                    <div class="text-sm space-y-1">
                        <p>📊 ${result.total_articles} articles traités</p>
                        <p>✨ ${result.new_articles} nouveaux articles analysés par RoBERTa</p>
                        <p>📡 ${result.processed_feeds} flux RSS traités</p>
                    </div>
                </div>
            `;
        } else {
            resultHTML = `
                <div class="text-blue-600">
                    <div class="flex items-center mb-2">
                        <i class="fas fa-info-circle mr-2"></i>
                        <span class="font-medium">ℹ Analyse terminée</span>
                    </div>
                    <div class="text-sm">
                        <p>Aucun nouvel article trouvé dans les flux RSS</p>
                        <p>${result.total_articles} articles déjà en base de données</p>
                        <p>${result.processed_feeds} flux vérifiés</p>
                    </div>
                </div>
            `;
        }

        if (result.errors && result.errors.length > 0) {
            const maxErrors = 5;
            resultHTML += `
                <div class="mt-3 text-orange-600 bg-orange-50 p-3 rounded border border-orange-200">
                    <div class="flex items-center mb-2">
                        <i class="fas fa-exclamation-triangle mr-2"></i>
                        <span class="font-medium">⚠ Flux en erreur (${result.errors.length}):</span>
                    </div>
                    <div class="text-xs space-y-1 max-h-32 overflow-y-auto">
                        ${result.errors.slice(0, maxErrors).map(error => 
                            `<p class="font-mono">• ${this.escapeHtml(error)}</p>`
                        ).join('')}
                        ${result.errors.length > maxErrors ? 
                            `<p class="italic">... et ${result.errors.length - maxErrors} autres erreurs</p>` : ''}
                    </div>
                </div>
            `;
        }

        resultDiv.innerHTML = resultHTML;
    }

    static getFeedUrls() {
        const feedsTextarea = document.getElementById('feedUrls');
        if (!feedsTextarea) return [];

        return feedsTextarea.value
            .split('\n')
            .map(url => url.trim())
            .filter(url => url.length > 0)
            .filter(url => this.isValidUrl(url))
            .filter((url, index, self) => self.indexOf(url) === index); // Supprimer les doublons
    }

    static isValidUrl(string) {
        try {
            const url = new URL(string);
            return url.protocol === 'http:' || url.protocol === 'https:';
        } catch (_) {
            return false;
        }
    }

    /**
     * Rafraîchir toutes les données affichées après analyse
     */
    static async refreshDisplayedData() {
        const refreshPromises = [];

        // Recharger les articles récents
        if (typeof ArticleManager !== 'undefined' && ArticleManager.loadRecentArticles) {
            refreshPromises.push(
                ArticleManager.loadRecentArticles().catch(e => 
                    console.warn('Erreur refresh articles:', e)
                )
            );
        }

        // Recharger les statistiques du dashboard
        if (typeof DashboardManager !== 'undefined' && DashboardManager.loadDashboardData) {
            refreshPromises.push(
                DashboardManager.loadDashboardData().catch(e => 
                    console.warn('Erreur refresh dashboard:', e)
                )
            );
        }

        // Recharger les stats rapides
        refreshPromises.push(
            this.loadQuickStats().catch(e => 
                console.warn('Erreur refresh stats:', e)
            )
        );

        await Promise.allSettled(refreshPromises);
    }

    static async loadQuickStats() {
        const totalArticlesEl = document.getElementById('totalArticles');
        const positiveArticlesEl = document.getElementById('positiveArticles');
        const totalThemesEl = document.getElementById('totalThemes');

        if (totalArticlesEl || positiveArticlesEl || totalThemesEl) {
            try {
                const data = await ApiClient.get('/api/stats');
                
                if (totalArticlesEl) {
                    this.animateCounter(totalArticlesEl, data.total_articles || 0);
                }
                if (positiveArticlesEl) {
                    this.animateCounter(positiveArticlesEl, data.sentiment_distribution?.positive || 0);
                }
                if (totalThemesEl) {
                    this.animateCounter(totalThemesEl, Object.keys(data.theme_stats || {}).length);
                }
            } catch (error) {
                console.error('Erreur chargement stats:', error);
            }
        }
    }

    /**
     * Animation des compteurs (effet visuel)
     */
    static animateCounter(element, targetValue) {
        const currentValue = parseInt(element.textContent) || 0;
        const duration = 800;
        const steps = 30;
        const increment = (targetValue - currentValue) / steps;
        let step = 0;

        const timer = setInterval(() => {
            step++;
            const newValue = Math.round(currentValue + (increment * step));
            element.textContent = newValue;

            if (step >= steps) {
                element.textContent = targetValue;
                clearInterval(timer);
            }
        }, duration / steps);
    }

    static showResult(message, type = 'info') {
        const resultDiv = document.getElementById('updateResult');
        if (!resultDiv) return;

        const config = {
            success: { color: 'text-green-600', icon: 'check-circle' },
            error: { color: 'text-red-600', icon: 'exclamation-triangle' },
            info: { color: 'text-blue-600', icon: 'info-circle' }
        };

        const { color, icon } = config[type] || config.info;

        resultDiv.innerHTML = `
            <div class="${color} flex items-center">
                <i class="fas fa-${icon} mr-2"></i>
                <span>${message}</span>
            </div>
        `;
    }

    /**
     * Extraire le nom de domaine pour l'affichage
     */
    static extractDomainName(url) {
        try {
            const urlObj = new URL(url);
            return urlObj.hostname.replace('www.', '');
        } catch {
            return url.substring(0, 30) + '...';
        }
    }

    /**
     * Échapper le HTML pour éviter les injections
     */
    static escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Analyser un flux spécifique (utilitaire)
     */
    static async analyzeSingleFeed(feedUrl) {
        try {
            const data = await ApiClient.post('/api/update-feeds', { feeds: [feedUrl] });
            return data;
        } catch (error) {
            console.error('Erreur analyse flux:', error);
            throw error;
        }
    }

    /**
     * Tester un flux (utilitaire)
     */
    static async testFeed(feedUrl) {
        try {
            const response = await fetch(`/api/test-feed?url=${encodeURIComponent(feedUrl)}`);
            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Erreur test flux:', error);
            throw error;
        }
    }
}

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function () {
    window.FeedManager = FeedManager;
    FeedManager.init();
    console.log('✅ FeedManager initialisé avec optimisations');
});