import logging
import threading
from typing import Dict, Any

# Importations conditionnelles
try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False

try:
    import nltk
    from nltk.sentiment import SentimentIntensityAnalyzer
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    def __init__(self):
        self.sia = None
        self._initialize_nltk()
    
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
        
        # Lance le téléchargement dans un thread séparé
        thread = threading.Thread(target=download_nltk_data)
        thread.daemon = True
        thread.start()
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyse le sentiment d'un texte en utilisant TextBlob et VADER
        Retourne un dictionnaire avec le score et le type de sentiment
        """
        if not text or len(text.strip()) < 10:
            return {
                'score': 0.0,
                'type': 'neutral',
                'confidence': 0.0
            }
        
        try:
            # Analyse avec TextBlob
            if TEXTBLOB_AVAILABLE:
                blob = TextBlob(text)
                polarity = blob.sentiment.polarity
                subjectivity = blob.sentiment.subjectivity
            else:
                polarity = 0.0
                subjectivity = 0.0
            
            # Analyse avec VADER
            if self.sia:
                vader_scores = self.sia.polarity_scores(text)
                vader_compound = vader_scores['compound']
            else:
                vader_compound = 0.0
            
            # Combinaison des scores
            if TEXTBLOB_AVAILABLE and self.sia:
                combined_score = (polarity + vader_compound) / 2
            elif TEXTBLOB_AVAILABLE:
                combined_score = polarity
            elif self.sia:
                combined_score = vader_compound
            else:
                combined_score = 0.0
            
            # Détermination du type de sentiment
            if combined_score > 0.1:
                sentiment_type = 'positive'
                confidence = abs(combined_score)
            elif combined_score < -0.1:
                sentiment_type = 'negative'
                confidence = abs(combined_score)
            else:
                sentiment_type = 'neutral'
                confidence = 1.0 - abs(combined_score)
            
            return {
                'score': combined_score,
                'type': sentiment_type,
                'confidence': min(confidence, 1.0)
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse des sentiments: {e}")
            return {
                'score': 0.0,
                'type': 'neutral',
                'confidence': 0.0
            }
    
    def analyze_article(self, title: str, content: str) -> Dict[str, Any]:
        """Analyse le sentiment d'un article complet"""
        full_text = f"{title}. {content}"
        return self.analyze_sentiment(full_text)