// static/js/dashboard.js - VERSION COMPLÈTE AMÉLIORÉE

class DashboardManager {
    static charts = {
        sentiment: null,
        theme: null,
        timeline: null,
        sentimentComparison: null
    };

    static animationConfig = {
        duration: 1000,
        easing: 'easeInOutCubic'
    };

    static chartColors = {
        positive: '#10B981',
        negative: '#EF4444',
        neutral: '#6B7280',
        positiveLight: '#A7F3D0',
        negativeLight: '#FCA5A5',
        neutralLight: '#D1D5DB',
        gradients: {
            blue: ['#3B82F6', '#1E40AF'],
            green: ['#10B981', '#047857'],
            red: ['#EF4444', '#DC2626'],
            purple: ['#8B5CF6', '#7C3AED'],
            orange: ['#F59E0B', '#D97706']
        }
    };

    static async loadDashboardData() {
        try {
            console.log('📊 Chargement des données du dashboard...');
            const data = await ApiClient.get('/api/stats');
            console.log('📈 Données reçues:', data);

            this.updateStatsCards(data);
            this.createCharts(data);
            this.loadPopularThemes(data.theme_stats);
            this.updateQuickStats(data);

            // Stocker les données pour les mises à jour futures
            this.currentData = data;

        } catch (error) {
            console.error('❌ Erreur chargement dashboard:', error);
            this.showErrorMessage('Erreur lors du chargement des données');
        }
    }

    static updateStatsCards(data) {
        const elements = {
            'statTotalArticles': data.total_articles || 0,
            'statPositiveArticles': data.sentiment_distribution?.positive || 0,
            'statNegativeArticles': data.sentiment_distribution?.negative || 0,
            'statActiveThemes': Object.keys(data.theme_stats || {}).length
        };

        // Animation des compteurs
        Object.entries(elements).forEach(([id, newValue]) => {
            this.animateCounter(id, newValue);
        });

        console.log('✅ Statistiques mises à jour avec animation');
    }

    static animateCounter(elementId, targetValue) {
        const element = document.getElementById(elementId);
        if (!element) return;

        const startValue = parseInt(element.textContent) || 0;
        const duration = 1500; // 1.5 secondes
        const startTime = performance.now();

        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // Easing function (ease out)
            const easeOut = 1 - Math.pow(1 - progress, 3);
            const currentValue = Math.round(startValue + (targetValue - startValue) * easeOut);

            element.textContent = currentValue.toLocaleString('fr-FR');

            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };

        requestAnimationFrame(animate);
    }

    static createCharts(data) {
        this.createSentimentChart(data.sentiment_distribution);
        this.createThemeChart(data.theme_stats);
        this.createTimelineChart(data.timeline_data);
        this.createSentimentComparisonChart(data);
    }

    static createSentimentChart(sentimentData) {
        const ctx = document.getElementById('sentimentChart');
        if (!ctx) return;

        // Détruire le graphique existant
        if (this.charts.sentiment) {
            this.charts.sentiment.destroy();
        }

        const labels = ['Très Positif', 'Positif', 'Neutre', 'Négatif', 'Très Négatif'];

        // Calculer une distribution plus fine
        const refinedData = this.calculateRefinedSentimentDistribution(sentimentData);

        console.log('📈 Distribution raffinée:', refinedData);

        this.charts.sentiment = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: [
                        refinedData.very_positive,
                        refinedData.positive,
                        refinedData.neutral,
                        refinedData.negative,
                        refinedData.very_negative
                    ],
                    backgroundColor: [
                        this.chartColors.positive,
                        this.chartColors.positiveLight,
                        this.chartColors.neutral,
                        this.chartColors.negativeLight,
                        this.chartColors.negative
                    ],
                    borderWidth: 3,
                    borderColor: '#FFFFFF',
                    hoverBorderWidth: 5,
                    hoverOffset: 10
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '60%',
                animation: {
                    animateRotate: true,
                    duration: this.animationConfig.duration,
                    easing: this.animationConfig.easing
                },
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true,
                            font: { size: 12, weight: '500' },
                            generateLabels: function (chart) {
                                const data = chart.data;
                                return data.labels.map((label, i) => {
                                    const value = data.datasets[0].data[i];
                                    const total = data.datasets[0].data.reduce((a, b) => a + b, 0);
                                    const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                    return {
                                        text: `${label}: ${value} (${percentage}%)`,
                                        fillStyle: data.datasets[0].backgroundColor[i],
                                        hidden: false,
                                        index: i
                                    };
                                });
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#FFFFFF',
                        bodyColor: '#FFFFFF',
                        borderColor: '#FFFFFF',
                        borderWidth: 1,
                        cornerRadius: 8,
                        callbacks: {
                            label: function (context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                return `${label}: ${value} articles (${percentage}%)`;
                            }
                        }
                    }
                },
                onHover: (event, elements) => {
                    event.native.target.style.cursor = elements.length > 0 ? 'pointer' : 'default';
                }
            }
        });
    }

    static calculateRefinedSentimentDistribution(sentimentData) {
        // Si pas de données détaillées, simuler une distribution
        if (!sentimentData) {
            return {
                very_positive: 0,
                positive: 0,
                neutral: 0,
                negative: 0,
                very_negative: 0
            };
        }

        const total = sentimentData.positive + sentimentData.negative + sentimentData.neutral;
        if (total === 0) {
            return { very_positive: 0, positive: 0, neutral: 0, negative: 0, very_negative: 0 };
        }

        // Pour l'instant, répartissons la distribution de manière réaliste
        const positive = sentimentData.positive;
        const negative = sentimentData.negative;
        const neutral = sentimentData.neutral;

        return {
            very_positive: Math.round(positive * 0.3), // 30% des positifs sont très positifs
            positive: positive - Math.round(positive * 0.3),
            neutral: neutral,
            negative: negative - Math.round(negative * 0.3), // 30% des négatifs sont très négatifs
            very_negative: Math.round(negative * 0.3)
        };
    }

    static createThemeChart(themeData) {
        const ctx = document.getElementById('themeChart');
        if (!ctx) return;

        if (this.charts.theme) {
            this.charts.theme.destroy();
        }

        if (!themeData || Object.keys(themeData).length === 0) {
            this.showEmptyChartMessage(ctx, 'Aucun thème avec des articles');
            return;
        }

        const themes = Object.entries(themeData)
            .filter(([_, data]) => data.article_count > 0)
            .sort((a, b) => b[1].article_count - a[1].article_count)
            .slice(0, 12); // Augmenter à 12 thèmes

        console.log('📊 Thèmes pour graphique:', themes);

        if (themes.length === 0) {
            this.showEmptyChartMessage(ctx, 'Aucun article associé aux thèmes');
            return;
        }

        const labels = themes.map(([_, data]) => data.name);
        const counts = themes.map(([_, data]) => data.article_count);
        const colors = themes.map(([_, data]) => this.generateThemeColor(data.color || '#6366f1', data.article_count));

        this.charts.theme = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Nombre d\'articles',
                    data: counts,
                    backgroundColor: colors,
                    borderColor: colors.map(color => color.replace('0.8', '1')),
                    borderWidth: 2,
                    borderRadius: 8,
                    borderSkipped: false,
                    hoverBackgroundColor: colors.map(color => color.replace('0.8', '1')),
                    hoverBorderColor: colors.map(color => color.replace('0.6', '0.9'))
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: this.animationConfig.duration,
                    easing: this.animationConfig.easing
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#FFFFFF',
                        bodyColor: '#FFFFFF',
                        borderColor: '#FFFFFF',
                        borderWidth: 1,
                        cornerRadius: 8,
                        callbacks: {
                            title: function (context) {
                                return context[0].label;
                            },
                            label: function (context) {
                                const value = context.parsed.y;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                return `Articles: ${value} (${percentage}%)`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1,
                            precision: 0,
                            font: { size: 11 }
                        },
                        title: {
                            display: true,
                            text: 'Nombre d\'articles',
                            font: { size: 12, weight: 'bold' }
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)',
                            lineWidth: 1
                        }
                    },
                    x: {
                        ticks: {
                            maxRotation: 45,
                            minRotation: 45,
                            font: { size: 10 }
                        },
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }

    static generateThemeColor(baseColor, count) {
        // Générer une variation de couleur basée sur l'activité
        const intensity = Math.min(count / 10, 1); // Normaliser l'intensité
        const alpha = 0.4 + (intensity * 0.4); // Entre 0.4 et 0.8

        // Convertir hex en rgba
        const hex = baseColor.replace('#', '');
        const r = parseInt(hex.substr(0, 2), 16);
        const g = parseInt(hex.substr(2, 2), 16);
        const b = parseInt(hex.substr(4, 2), 16);

        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }

    static showEmptyChartMessage(ctx, message) {
        const parent = ctx.parentElement;
        parent.innerHTML = `
            <div class="flex items-center justify-center h-80 text-gray-500">
                <div class="text-center">
                    <i class="fas fa-chart-bar text-4xl mb-3"></i>
                    <p>${message}</p>
                    <p class="text-sm mt-2">Les données apparaîtront après l'analyse</p>
                </div>
            </div>
        `;
    }

    static async createTimelineChart(timelineData) {
        const ctx = document.getElementById('timelineChart');
        if (!ctx) return;

        if (this.charts.timeline) {
            this.charts.timeline.destroy();
        }

        // Récupérer les données si pas fournies
        if (!timelineData) {
            try {
                const response = await ApiClient.get('/api/stats/timeline');
                timelineData = response.timeline;
            } catch (error) {
                console.error('Erreur récupération timeline:', error);
                timelineData = null;
            }
        }

        if (!timelineData || timelineData.length === 0) {
            this.showEmptyChartMessage(ctx, 'Données d\'évolution temporelle non disponibles');
            return;
        }

        console.log('📈 Timeline data:', timelineData);

        const labels = timelineData.map(d => {
            const date = new Date(d.date);
            return date.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' });
        });

        const positiveData = timelineData.map(d => d.positive || 0);
        const negativeData = timelineData.map(d => d.negative || 0);
        const neutralData = timelineData.map(d => d.neutral || 0);

        this.charts.timeline = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Positif',
                        data: positiveData,
                        borderColor: this.chartColors.positive,
                        backgroundColor: this.chartColors.positiveLight,
                        tension: 0.4,
                        fill: true,
                        pointBackgroundColor: this.chartColors.positive,
                        pointBorderColor: '#FFFFFF',
                        pointBorderWidth: 2,
                        pointRadius: 5,
                        pointHoverRadius: 8
                    },
                    {
                        label: 'Neutre',
                        data: neutralData,
                        borderColor: this.chartColors.neutral,
                        backgroundColor: this.chartColors.neutralLight,
                        tension: 0.4,
                        fill: true,
                        pointBackgroundColor: this.chartColors.neutral,
                        pointBorderColor: '#FFFFFF',
                        pointBorderWidth: 2,
                        pointRadius: 5,
                        pointHoverRadius: 8
                    },
                    {
                        label: 'Négatif',
                        data: negativeData,
                        borderColor: this.chartColors.negative,
                        backgroundColor: this.chartColors.negativeLight,
                        tension: 0.4,
                        fill: true,
                        pointBackgroundColor: this.chartColors.negative,
                        pointBorderColor: '#FFFFFF',
                        pointBorderWidth: 2,
                        pointRadius: 5,
                        pointHoverRadius: 8
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                animation: {
                    duration: this.animationConfig.duration,
                    easing: this.animationConfig.easing
                },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            font: { size: 12, weight: '500' },
                            padding: 20
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#FFFFFF',
                        bodyColor: '#FFFFFF',
                        borderColor: '#FFFFFF',
                        borderWidth: 1,
                        cornerRadius: 8,
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            title: function (context) {
                                return `Date: ${context[0].label}`;
                            },
                            label: function (context) {
                                return `${context.dataset.label}: ${context.parsed.y} articles`;
                            },
                            footer: function (tooltipItems) {
                                let total = 0;
                                tooltipItems.forEach(item => {
                                    total += item.parsed.y;
                                });
                                return `Total: ${total} articles`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: true,
                            color: 'rgba(0, 0, 0, 0.1)'
                        },
                        title: {
                            display: true,
                            text: 'Date',
                            font: { size: 12, weight: 'bold' }
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            borderDash: [4, 4],
                            color: 'rgba(0, 0, 0, 0.1)'
                        },
                        ticks: {
                            stepSize: 1,
                            precision: 0,
                            font: { size: 11 }
                        },
                        title: {
                            display: true,
                            text: 'Nombre d\'articles',
                            font: { size: 12, weight: 'bold' }
                        }
                    }
                }
            }
        });
    }

    static createSentimentComparisonChart(data) {
        const ctx = document.getElementById('sentimentComparisonChart');
        if (!ctx) return;

        if (this.charts.sentimentComparison) {
            this.charts.sentimentComparison.destroy();
        }

        // Graphique de comparaison des sentiments par période
        const comparisonData = this.calculateSentimentComparison(data);

        this.charts.sentimentComparison = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ['Très Positif', 'Positif', 'Neutre', 'Négatif', 'Très Négatif'],
                datasets: [{
                    label: 'Distribution actuelle',
                    data: comparisonData.current,
                    borderColor: this.chartColors.gradients.blue[0],
                    backgroundColor: this.chartColors.gradients.blue[0] + '20',
                    pointBackgroundColor: this.chartColors.gradients.blue[0],
                    pointBorderColor: '#FFFFFF',
                    pointBorderWidth: 2,
                    pointRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: this.animationConfig.duration,
                    easing: this.animationConfig.easing
                },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            font: { size: 12, weight: '500' }
                        }
                    }
                },
                scales: {
                    r: {
                        beginAtZero: true,
                        max: Math.max(...comparisonData.current) * 1.2,
                        ticks: {
                            stepSize: Math.ceil(Math.max(...comparisonData.current) / 5)
                        }
                    }
                }
            }
        });
    }

    static calculateSentimentComparison(data) {
        const refined = this.calculateRefinedSentimentDistribution(data.sentiment_distribution);
        return {
            current: [
                refined.very_positive,
                refined.positive,
                refined.neutral,
                refined.negative,
                refined.very_negative
            ]
        };
    }

    static loadPopularThemes(themeStats) {
        const container = document.getElementById('popularThemes');
        if (!container) return;

        if (!themeStats || Object.keys(themeStats).length === 0) {
            container.innerHTML = this.getNoThemesTemplate();
            return;
        }

        const sortedThemes = Object.entries(themeStats)
            .filter(([_, data]) => data.article_count > 0)
            .sort((a, b) => b[1].article_count - a[1].article_count)
            .slice(0, 8); // Augmenter à 8 thèmes

        console.log('🏆 Thèmes populaires:', sortedThemes);

        if (sortedThemes.length === 0) {
            container.innerHTML = this.getNoThemesTemplate();
            return;
        }

        container.innerHTML = sortedThemes.map(([themeId, data], index) => {
            const percentage = this.calculateThemePercentage(data.article_count, sortedThemes);
            return `
                <div class="group relative overflow-hidden bg-gradient-to-r from-gray-50 to-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-all duration-300 cursor-pointer"
                     onclick="DashboardManager.viewThemeArticles('${themeId}')">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-3 flex-1">
                            <div class="w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-sm"
                                 style="background-color: ${data.color || '#6366f1'}">
                                ${index + 1}
                            </div>
                            <div class="flex-1">
                                <h4 class="font-semibold text-gray-800 group-hover:text-indigo-600 transition-colors">
                                    ${data.name}
                                </h4>
                                <div class="flex items-center space-x-2 mt-1">
                                    <span class="text-sm text-gray-600">${data.article_count} article${data.article_count !== 1 ? 's' : ''}</span>
                                    <div class="flex-1 bg-gray-200 rounded-full h-2">
                                        <div class="h-2 rounded-full transition-all duration-500"
                                             style="width: ${percentage}%; background-color: ${data.color || '#6366f1'}"></div>
                                    </div>
                                    <span class="text-xs text-gray-500">${percentage}%</span>
                                </div>
                            </div>
                        </div>
                        <div class="text-indigo-600 opacity-0 group-hover:opacity-100 transition-opacity">
                            <i class="fas fa-chevron-right"></i>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    static calculateThemePercentage(themeCount, allThemes) {
        const total = allThemes.reduce((sum, [_, data]) => sum + data.article_count, 0);
        return total > 0 ? Math.round((themeCount / total) * 100) : 0;
    }

    static getNoThemesTemplate() {
        return `
            <div class="text-center py-12 text-gray-500">
                <div class="mb-4">
                    <i class="fas fa-tags text-4xl mb-3 opacity-50"></i>
                </div>
                <h3 class="text-lg font-semibold mb-2">Aucun thème disponible</h3>
                <p class="text-sm">Les thèmes apparaîtront après l'analyse des articles</p>
                <button onclick="DashboardManager.loadDashboardData()" 
                        class="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition">
                    Actualiser
                </button>
            </div>
        `;
    }

    static viewThemeArticles(themeId) {
        console.log('🔍 Voir articles du thème:', themeId);
        // Rediriger vers la page des articles filtrés par thème
        if (typeof FilterManager !== 'undefined') {
            FilterManager.showAdvancedFilters();
            setTimeout(() => {
                const themeSelect = document.getElementById('filterTheme');
                if (themeSelect) {
                    themeSelect.value = themeId;
                    FilterManager.applyFilters();
                }
            }, 500);
        } else {
            // Fallback simple
            window.location.href = `/api/articles?theme=${themeId}&limit=50`;
        }
    }

    static updateQuickStats(data) {
        // Mettre à jour les statistiques rapides sur l'index si présent
        const totalArticles = document.getElementById('totalArticles');
        const positiveArticles = document.getElementById('positiveArticles');
        const totalThemes = document.getElementById('totalThemes');

        if (totalArticles) {
            this.animateCounter('totalArticles', data.total_articles || 0);
        }
        if (positiveArticles) {
            this.animateCounter('positiveArticles', data.sentiment_distribution?.positive || 0);
        }
        if (totalThemes) {
            this.animateCounter('totalThemes', Object.keys(data.theme_stats || {}).length);
        }
    }

    static showErrorMessage(message) {
        // Afficher un message d'erreur dans les cartes de statistiques
        const errorHtml = `
            <div class="flex items-center justify-center p-4 bg-red-50 border border-red-200 rounded-lg">
                <i class="fas fa-exclamation-triangle text-red-500 mr-2"></i>
                <span class="text-red-700">${message}</span>
            </div>
        `;

        // Remplacer le contenu des cartes avec erreur
        const cards = ['statTotalArticles', 'statPositiveArticles', 'statNegativeArticles', 'statActiveThemes'];
        cards.forEach(cardId => {
            const element = document.getElementById(cardId);
            if (element) {
                const parent = element.closest('.bg-white');
                if (parent) {
                    parent.querySelector('div').innerHTML = errorHtml;
                }
            }
        });
    }

    // Méthodes utilitaires pour l'actualisation en temps réel
    static startRealTimeUpdates() {
        // Actualiser toutes les 30 secondes
        setInterval(() => {
            this.loadDashboardData();
        }, 30000);

        // Actualiser les cartes de statistiques plus fréquemment
        setInterval(() => {
            this.updateQuickStats(this.currentData || {});
        }, 10000);
    }

    static refreshCharts() {
        // Rafraîchir uniquement les graphiques sans recharger toutes les données
        if (this.currentData) {
            this.createCharts(this.currentData);
        }
    }

    // Gestion des erreurs
    static handleChartError(chartName, error) {
        console.error(`❌ Erreur graphique ${chartName}:`, error);

        // Afficher un message d'erreur dans le conteneur du graphique
        const chartContainer = document.getElementById(`${chartName}Container`);
        if (chartContainer) {
            chartContainer.innerHTML = `
                <div class="flex items-center justify-center h-64 text-red-500">
                    <div class="text-center">
                        <i class="fas fa-exclamation-triangle text-3xl mb-3"></i>
                        <p>Erreur d'affichage du graphique</p>
                        <button onclick="DashboardManager.refreshCharts()" 
                                class="mt-2 px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700">
                            Réessayer
                        </button>
                    </div>
                </div>
            `;
        }
    }
}

// Initialisation du dashboard
document.addEventListener('DOMContentLoaded', function () {
    window.DashboardManager = DashboardManager;
    console.log('✅ DashboardManager amélioré initialisé');

    // Charger les données si on est sur la page dashboard
    if (document.getElementById('sentimentChart')) {
        DashboardManager.loadDashboardData();

        // Démarrer les mises à jour en temps réel
        DashboardManager.startRealTimeUpdates();

        // Gérer la visibilité de la page pour optimiser les performances
        document.addEventListener('visibilitychange', function () {
            if (document.hidden) {
                // Pause les animations quand la page n'est pas visible
                Object.values(DashboardManager.charts).forEach(chart => {
                    if (chart && chart.stop) chart.stop();
                });
            } else {
                // Reprendre les animations quand la page devient visible
                DashboardManager.refreshCharts();
            }
        });
    }
});

// Exposer la classe globalement
window.DashboardManager = DashboardManager;