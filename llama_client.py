# Flask/llama_client.py
"""
Client Python pour communiquer avec le serveur Llama.cpp
Gère la génération de rapports d'analyse géopolitique
"""

import logging
import requests
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class LlamaClient:
    """Client pour interagir avec llama.cpp server"""
    
    def __init__(self, endpoint: str = "http://localhost:8080"):
        self.endpoint = endpoint
        self.timeout = 180  # 3 minutes pour être large
        
        # Templates de prompts par type de rapport
        self.prompt_templates = {
            'geopolitique': self._build_geopolitique_prompt,
            'economique': self._build_economique_prompt,
            'securite': self._build_securite_prompt,
            'synthese': self._build_synthese_prompt
        }
    
    def test_connection(self) -> bool:
        """Teste la connexion au serveur Llama"""
        try:
            response = requests.get(
                f"{self.endpoint}/health",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Connexion Llama échouée: {e}")
            return False
    
    def _build_geopolitique_prompt(self, articles: List[Dict], 
                                   context: Dict) -> str:
        """Construit le prompt pour analyse géopolitique"""
        
        # Préparer le résumé des données
        sentiment_summary = f"""
Positifs: {context.get('sentiment_positive', 0)} articles
Négatifs: {context.get('sentiment_negative', 0)} articles
Neutres: {context.get('sentiment_neutral', 0)} articles
"""
        
        # Extraire les titres les plus pertinents
        top_articles = "\n".join([
            f"- {art['title']} ({art.get('source', 'source inconnue')})"
            for art in articles[:10]
        ])
        
        themes_covered = context.get('themes', [])
        themes_text = ", ".join(themes_covered) if themes_covered else "Tous thèmes"
        
        prompt = f"""Tu es GEOPOL, un expert en analyse géopolitique reconnu. Tu dois produire un rapport professionnel structuré et factuel.

CONTEXTE DE L'ANALYSE
======================
Période: {context.get('period', 'Non spécifiée')}
Nombre d'articles: {len(articles)}
Thèmes couverts: {themes_text}

DISTRIBUTION DES SENTIMENTS
============================
{sentiment_summary}

ARTICLES PRINCIPAUX
===================
{top_articles}

RAPPORT GÉOPOLITIQUE DEMANDÉ
=============================

Produis un rapport structuré en 4 sections :

## 1. SYNTHÈSE EXÉCUTIVE (2-3 phrases)
Résumé des tendances majeures observées

## 2. ANALYSE DES TENDANCES
- Identifier 3-4 tendances géopolitiques principales
- Pour chaque tendance : contexte, acteurs, implications
- Utiliser un langage professionnel et précis

## 3. POINTS DE TENSION DÉTECTÉS
- Signaler les zones de conflit ou tension croissante
- Expliquer les causes sous-jacentes
- Évaluer le niveau de risque (faible/moyen/élevé)

## 4. PERSPECTIVES ET RECOMMANDATIONS
- Scénarios probables à court terme (1-3 mois)
- Actions de veille recommandées
- Indicateurs à surveiller

INSTRUCTIONS CRITIQUES :
- Sois factuel et nuancé, évite les généralisations
- Base-toi UNIQUEMENT sur les articles fournis
- Utilise un ton professionnel adapté à un briefing stratégique
- Cite les sources pertinentes quand nécessaire
- Longueur cible : 800-1200 mots

Commence directement par "## 1. SYNTHÈSE EXÉCUTIVE" sans préambule.
"""
        return prompt
    
    def _build_economique_prompt(self, articles: List[Dict], 
                                 context: Dict) -> str:
        """Construit le prompt pour analyse économique"""
        
        top_articles = "\n".join([
            f"- {art['title']}"
            for art in articles[:10]
        ])
        
        prompt = f"""Tu es un analyste économique senior spécialisé en macroéconomie. Produis une analyse structurée.

DONNÉES À ANALYSER
==================
Période: {context.get('period', 'Non spécifiée')}
Articles analysés: {len(articles)}

TITRES CLÉS
===========
{top_articles}

RAPPORT ÉCONOMIQUE DEMANDÉ
===========================

## 1. INDICATEURS MACROÉCONOMIQUES
- Résumer les tendances économiques principales (croissance, inflation, marchés)
- Identifier les secteurs en mouvement

## 2. POLITIQUES ÉCONOMIQUES
- Analyser les décisions politiques majeures
- Impact sur les marchés et l'économie réelle
- Réponse des acteurs économiques

## 3. RISQUES ET OPPORTUNITÉS
- Identifier les risques systémiques
- Signaler les opportunités d'investissement
- Recommandations stratégiques

## 4. PRÉVISIONS À COURT TERME
- Scénarios probables (3-6 mois)
- Facteurs de volatilité à surveiller

Base-toi UNIQUEMENT sur les articles fournis. Longueur : 600-900 mots.
Commence par "## 1. INDICATEURS MACROÉCONOMIQUES".
"""
        return prompt
    
    def _build_securite_prompt(self, articles: List[Dict], 
                               context: Dict) -> str:
        """Construit le prompt pour analyse sécurité"""
        
        top_articles = "\n".join([
            f"- {art['title']}"
            for art in articles[:8]
        ])
        
        prompt = f"""Tu es un expert en sécurité internationale et analyse des menaces. Produis un briefing sécuritaire.

CONTEXTE
========
Période: {context.get('period', 'Non spécifiée')}
Articles: {len(articles)}

ÉVÉNEMENTS CLÉS
===============
{top_articles}

BRIEFING SÉCURITAIRE
====================

## 1. MENACES ÉMERGENTES
- Identifier les nouvelles menaces ou escalades
- Qualifier le niveau de risque (critique/élevé/modéré)

## 2. ACTEURS ET DYNAMIQUES
- Cartographier les acteurs impliqués (États, groupes)
- Analyser les rapports de force

## 3. IMPLICATIONS RÉGIONALES
- Impact sur la stabilité régionale
- Risques de contagion

## 4. RECOMMANDATIONS OPÉRATIONNELLES
- Mesures de vigilance à adopter
- Zones à surveiller prioritairement

Ton professionnel et factuel. 500-800 mots.
Commence par "## 1. MENACES ÉMERGENTES".
"""
        return prompt
    
    def _build_synthese_prompt(self, articles: List[Dict], 
                               context: Dict) -> str:
        """Construit le prompt pour synthèse hebdomadaire"""
        
        top_articles = "\n".join([
            f"- {art['title']}"
            for art in articles[:15]
        ])
        
        prompt = f"""Tu es GEOPOL, spécialiste en synthèse d'actualité internationale. Produis une synthèse hebdomadaire.

PÉRIODE COUVERTE
================
{context.get('period', 'Dernière semaine')}
{len(articles)} articles analysés

ARTICLES MAJEURS
================
{top_articles}

SYNTHÈSE HEBDOMADAIRE
=====================

## 1. FAITS MARQUANTS
- Résumer les 5 événements majeurs de la semaine
- Une phrase par événement, factuelle

## 2. TENDANCES OBSERVÉES
- Identifier 3 tendances significatives
- Expliquer leur importance stratégique

## 3. ÉVOLUTIONS GÉOPOLITIQUES
- Changements dans les équilibres de pouvoir
- Nouvelles alliances ou tensions

## 4. AGENDA DE LA SEMAINE À VENIR
- Événements à surveiller
- Échéances importantes

Style concis et informatif. 600-900 mots.
Commence par "## 1. FAITS MARQUANTS".
"""
        return prompt
    
    def generate_analysis(self, report_type: str, articles: List[Dict],
                         context: Dict) -> Dict:
        """
        Génère une analyse avec Llama
        
        Args:
            report_type: Type de rapport (geopolitique, economique, etc.)
            articles: Liste d'articles à analyser
            context: Contexte additionnel (période, thèmes, etc.)
            
        Returns:
            Dict avec 'success', 'analysis' et éventuellement 'error'
        """
        
        # Vérifier la connexion
        if not self.test_connection():
            logger.warning("⚠️ Serveur Llama inaccessible - mode dégradé")
            return {
                'success': False,
                'error': 'Serveur Llama inaccessible',
                'analysis': self._generate_fallback_analysis(
                    report_type, articles, context
                )
            }
        
        try:
            # Construire le prompt
            prompt_builder = self.prompt_templates.get(
                report_type, 
                self._build_geopolitique_prompt
            )
            prompt = prompt_builder(articles, context)
            
            logger.info(f"🦙 Envoi prompt à Llama ({len(prompt)} caractères)")
            
            # Construction du prompt ChatML complet
            full_prompt = f"""<|im_start|>system
Tu es un analyste géopolitique professionnel. Ta mission est d'analyser des articles de presse et de produire des rapports structurés. Tu ne fais jamais de commentaires sur tes capacités, tu analyses directement les données fournies.<|im_end|>
<|im_start|>user
{prompt}<|im_end|>
<|im_start|>assistant
## SYNTHÈSE EXÉCUTIVE

"""
            
            # Appel au serveur Llama avec format optimisé
            logger.info(f"📤 Envoi requête à {self.endpoint}/completion")
            
            response = requests.post(
                f"{self.endpoint}/completion",
                json={
                    "prompt": full_prompt,
                    "temperature": 0.7,
                    "max_tokens": 2000,
                    "stop": ["<|im_end|>", "<|im_start|>", "user:", "assistant:"],
                    "stream": False
                },
                headers={
                    "Content-Type": "application/json"
                },
                timeout=self.timeout
            )
            
            logger.info(f"📥 Réponse HTTP: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Contenu erreur: {response.text[:500]}")
                raise Exception(f"Erreur serveur Llama: {response.status_code}")
            
            data = response.json()
            logger.debug(f"Clés JSON reçues: {list(data.keys())}")
            
            # Extraire la réponse (format /completion)
            analysis_text = data.get('content', '').strip()
            
            # Nettoyer les balises ChatML résiduelles
            analysis_text = analysis_text.replace('<|im_start|>', '').replace('<|im_end|>', '')
            analysis_text = analysis_text.replace('assistant:', '').replace('user:', '')
            analysis_text = analysis_text.strip()
            
            # Si le contenu commence par le prompt system/user, extraire seulement la réponse
            if '<|im_start|>assistant' in analysis_text:
                # Extraire tout ce qui suit le marqueur assistant
                parts = analysis_text.split('<|im_start|>assistant')
                if len(parts) > 1:
                    analysis_text = parts[-1].split('<|im_end|>')[0].strip()
            
            if not analysis_text:
                raise Exception("Réponse vide de Llama")
            
            # Vérification souple : seulement si TOUTE la réponse est le prompt
            if len(analysis_text) < 100 and ("Tu es" in analysis_text or "CONTEXTE" in analysis_text):
                raise Exception("Réponse trop courte ou invalide")
            
            logger.info(f"✅ Analyse générée ({len(analysis_text)} caractères)")
            logger.debug(f"Début de l'analyse: {analysis_text[:200]}")
            
            return {
                'success': True,
                'analysis': analysis_text,
                'model_used': 'llama3.2-3b-Q4_K_M',
                'prompt_tokens': len(prompt.split()),
                'completion_tokens': len(analysis_text.split())
            }
            
        except requests.Timeout:
            logger.error("⏱️ Timeout Llama - mode dégradé")
            return {
                'success': False,
                'error': 'Timeout - analyse trop longue',
                'analysis': self._generate_fallback_analysis(
                    report_type, articles, context
                )
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur Llama: {e}")
            return {
                'success': False,
                'error': str(e),
                'analysis': self._generate_fallback_analysis(
                    report_type, articles, context
                )
            }
    
    def _generate_fallback_analysis(self, report_type: str, 
                                    articles: List[Dict],
                                    context: Dict) -> str:
        """
        Génère une analyse de secours (mode dégradé)
        """
        
        sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
        for article in articles:
            sentiment = article.get('sentiment', 'neutral')
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        
        # Identifier les sources principales
        sources = {}
        for article in articles:
            source = article.get('source', 'Source inconnue')
            sources[source] = sources.get(source, 0) + 1
        
        top_sources = sorted(sources.items(), key=lambda x: x[1], reverse=True)[:3]
        
        analysis = f"""
## RAPPORT {report_type.upper()} - MODE DÉGRADÉ

**Note importante:** Ce rapport a été généré en mode dégradé (serveur IA indisponible). L'analyse est limitée aux statistiques descriptives.

### 📊 Vue d'ensemble

**Période analysée:** {context.get('period', 'Non spécifiée')}  
**Articles traités:** {len(articles)}  
**Thèmes couverts:** {', '.join(context.get('themes', ['Tous thèmes']))}

### 📈 Distribution des sentiments

- **Positifs:** {sentiment_counts['positive']} articles ({sentiment_counts['positive']/len(articles)*100:.1f}%)
- **Négatifs:** {sentiment_counts['negative']} articles ({sentiment_counts['negative']/len(articles)*100:.1f}%)
- **Neutres:** {sentiment_counts['neutral']} articles ({sentiment_counts['neutral']/len(articles)*100:.1f}%)

### 📰 Sources principales

{chr(10).join([f'{i+1}. {source} ({count} articles)' for i, (source, count) in enumerate(top_sources)])}

### 📋 Articles significatifs

{chr(10).join([f'**{i+1}.** {article["title"]}' for i, article in enumerate(articles[:5])])}

### ⚠️ Limitations

Cette analyse automatique ne remplace pas l'expertise humaine. Pour une analyse approfondie avec IA :

1. Vérifiez que le serveur Llama est démarré : `http://localhost:8080/health`
2. Relancez la génération du rapport
3. Ou consultez les articles individuellement pour une analyse manuelle

---
*Généré par GEOPOL Analytics - {datetime.now().strftime('%d/%m/%Y à %H:%M')}*
"""
        
        return analysis


# Instance globale (singleton)
_llama_client = None

def get_llama_client() -> LlamaClient:
    """Retourne l'instance singleton du client Llama"""
    global _llama_client
    if _llama_client is None:
        _llama_client = LlamaClient()
    return _llama_client
