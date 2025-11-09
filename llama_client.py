# Flask/llama_client.py
"""
Client Python pour communiquer avec le serveur Llama.cpp
Gère la génération de rapports d'analyse géopolitique
Version optimisée avec gestion d'erreurs robuste
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
        self.timeout = 180  # 3 minutes pour analyses longues
        
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
        
        # Résumé des sentiments
        sentiment_summary = f"""
Positifs: {context.get('sentiment_positive', 0)} articles
Négatifs: {context.get('sentiment_negative', 0)} articles
Neutres: {context.get('sentiment_neutral', 0)} articles
"""
        
        # Top articles
        top_articles = "\n".join([
            f"- {art['title']} ({art.get('source', 'source inconnue')})"
            for art in articles[:10]
        ])
        
        themes_text = ", ".join(context.get('themes', [])) or "Tous thèmes"
        
        prompt = f"""Tu es GEOPOL, expert en analyse géopolitique. Produis un rapport structuré et factuel.

CONTEXTE
========
Période: {context.get('period', 'Non spécifiée')}
Articles: {len(articles)}
Thèmes: {themes_text}

SENTIMENTS
==========
{sentiment_summary}

ARTICLES CLÉS
=============
{top_articles}

RAPPORT DEMANDÉ
===============

## 1. SYNTHÈSE EXÉCUTIVE
Résumé en 2-3 phrases des tendances majeures

## 2. ANALYSE DES TENDANCES
- 3-4 tendances géopolitiques principales
- Contexte, acteurs, implications pour chacune

## 3. POINTS DE TENSION
- Zones de conflit ou tensions croissantes
- Causes sous-jacentes
- Niveau de risque (faible/moyen/élevé)

## 4. PERSPECTIVES
- Scénarios probables (1-3 mois)
- Actions de veille recommandées
- Indicateurs à surveiller

CONSIGNES:
- Factuel et nuancé
- Basé UNIQUEMENT sur les articles fournis
- Ton professionnel
- 800-1200 mots

Commence par "## 1. SYNTHÈSE EXÉCUTIVE".
"""
        return prompt
    
    def _build_economique_prompt(self, articles: List[Dict], 
                                 context: Dict) -> str:
        """Construit le prompt pour analyse économique"""
        
        top_articles = "\n".join([
            f"- {art['title']}"
            for art in articles[:10]
        ])
        
        prompt = f"""Tu es un analyste économique senior. Produis une analyse structurée.

DONNÉES
=======
Période: {context.get('period', 'Non spécifiée')}
Articles: {len(articles)}

TITRES CLÉS
===========
{top_articles}

RAPPORT ÉCONOMIQUE
==================

## 1. INDICATEURS MACROÉCONOMIQUES
- Tendances économiques (croissance, inflation, marchés)
- Secteurs en mouvement

## 2. POLITIQUES ÉCONOMIQUES
- Décisions politiques majeures
- Impact sur les marchés
- Réponses des acteurs

## 3. RISQUES ET OPPORTUNITÉS
- Risques systémiques
- Opportunités d'investissement
- Recommandations

## 4. PRÉVISIONS
- Scénarios 3-6 mois
- Facteurs de volatilité

600-900 mots. Commence par "## 1. INDICATEURS MACROÉCONOMIQUES".
"""
        return prompt
    
    def _build_securite_prompt(self, articles: List[Dict], 
                               context: Dict) -> str:
        """Construit le prompt pour analyse sécurité"""
        
        top_articles = "\n".join([
            f"- {art['title']}"
            for art in articles[:8]
        ])
        
        prompt = f"""Tu es un expert en sécurité internationale. Produis un briefing sécuritaire.

CONTEXTE
========
Période: {context.get('period', 'Non spécifiée')}
Articles: {len(articles)}

ÉVÉNEMENTS
==========
{top_articles}

BRIEFING SÉCURITAIRE
====================

## 1. MENACES ÉMERGENTES
- Nouvelles menaces ou escalades
- Niveau de risque

## 2. ACTEURS ET DYNAMIQUES
- Acteurs impliqués
- Rapports de force

## 3. IMPLICATIONS RÉGIONALES
- Impact sur la stabilité
- Risques de contagion

## 4. RECOMMANDATIONS
- Mesures de vigilance
- Zones prioritaires

500-800 mots. Commence par "## 1. MENACES ÉMERGENTES".
"""
        return prompt
    
    def _build_synthese_prompt(self, articles: List[Dict], 
                               context: Dict) -> str:
        """Construit le prompt pour synthèse hebdomadaire"""
        
        top_articles = "\n".join([
            f"- {art['title']}"
            for art in articles[:15]
        ])
        
        prompt = f"""Tu es GEOPOL, spécialiste en synthèse d'actualité. Produis une synthèse hebdomadaire.

PÉRIODE
=======
{context.get('period', 'Dernière semaine')}
{len(articles)} articles

ARTICLES MAJEURS
================
{top_articles}

SYNTHÈSE HEBDOMADAIRE
=====================

## 1. FAITS MARQUANTS
- 5 événements majeurs (une phrase chacun)

## 2. TENDANCES
- 3 tendances significatives
- Importance stratégique

## 3. ÉVOLUTIONS GÉOPOLITIQUES
- Changements dans les équilibres
- Nouvelles alliances ou tensions

## 4. AGENDA À VENIR
- Événements à surveiller
- Échéances importantes

600-900 mots. Commence par "## 1. FAITS MARQUANTS".
"""
        return prompt
    
    def generate_analysis(self, report_type: str, articles: List[Dict],
                         context: Dict) -> Dict:
        """
        Génère une analyse avec Llama
        
        Args:
            report_type: Type (geopolitique, economique, securite, synthese)
            articles: Liste d'articles à analyser
            context: Contexte (période, thèmes, sentiments)
            
        Returns:
            Dict avec 'success', 'analysis', et éventuellement 'error'
        """
        
        # Test connexion
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
            
            # Format instruction (optimal pour Llama 3)
            instruction_prompt = f"""### Instruction:
Tu es un analyste géopolitique professionnel. Analyse les articles ci-dessous et produis un rapport structuré.

### Articles à analyser:
{prompt}

### Rapport d'analyse:
"""
            
            # Appel API
            response = requests.post(
                f"{self.endpoint}/completion",
                json={
                    "prompt": instruction_prompt,
                    "temperature": 0.7,
                    "max_tokens": 2500,
                    "stop": ["###", "\n\n\n\n"],
                    "stream": False
                },
                headers={"Content-Type": "application/json"},
                timeout=self.timeout
            )
            
            logger.info(f"📥 Réponse HTTP: {response.status_code}")
            
            if response.status_code != 200:
                raise Exception(f"Erreur serveur: {response.status_code}")
            
            data = response.json()
            analysis_text = data.get('content', '').strip()
            
            if not analysis_text or len(analysis_text) < 200:
                raise Exception(f"Réponse invalide ({len(analysis_text)} chars)")
            
            logger.info(f"✅ Analyse générée ({len(analysis_text)} caractères)")
            
            return {
                'success': True,
                'analysis': analysis_text,
                'model_used': 'llama3.2-3b-Q4_K_M',
                'prompt_tokens': len(prompt.split()),
                'completion_tokens': len(analysis_text.split())
            }
            
        except requests.Timeout:
            logger.error("⏱️ Timeout Llama")
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
        """Génère une analyse de secours (mode dégradé)"""
        
        # Gestion du cas où articles est vide
        if not articles:
            return f"""
## RAPPORT {report_type.upper()} - MODE DÉGRADÉ

**⚠️ Aucun article disponible pour l'analyse**

Période: {context.get('period', 'Non spécifiée')}
Thèmes: {', '.join(context.get('themes', ['Tous thèmes']))}

Aucun article n'a été trouvé pour générer cette analyse.

---
*Généré par GEOPOL Analytics - {datetime.now().strftime('%d/%m/%Y à %H:%M')}*
"""
        
        # Compter les sentiments
        sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
        for article in articles:
            sentiment = article.get('sentiment', 'neutral')
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        
        # Calcul des pourcentages avec sécurité
        total_articles = len(articles)
        positive_pct = (sentiment_counts['positive'] / total_articles * 100) if total_articles > 0 else 0
        negative_pct = (sentiment_counts['negative'] / total_articles * 100) if total_articles > 0 else 0
        neutral_pct = (sentiment_counts['neutral'] / total_articles * 100) if total_articles > 0 else 0
        
        # Sources principales
        sources = {}
        for article in articles:
            source = article.get('source', 'Source inconnue')
            sources[source] = sources.get(source, 0) + 1
        
        top_sources = sorted(sources.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Générer le rapport de secours
        analysis = f"""
## RAPPORT {report_type.upper()} - MODE DÉGRADÉ

**⚠️ Note:** Ce rapport a été généré en mode dégradé (serveur IA indisponible). L'analyse est limitée aux statistiques descriptives.

### 📊 Vue d'ensemble

**Période:** {context.get('period', 'Non spécifiée')}  
**Articles:** {total_articles}  
**Thèmes:** {', '.join(context.get('themes', ['Tous thèmes']))}

### 📈 Distribution des sentiments

- **Positifs:** {sentiment_counts['positive']} articles ({positive_pct:.1f}%)
- **Négatifs:** {sentiment_counts['negative']} articles ({negative_pct:.1f}%)
- **Neutres:** {sentiment_counts['neutral']} articles ({neutral_pct:.1f}%)

### 📰 Sources principales

{chr(10).join([f'{i+1}. {source} ({count} articles)' for i, (source, count) in enumerate(top_sources)])}

### 📋 Articles significatifs

{chr(10).join([f'**{i+1}.** {article["title"]}' for i, article in enumerate(articles[:5])])}

### ⚠️ Limitations

Cette analyse automatique ne remplace pas l'expertise humaine. 

**Pour une analyse approfondie avec IA :**
1. Vérifiez que le serveur Llama est démarré : `http://localhost:8080/health`
2. Relancez la génération du rapport
3. Ou consultez les articles individuellement

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
        logger.info("✅ LlamaClient initialisé")
    return _llama_client