  
static async generateIAReport() {
        const btn = document.getElementById('generateReportBtn');
        const resultDiv = document.getElementById('iaReportResult');

        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Génération en cours...';
        
        // Affichage progressif
        resultDiv.innerHTML = `
            <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div class="flex items-center mb-3">
                    <i class="fas fa-spinner fa-spin text-blue-600 text-xl mr-3"></i>
                    <div class="flex-1">
                        <p class="text-blue-800 font-semibold">Génération du rapport en cours...</p>
                        <p class="text-blue-600 text-sm" id="progressStatus">Collecte des données...</p>
                    </div>
                </div>
                <div class="bg-white rounded p-2 mt-2">
                    <div class="h-2 bg-blue-200 rounded overflow-hidden">
                        <div id="progressBar" class="h-full bg-blue-600 transition-all duration-500" style="width: 0%"></div>
                    </div>
                </div>
            </div>
        `;

        try {
            const reportType = document.getElementById('reportType').value;
            const startDate = document.getElementById('startDate').value;
            const endDate = document.getElementById('endDate').value;
            const includeSentiment = document.getElementById('includeSentiment').checked;
            const includeSources = document.getElementById('includeSources').checked;
            const generatePDF = document.getElementById('generatePDF').checked;

            const selectedThemes = Array.from(document.querySelectorAll('.theme-checkbox:checked'))
                .map(cb => cb.value);

            const requestData = {
                report_type: reportType,
                start_date: startDate,
                end_date: endDate,
                themes: selectedThemes,
                include_sentiment: includeSentiment,
                include_sources: includeSources,
                generate_pdf: generatePDF
            };

            // Mise à jour progression: Collecte
            this.updateProgress(10, 'Collecte des articles...');

            const response = await fetch('/api/generate-ia-report', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });

            // Mise à jour progression: Analyse IA
            this.updateProgress(40, 'Analyse par le modèle IA Llama 3.2...');

            const data = await response.json();

            if (data.success) {
                this.updateProgress(100, 'Rapport généré avec succès !');
                setTimeout(() => {
                    this.displayIAReportResults(data, resultDiv, generatePDF);
                }, 500);
            } else {
                resultDiv.innerHTML = `
                    <div class="bg-red-50 border border-red-200 rounded-lg p-4">
                        <p class="text-red-800 font-semibold">❌ Erreur lors de la génération</p>
                        <p class="text-red-600 text-sm mt-1">${data.error || 'Erreur inconnue'}</p>
                        ${data.llama_error ? `<p class="text-red-500 text-xs mt-2">Détail: ${data.llama_error}</p>` : ''}
                    </div>
                `;
            }

        } catch (error) {
            resultDiv.innerHTML = `
                <div class="bg-red-50 border border-red-200 rounded-lg p-4">
                    <p class="text-red-800 font-semibold">❌ Erreur réseau</p>
                    <p class="text-red-600 text-sm mt-1">${error.message}</p>
                </div>
            `;
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-magic mr-2"></i>Générer le rapport IA';
        }
    }

    static updateProgress(percentage, statusText) {
        const progressBar = document.getElementById('progressBar');
        const statusElement = document.getElementById('progressStatus');
        
        if (progressBar) {
            progressBar.style.width = percentage + '%';
        }
        if (statusElement) {
            statusElement.textContent = statusText;
        }
    }