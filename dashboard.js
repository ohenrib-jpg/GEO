// static/js/dashboard.js - VERSION CORRIGÉE

class DashboardManager {
    static charts = {
        sentiment: null,
        theme: null,
        timeline: null
    };

    static async loadDashboardData() {
        try {
            const data = await ApiClient.get('/api/stats');
            console.log('📊 Données dashboard reçues:', data);
            
            this.updateStatsCards(data);
            this.createCharts(data);
            this.loadPopularThemes(data.theme_stats);
        } catch (error) {
            console.error('Erreur chargement dashboard:', error);
        }
    }

    static updateStatsCards(data) {
        const elements = {
            'statTotalArticles': data.total_articles || 0,
            'statPositiveArticles': data.sentiment_distribution?.positive || 0,
            'statNegativeArticles': data.sentiment_distribution?.negative || 0,
            'statActiveThemes': Object.keys(data.theme_stats || {}).length
        };

        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) element.textContent = value;
        });
        
        console.log('✅ Stats mises à jour:', elements);
    }

    static createCharts(data) {
        this.createSentimentChart(data.sentiment_distribution);
        this.createThemeChart(data.theme_stats);
        this.createTimelineChart(data.timeline_data);
    }

    static createSentimentChart(sentimentData) {
        const ctx = document.getElementById('sentimentChart');
        if (!ctx) return;

        if (this.charts.sentiment) {
            this.charts.sentiment.destroy();
        }

        const labels = ['Positif', 'Négatif', 'Neutre'];
        const sentimentValues = [
            sentimentData?.positive || 0,
            sentimentData?.negative || 0,
            sentimentData?.neutral || 0
        ];

        console.log('📈 Sentiments:', sentimentValues);

        this.charts.sentiment = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: sentimentValues,
                    backgroundColor: ['#10B981', '#EF4444', '#6B7280'],
                    borderWidth: 2,
                    borderColor: '#FFFFFF'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { 
                        position: 'bottom', 
                        labels: { 
                            padding: 20, 
                            usePointStyle: true,
                            font: { size: 12 }
                        } 
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }

    static createThemeChart(themeData) {
        const ctx = document.getElementById('themeChart');
        if (!ctx) return;

        if (this.charts.theme) {
            this.charts.theme.destroy();
        }

        if (!themeData || Object.keys(themeData).length === 0) {
            console.warn('⚠️ Aucune donnée de thème disponible');
            ctx.parentElement.innerHTML = `
                <div class="flex items-center justify-center h-80 text-gray-500">
                    <div class="text-center">
                        <i class="fas fa-chart-bar text-4xl mb-3"></i>
                        <p>Aucun article analysé par thème</p>
                        <p class="text-sm mt-2">Les thèmes apparaîtront après l'analyse des articles</p>
                    </div>
                </div>
            `;
            return;
        }

        const themes = Object.entries(themeData)
            .filter(([_, data]) => data.article_count > 0)
            .sort((a, b) => b[1].article_count - a[1].article_count)
            .slice(0, 10);

        console.log('📊 Thèmes pour graphique:', themes);

        if (themes.length === 0) {
            console.warn('⚠️ Aucun thème avec des articles');
            ctx.parentElement.innerHTML = `
                <div class="flex items-center justify-center h-80 text-gray-500">
                    <div class="text-center">
                        <i class="fas fa-chart-bar text-4xl mb-3"></i>
                        <p>Aucun article associé aux thèmes</p>
                    </div>
                </div>
            `;
            return;
        }

        const labels = themes.map(([_, data]) => data.name);
        const counts = themes.map(([_, data]) => data.article_count);
        const colors = themes.map(([_, data]) => data.color || '#6366f1');

        this.charts.theme = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Nombre d\'articles',
                    data: counts,
                    backgroundColor: colors,
                    borderWidth: 0,
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { 
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            title: function(context) {
                                return context[0].label;
                            },
                            label: function(context) {
                                return `Articles: ${context.parsed.y}`;
                            }
                        }
                    }
                },
                scales: {
                    y: { 
                        beginAtZero: true, 
                        ticks: { 
                            stepSize: 1,
                            precision: 0
                        },
                        title: {
                            display: true,
                            text: 'Nombre d\'articles'
                        }
                    },
                    x: {
                        ticks: {
                            maxRotation: 45,
                            minRotation: 45
                        }
                    }
                }
            }
        });
    }

    static async createTimelineChart(timelineData) {
        const ctx = document.getElementById('timelineChart');
        if (!ctx) return;

        if (this.charts.timeline) {
            this.charts.timeline.destroy();
        }

        // Si pas de données fournies, les récupérer
        if (!timelineData) {
            try {
                const response = await ApiClient.get('/api/stats/timeline');
                timelineData = response.timeline;
            } catch (error) {
                console.error('Erreur récupération timeline:', error);
                timelineData = null;
            }
        }

        // Si toujours pas de données, afficher un message
        if (!timelineData || timelineData.length === 0) {
            console.warn('⚠️ Aucune donnée timeline disponible');
            ctx.parentElement.innerHTML = `
                <div class="flex items-center justify-center h-96 text-gray-500">
                    <div class="text-center">
                        <i class="fas fa-chart-line text-4xl mb-3"></i>
                        <p>Données d'évolution temporelle non disponibles</p>
                        <p class="text-sm mt-2">L'historique s'enrichira au fil des analyses</p>
                    </div>
                </div>
            `;
            return;
        }

        console.log('📈 Timeline data:', timelineData);

        const labels = timelineData.map(d => d.date);
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
                        borderColor: '#10B981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'Négatif',
                        data: negativeData,
                        borderColor: '#EF4444',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'Neutre',
                        data: neutralData,
                        borderColor: '#6B7280',
                        backgroundColor: 'rgba(107, 114, 128, 0.1)',
                        tension: 0.4,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                plugins: {
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    x: { 
                        grid: { display: false },
                        title: {
                            display: true,
                            text: 'Date'
                        }
                    },
                    y: { 
                        beginAtZero: true, 
                        grid: { borderDash: [4, 4] },
                        ticks: {
                            stepSize: 1,
                            precision: 0
                        },
                        title: {
                            display: true,
                            text: 'Nombre d\'articles'
                        }
                    }
                }
            }
        });
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
            .slice(0, 10);

        console.log('🏆 Thèmes populaires:', sortedThemes);

        if (sortedThemes.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <i class="fas fa-tags text-3xl mb-3"></i>
                    <p>Aucun article associé aux thèmes</p>
                    <p class="text-sm mt-2">Lancez une analyse pour voir les thèmes populaires</p>
                </div>
            `;
            return;
        }

        container.innerHTML = sortedThemes.map(([themeId, data]) => `
            <div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition duration-200 cursor-pointer"
                 onclick="DashboardManager.viewThemeArticles('${themeId}')">
                <div class="flex items-center space-x-4 flex-1">
                    <div class="w-4 h-4 rounded-full flex-shrink-0" style="background-color: ${data.color || '#6366f1'}"></div>
                    <div class="flex-1">
                        <span class="font-medium text-gray-800">${data.name}</span>
                        <p class="text-sm text-gray-600">${data.article_count} article${data.article_count !== 1 ? 's' : ''}</p>
                    </div>
                </div>
                <button class="text-indigo-600 hover:text-indigo-800 text-sm font-medium flex items-center">
                    Voir <i class="fas fa-chevron-right ml-1"></i>
                </button>
            </div>
        `).join('');
    }

    static getNoThemesTemplate() {
        return `
            <div class="text-center py-8 text-gray-500">
                <i class="fas fa-tags text-3xl mb-3"></i>
                <p>Aucune donnée de thème disponible</p>
                <p class="text-sm mt-2">Les thèmes apparaîtront après l'analyse des articles</p>
            </div>
        `;
    }

    static viewThemeArticles(themeId) {
        console.log('🔍 Voir articles du thème:', themeId);
        // Rediriger vers la page des articles filtrés par thème
        if (typeof FilterManager !== 'undefined') {
            FilterManager.showAdvancedFilters();
            // Pré-sélectionner le thème après un court délai
            setTimeout(() => {
                const themeSelect = document.getElementById('filterTheme');
                if (themeSelect) {
                    themeSelect.value = themeId;
                    FilterManager.applyFilters();
                }
            }, 500);
        }
    }
}

// Initialisation du dashboard
document.addEventListener('DOMContentLoaded', function () {
    window.DashboardManager = DashboardManager;
    console.log('✅ DashboardManager initialisé');

    // Charger les données si on est sur la page dashboard
    if (document.getElementById('sentimentChart')) {
        DashboardManager.loadDashboardData();
        setInterval(() => DashboardManager.loadDashboardData(), 30000);
    }
});
