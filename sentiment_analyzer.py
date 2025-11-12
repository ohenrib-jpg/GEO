import logging
import threading
from typing import Dict, Any

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
        
        # Exécuter immédiatement pour le debug
        load_roberta()
    
    def analyze_sentiment_with_score(self, text: str) -> Dict[str, Any]:
        """
        ⭐ Analyse avec RoBERTa en priorité (4 catégories)
        Retourne: positive, neutral_positive, neutral_negative, negative
        """
        if not text or len(text.strip()) < 10:
            return {
                'score': 0.0,
                'type': 'neutral_positive',
                'confidence': 0.0,
                'model': 'none'
            }
        
        # ⭐ PRIORITÉ 1 : RoBERTa
        if self.roberta_pipeline:
            try:
                # Limiter le texte
                text_truncated = text[:500]
                result = self.roberta_pipeline(text_truncated)[0]
                
                label = result['label'].lower()
                score = result['score']
                
                # Conversion Cardiff → Score normalisé [-1, 1]
                if 'positive' in label:
                    roberta_score = score
                elif 'negative' in label:
                    roberta_score = -score
                else:  # neutral
                    roberta_score = 0.0
                
                # ⭐ 4 CATÉGORIES
                if roberta_score > 0.3:
                    sentiment_type = 'positive'
                elif 0.05 <= roberta_score <= 0.3:
                    sentiment_type = 'neutral_positive'
                elif -0.3 <= roberta_score < -0.05:
                    sentiment_type = 'neutral_negative'
                else:  # < -0.3
                    sentiment_type = 'negative'
                
                return {
                    'score': roberta_score,
                    'type': sentiment_type,
                    'confidence': score,
                    'model': 'roberta'
                }
                
            except Exception as e:
                logger.error(f"Erreur RoBERTa: {e}")
        
        # FALLBACK : Méthode traditionnelle
        return self._analyze_traditional(text)
    
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
        full_text = f"{title}. {content}"
        return self.analyze_sentiment_with_score(full_text)
