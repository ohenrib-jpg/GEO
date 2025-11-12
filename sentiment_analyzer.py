import logging
import threading
import re
from typing import Dict, Any, List

# Importations conditionnelles
try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False
    print("⚠️ TextBlob non disponible")

try:
    import nltk
    from nltk.sentiment import SentimentIntensityAnalyzer
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    print("⚠️ NLTK non disponible")

# ⭐ IMPORTATION RoBERTa
try:
    from transformers import pipeline
    ROBERTA_AVAILABLE = True
    print("✅ Transformers disponible - RoBERTa activable")
except ImportError:
    ROBERTA_AVAILABLE = False
    print("⚠️ Transformers non disponible - pip install transformers torch")

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    def __init__(self):
        self.sia = None
        self.roberta_pipeline = None
        
        # 🎯 Dictionnaires de mots-clés pour contexte géopolitique/économique
        self.positive_keywords = {
            'français': [
                'succès', 'réussite', 'croissance', 'progression', 'hausse', 'gain',
                'amélioration', 'progrès', 'avancée', 'victoire', 'accord', 'paix',
                'stabilité', 'prospérité', 'renaissance', 'essor', 'boom', 'record',
                'performance', 'excellence', 'innovation', 'développement', 'expansion',
                'optimisme', 'confiance', 'renforcement', 'augmentation', 'bénéfice',
                'profit', 'dividende', 'surplus', 'excédent', 'rebond', 'reprise'
            ],
            'anglais': [
                'success', 'growth', 'increase', 'gain', 'improvement', 'progress',
                'advance', 'victory', 'agreement', 'peace', 'stability', 'prosperity',
                'boom', 'record', 'performance', 'excellence', 'innovation', 'expansion',
                'optimism', 'confidence', 'profit', 'dividend', 'surplus', 'recovery'
            ]
        }
        
        self.negative_keywords = {
            'français': [
                'crise', 'guerre', 'conflit', 'échec', 'baisse', 'chute', 'perte',
                'recul', 'régression', 'défaite', 'rupture', 'tensions', 'instabilité',
                'récession', 'déclin', 'effondrement', 'catastrophe', 'menace',
                'risque', 'danger', 'inquiétude', 'peur', 'panique', 'déficit',
                'dette', 'faillite', 'licenciement', 'fermeture', 'sanction',
                'condamnation', 'attaque', 'attentat', 'violence', 'mort'
            ],
            'anglais': [
                'crisis', 'war', 'conflict', 'failure', 'decline', 'fall', 'loss',
                'defeat', 'tensions', 'instability', 'recession', 'collapse',
                'catastrophe', 'threat', 'risk', 'danger', 'fear', 'panic',
                'deficit', 'debt', 'bankruptcy', 'layoff', 'closure', 'sanction',
                'attack', 'violence', 'death'
            ]
        }
        
        # 📊 Indicateurs économiques neutres (éviter les faux négatifs)
        self.neutral_economic_terms = [
            'ratio', 'solvabilité', 'prime', 'brut', 'net', 'milliard', 'million',
            'franc', 'euro', 'dollar', 'pourcentage', '%', 'trimestre', 'semestre',
            'annuel', 'exercice', 'bilan', 'résultat', 'chiffre', 'affaires',
            'quarter', 'annual', 'fiscal', 'revenue', 'turnover', 'balance'
        ]
        
        self._initialize_nltk()
        self._initialize_roberta()
    
    def _initialize_nltk(self):
        """Initialise NLTK en arrière-plan"""
        if not NLTK_AVAILABLE:
            return
            
        def download_nltk_data():
            try:
                nltk.data.find('vader_lexicon')
                logger.info("✅ VADER lexicon déjà disponible")
            except LookupError:
                logger.info("📥 Téléchargement de VADER lexicon...")
                nltk.download('vader_lexicon', quiet=True)
                logger.info("✅ VADER lexicon téléchargé")
            
            self.sia = SentimentIntensityAnalyzer()
        
        thread = threading.Thread(target=download_nltk_data)
        thread.daemon = True
        thread.start()
    
    def _initialize_roberta(self):
        """⭐ Initialise RoBERTa en arrière-plan"""
        if not ROBERTA_AVAILABLE:
            print("⚠️ RoBERTa non disponible - mode fallback activé")
            return
            
        def load_roberta():
            try:
                print("🤖 Chargement de RoBERTa (cardiffnlp/twitter-roberta-base-sentiment-latest)...")
                self.roberta_pipeline = pipeline(
                    "sentiment-analysis",
                    model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                    truncation=True,
                    max_length=512,
                    device=-1  # Forcer l'utilisation du CPU
                )
                print("✅ RoBERTa chargé avec succès !")
            except Exception as e:
                print(f"❌ Erreur chargement RoBERTa: {e}")
                self.roberta_pipeline = None
        
        load_roberta()
    
    def _extract_keywords(self, text: str) -> Dict[str, int]:
        """🔍 Extrait et compte les mots-clés positifs/négatifs"""
        text_lower = text.lower()
        
        positive_count = 0
        negative_count = 0
        
        # Compter les mots-clés français
        for keyword in self.positive_keywords['français']:
            positive_count += len(re.findall(r'\b' + re.escape(keyword) + r'\b', text_lower))
        
        for keyword in self.negative_keywords['français']:
            negative_count += len(re.findall(r'\b' + re.escape(keyword) + r'\b', text_lower))
        
        # Compter les mots-clés anglais
        for keyword in self.positive_keywords['anglais']:
            positive_count += len(re.findall(r'\b' + re.escape(keyword) + r'\b', text_lower))
        
        for keyword in self.negative_keywords['anglais']:
            negative_count += len(re.findall(r'\b' + re.escape(keyword) + r'\b', text_lower))
        
        return {
            'positive': positive_count,
            'negative': negative_count,
            'total': positive_count + negative_count
        }
    
    def _is_economic_neutral(self, text: str) -> bool:
        """📊 Détecte si le texte est un rapport économique neutre"""
        text_lower = text.lower()
        
        # Compter les termes économiques neutres
        neutral_count = sum(
            1 for term in self.neutral_economic_terms 
            if term in text_lower
        )
        
        # Si > 3 termes économiques et pas de mots-clés émotionnels forts
        keywords = self._extract_keywords(text)
        
        return neutral_count >= 3 and keywords['total'] < 2
    
    def _detect_positive_indicators(self, text: str) -> float:
        """📈 Détecte les indicateurs positifs spécifiques (hausses, gains, etc.)"""
        text_lower = text.lower()
        score = 0.0
        
        # Patterns de hausse
        if re.search(r'(progresser|grimpe|augmente|hausse|bond|+\d+%)', text_lower):
            score += 0.3
        
        # Chiffres en hausse avec %
        if re.search(r'\+\s*\d+[\.,]?\d*\s*%', text):
            score += 0.2
        
        # Records positifs
        if re.search(r'(record|historique|jamais vu|exceptionnel)', text_lower):
            score += 0.2
        
        return min(score, 0.8)  # Cap à 0.8
    
    def _detect_negative_indicators(self, text: str) -> float:
        """📉 Détecte les indicateurs négatifs spécifiques"""
        text_lower = text.lower()
        score = 0.0
        
        # Patterns de baisse
        if re.search(r'(chute|effondre|plonge|baisse|recul|-\d+%)', text_lower):
            score += 0.3
        
        # Chiffres en baisse avec %
        if re.search(r'-\s*\d+[\.,]?\d*\s*%', text):
            score += 0.2
        
        # Mots très négatifs
        if re.search(r'(catastrophe|crise majeure|guerre|attentat)', text_lower):
            score += 0.4
        
        return min(score, 0.8)  # Cap à 0.8
    
    def analyze_sentiment_with_score(self, text: str) -> Dict[str, Any]:
        """
        🎯 Analyse hybride optimisée pour la géopolitique/économie
        """
        if not text or len(text.strip()) < 10:
            return {
                'score': 0.0,
                'type': 'neutral_positive',
                'confidence': 0.0,
                'model': 'none'
            }
        
        # 🔍 Étape 1 : Analyse contextuelle
        keywords = self._extract_keywords(text)
        is_economic = self._is_economic_neutral(text)
        positive_indicators = self._detect_positive_indicators(text)
        negative_indicators = self._detect_negative_indicators(text)
        
        # 📊 Étape 2 : Score contextuel basé sur les mots-clés
        if keywords['total'] > 0:
            keyword_score = (keywords['positive'] - keywords['negative']) / (keywords['total'] + 1)
            # Normaliser entre -1 et 1
            keyword_score = max(-1.0, min(1.0, keyword_score))
        else:
            keyword_score = 0.0
        
        # Ajuster avec les indicateurs
        keyword_score += positive_indicators - negative_indicators
        keyword_score = max(-1.0, min(1.0, keyword_score))
        
        # 🤖 Étape 3 : RoBERTa (avec pondération réduite si économique)
        roberta_score = 0.0
        roberta_confidence = 0.0
        
        if self.roberta_pipeline:
            try:
                text_truncated = text[:500]
                result = self.roberta_pipeline(text_truncated)[0]
                
                label = result['label'].lower()
                confidence = result['score']
                
                # Conversion label → score
                if 'positive' in label:
                    roberta_score = confidence
                elif 'negative' in label:
                    roberta_score = -confidence
                else:
                    roberta_score = 0.0
                
                roberta_confidence = confidence
                
            except Exception as e:
                logger.error(f"Erreur RoBERTa: {e}")
        
        # 📐 Étape 4 : Pondération intelligente
        if is_economic and keywords['total'] < 2:
            # Texte économique neutre : donner plus de poids au contexte
            if abs(keyword_score) < 0.1 and abs(roberta_score) < 0.5:
                # Probablement vraiment neutre
                final_score = 0.0
            else:
                # Favoriser l'analyse contextuelle
                final_score = keyword_score * 0.7 + roberta_score * 0.3
        else:
            # Texte avec contenu émotionnel : équilibrer
            if self.roberta_pipeline:
                # RoBERTa disponible : pondération 50/50
                final_score = keyword_score * 0.5 + roberta_score * 0.5
            else:
                # Pas de RoBERTa : utiliser uniquement le contexte
                final_score = keyword_score
        
        # 🎯 Étape 5 : Analyse traditionnelle en complément
        traditional_result = self._analyze_traditional(text)
        
        # Ajuster avec l'analyse traditionnelle (poids faible)
        if traditional_result['model'] != 'error':
            final_score = final_score * 0.8 + traditional_result['score'] * 0.2
        
        # Normaliser
        final_score = max(-1.0, min(1.0, final_score))
        
        # 📊 Étape 6 : Déterminer le type de sentiment (4 catégories)
        if final_score > 0.2:
            sentiment_type = 'positive'
        elif 0.0 <= final_score <= 0.2:
            sentiment_type = 'neutral_positive'
        elif -0.2 <= final_score < 0.0:
            sentiment_type = 'neutral_negative'
        else:
            sentiment_type = 'negative'
        
        # Confiance finale (moyenne des confidences disponibles)
        confidence = abs(final_score)
        if roberta_confidence > 0:
            confidence = (confidence + roberta_confidence) / 2
        
        return {
            'score': final_score,
            'type': sentiment_type,
            'confidence': confidence,
            'model': 'hybrid_geopolitical',
            'details': {
                'keyword_score': keyword_score,
                'roberta_score': roberta_score if self.roberta_pipeline else None,
                'is_economic': is_economic,
                'keywords': keywords,
                'positive_indicators': positive_indicators,
                'negative_indicators': negative_indicators
            }
        }
    
    def _analyze_traditional(self, text: str) -> Dict[str, Any]:
        """Analyse traditionnelle (TextBlob + VADER)"""
        try:
            # TextBlob
            if TEXTBLOB_AVAILABLE:
                blob = TextBlob(text)
                polarity = blob.sentiment.polarity
            else:
                polarity = 0.0
            
            # VADER
            if self.sia:
                vader_scores = self.sia.polarity_scores(text)
                vader_compound = vader_scores['compound']
            else:
                vader_compound = 0.0
            
            # Combinaison
            if TEXTBLOB_AVAILABLE and self.sia:
                combined_score = (polarity + vader_compound) / 2
            elif TEXTBLOB_AVAILABLE:
                combined_score = polarity
            elif self.sia:
                combined_score = vader_compound
            else:
                combined_score = 0.0
            
            # 4 catégories
            if combined_score > 0.1:
                sentiment_type = 'positive'
            elif 0.0 <= combined_score <= 0.1:
                sentiment_type = 'neutral_positive'
            elif -0.1 <= combined_score < 0.0:
                sentiment_type = 'neutral_negative'
            else:
                sentiment_type = 'negative'
            
            return {
                'score': combined_score,
                'type': sentiment_type,
                'confidence': abs(combined_score),
                'model': 'traditional'
            }
            
        except Exception as e:
            logger.error(f"Erreur analyse traditionnelle: {e}")
            return {
                'score': 0.0,
                'type': 'neutral_positive',
                'confidence': 0.0,
                'model': 'error'
            }
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Méthode de compatibilité (appelle analyze_sentiment_with_score)"""
        return self.analyze_sentiment_with_score(text)
    
    def analyze_article(self, title: str, content: str) -> Dict[str, Any]:
        """Analyse le sentiment d'un article complet"""
        # Donner plus de poids au titre (souvent plus significatif)
        full_text = f"{title} {title} {content}"
        return self.analyze_sentiment_with_score(full_text)