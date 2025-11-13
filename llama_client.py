# Flask/llama_client.py - VERSION CORRIGÉE
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
        self.timeout = 180  # 3 minutes
        
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
            # ⚠️ CORRECTION : Llama.cpp n'a pas de /health, tester avec /v1/models
            response = requests.get(
                f"{self.endpoint}/v1/models",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"⚠️ Connexion Llama échouée: {e}")
            return False
    
    def _build_geopolitique_prompt(self, articles: List[Dict], context: Dict) -> str:
        """Construit le prompt pour analyse géopolitique"""
        
        sentiment_summary = f"""
Positifs: {context.get('sentiment_positive', 0)} articles
Négatifs: {context.get('sentiment_negative', 0)} articles
Neutres: {context.get('sentiment_neutral', 0)} articles
"""
        
        top_articles = "\n".join([
            f"- {art['title']}"
            for art in articles[:8]
        ])
        
        themes_covered = context.get('themes', [])
        themes_text = ", ".join(themes_covered) if themes_covered else "Tous thèmes"
        
        prompt = f"""Analyse géopolitique professionnelle

CONTEXTE
========
Période: {context.get('period', 'Non spécifiée')}
Articles analysés: {len(articles)}
Thèmes: {themes_text}

SENTIMENTS
==========
{sentiment_summary}

TITRES PRINCIPAUX
=================
{top_articles}

CONSIGNE
========
Produis un rapport structuré en 4 sections COURTES (200 mots maximum par section) :

1. SYNTHÈSE EXÉCUTIVE
- 3 tendances majeures en 1-2 phrases chacune

2. POINTS CLÉS
- 3-4 faits marquants
- Contexte minimal

3. TENSIONS
- Zones de conflit identifiées
- Niveau de risque (faible/moyen/élevé)

4. PERSPECTIVES
- Scénarios probables (1-3 mois)
- 2-3 indicateurs à surveiller

IMPÉRATIF: Sois concis, factuel et professionnel. Base-toi UNIQUEMENT sur les titres fournis.
Commence DIRECTEMENT par "## 1. SYNTHÈSE EXÉCUTIVE" sans introduction.
"""
        return prompt
    
    def _build_economique_prompt(self, articles: List[Dict], context: Dict) -> str:
        """Construit le prompt pour analyse économique"""
        
        top_articles = "\n".join([f"- {art['title']}" for art in articles[:8]])
        
        prompt = f"""Analyse économique

CONTEXTE
========
Période: {context.get('period', 'Non spécifiée')}
Articles: {len(articles)}

TITRES
======
{top_articles}

RAPPORT (4 sections courtes)
============================

1. INDICATEURS MACROÉCONOMIQUES
- Tendances principales (croissance, inflation, marchés)
- Secteurs en mouvement

2. POLITIQUES ÉCONOMIQUES
- Décisions majeures
- Impact sur les marchés

3. RISQUES ET OPPORTUNITÉS
- Risques systémiques identifiés
- Opportunités d'investissement

4. PRÉVISIONS (3-6 mois)
- Scénarios probables
- Facteurs de volatilité

Commence par "## 1. INDICATEURS MACROÉCONOMIQUES". 600 mots maximum.
"""
        return prompt
    
    def _build_securite_prompt(self, articles: List[Dict], context: Dict) -> str:
        """Construit le prompt pour analyse sécurité"""
        
        top_articles = "\n".join([f"- {art['title']}" for art in articles[:8]])
        
        prompt = f"""Briefing sécurité

CONTEXTE
========
Période: {context.get('period', 'Non spécifiée')}
Articles: {len(articles)}

ÉVÉNEMENTS
==========
{top_articles}

BRIEFING (4 sections)
====================

1. MENACES ÉMERGENTES
- Nouvelles menaces ou escalades
- Niveau de risque

2. ACTEURS ET DYNAMIQUES
- Acteurs impliqués (États, groupes)
- Rapports de force

3. IMPLICATIONS RÉGIONALES
- Impact sur la stabilité
- Risques de contagion

4. RECOMMANDATIONS
- Mesures de vigilance
- Zones à surveiller

Commence par "## 1. MENACES ÉMERGENTES". 500 mots maximum.
"""
        return prompt
    
    def _build_synthese_prompt(self, articles: List[Dict], context: Dict) -> str:
        """Construit le prompt pour synthèse hebdomadaire"""
        
        top_articles = "\n".join([f"- {art['title']}" for art in articles[:12]])
        
        prompt = f"""Synthèse hebdomadaire

PÉRIODE
=======
{context.get('period', 'Dernière semaine')}
{len(articles)} articles

ARTICLES
========
{top_articles}

SYNTHÈSE (4 sections)
====================

1. FAITS MARQUANTS
- 5 événements majeurs (1 phrase chacun)

2. TENDANCES
- 3 tendances significatives
- Importance stratégique

3. ÉVOLUTIONS GÉOPOLITIQUES
- Changements dans les équilibres de pouvoir
- Nouvelles alliances ou tensions

4. AGENDA SEMAINE À VENIR
- Événements à surveiller
- Échéances importantes

Commence par "## 1. FAITS MARQUANTS". 600 mots maximum.
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
                'error': 'Serveur Llama inaccessible sur ' + self.endpoint,
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
            
            # 🔧 CORRECTION : Utiliser /completion au lieu de /v1/chat/completions
            logger.info(f"📤 Envoi requête à {self.endpoint}/completion")
            
            response = requests.post(
                f"{self.endpoint}/completion",
                json={
                    "prompt": prompt,
                    "temperature": 0.7,
                    "top_k": 40,
                    "top_p": 0.9,
                    "n_predict": 1500,  # Nombre de tokens à générer
                    "stop": ["##", "CONTEXTE", "CONSIGNE"],  # Arrêter si on répète le prompt
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
            
            if not analysis_text:
                raise Exception("Réponse vide de Llama")
            
            # Nettoyer les répétitions du prompt
            if "CONTEXTE" in analysis_text or "CONSIGNE" in analysis_text:
                # Ne garder que ce qui vient après le dernier "##"
                parts = analysis_text.split("##")
                if len(parts) > 1:
                    analysis_text = "## " + parts[-1].strip()
            
            # Vérification : au moins 100 caractères
            if len(analysis_text) < 100:
                raise Exception("Réponse trop courte ou invalide")
            
            logger.info(f"✅ Analyse générée ({len(analysis_text)} caractères)")
            
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

**Note:** Ce rapport a été généré en mode dégradé (serveur IA indisponible). L'analyse est limitée aux statistiques descriptives.

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

1. Vérifiez que le serveur Llama est démarré : `{self.endpoint}`
2. Testez avec : `curl {self.endpoint}/v1/models`
3. Relancez la génération du rapport

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