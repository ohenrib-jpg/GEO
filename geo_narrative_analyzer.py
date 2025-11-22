# Flask/geo_narrative_analyzer.py - AVEC IMPORTS COMPLETS

from collections import defaultdict  # ✅ IMPORT MANQUANT
from datetime import datetime        # ✅ IMPORT MANQUANT
import re

class GeoNarrativeAnalyzer:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.verb_patterns_cache = {}
    
    def detect_transnational_patterns(self, days=7, min_countries=2):
        """Détecte les patterns verbaux transnationaux"""
        articles = self._get_recent_articles_by_country(days)
        return self._analyze_verb_patterns(articles, min_countries)
    
    # =========================================================================
    # 2. ANALYSE DES PATTERNS VERBAUX
    # =========================================================================
    
    def _analyze_verb_patterns(self, articles_by_country, min_countries):
        """CŒUR ALGORITHMIQUE - Analyse les cooccurrences verbales entre pays"""
        # ❌ PLUS BESOIN de "from collections import defaultdict" ici
        # ✅ Car déjà importé en haut du fichier
        
        # 1. Extraire les patterns par pays
        country_patterns = {}
        for country, articles in articles_by_country.items():
            verb_patterns = self._extract_verb_patterns(articles)
            country_patterns[country] = verb_patterns
        
        # 2. Détecter les patterns communs
        transnational_patterns = []
        for pattern, countries in self._find_common_patterns(country_patterns).items():
            if len(countries) >= min_countries:
                transnational_patterns.append({
                    'pattern': pattern,
                    'countries': countries,
                    'strength': len(countries),
                    'first_detected': datetime.now().isoformat()  # ✅ datetime disponible
                })
        
        return transnational_patterns
    
    def _extract_verb_patterns(self, articles):
        """Extrait les patterns verbe + contexte des articles d'un pays"""
        patterns = defaultdict(int)  # ✅ defaultdict disponible
        
        for article in articles:
            text = f"{article['title']} {article['content']}"
            sentences = self._split_sentences(text)
            
            for sentence in sentences:
                verbs = self._extract_verbs(sentence)
                for verb in verbs:
                    pattern = self._build_pattern(verb, sentence)
                    if pattern:
                        patterns[pattern] += 1
        
        return dict(patterns)
    
    def _extract_verbs(self, sentence):
        """Extrait les verbes d'une phrase (version simplifiée)"""
        # ✅ re disponible (importé en haut)
        verbs = []
        words = re.findall(r'\b\w+\b', sentence.lower())
        
        # Liste de verbes courants (à étendre)
        common_verbs = {'est', 'sont', 'a', 'ont', 'fait', 'dis', 'affirme', 
                       'déclare', 'annonce', 'précise', 'souligne', 'ajoute'}
        
        for word in words:
            if word in common_verbs:
                verbs.append(word)
        
        return verbs
    
    def _build_pattern(self, verb, sentence):
        """Construit un pattern à partir d'un verbe et de son contexte"""
        words = sentence.lower().split()
        if verb in words:
            verb_index = words.index(verb)
            start = max(0, verb_index - 2)  # 2 mots avant
            end = min(len(words), verb_index + 3)  # 2 mots après
            
            context = words[start:end]
            return " ".join(context)
        
        return None
    
    def _find_common_patterns(self, country_patterns):
        """Trouve les patterns communs à plusieurs pays"""
        # ✅ defaultdict disponible
        pattern_countries = defaultdict(list)
        
        for country, patterns in country_patterns.items():
            for pattern in patterns.keys():
                pattern_countries[pattern].append(country)
        
        return pattern_countries
    
    def _split_sentences(self, text):
        """Découpe un texte en phrases"""
        # ✅ re disponible
        return re.split(r'[.!?]+', text)
    
    # =========================================================================
    # 1. RÉCUPÉRATION DES DONNÉES
    # =========================================================================
    
    def _get_recent_articles_by_country(self, days):
        """Récupère les articles groupés par pays"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT a.id, a.title, a.content, a.feed_url, a.pub_date,
                   CASE 
                     WHEN a.feed_url LIKE '%fr.%' THEN 'FR'
                     WHEN a.feed_url LIKE '%de.%' THEN 'DE' 
                     WHEN a.feed_url LIKE '%uk.%' THEN 'UK'
                     WHEN a.feed_url LIKE '%us.%' THEN 'US'
                     ELSE 'OTHER'
                   END as country
            FROM articles a
            WHERE a.pub_date >= datetime('now', '-' || ? || ' days')
            ORDER BY country, a.pub_date DESC
        """, (days,))
        
        articles_by_country = {}
        for row in cursor.fetchall():
            country = row[5]
            if country not in articles_by_country:
                articles_by_country[country] = []
            
            articles_by_country[country].append({
                'id': row[0], 'title': row[1], 'content': row[2],
                'feed_url': row[3], 'pub_date': row[4], 'country': country
            })
        
        conn.close()
        return articles_by_country