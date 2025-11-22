// static/js/entity-manager.js - Gestionnaire d'entités géopolitiques

class EntityManager {
    static currentView = 'dashboard';
    
    static async showEntityPanel() {
        const content = document.getElementById('themeManagerContent');
        const title = document.getElementById('modalTitle');
        
        if (!content || !title) return;
        
        title.textContent = '🌍 Entités Géopolitiques';
        
        content.innerHTML = `
            <div class="max-w-7xl mx-auto space-y-6">
                <!-- En-tête avec statistiques -->
                <div class="bg-gradient-to-r from-blue-50 to-indigo-50 border-l-4 border-blue-500 p-4 rounded-lg">
                    <div class="flex items-center justify-between">
                        <div>
                            <h3 class="text-lg font-semibold text-gray-800">Extraction d'Entités Géopolitiques</h3>
                            <p class="text-sm text-gray-600 mt-1">
                                Identification automatique de pays, organisations, personnalités et événements
                            </p>
                        </div>
                        <div class="text-right">
                            <button onclick="EntityManager.batchAnalyzeArticles()" 
                                    class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition duration-200">
                                <i class="fas fa-robot mr-2"></i>Analyser tous les articles
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Navigation par onglets -->
                <div class="border-b border-gray-200">
                    <nav class="flex space-x-4">
                        <button onclick="EntityManager.switchView('dashboard')" 
                                class="entity-tab ${this.currentView === 'dashboard' ? 'active' : ''}"
                                data-view="dashboard">
                            <i class="fas fa-chart-bar mr-2"></i>Tableau de bord
                        </button>
                        <button onclick="EntityManager.switchView('top-entities')" 
                                class="entity-tab ${this.currentView === 'top-entities' ? 'active' : ''}"
                                data-view="top-entities">
                            <i class="fas fa-trophy mr-2"></i>Top Entités
                        </button>
                        <button onclick="EntityManager.switchView('network')" 
                                class="entity-tab ${this.currentView === 'network' ? 'active' : ''}"
                                data-view="network">
                            <i class="fas fa-project-diagram mr-2"></i>Réseau
                        </button>
                        <button onclick="EntityManager.switchView('search')" 
                                class="entity-tab ${this.currentView === 'search' ? 'active' : ''}"
                                data-view="search">
                            <i class="fas fa-search mr-2"></i>Recherche
                        </button>
                    </nav>
                </div>

                <!-- Contenu dynamique -->
                <div id="entityViewContent" class="min-h-96">
                    <div class="text-center py-8 text-gray-500">
                        <i class="fas fa-spinner fa-spin text-2xl mb-2"></i>
                        <p>Chargement...</p>
                    </div>
                </div>
            </div>

            <style>
                .entity-tab {
                    padding: 0.75rem 1rem;
                    border-bottom: 2px solid transparent;
                    color: #6B7280;
                    transition: all 0.2s;
                }
                .entity-tab:hover {
                    color: #4B5563;
                    border-bottom-color: #E5E7EB;
                }
                .entity-tab.active {
                    color: #2563EB;
                    border-bottom-color: #2563EB;
                    font-weight: 600;
                }
            </style>
        `;
        
        ModalManager.showModal('themeManagerModal');
        this.switchView(this.currentView);
    }
    
    static async switchView(view) {
        this.currentView = view;
        
        // Mettre à jour les onglets
        document.querySelectorAll('.entity-tab').forEach(tab => {
            if (tab.dataset.view === view) {
                tab.classList.add('active');
            } else {
                tab.classList.remove('active');
            }
        });
        
        // Charger le contenu
        const container = document.getElementById('entityViewContent');
        if (!container) return;
        
        switch (view) {
            case 'dashboard':
                await this.loadDashboard(container);
                break;
            case 'top-entities':
                await this.loadTopEntities(container);
                break;
            case 'network':
                await this.loadNetwork(container);
                break;
            case 'search':
                await this.loadSearch(container);
                break;
        }
    }
    
    static async loadDashboard(container) {
        container.innerHTML = '<div class="text-center py-8"><i class="fas fa-spinner fa-spin text-2xl"></i></div>';
        
        try {
            // Charger les catégories
            const categoriesResp = await fetch('/api/entities/categories');
            const categoriesData = await categoriesResp.json();
            
            if (!categoriesData.success) throw new Error('Erreur catégories');
            
            // Charger top entités
            const topResp = await fetch('/api/entities/top?limit=10');
            const topData = await topResp.json();
            
            if (!topData.success) throw new Error('Erreur top entités');
            
            container.innerHTML = `
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
                    ${categoriesData.categories.map(cat => `
                        <div class="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
                            <div class="flex items-center justify-between mb-4">
                                <div class="bg-${this.getCategoryColor(cat.category)}-100 p-3 rounded-full">
                                    <i class="fas ${this.getCategoryIcon(cat.category)} text-${this.getCategoryColor(cat.category)}-600 text-2xl"></i>
                                </div>
                            </div>
                            <h3 class="text-2xl font-bold text-gray-800 mb-1">${cat.unique_count}</h3>
                            <p class="text-sm text-gray-600">${this.getCategoryLabel(cat.category)}</p>
                            <p class="text-xs text-gray-500 mt-2">${cat.total_mentions} mentions</p>
                        </div>
                    `).join('')}
                </div>

                <div class="bg-white rounded-lg shadow-md p-6">
                    <h3 class="text-xl font-bold text-gray-800 mb-4">
                        🏆 Top 10 Entités
                    </h3>
                    <div class="space-y-3">
                        ${topData.entities.slice(0, 10).map((entity, i) => `
                            <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
                                 onclick="EntityManager.showEntityDetails('${entity.entity}')">
                                <div class="flex items-center space-x-3">
                                    <span class="text-lg font-bold text-gray-400">#${i + 1}</span>
                                    <div>
                                        <p class="font-semibold text-gray-800">${entity.entity}</p>
                                        <p class="text-xs text-gray-500">
                                            ${this.getCategoryLabel(entity.category)} • ${entity.articles} articles
                                        </p>
                                    </div>
                                </div>
                                <div class="text-right">
                                    <p class="text-sm font-bold text-gray-700">${entity.mentions}</p>
                                    <p class="text-xs text-gray-500">mentions</p>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
            
        } catch (error) {
            console.error('Erreur chargement dashboard:', error);
            container.innerHTML = `
                <div class="text-center py-8 text-red-500">
                    <i class="fas fa-exclamation-triangle text-2xl mb-2"></i>
                    <p>Erreur de chargement</p>
                </div>
            `;
        }
    }
    
    static async loadTopEntities(container) {
        container.innerHTML = `
            <div class="space-y-6">
                <!-- Filtres -->
                <div class="bg-white rounded-lg shadow-md p-4">
                    <div class="flex items-center space-x-4">
                        <label class="text-sm font-medium text-gray-700">Catégorie:</label>
                        <select id="entityCategoryFilter" onchange="EntityManager.filterTopEntities()" 
                                class="flex-1 p-2 border border-gray-300 rounded-lg">
                            <option value="">Toutes</option>
                            <option value="location">🌍 Lieux</option>
                            <option value="organization">🏛️ Organisations</option>
                            <option value="person">👤 Personnalités</option>
                            <option value="group">👥 Groupes</option>
                        </select>
                        <select id="entityLimitFilter" onchange="EntityManager.filterTopEntities()"
                                class="p-2 border border-gray-300 rounded-lg">
                            <option value="20">Top 20</option>
                            <option value="50">Top 50</option>
                            <option value="100">Top 100</option>
                        </select>
                    </div>
                </div>

                <!-- Liste -->
                <div id="topEntitiesList" class="bg-white rounded-lg shadow-md p-6">
                    <div class="text-center py-4">
                        <i class="fas fa-spinner fa-spin text-2xl"></i>
                    </div>
                </div>
            </div>
        `;
        
        this.filterTopEntities();
    }
    
    static async filterTopEntities() {
        const category = document.getElementById('entityCategoryFilter')?.value || '';
        const limit = document.getElementById('entityLimitFilter')?.value || '20';
        const container = document.getElementById('topEntitiesList');
        
        if (!container) return;
        
        container.innerHTML = '<div class="text-center py-4"><i class="fas fa-spinner fa-spin text-2xl"></i></div>';
        
        try {
            const url = `/api/entities/top?limit=${limit}${category ? `&category=${category}` : ''}`;
            const response = await fetch(url);
            const data = await response.json();
            
            if (!data.success) throw new Error('Erreur');
            
            container.innerHTML = `
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    ${data.entities.map((entity, i) => `
                        <div class="border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                             onclick="EntityManager.showEntityDetails('${entity.entity}')">
                            <div class="flex items-center justify-between mb-2">
                                <div class="flex items-center space-x-2">
                                    <span class="text-2xl font-bold text-gray-300">${i + 1}</span>
                                    <span class="text-lg font-semibold text-gray-800">${entity.entity}</span>
                                </div>
                                <span class="text-xs px-2 py-1 rounded-full ${this.getCategoryBadge(entity.category)}">
                                    ${this.getCategoryLabel(entity.category)}
                                </span>
                            </div>
                            <div class="flex items-center justify-between text-sm text-gray-600">
                                <span><i class="fas fa-hashtag mr-1"></i>${entity.mentions} mentions</span>
                                <span><i class="fas fa-newspaper mr-1"></i>${entity.articles} articles</span>
                                <span class="${entity.avg_sentiment > 0 ? 'text-green-600' : 'text-red-600'}">
                                    <i class="fas ${entity.avg_sentiment > 0 ? 'fa-smile' : 'fa-frown'} mr-1"></i>
                                    ${(entity.avg_sentiment * 100).toFixed(0)}%
                                </span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
            
        } catch (error) {
            console.error('Erreur filtrage:', error);
            container.innerHTML = '<div class="text-center py-4 text-red-500">Erreur de chargement</div>';
        }
    }
    
    static async loadSearch(container) {
        container.innerHTML = `
            <div class="space-y-6">
                <div class="bg-white rounded-lg shadow-md p-6">
                    <div class="flex items-center space-x-4">
                        <input type="text" id="entitySearchInput" 
                               placeholder="Rechercher une entité..." 
                               class="flex-1 p-3 border border-gray-300 rounded-lg"
                               onkeyup="if(event.key === 'Enter') EntityManager.searchEntities()">
                        <button onclick="EntityManager.searchEntities()" 
                                class="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700">
                            <i class="fas fa-search mr-2"></i>Rechercher
                        </button>
                    </div>
                </div>

                <div id="searchResults" class="bg-white rounded-lg shadow-md p-6">
                    <div class="text-center py-8 text-gray-500">
                        <i class="fas fa-search text-3xl mb-3"></i>
                        <p>Entrez un terme de recherche</p>
                    </div>
                </div>
            </div>
        `;
    }
    
    static async searchEntities() {
        const searchInput = document.getElementById('entitySearchInput');
        const resultsContainer = document.getElementById('searchResults');
        
        if (!searchInput || !resultsContainer) return;
        
        const term = searchInput.value.trim();
        if (!term) return;
        
        resultsContainer.innerHTML = '<div class="text-center py-4"><i class="fas fa-spinner fa-spin text-2xl"></i></div>';
        
        try {
            const response = await fetch(`/api/entities/search?q=${encodeURIComponent(term)}`);
            const data = await response.json();
            
            if (!data.success) throw new Error('Erreur');
            
            if (data.results.length === 0) {
                resultsContainer.innerHTML = `
                    <div class="text-center py-8 text-gray-500">
                        <i class="fas fa-inbox text-3xl mb-3"></i>
                        <p>Aucun résultat pour "${term}"</p>
                    </div>
                `;
                return;
            }
            
            resultsContainer.innerHTML = `
                <h4 class="font-semibold text-gray-800 mb-4">${data.count} résultat(s) trouvé(s)</h4>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    ${data.results.map(entity => `
                        <div class="border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                             onclick="EntityManager.showEntityDetails('${entity.entity}')">
                            <h5 class="font-semibold text-gray-800 mb-2">${entity.entity}</h5>
                            <div class="flex items-center justify-between text-sm">
                                <span class="text-xs px-2 py-1 rounded-full ${this.getCategoryBadge(entity.category)}">
                                    ${this.getCategoryLabel(entity.category)}
                                </span>
                                <span class="text-gray-600">${entity.mentions} mentions</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
            
        } catch (error) {
            console.error('Erreur recherche:', error);
            resultsContainer.innerHTML = '<div class="text-center py-4 text-red-500">Erreur de recherche</div>';
        }
    }
    
    static async batchAnalyzeArticles() {
        if (!confirm('Analyser tous les articles non traités ? Cela peut prendre plusieurs minutes.')) {
            return;
        }
        
        try {
            const response = await fetch('/api/entities/batch-analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const data = await response.json();
            
            if (data.success) {
                alert(`✅ Analyse terminée !\n\n` +
                      `Traités: ${data.processed}\n` +
                      `Erreurs: ${data.errors}\n` +
                      `Total: ${data.total}`);
                this.switchView(this.currentView);
            } else {
                alert('❌ Erreur: ' + data.error);
            }
            
        } catch (error) {
            alert('❌ Erreur réseau: ' + error.message);
        }
    }
    
    static getCategoryIcon(category) {
        const icons = {
            location: 'fa-map-marker-alt',
            organization: 'fa-building',
            person: 'fa-user',
            event: 'fa-calendar',
            group: 'fa-users'
        };
        return icons[category] || 'fa-tag';
    }
    
    static getCategoryColor(category) {
        const colors = {
            location: 'blue',
            organization: 'purple',
            person: 'green',
            event: 'orange',
            group: 'red'
        };
        return colors[category] || 'gray';
    }
    
    static getCategoryLabel(category) {
        const labels = {
            location: 'Lieux',
            organization: 'Organisations',
            person: 'Personnalités',
            event: 'Événements',
            group: 'Groupes'
        };
        return labels[category] || category;
    }
    
    static getCategoryBadge(category) {
        const color = this.getCategoryColor(category);
        return `bg-${color}-100 text-${color}-800`;
    }
    
    static async showEntityDetails(entityText) {
        // Afficher modal avec détails
        console.log('Détails entité:', entityText);
        alert(`Détails pour: ${entityText}\n(À implémenter)`);
    }
    
    static async loadNetwork(container) {
        container.innerHTML = `
            <div class="bg-yellow-50 border-l-4 border-yellow-500 p-4">
                <p class="text-yellow-800">
                    <i class="fas fa-info-circle mr-2"></i>
                    Visualisation réseau en développement
                </p>
            </div>
        `;
    }
}

// Initialisation
document.addEventListener('DOMContentLoaded', function() {
    window.EntityManager = EntityManager;
    console.log('✅ EntityManager initialisé');
});