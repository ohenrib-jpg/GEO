// static/js/ticker-banner.js - VERSION CORRIGÉE

class TickerBanner {
    constructor() {
        this.tickerData = {
            articles: [],
            stocks: [],
            indicators: [],
            social: {}
        };
        this.updateInterval = null;
        this.scrollSpeed = 80; // pixels par seconde
    }

    async initialize() {
        console.log('🎬 Initialisation du bandeau ticker...');
        this.createBannerHTML();
        await this.loadAllData();
        this.startAutoRefresh();
        console.log('✅ Bandeau ticker initialisé');
    }

    createBannerHTML() {
        // Vérifier si le bandeau existe déjà
        if (document.getElementById('ticker-banner')) {
            return;
        }

        // Créer le HTML du bandeau
        const bannerHTML = `
            <div id="ticker-banner" class="fixed top-0 left-0 right-0 z-50 bg-gradient-to-r from-gray-900 via-blue-900 to-gray-900 text-white shadow-lg border-b-2 border-blue-500">
                <div class="relative overflow-hidden h-10">
                    <!-- Contenu défilant -->
                    <div id="ticker-content" class="absolute whitespace-nowrap flex items-center h-full space-x-8 animate-ticker">
                        <div class="flex items-center space-x-8">
                            <span class="text-yellow-400 font-bold">
                                <i class="fas fa-sync-alt fa-spin mr-2"></i>Chargement...
                            </span>
                        </div>
                    </div>
                </div>
                
                <!-- Bouton de contrôle -->
                <button id="ticker-toggle" 
                        class="absolute right-2 top-1/2 transform -translate-y-1/2 bg-blue-600 hover:bg-blue-700 text-white px-2 py-1 rounded text-xs transition-colors">
                    <i class="fas fa-pause"></i>
                </button>
            </div>
            
            <style>
                #ticker-banner {
                    animation: slideDown 0.3s ease-out;
                }
                
                @keyframes slideDown {
                    from {
                        transform: translateY(-100%);
                    }
                    to {
                        transform: translateY(0);
                    }
                }
                
                @keyframes ticker {
                    0% {
                        transform: translateX(100%);
                    }
                    100% {
                        transform: translateX(-100%);
                    }
                }
                
                .animate-ticker {
                    animation: ticker 60s linear infinite;
                }
                
                .ticker-paused {
                    animation-play-state: paused !important;
                }
                
                /* Ajuster le contenu principal pour ne pas être caché */
                body {
                    padding-top: 40px;
                }
                
                /* Effet de glow pour les éléments importants */
                .ticker-highlight {
                    text-shadow: 0 0 10px rgba(96, 165, 250, 0.5);
                }
                
                /* Couleurs par sentiment */
                .ticker-positive {
                    color: #10B981;
                }
                
                .ticker-negative {
                    color: #EF4444;
                }
                
                .ticker-neutral {
                    color: #60A5FA;
                }
                
                .ticker-warning {
                    color: #F59E0B;
                }
            </style>
        `;

        // Insérer le bandeau au début du body
        document.body.insertAdjacentHTML('afterbegin', bannerHTML);

        // Configurer le bouton pause/play
        const toggleBtn = document.getElementById('ticker-toggle');
        toggleBtn.addEventListener('click', () => this.toggleAnimation());
    }

    async loadAllData() {
        try {
            await Promise.all([
                this.loadRecentArticles(),
                this.loadStockData(),
                this.loadIndicators(),
                this.loadSocialData()
            ]);

            this.updateTickerContent();
        } catch (error) {
            console.error('❌ Erreur chargement données ticker:', error);
            this.showError();
        }
    }

    async loadRecentArticles() {
        try {
            const response = await fetch('/api/articles?limit=5');
            const data = await response.json();
            
            if (data.articles) {
                this.tickerData.articles = data.articles.map(article => ({
                    title: this.truncateText(article.title, 80),
                    sentiment: article.detailed_sentiment || article.sentiment,
                    score: article.sentiment_score || 0,
                    pubDate: article.pub_date
                }));
            }
        } catch (error) {
            console.error('Erreur chargement articles:', error);
        }
    }

    async loadStockData() {
        try {
            const response = await fetch('/api/weak-indicators/stocks/data');
            
            // Vérifier si le service est disponible
            if (response.status === 404 || response.status === 503) {
                console.log('ℹ️ Service stocks non disponible, ignoré');
                return;
            }
            
            const data = await response.json();
            
            if (data.success && data.stocks) {
                this.tickerData.stocks = Object.values(data.stocks).map(stock => ({
                    symbol: stock.symbol,
                    price: stock.price,
                    change: stock.change_percent,
                    trend: stock.change_percent >= 0 ? 'up' : 'down'
                }));
            }
        } catch (error) {
            console.log('ℹ️ Données boursières non disponibles:', error.message);
        }
    }

    async loadIndicators() {
        try {
            const response = await fetch('/indicateurs/api/indicators');
            const data = await response.json();
            
            if (data.success && data.indicators) {
                this.tickerData.indicators = [];
                
                // 🔧 CORRECTION : Accéder correctement aux données imbriquées
                const indicators = data.indicators;
                
                // PIB
                if (indicators.pib && indicators.pib.success) {
                    const pib = indicators.pib;
                    this.tickerData.indicators.push({
                        name: 'PIB',
                        value: pib.value,
                        unit: pib.unit,
                        change: pib.change,
                        trend: pib.trend
                    });
                }
                
                // Chômage
                if (indicators.chomage && indicators.chomage.success) {
                    const chomage = indicators.chomage;
                    this.tickerData.indicators.push({
                        name: 'Chômage',
                        value: chomage.value,
                        unit: chomage.unit,
                        change: chomage.change,
                        trend: chomage.trend
                    });
                }
                
                // CAC 40
                if (indicators.cac40 && indicators.cac40.success) {
                    const cac = indicators.cac40;
                    this.tickerData.indicators.push({
                        name: 'CAC 40',
                        value: cac.value,
                        unit: cac.unit,
                        change: cac.change,
                        trend: cac.trend
                    });
                }
                
                // Inflation
                if (indicators.inflation && indicators.inflation.success) {
                    const inflation = indicators.inflation;
                    this.tickerData.indicators.push({
                        name: 'Inflation',
                        value: inflation.value,
                        unit: inflation.unit,
                        change: inflation.change,
                        trend: inflation.trend
                    });
                }
            }
        } catch (error) {
            console.error('Erreur chargement indicateurs:', error);
        }
    }

    async loadSocialData() {
        try {
            const response = await fetch('/api/social/statistics?days=1');
            
            // Vérifier si le service est disponible
            if (response.status === 503) {
                console.log('ℹ️ Service social non disponible, ignoré');
                return;
            }
            
            const data = await response.json();
            
            if (data.success && data.statistics) {
                this.tickerData.social = {
                    totalPosts: data.statistics.total_posts || 0,
                    positive: data.statistics.sentiment_distribution?.positive || 0,
                    negative: data.statistics.sentiment_distribution?.negative || 0
                };
            }

            // Récupérer le Factor Z
            const comparisonResponse = await fetch('/api/social/comparison-history?limit=1');
            
            // Vérifier si le service est disponible
            if (comparisonResponse.status === 503) {
                console.log('ℹ️ Service comparaison social non disponible, ignoré');
                return;
            }
            
            const comparisonData = await comparisonResponse.json();
            
            if (comparisonData.success && comparisonData.history?.length > 0) {
                this.tickerData.social.factorZ = comparisonData.history[0].factor_z;
            }
        } catch (error) {
            console.log('ℹ️ Données sociales non disponibles:', error.message);
        }
    }

    updateTickerContent() {
        const tickerContent = document.getElementById('ticker-content');
        if (!tickerContent) return;

        const items = [];

        // 1. Heure actuelle
        items.push(`
            <span class="ticker-highlight font-bold">
                <i class="fas fa-clock mr-1"></i>
                ${this.getCurrentTime()}
            </span>
        `);

        // 2. Articles récents avec sentiment
        if (this.tickerData.articles.length > 0) {
            this.tickerData.articles.forEach(article => {
                const sentimentClass = this.getSentimentClass(article.sentiment);
                const sentimentIcon = this.getSentimentIcon(article.sentiment);
                
                items.push(`
                    <span class="flex items-center">
                        <i class="fas fa-newspaper mr-2 text-blue-400"></i>
                        <span class="font-medium">${article.title}</span>
                        <span class="ml-2 ${sentimentClass}">
                            ${sentimentIcon} ${(article.score * 100).toFixed(0)}%
                        </span>
                    </span>
                `);
            });
        }

        // 3. Données boursières
        if (this.tickerData.stocks.length > 0) {
            this.tickerData.stocks.forEach(stock => {
                const trendClass = stock.trend === 'up' ? 'ticker-positive' : 'ticker-negative';
                const trendIcon = stock.trend === 'up' ? '📈' : '📉';
                
                items.push(`
                    <span class="flex items-center">
                        <i class="fas fa-chart-line mr-2 text-yellow-400"></i>
                        <span class="font-bold">${stock.symbol}</span>
                        <span class="ml-2">${stock.price.toFixed(2)}€</span>
                        <span class="ml-2 ${trendClass}">
                            ${trendIcon} ${stock.change >= 0 ? '+' : ''}${stock.change.toFixed(2)}%
                        </span>
                    </span>
                `);
            });
        }

        // 4. Indicateurs français
        if (this.tickerData.indicators.length > 0) {
            this.tickerData.indicators.forEach(indicator => {
                const trendIcon = indicator.trend === 'up' ? '↗️' : 
                                indicator.trend === 'down' ? '↘️' : '➡️';
                
                // 🔧 CORRECTION : Affichage correct selon le type de données
                let displayValue = '';
                if (indicator.unit === '%') {
                    displayValue = `${indicator.value.toFixed(1)}%`;
                } else if (indicator.unit === 'Milliards €') {
                    displayValue = `${indicator.value.toLocaleString('fr-FR')} Mds €`;
                } else if (indicator.unit === 'points') {
                    displayValue = `${indicator.value.toLocaleString('fr-FR')} pts`;
                } else {
                    displayValue = `${indicator.value.toLocaleString('fr-FR')}${indicator.unit}`;
                }
                
                items.push(`
                    <span class="flex items-center">
                        <i class="fas fa-chart-bar mr-2 text-purple-400"></i>
                        <span class="font-medium">${indicator.name}:</span>
                        <span class="ml-2 font-bold">${displayValue}</span>
                        ${indicator.change !== undefined ? `
                            <span class="ml-2 text-sm">
                                ${trendIcon} ${indicator.change > 0 ? '+' : ''}${indicator.change}
                            </span>
                        ` : ''}
                    </span>
                `);
            });
        }

        // 5. Réseaux sociaux
        if (this.tickerData.social.totalPosts > 0) {
            items.push(`
                <span class="flex items-center">
                    <i class="fas fa-share-alt mr-2 text-cyan-400"></i>
                    <span class="font-medium">Réseaux Sociaux:</span>
                    <span class="ml-2 ticker-positive">${this.tickerData.social.positive} positifs</span>
                    <span class="mx-1">•</span>
                    <span class="ticker-negative">${this.tickerData.social.negative} négatifs</span>
                </span>
            `);

            if (this.tickerData.social.factorZ !== undefined) {
                const factorZClass = this.getFactorZClass(this.tickerData.social.factorZ);
                
                items.push(`
                    <span class="flex items-center">
                        <i class="fas fa-balance-scale mr-2 text-orange-400"></i>
                        <span class="font-medium">Factor Z:</span>
                        <span class="ml-2 ${factorZClass} font-bold">
                            ${this.tickerData.social.factorZ.toFixed(3)}
                        </span>
                    </span>
                `);
            }
        }

        // Dupliquer le contenu pour un défilement continu
        const htmlContent = items.join('<span class="mx-4 text-gray-600">•</span>');
        tickerContent.innerHTML = `
            <div class="flex items-center space-x-8">
                ${htmlContent}
            </div>
            <div class="flex items-center space-x-8">
                ${htmlContent}
            </div>
        `;
    }

    startAutoRefresh() {
        // Rafraîchir toutes les 40 secondes
        this.updateInterval = setInterval(() => {
            this.loadAllData();
        }, 40000);

        // Mettre à jour l'heure chaque seconde
        setInterval(() => {
            this.updateClock();
        }, 1000);
    }

    updateClock() {
        const clockElements = document.querySelectorAll('#ticker-content .fa-clock');
        clockElements.forEach(el => {
            const timeSpan = el.parentElement;
            if (timeSpan) {
                timeSpan.innerHTML = `
                    <i class="fas fa-clock mr-1"></i>
                    ${this.getCurrentTime()}
                `;
            }
        });
    }

    toggleAnimation() {
        const tickerContent = document.getElementById('ticker-content');
        const toggleBtn = document.getElementById('ticker-toggle');
        
        if (tickerContent.classList.contains('ticker-paused')) {
            tickerContent.classList.remove('ticker-paused');
            toggleBtn.innerHTML = '<i class="fas fa-pause"></i>';
        } else {
            tickerContent.classList.add('ticker-paused');
            toggleBtn.innerHTML = '<i class="fas fa-play"></i>';
        }
    }

    showError() {
        const tickerContent = document.getElementById('ticker-content');
        if (tickerContent) {
            tickerContent.innerHTML = `
                <div class="flex items-center space-x-8">
                    <span class="text-red-400">
                        <i class="fas fa-exclamation-triangle mr-2"></i>
                        Erreur de chargement des données
                    </span>
                </div>
            `;
        }
    }

    // Utilitaires
    getCurrentTime() {
        const now = new Date();
        return now.toLocaleTimeString('fr-FR', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    }

    getSentimentClass(sentiment) {
        switch (sentiment?.toLowerCase()) {
            case 'positive': return 'ticker-positive';
            case 'negative': return 'ticker-negative';
            case 'neutral_positive': return 'text-blue-400';
            case 'neutral_negative': return 'text-yellow-400';
            default: return 'ticker-neutral';
        }
    }

    getSentimentIcon(sentiment) {
        switch (sentiment?.toLowerCase()) {
            case 'positive': return '😊';
            case 'negative': return '😟';
            case 'neutral_positive': return '🙂';
            case 'neutral_negative': return '😐';
            default: return '😶';
        }
    }

    getFactorZClass(factorZ) {
        const absZ = Math.abs(factorZ);
        if (absZ > 2.5) return 'ticker-negative';
        if (absZ > 1.5) return 'ticker-warning';
        if (absZ > 0.5) return 'ticker-neutral';
        return 'ticker-positive';
    }

    truncateText(text, maxLength) {
        if (!text) return '';
        return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    }

    destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
        const banner = document.getElementById('ticker-banner');
        if (banner) {
            banner.remove();
        }
    }
}

// Initialisation automatique
document.addEventListener('DOMContentLoaded', function() {
    // Attendre que les autres scripts soient chargés
    setTimeout(() => {
        window.tickerBanner = new TickerBanner();
        window.tickerBanner.initialize();
        console.log('✅ TickerBanner initialisé globalement');
    }, 1000);
});

console.log('✅ ticker-banner.js chargé');
