// static/js/advanced-analysis.js - Analyse avancée (Bayésien + Corroboration + IA)

class AdvancedAnalysisManager {
    static async showAnalysisPanel() {
        const content = document.getElementById('themeManagerContent');
        const title = document.getElementById('modalTitle');

        if (!content || !title) return;

        title.textContent = '🔬 Analyse Avancée';

        content.innerHTML = `
            <div class="max-w-6xl mx-auto space-y-6">
                <!-- En-tête explicatif -->
                <div class="bg-gradient-to-r from-purple-50 to-blue-50 border-l-4 border-purple-500 p-4 rounded-lg">
                    <div class="flex items-start">
                        <div class="flex-shrink-0">
                            <i class="fas fa-info-circle text-purple-500 text-2xl"></i>
                        </div>
                        <div class="ml-3">
                            <h3 class="text-lg font-semibold text-gray-800">Analyse Bayésienne & Corroboration</h3>
                            <p class="mt-2 text-sm text-gray-600">
                                L'analyse bayésienne améliore la précision du sentiment en combinant plusieurs sources d'évidence.
                                La corroboration identifie les articles similaires pour renforcer ou nuancer l'analyse.
                            </p>
                        </div>
                    </div>
                </div>

                <!-- Actions rapides -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <!-- Analyse d'un article -->
                    <div class="bg-white rounded-lg shadow-md p-6">
                        <h3 class="text-xl font-bold text-gray-800 mb-4">
                            <i class="fas fa-microscope text-indigo-600 mr-2"></i>
                            Analyser un article
                        </h3>
                        <p class="text-gray-600 mb-4 text-sm">
                            Analyse complète (corroboration + bayésien) d'un article spécifique
                        </p>
                        <div class="space-y-3">
                            <input type="number" 
                                   id="singleArticleId" 
                                   placeholder="ID de l'article"
                                   class="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500">
                            <button onclick="AdvancedAnalysisManager.analyzeSingleArticle()"
                                    id="analyzeSingleBtn"
                                    class="w-full bg-indigo-600 text-white px-4 py-3 rounded-lg hover:bg-indigo-700 transition duration-200">
                                <i class="fas fa-play mr-2"></i>Lancer l'analyse
                            </button>
                        </div>
                        <div id="singleAnalysisResult" class="mt-4"></div>
                    </div>

                    <!-- Analyse batch -->
                    <div class="bg-white rounded-lg shadow-md p-6">
                        <h3 class="text-xl font-bold text-gray-800 mb-4">
                            <i class="fas fa-layer-group text-green-600 mr-2"></i>
                            Analyse en masse
                        </h3>
                        <p class="text-gray-600 mb-4 text-sm">
                            Traiter tous les articles récents (7 derniers jours)
                        </p>
                        <div class="space-y-3">
                            <button onclick="AdvancedAnalysisManager.batchAnalyzeCorroboration()"
                                    id="batchCorroborationBtn"
                                    class="w-full bg-blue-600 text-white px-4 py-3 rounded-lg hover:bg-blue-700 transition duration-200">
                                <i class="fas fa-network-wired mr-2"></i>Corroboration batch
                            </button>
                            <button onclick="GeoNarrativeManager.showGeoNarrativePanel()"
                                     class="btn btn-geo-narrative">
                               <i class="fas fa-globe-europe"></i>
                               Cartographie Narrative
                           </button>
                        </div>
                        <div id="batchAnalysisResult" class="mt-4"></div>
                    </div>
                </div>

                <!-- SECTION IA LOCALE POUR RAPPORTS -->
                <div class="bg-white rounded-lg shadow-md p-6">
                    <h3 class="text-xl font-bold text-gray-800 mb-4">
                        <i class="fas fa-robot text-orange-500 mr-2"></i>
                        Analyse IA Locale (Llama 3.2)
                    </h3>
                    <p class="text-gray-600 mb-4 text-sm">
                        Génération de rapports d'analyse géopolitique avec l'IA locale
                    </p>
                    
                    <div class="space-y-4">
                        <!-- Sélection du type de rapport -->
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">
                                Type de rapport
                            </label>
                            <select id="reportType" class="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500">
                                <option value="geopolitique">Analyse Géopolitique</option>
                                <option value="economique">Analyse Économique</option>
                                <option value="securite">Analyse Sécurité</option>
                                <option value="synthese">Synthèse Hebdomadaire</option>
                            </select>
                        </div>

                        <!-- Période d'analyse -->
                        <div class="grid grid-cols-2 gap-4">
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">
                                    Date de début
                                </label>
                                <input type="date" id="startDate" class="w-full p-2 border border-gray-300 rounded-lg">
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">
                                    Date de fin
                                </label>
                                <input type="date" id="endDate" class="w-full p-2 border border-gray-300 rounded-lg">
                            </div>
                        </div>

                        <!-- Thèmes à inclure -->
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">
                                Thèmes à analyser
                            </label>
                            <div id="themeSelection" class="space-y-2 max-h-32 overflow-y-auto border border-gray-300 rounded-lg p-3">
                                <!-- Les thèmes seront chargés dynamiquement -->
                                <div class="text-center text-gray-500 py-4">
                                    <i class="fas fa-spinner fa-spin mr-2"></i>
                                    Chargement des thèmes...
                                </div>
                            </div>
                        </div>

                        <!-- Options avancées -->
                        <div class="bg-gray-50 p-4 rounded-lg">
                            <label class="flex items-center">
                                <input type="checkbox" id="includeSentiment" checked class="rounded border-gray-300 text-orange-600 focus:ring-orange-500">
                                <span class="ml-2 text-sm text-gray-700">Inclure l'analyse des sentiments</span>
                            </label>
                            <label class="flex items-center mt-2">
                                <input type="checkbox" id="includeSources" checked class="rounded border-gray-300 text-orange-600 focus:ring-orange-500">
                                <span class="ml-2 text-sm text-gray-700">Inclure les sources</span>
                            </label>
                            <label class="flex items-center mt-2">
                                <input type="checkbox" id="generatePDF" checked class="rounded border-gray-300 text-orange-600 focus:ring-orange-500">
                                <span class="ml-2 text-sm text-gray-700">Générer un PDF</span>
                            </label>
                        </div>

                        <!-- Bouton de génération -->
                        <button onclick="AdvancedAnalysisManager.generateIAReport()"
                                id="generateReportBtn"
                                class="w-full bg-orange-600 text-white px-4 py-3 rounded-lg hover:bg-orange-700 transition duration-200 font-semibold">
                            <i class="fas fa-magic mr-2"></i>Générer le rapport IA
                        </button>

                        <!-- Résultats de l'IA -->
                        <div id="iaReportResult" class="mt-4"></div>
                    </div>
                </div>

                <!-- Résultats détaillés -->
                <div id="detailedResults" class="hidden">
                    <div class="bg-white rounded-lg shadow-md p-6">
                        <h3 class="text-xl font-bold text-gray-800 mb-4">
                            📊 Résultats détaillés
                        </h3>
                        <div id="resultsContent"></div>
                    </div>
                </div>

                <!-- Historique des analyses -->
                <div class="bg-white rounded-lg shadow-md p-6">
                    <h3 class="text-xl font-bold text-gray-800 mb-4">
                        <i class="fas fa-history text-gray-600 mr-2"></i>
                        Articles avec analyse avancée
                    </h3>
                    <div id="analyzedArticlesList" class="space-y-3">
                        <div class="text-center py-4 text-gray-500">
                            <i class="fas fa-spinner fa-spin text-xl mb-2"></i>
                            <p>Chargement...</p>
                        </div>
                    </div>
                </div>
            </div>
        `;

        ModalManager.showModal('themeManagerModal');
        this.loadAnalyzedArticles();
        this.loadThemesForIA();
    }

    static async loadThemesForIA() {
        const container = document.getElementById('themeSelection');
        if (!container) return;

        try {
            const response = await fetch('/api/themes');
            const data = await response.json();

            if (data.themes && data.themes.length > 0) {
                container.innerHTML = data.themes.map(theme => `
                    <label class="flex items-center">
                        <input type="checkbox" value="${theme.id}" checked 
                               class="theme-checkbox rounded border-gray-300 text-orange-600 focus:ring-orange-500">
                        <span class="ml-2 text-sm text-gray-700">${theme.name}</span>
                    </label>
                `).join('');
            } else {
                container.innerHTML = '<p class="text-gray-500 text-sm">Aucun thème disponible</p>';
            }
        } catch (error) {
            container.innerHTML = '<p class="text-red-500 text-sm">Erreur de chargement des thèmes</p>';
        }
    }

    static async generateIAReport() {
        const btn = document.getElementById('generateReportBtn');
        const resultDiv = document.getElementById('iaReportResult');

        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Génération en cours...';
        resultDiv.innerHTML = '<div class="text-blue-600 text-sm">🔄 L\'IA analyse les articles et génère le rapport...</div>';

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

            const response = await fetch('/api/generate-ia-report', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });

            const data = await response.json();

            if (data.success) {
                this.displayIAReportResults(data, resultDiv, generatePDF);
            } else {
                resultDiv.innerHTML = `
                    <div class="bg-red-50 border border-red-200 rounded-lg p-4">
                        <p class="text-red-800 font-semibold">❌ Erreur lors de la génération</p>
                        <p class="text-red-600 text-sm mt-1">${data.error || 'Erreur inconnue'}</p>
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

    static displayIAReportResults(data, container, generatePDF) {
        let pdfSection = '';

        if (generatePDF && data.analysis_html) {
            // Échapper le HTML pour le passer en paramètre JS de manière sécurisée
            const safeHtml = data.analysis_html
                .replace(/\\/g, '\\\\')  // Échapper les backslashes
                .replace(/`/g, '\\`')    // Échapper les backticks
                .replace(/\$/g, '\\$')   // Échapper les dollars
                .replace(/'/g, "\\'")    // Échapper les apostrophes
                .replace(/"/g, '\\"');   // Échapper les guillemets

            pdfSection = `
        <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 class="font-semibold text-blue-800 mb-2">📄 Générer le PDF</h4>
            <p class="text-blue-600 text-sm mb-3">Cliquez pour générer et télécharger le rapport PDF.</p>
            <button id="pdfGenerateBtn" 
                    class="inline-flex items-center bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition duration-200">
                <i class="fas fa-download mr-2"></i>Générer le PDF
            </button>
        </div>
        `;
        }

        container.innerHTML = `
        <div class="space-y-4">
            <div class="bg-green-50 border border-green-200 rounded-lg p-4">
                <p class="text-green-800 font-semibold">✅ Rapport généré avec succès !</p>
            </div>
            
            <div class="bg-white border border-gray-200 rounded-lg p-4">
                <h4 class="font-semibold text-gray-800 mb-3">📋 Résumé du rapport</h4>
                <div class="space-y-2 text-sm">
                    <p><strong>Type:</strong> ${data.report_type}</p>
                    <p><strong>Articles analysés:</strong> ${data.articles_analyzed}</p>
                    <p><strong>Thèmes couverts:</strong> ${data.themes_covered?.join(', ') || 'Tous'}</p>
                    <p><strong>Période:</strong> ${data.period}</p>
                    ${data.llama_status ? `
                        <p><strong>Mode:</strong> 
                            <span class="px-2 py-1 rounded text-xs ${data.llama_status.success ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}">
                                ${data.llama_status.mode}
                            </span>
                        </p>
                    ` : ''}
                </div>
            </div>

            <div class="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <h4 class="font-semibold text-gray-800 mb-3">🧠 Analyse IA</h4>
                <div class="prose prose-sm max-w-none" id="analysisContent">
                    ${data.analysis_html || '<p class="text-gray-600">Aucune analyse disponible</p>'}
                </div>
            </div>

            ${pdfSection}
        </div>
    `;

        // Attacher l'événement au bouton PDF après injection du HTML
        if (generatePDF && data.analysis_html) {
            setTimeout(() => {
                const pdfBtn = document.getElementById('pdfGenerateBtn');
                if (pdfBtn) {
                    pdfBtn.addEventListener('click', () => {
                        AdvancedAnalysisManager.generatePDFFromAnalysis(data.report_type, data.analysis_html);
                    });
                }
            }, 100);
        }
    }

    static async generatePDFFromAnalysis(reportType, htmlContent) {
        try {
            const response = await fetch('/api/generate-pdf', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    html_content: htmlContent,
                    title: `Rapport ${reportType}`,
                    type: reportType
                })
            });

            if (response.ok) {
                // Télécharger le PDF
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = `rapport_${reportType}_${new Date().toISOString().slice(0, 10)}.pdf`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            } else {
                const errorData = await response.json();
                alert('Erreur lors de la génération du PDF: ' + (errorData.error || 'Erreur inconnue'));
            }
        } catch (error) {
            console.error('Erreur génération PDF:', error);
            alert('Erreur lors de la génération du PDF: ' + error.message);
        }
    }

    static async analyzeSingleArticle() {
        const articleId = document.getElementById('singleArticleId').value;
        const resultDiv = document.getElementById('singleAnalysisResult');
        const btn = document.getElementById('analyzeSingleBtn');

        if (!articleId) {
            this.showAlert(resultDiv, 'Veuillez entrer un ID d\'article', 'error');
            return;
        }

        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Analyse en cours...';
        resultDiv.innerHTML = '<p class="text-blue-600 text-sm">⏳ Analyse en cours...</p>';

        try {
            const response = await fetch(`/api/advanced/full-analysis/${articleId}`, {
                method: 'POST'
            });

            const data = await response.json();

            if (data.success) {
                this.displaySingleAnalysisResults(data, resultDiv);
                this.loadAnalyzedArticles();
            } else {
                this.showAlert(resultDiv, data.error || 'Erreur lors de l\'analyse', 'error');
            }
        } catch (error) {
            this.showAlert(resultDiv, 'Erreur réseau: ' + error.message, 'error');
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-play mr-2"></i>Lancer l\'analyse';
        }
    }

    static displaySingleAnalysisResults(data, container) {
        const corr = data.corroboration;
        const bayes = data.bayesian_analysis;

        container.innerHTML = `
            <div class="mt-4 space-y-3">
                <div class="bg-green-50 border border-green-200 rounded-lg p-3">
                    <p class="font-semibold text-green-800">✅ Analyse terminée avec succès</p>
                </div>
                
                <div class="grid grid-cols-2 gap-3 text-sm">
                    <div class="bg-blue-50 p-3 rounded">
                        <p class="font-medium text-blue-800">Corroborations</p>
                        <p class="text-2xl font-bold text-blue-600">${corr.count}</p>
                    </div>
                    <div class="bg-purple-50 p-3 rounded">
                        <p class="font-medium text-purple-800">Confiance bayésienne</p>
                        <p class="text-2xl font-bold text-purple-600">${(bayes.bayesian_confidence * 100).toFixed(1)}%</p>
                    </div>
                </div>

                <div class="bg-gray-50 p-3 rounded text-sm">
                    <p><strong>Sentiment original:</strong> ${bayes.original_score?.toFixed(3) || 'N/A'}</p>
                    <p><strong>Sentiment bayésien:</strong> ${bayes.bayesian_score?.toFixed(3) || 'N/A'}</p>
                    <p><strong>Type:</strong> <span class="px-2 py-1 rounded ${this.getSentimentBadge(bayes.sentiment_type)}">${bayes.sentiment_type}</span></p>
                    <p><strong>Évidences utilisées:</strong> ${bayes.evidence_count}</p>
                </div>

                ${corr.count > 0 ? `
                    <div class="mt-3">
                        <p class="font-semibold text-gray-700 mb-2">Top articles corroborants:</p>
                        <div class="space-y-2">
                            ${corr.articles.slice(0, 3).map(art => `
                                <div class="bg-white border border-gray-200 p-2 rounded text-sm">
                                    <p class="font-medium">${art.title}</p>
                                    <p class="text-gray-600">Similarité: ${(art.similarity * 100).toFixed(1)}%</p>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
    }

    static async batchAnalyzeCorroboration() {
        const resultDiv = document.getElementById('batchAnalysisResult');
        const btn = document.getElementById('batchCorroborationBtn');

        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Traitement...';
        resultDiv.innerHTML = '<p class="text-blue-600 text-sm mt-3">⏳ Traitement en cours...</p>';

        try {
            const response = await fetch('/api/corroboration/batch-process', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({})
            });

            const data = await response.json();

            if (data.success) {
                const stats = data.stats;
                resultDiv.innerHTML = `
                    <div class="mt-3 bg-green-50 border border-green-200 rounded-lg p-3 text-sm">
                        <p class="font-semibold text-green-800">✅ Traitement terminé</p>
                        <div class="mt-2 space-y-1">
                            <p>📄 Articles traités: <strong>${stats.processed}</strong></p>
                            <p>🔗 Corroborations trouvées: <strong>${stats.corroborations_found}</strong></p>
                            ${stats.errors > 0 ? `<p>⚠️ Erreurs: ${stats.errors}</p>` : ''}
                        </div>
                    </div>
                `;
                this.loadAnalyzedArticles();
            } else {
                this.showAlert(resultDiv, data.error || 'Erreur', 'error');
            }
        } catch (error) {
            this.showAlert(resultDiv, 'Erreur: ' + error.message, 'error');
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-network-wired mr-2"></i>Corroboration batch';
        }
    }

    static async batchAnalyzeBayesian() {
        const resultDiv = document.getElementById('batchAnalysisResult');
        const btn = document.getElementById('batchBayesianBtn');

        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Analyse...';
        resultDiv.innerHTML = '<p class="text-purple-600 text-sm mt-3">⏳ Analyse bayésienne en cours...</p>';

        try {
            const response = await fetch('/api/bayesian/batch-analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({})
            });

            const data = await response.json();

            if (data.success) {
                const results = data.results;
                resultDiv.innerHTML = `
                    <div class="mt-3 bg-purple-50 border border-purple-200 rounded-lg p-3 text-sm">
                        <p class="font-semibold text-purple-800">✅ Analyse terminée</p>
                        <div class="mt-2 space-y-1">
                            <p>📊 Articles analysés: <strong>${results.analyzed}</strong></p>
                            <p>🔄 Sentiments mis à jour: <strong>${results.updated}</strong></p>
                            ${results.errors.length > 0 ? `<p>⚠️ Erreurs: ${results.errors.length}</p>` : ''}
                        </div>
                    </div>
                `;
                this.loadAnalyzedArticles();
            } else {
                this.showAlert(resultDiv, data.error || 'Erreur', 'error');
            }
        } catch (error) {
            this.showAlert(resultDiv, 'Erreur: ' + error.message, 'error');
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-brain mr-2"></i>Analyse bayésienne batch';
        }
    }

    static async loadAnalyzedArticles() {
        const container = document.getElementById('analyzedArticlesList');
        if (!container) return;

        try {
            const response = await fetch('/api/articles?limit=20');
            const data = await response.json();

            if (!data.articles || data.articles.length === 0) {
                container.innerHTML = `
                    <p class="text-center text-gray-500 py-4">
                        Aucun article analysé pour le moment
                    </p>
                `;
                return;
            }

            container.innerHTML = data.articles.map(article => `
                <div class="border border-gray-200 rounded-lg p-4 hover:shadow-md transition">
                    <div class="flex justify-between items-start">
                        <div class="flex-1">
                            <h4 class="font-semibold text-gray-800">${article.title}</h4>
                            <p class="text-sm text-gray-600 mt-1">
                                ID: ${article.id} • 
                                <span class="px-2 py-1 rounded text-xs ${this.getSentimentBadge(article.sentiment)}">
                                    ${article.sentiment || 'N/A'}
                                </span>
                            </p>
                        </div>
                        <button onclick="AdvancedAnalysisManager.viewArticleDetails(${article.id})"
                                class="text-indigo-600 hover:text-indigo-800 text-sm">
                            <i class="fas fa-eye mr-1"></i>Détails
                        </button>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            container.innerHTML = `
                <p class="text-center text-red-500 py-4">
                    Erreur de chargement: ${error.message}
                </p>
            `;
        }
    }

    static async viewArticleDetails(articleId) {
        try {
            const response = await fetch(`/api/corroboration/stats/${articleId}`);

            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }

            const data = await response.json();

            alert(`Article #${articleId}\n\nCorroborations: ${data.corroboration_count}\nSimilarité moyenne: ${(data.average_similarity * 100).toFixed(1)}%`);

        } catch (error) {
            console.error('Erreur détails article:', error);
            alert('Impossible de charger les détails: ' + error.message);
        }
    }

    static getSentimentBadge(sentiment) {
        switch (sentiment) {
            case 'positive': return 'bg-green-100 text-green-800';
            case 'negative': return 'bg-red-100 text-red-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    }

    static showAlert(container, message, type = 'info') {
        const colors = {
            success: 'green',
            error: 'red',
            info: 'blue'
        };
        const color = colors[type] || 'blue';

        container.innerHTML = `
            <div class="mt-3 bg-${color}-50 border border-${color}-200 rounded-lg p-3 text-sm">
                <p class="text-${color}-800">${message}</p>
            </div>
        `;
    }
}

// Initialisation
document.addEventListener('DOMContentLoaded', function () {
    window.AdvancedAnalysisManager = AdvancedAnalysisManager;
    console.log('✅ AdvancedAnalysisManager initialisé avec interface IA');
});