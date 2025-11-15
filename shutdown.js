// static/js/shutdown.js

class ShutdownManager {
    constructor() {
        this.shutdownBtn = document.getElementById('shutdownBtn');
        this.isShuttingDown = false;

        if (this.shutdownBtn) {
            this.initShutdownHandler();
        }
    }

    initShutdownHandler() {
        this.shutdownBtn.addEventListener('click', () => {
            this.initiateShutdown();
        });
    }

    async initiateShutdown() {
        if (this.isShuttingDown) return;

        const confirmed = confirm(
            '⚠️ Êtes-vous sûr de vouloir arrêter le système ?\n\n' +
            'Cette action va :\n' +
            '• Arrêter tous les processus en cours\n' +
            '• Sauvegarder les données\n' +
            '• Fermer proprement l\'application\n\n' +
            'L\'application se fermera automatiquement.'
        );

        if (!confirmed) return;

        this.isShuttingDown = true;
        this.updateButtonState('Arrêt en cours...', true);

        try {
            const response = await fetch('/api/system/shutdown', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (response.ok) {
                this.showShutdownMessage('✅ Arrêt réussi - Fermeture...');
                setTimeout(() => {
                    window.close();
                    // Redirection vers une page de confirmation si la fenêtre ne se ferme pas
                    window.location.href = '/shutdown-complete';
                }, 2000);
            } else {
                throw new Error('Erreur lors de l\'arrêt');
            }
        } catch (error) {
            console.error('Erreur arrêt:', error);
            this.showShutdownMessage('❌ Erreur lors de l\'arrêt', true);
            this.updateButtonState('Réessayer', false);
            this.isShuttingDown = false;
        }
    }

    updateButtonState(text, disabled) {
        this.shutdownBtn.innerHTML = disabled ?
            `<i class="fas fa-spinner fa-spin mr-2"></i>${text}` :
            `<i class="fas fa-power-off mr-2"></i>${text}`;

        this.shutdownBtn.disabled = disabled;
        this.shutdownBtn.classList.toggle('bg-red-600', !disabled);
        this.shutdownBtn.classList.toggle('bg-gray-400', disabled);
        this.shutdownBtn.classList.toggle('hover:bg-red-700', !disabled);
    }

    showShutdownMessage(message, isError = false) {
        // Créer une notification
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${isError ? 'bg-red-500 text-white' : 'bg-green-500 text-white'
            }`;
        notification.innerHTML = `
            <div class="flex items-center">
                <i class="fas ${isError ? 'fa-exclamation-triangle' : 'fa-check-circle'} mr-2"></i>
                <span>${message}</span>
            </div>
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
}

// Initialisation
document.addEventListener('DOMContentLoaded', () => {
    new ShutdownManager();
});