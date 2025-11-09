# Flask/sentiment_analyzer.py - VERSION AMÉLIORÉE
import logging
import threading
from typing import Dict, Any
import numpy as np
from scipy import stats

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

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    def __init__(self):
        self.sia = None
        self.transformer_pipeline = None
        self._initialize_nltk()
        self._initialize_transformer()
    
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
    
    def _initialize_transformer(self):
        """Initialise le modèle de transformers pour une analyse plus précise"""
        if not TRANSFORMERS_AVAILABLE:
            return
            
        try:
            # Utilisation d'un modèle multilingue pour une meilleure couverture
            self.transformer_pipeline = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                return_all_scores=True
            )
            logger.info("✅ Modèle Transformer initialisé")
        except Exception as e:
            logger.warning(f"⚠️ Impossible d'initialiser le modèle Transformer: {e}")
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyse le sentiment d'un texte avec plusieurs approches pour plus d'objectivité
        Retourne un dictionnaire avec le score, le type de sentiment et la confiance
        """
        if not text or len(text.strip()) < 10:
            return {
                'score': 0.0,
                'type': 'neutral',
                'confidence': 0.0,
                'method': 'none'
            }
        
        try:
            scores = []
            methods = []
            confidences = []
            
            # Analyse avec TextBlob
            if TEXTBLOB_AVAILABLE:
                blob = TextBlob(text)
                polarity = blob.sentiment.polarity
                subjectivity = blob.sentiment.subjectivity
                scores.append(polarity)
                methods.append('textblob')
                # Confiance basée sur la subjectivité (plus subjectif = moins confiant)
                confidences.append(1.0 - subjectivity)
            
            # Analyse avec VADER
            if self.sia:
                vader_scores = self.sia.polarity_scores(text)
                vader_compound = vader_scores['compound']
                scores.append(vader_compound)
                methods.append('vader')
                # Confiance basée sur la force des émotions
                emotion_strength = abs(vader_scores['pos'] - vader_scores['neg'])
                confidences.append(min(1.0, emotion_strength * 2))
            
            # Analyse avec Transformer (si disponible)
            if self.transformer_pipeline:
                try:
                    transformer_result = self.transformer_pipeline(text[:512])  # Limite de tokens
                    # Extraire le score de la classe la plus probable
                    best_score = max(transformer_result[0], key=lambda x: x['score'])
                    if best_score['label'] == 'LABEL_2':  # POSITIF
                        transformer_score = best_score['score']
                    elif best_score['label'] == 'LABEL_0':  # NÉGATIF
                        transformer_score = -best_score['score']
                    else:  # NEUTRE
                        transformer_score = 0
                    
                    scores.append(transformer_score)
                    methods.append('transformer')
                    confidences.append(best_score['score'])
                except Exception as e:
                    logger.debug(f"Erreur analyse transformer: {e}")
            
            if not scores:
                return {
                    'score': 0.0,
                    'type': 'neutral',
                    'confidence': 0.0,
                    'method': 'none'
                }
            
            # Calcul du score final pondéré par la confiance
            if confidences:
                # Moyenne pondérée par la confiance
                weighted_sum = sum(s * c for s, c in zip(scores, confidences))
                total_confidence = sum(confidences)
                combined_score = weighted_sum / total_confidence if total_confidence > 0 else 0
                avg_confidence = sum(confidences) / len(confidences)
            else:
                # Moyenne simple si pas de confiance
                combined_score = sum(scores) / len(scores)
                avg_confidence = 0.5
            
            # Détermination du type de sentiment avec seuils plus stricts
            if combined_score > 0.2:
                sentiment_type = 'positive'
            elif combined_score < -0.2:
                sentiment_type = 'negative'
            else:
                sentiment_type = 'neutral'
            
            # Calcul de l'écart-type pour la variabilité
            std_dev = np.std(scores) if len(scores) > 1 else 0
            
            return {
                'score': round(combined_score, 4),
                'type': sentiment_type,
                'confidence': round(min(avg_confidence, 1.0), 4),
                'method': '+'.join(methods) if methods else 'none',
                'variability': round(std_dev, 4),
                'individual_scores': dict(zip(methods, [round(s, 4) for s in scores])) if methods else {}
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse des sentiments: {e}")
            return {
                'score': 0.0,
                'type': 'neutral',
                'confidence': 0.0,
                'method': 'error',
                'error': str(e)
            }
    
    def analyze_article(self, title: str, content: str) -> Dict[str, Any]:
        """Analyse le sentiment d'un article complet avec contexte"""
        full_text = f"{title}. {content}"
        result = self.analyze_sentiment(full_text)
        
        # Ajout d'informations contextuelles
        result['text_length'] = len(full_text)
        result['title_sentiment'] = self.analyze_sentiment(title)['score'] if title else 0
        result['content_sentiment'] = self.analyze_sentiment(content)['score'] if content else 0
        
        return result
