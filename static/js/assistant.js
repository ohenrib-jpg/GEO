// static/js/assistant.js - VERSION CORRIGÉE ET UNIFIÉE
class GEOAssistant {
    constructor() {
        this.isOpen = false;
        this.isMinimized = false;
        this.conversationHistory = [];
        this.currentContext = {};
        this.serverStatus = 'checking';
        this.init();
    }

    init() {
        this.createDOM();
        this.setupEventListeners();
        this.checkServerStatus();
        console.log("🤖 GEO Assistant initialisé");
    }

    async checkServerStatus() {
        try {
            const response = await fetch('/api/assistant/status');
            const data = await response.json();

            if (data.success) {
                this.serverStatus = data.connected ? 'connected' : 'disconnected';
                this.updateStatusDisplay();
            } else {
                this.serverStatus = 'error';
                this.updateStatusDisplay();
            }
        } catch (error) {
            this.serverStatus = 'error';
            this.updateStatusDisplay();
        }
    }

    updateStatusDisplay() {
        const statusElement = document.querySelector('.status-indicator');
        const modelInfo = document.querySelector('.model-info');

        if (!statusElement) return;

        switch (this.serverStatus) {
            case 'connected':
                statusElement.className = 'status-indicator online';
                statusElement.innerHTML = '● En ligne';
                if (modelInfo) modelInfo.textContent = 'Mistral 7B - Prêt';
                break;
            case 'disconnected':
                statusElement.className = 'status-indicator offline';
                statusElement.innerHTML = '● Hors ligne';
                if (modelInfo) modelInfo.textContent = 'Mistral 7B - Offline';
                break;
            case 'error':
                statusElement.className = 'status-indicator error';
                statusElement.innerHTML = '● Erreur';
                if (modelInfo) modelInfo.textContent = 'Service indisponible';
                break;
            default:
                statusElement.className = 'status-indicator checking';
                statusElement.innerHTML = '● Vérification...';
        }
    }

    async sendMessage() {
        const input = document.getElementById('assistant-input');
        const message = input.value.trim();

        if (!message) return;

        // Ajouter le message utilisateur
        this.addMessage('user', message);
        input.value = '';

        // Indicateur de frappe
        this.showTypingIndicator();

        try {
            const pageType = this.detectPageType();
            const response = await fetch('/api/assistant/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    page: pageType
                })
            });

            const data = await response.json();
            this.hideTypingIndicator();

            if (data.success) {
                this.addMessage('assistant', data.response);
                this.serverStatus = 'connected';
                this.updateStatusDisplay();
            } else {
                this.addMessage('assistant',
                    data.response || `Erreur: ${data.error}`,
                    'error'
                );

                // Si erreur de connexion, mettre à jour le statut
                if (data.error && data.error.includes('inaccessible')) {
                    this.serverStatus = 'disconnected';
                    this.updateStatusDisplay();
                }
            }

        } catch (error) {
            this.hideTypingIndicator();
            this.addMessage('assistant',
                'Erreur de connexion au serveur.',
                'error'
            );
            this.serverStatus = 'error';
            this.updateStatusDisplay();
        }
    }

    addMessage(role, content, type = 'normal') {
        const messagesContainer = document.getElementById('assistant-messages');
        const messageDiv = document.createElement('div');

        messageDiv.className = `message ${role}-message ${type}`;
        messageDiv.innerHTML = `
            <div class="message-avatar">
                <i class="fas ${role === 'user' ? 'fa-user' : 'fa-robot'}"></i>
            </div>
            <div class="message-content">
                <div class="message-text">${this.formatMessage(content)}</div>
                <div class="message-time">${new Date().toLocaleTimeString('fr-FR')}</div>
            </div>
        `;

        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    formatMessage(content) {
        // Formater les messages (markdown basique)
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>');
    }

    showTypingIndicator() {
        const messagesContainer = document.getElementById('assistant-messages');
        const typingDiv = document.createElement('div');
        typingDiv.id = 'typing-indicator';
        typingDiv.className = 'message assistant-message typing';
        typingDiv.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;

        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    detectPageType() {
        const path = window.location.pathname;
        if (path.includes('economic-dashboard') || path.includes('/economic-dashboard'))
            return 'economic-dashboard';
        if (path.includes('indicateurs-francais') || path.includes('/indicateurs'))
            return 'indicateurs-francais';
        if (path.includes('geopolitique') || path.includes('/archiviste'))
            return 'geopolitique';
        if (path.includes('social') || path.includes('/social'))
            return 'social';
        return 'generic';
    }

    createDOM() {
        const assistantHTML = `
            <div id="geo-assistant" class="geo-assistant hidden">
                <div class="assistant-header">
                    <div class="header-content">
                        <i class="fas fa-robot mr-2"></i>
                        <span class="assistant-title">GEOPOL Assistant</span>
                        <div class="header-actions">
                            <button id="assistant-minimize" class="btn-icon" title="Réduire">
                                <i class="fas fa-window-minimize"></i>
                            </button>
                            <button id="assistant-close" class="btn-icon" title="Fermer">
                                <i class="fas fa-times"></i>
                            </button>
                        </div>
                    </div>
                </div>
                
                <div class="assistant-body">
                    <div id="assistant-messages" class="assistant-messages">
                        <div class="message assistant-message">
                            <div class="message-avatar">
                                <i class="fas fa-robot"></i>
                            </div>
                            <div class="message-content">
                                <p>Bonjour ! Je suis GEOPOL Assistant. Je peux vous aider à analyser les données économiques et géopolitiques.</p>
                                <div class="message-time">${new Date().toLocaleTimeString('fr-FR')}</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="assistant-input-container">
                        <div class="quick-actions">
                            <button class="quick-action" data-action="explain-data">
                                <i class="fas fa-chart-line"></i>
                                Expliquer ces données
                            </button>
                            <button class="quick-action" data-action="economic-context">
                                <i class="fas fa-euro-sign"></i>
                                Contexte économique
                            </button>
                        </div>
                        
                        <div class="input-group">
                            <input type="text" id="assistant-input" 
                                   placeholder="Posez votre question..." 
                                   maxlength="500">
                            <button id="assistant-send" class="btn-send">
                                <i class="fas fa-paper-plane"></i>
                            </button>
                        </div>
                    </div>
                </div>
                
                <div class="assistant-footer">
                    <div class="footer-info">
                        <span class="model-info">Mistral 7B</span>
                        <span class="status-indicator checking">● Vérification...</span>
                    </div>
                </div>
            </div>
            
            <button id="assistant-toggle" class="assistant-toggle">
                <i class="fas fa-robot"></i>
                <span class="notification-dot"></span>
            </button>
        `;

        document.body.insertAdjacentHTML('beforeend', assistantHTML);
    }

    setupEventListeners() {
        // Toggle de l'assistant
        document.getElementById('assistant-toggle').addEventListener('click', () => this.toggleAssistant());

        // Actions de l'en-tête
        document.getElementById('assistant-minimize').addEventListener('click', () => this.toggleMinimize());
        document.getElementById('assistant-close').addEventListener('click', () => this.closeAssistant());

        // Envoi de message
        document.getElementById('assistant-send').addEventListener('click', () => this.sendMessage());
        document.getElementById('assistant-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });

        // Actions rapides
        document.querySelectorAll('.quick-action').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = e.currentTarget.dataset.action;
                this.handleQuickAction(action);
            });
        });
    }

    handleQuickAction(action) {
        const actions = {
            'explain-data': {
                message: "Peux-tu m'expliquer ces données en détail ? Qu'est-ce que cela signifie ?",
                context: 'analysis'
            },
            'economic-context': {
                message: "Quel est le contexte économique actuel autour de ces indicateurs ?",
                context: 'economic'
            }
        };

        if (actions[action]) {
            const input = document.getElementById('assistant-input');
            input.value = actions[action].message;
            this.sendMessage();
        }
    }

    toggleAssistant() {
        const assistant = document.getElementById('geo-assistant');
        const toggle = document.getElementById('assistant-toggle');

        if (this.isMinimized) {
            this.isMinimized = false;
            assistant.classList.remove('minimized');
        }

        this.isOpen = !this.isOpen;

        if (this.isOpen) {
            assistant.classList.remove('hidden');
            toggle.classList.add('active');
        } else {
            assistant.classList.add('hidden');
            toggle.classList.remove('active');
        }
    }

    toggleMinimize() {
        this.isMinimized = !this.isMinimized;
        const assistant = document.getElementById('geo-assistant');

        if (this.isMinimized) {
            assistant.classList.add('minimized');
        } else {
            assistant.classList.remove('minimized');
        }
    }

    closeAssistant() {
        this.isOpen = false;
        this.isMinimized = false;

        const assistant = document.getElementById('geo-assistant');
        const toggle = document.getElementById('assistant-toggle');

        assistant.classList.add('hidden');
        toggle.classList.remove('active');
    }
}

// Initialisation globale
document.addEventListener('DOMContentLoaded', function () {
    window.GEOAssistant = new GEOAssistant();
    console.log("🤖 GEOPOL Assistant chargé");
});