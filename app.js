// static/js/app.js - Fonctions globales et utilitaires

// Configuration
const CONFIG = {
    API_BASE_URL: '',
    DEBOUNCE_DELAY: 300
};

// Utilitaires de formatage
class Formatters {
    static formatDate(dateString) {
        if (!dateString) return 'Date inconnue';
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('fr-FR', {
                day: 'numeric',
                month: 'short',
                year: 'numeric'
            });
        } catch (e) {
            return 'Date invalide';
        }
    }

    static truncateText(text, maxLength = 200) {
        if (!text) return 'Aucun contenu';
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

    static getSentimentColor(sentiment) {
        switch (sentiment) {
            case 'positive': return 'border-green-500';
            case 'negative': return 'border-red-500';
            default: return 'border-gray-500';
        }
    }

    static getSentimentBadge(sentiment) {
        switch (sentiment) {
            case 'positive': return 'bg-green-100 text-green-800';
            case 'negative': return 'bg-red-100 text-red-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    }

    static getSentimentIcon(sentiment) {
        switch (sentiment) {
            case 'positive': return 'fa-smile';
            case 'negative': return 'fa-frown';
            default: return 'fa-meh';
        }
    }
}

// Gestionnaire d'API
class ApiClient {
    static async get(url) {
        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('API GET Error:', error);
            throw error;
        }
    }

    static async post(url, data) {
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('API POST Error:', error);
            throw error;
        }
    }

    static async delete(url) {
        try {
            const response = await fetch(url, { method: 'DELETE' });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('API DELETE Error:', error);
            throw error;
        }
    }
}

// Gestionnaire de modales
class ModalManager {
    static showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('hidden');
        }
    }

    static hideModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    static setupModalClose(modalId, closeButtonId) {
        const modal = document.getElementById(modalId);
        const closeBtn = document.getElementById(closeButtonId);

        if (modal && closeBtn) {
            closeBtn.addEventListener('click', () => this.hideModal(modalId));
            modal.addEventListener('click', (e) => {
                if (e.target === modal) this.hideModal(modalId);
            });
        }
    }
}

// Gestionnaire de navigation
class NavigationManager {
    static init() {
        this.setupMobileMenu();
        this.setupCurrentTime();
        this.setupNavigationLinks();
    }

    static setupMobileMenu() {
        const menuToggle = document.getElementById('menuToggle');
        const overlay = document.getElementById('overlay');
        const sidebar = document.querySelector('.sidebar');

        if (menuToggle && overlay && sidebar) {
            menuToggle.addEventListener('click', () => {
                sidebar.classList.toggle('active');
                overlay.classList.toggle('hidden');
            });

            overlay.addEventListener('click', () => {
                sidebar.classList.remove('active');
                overlay.classList.add('hidden');
            });
        }
    }

    static setupCurrentTime() {
        const updateTime = () => {
            const now = new Date();
            const currentTimeElement = document.getElementById('currentTime');
            if (currentTimeElement) {
                currentTimeElement.textContent = now.toLocaleTimeString('fr-FR', {
                    hour: '2-digit',
                    minute: '2-digit'
                });
            }
        };

        updateTime();
        setInterval(updateTime, 1000);
    }

    static setupNavigationLinks() {
        // Navigation vers la gestion des thèmes
        const navThemes = document.querySelector('.nav-themes');
        if (navThemes) {
            navThemes.addEventListener('click', function (e) {
                e.preventDefault();
                if (typeof ThemeManager !== 'undefined') {
                    ThemeManager.loadThemes();
                    ModalManager.showModal('themeManagerModal');
                } else {
                    console.error('ThemeManager non disponible');
                }
            });
        }

        // Navigation vers les articles
        const navArticles = document.querySelector('.nav-articles');
        if (navArticles) {
            navArticles.addEventListener('click', function (e) {
                e.preventDefault();
                if (typeof ArticleManager !== 'undefined') {
                    ArticleManager.showAllArticles();
                } else {
                    console.error('ArticleManager non disponible');
                }
            });
        }

        // Navigation vers les paramètres
        const navSettings = document.querySelector('.nav-settings');
        if (navSettings) {
            navSettings.addEventListener('click', function (e) {
                e.preventDefault();
                if (typeof SettingsManager !== 'undefined') {
                    SettingsManager.showSettings();
                } else {
                    console.error('SettingsManager non disponible');
                }
            });
        }
    }
}

// Initialisation globale
document.addEventListener('DOMContentLoaded', function () {
    NavigationManager.init();
    ModalManager.setupModalClose('themeManagerModal', 'closeThemeManager');

    console.log('✅ App initialisée');
});

// Exposer les classes globalement
window.Formatters = Formatters;
window.ApiClient = ApiClient;
window.ModalManager = ModalManager;
window.NavigationManager = NavigationManager;