import logging
import threading
from typing import Dict, Any, List, Tuple
import numpy as np

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

try:
    from transformers import pipeline
    ROBERTA_AVAILABLE = True
    print("✅ Transformers disponible - RoBERTa activable")
except ImportError:
    ROBERTA_AVAILABLE = False
    print("⚠️ Transformers non disponible")

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    def __init__(self):
        self.sia = None
        self.roberta_pipeline = None
        
        # 🎯 LEXIQUE GÉOPOLITIQUE
        self.geopolitical_modifiers = {
            # Termes négatifs spécifiques
            'conflit': -0.4, 'guerre': -0.6, 'invasion': -0.7,
            'sanction': -0.5, 'embargo': -0.5, 'crise': -0.4,
            'tension': -0.3, 'menace': -0.4, 'attaque': -0.6,
            'bombardement': -0.7, 'victime': -0.5, 'destruction': -0.6,
            'réfugié': -0.4, 'famine': -0.6, 'répression': -0.5,
            
            # Termes positifs spécifiques
            'accord': 0.4, 'paix': 0.5, 'coopération': 0.4,
            'diplomatie': 0.3, 'négociation': 0.3, 'traité': 0.4,
            'alliance': 0.4, 'stabilité': 0.3, 'développement': 0.3,
            'croissance': 0.3, 'investissement': 0.3, 'partenariat': 0.4,
            
            # Termes neutres contextuels
            'élection': 0.0, 'sommet': 0.0, 'réunion': 0.0,
            'déclaration': 0.0, 'annonce': 0.0, 'visite': 0.0
        }
        
        # 📊 SEUILS CALIBRÉS (basés sur analyse de corpus géopolitique)
        self.thresholds = {
            'positive': 0.25,           # Plus bas qu'avant
            'neutral_positive': 0.08,   # Zone tampon plus large
            'neutral_negative': -0.08,  # Symétrique
            'negative': -0.25           # Plus bas qu'avant
        }
        
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
        """Initialise RoBERTa en arrière-plan"""
        if not ROBERTA_AVAILABLE:
            print("⚠️ RoBERTa non disponible - mode fallback activé")
            return
            
        def load_roberta():
            try:
                print("🤖 Chargement de RoBERTa...")
                self.roberta_pipeline = pipeline(
                    "sentiment-analysis",
                    model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                    truncation=True,
                    max_length=512,
                    device=-1
                )
                print("✅ RoBERTa chargé avec succès !")
            except Exception as e:
                print(f"❌ Erreur chargement RoBERTa: {e}")
                self.roberta_pipeline = None
        
        load_roberta()
    
    def _apply_geopolitical_context(self, text: str, base_score: float) -> float:
        """
        🎯 Ajuste le score en fonction du contexte géopolitique
        """
        text_lower = text.lower()
        adjustment = 0.0
        matches = 0
        
        for term, modifier in self.geopolitical_modifiers.items():
            if term in text_lower:
                adjustment += modifier
                matches += 1
        
        # Moyenne des ajustements trouvés
        if matches > 0:
            adjustment = adjustment / matches
            # Mélange avec le score de base (70% base, 30% contexte)
            adjusted_score = (base_score * 0.7) + (adjustment * 0.3)
            logger.debug(f"🎯 Ajustement géo: {base_score:.3f} → {adjusted_score:.3f} ({matches} termes)")
            return adjusted_score
        
        return base_score
    
    def _smooth_score(self, score: float) -> float:
        """
        📊 Lisse le score pour éviter les catégorisations extrêmes
        Applique une fonction sigmoïde douce
        """
        # Sigmoïde qui compresse les valeurs extrêmes
        smoothed = np.tanh(score * 0.8)
        return float(smoothed)
    
    def _categorize_sentiment(self, score: float, confidence: float) -> str:
        """
        🏷️ Catégorise le sentiment avec prise en compte de la confiance
        """
        # Si confiance faible, préférer le neutre
        if confidence < 0.4:
            if score >= 0:
                return 'neutral_positive'
            else:
                return 'neutral_negative'
        
        # Catégorisation normale
        if score >= self.thresholds['positive']:
            return 'positive'
        elif score >= self.thresholds['neutral_positive']:
            return 'neutral_positive'
        elif score >= self.thresholds['neutral_negative']:
            return 'neutral_negative'
        else:
            return 'negative'
    
    def analyze_sentiment_with_score(self, text: str) -> Dict[str, Any]:
        """
        ⭐ Analyse principale avec améliorations
        """
        if not text or len(text.strip()) < 10:
            return {
                'score': 0.0,
                'type': 'neutral_positive',
                'confidence': 0.0,
                'model': 'none'
            }
        
        # PRIORITÉ 1 : RoBERTa
        if self.roberta_pipeline:
            try:
                text_truncated = text[:500]
                result = self.roberta_pipeline(text_truncated)[0]
                
                label = result['label'].lower()
                raw_confidence = result['score']
                
                # Conversion Cardiff → Score brut [-1, 1]
                if 'positive' in label:
                    raw_score = raw_confidence
                elif 'negative' in label:
                    raw_score = -raw_confidence
                else:
                    raw_score = 0.0
                
                # 🎯 APPLICATION DU CONTEXTE GÉOPOLITIQUE
                geo_adjusted_score = self._apply_geopolitical_context(text, raw_score)
                
                # 📊 LISSAGE
                smoothed_score = self._smooth_score(geo_adjusted_score)
                
                # 🏷️ CATÉGORISATION INTELLIGENTE
                sentiment_type = self._categorize_sentiment(smoothed_score, raw_confidence)
                
                return {
                    'score': smoothed_score,
                    'type': sentiment_type,
                    'confidence': raw_confidence,
                    'model': 'roberta_enhanced',
                    'raw_score': raw_score,  # Pour debug
                    'geo_adjusted': geo_adjusted_score  # Pour debug
                }
                
            except Exception as e:
                logger.error(f"Erreur RoBERTa: {e}")
        
        # FALLBACK : Méthode traditionnelle améliorée
        return self._analyze_traditional_enhanced(text)
    
    def _analyze_traditional_enhanced(self, text: str) -> Dict[str, Any]:
        """
        📚 Analyse traditionnelle avec améliorations
        """
        try:
            scores = []
            
            # TextBlob
            if TEXTBLOB_AVAILABLE:
                blob = TextBlob(text)
                scores.append(blob.sentiment.polarity)
            
            # VADER
            if self.sia:
                vader_scores = self.sia.polarity_scores(text)
                scores.append(vader_scores['compound'])
            
            # Moyenne des scores disponibles
            if scores:
                raw_score = np.mean(scores)
            else:
                raw_score = 0.0
            
            # 🎯 Contexte géopolitique
            geo_adjusted = self._apply_geopolitical_context(text, raw_score)
            
            # 📊 Lissage
            smoothed = self._smooth_score(geo_adjusted)
            
            # Confiance basée sur l'accord entre modèles
            if len(scores) > 1:
                confidence = 1.0 - (np.std(scores) / 2.0)  # Plus d'accord = plus de confiance
            else:
                confidence = 0.5
            
            # 🏷️ Catégorisation
            sentiment_type = self._categorize_sentiment(smoothed, confidence)
            
            return {
                'score': smoothed,
                'type': sentiment_type,
                'confidence': confidence,
                'model': 'traditional_enhanced',
                'raw_score': raw_score,
                'geo_adjusted': geo_adjusted
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
        """Méthode de compatibilité"""
        return self.analyze_sentiment_with_score(text)
    
    def analyze_article(self, title: str, content: str) -> Dict[str, Any]:
        """
        📰 Analyse d'article avec pondération titre/contenu
        """
        # Le titre a plus d'importance (60/40)
        title_analysis = self.analyze_sentiment_with_score(title)
        content_analysis = self.analyze_sentiment_with_score(content[:1000])
        
        # Score combiné
        combined_score = (title_analysis['score'] * 0.6) + (content_analysis['score'] * 0.4)
        combined_confidence = (title_analysis['confidence'] * 0.6) + (content_analysis['confidence'] * 0.4)
        
        # Recatégorisation
        sentiment_type = self._categorize_sentiment(combined_score, combined_confidence)
        
        return {
            'score': combined_score,
            'type': sentiment_type,
            'confidence': combined_confidence,
            'model': title_analysis['model'],
            'title_score': title_analysis['score'],
            'content_score': content_analysis['score']
        }
    
    def get_sentiment_explanation(self, result: Dict[str, Any]) -> str:
        """
        💬 Génère une explication textuelle du sentiment
        """
        score = result['score']
        sentiment = result['type']
        confidence = result['confidence']
        
        explanations = {
            'positive': f"Sentiment positif (score: {score:.2f}, confiance: {confidence:.0%})",
            'neutral_positive': f"Légèrement positif (score: {score:.2f}, confiance: {confidence:.0%})",
            'neutral_negative': f"Légèrement négatif (score: {score:.2f}, confiance: {confidence:.0%})",
            'negative': f"Sentiment négatif (score: {score:.2f}, confiance: {confidence:.0%})"
        }
        
        return explanations.get(sentiment, "Sentiment indéterminé")