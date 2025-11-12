#!/usr/bin/env python3
# diagnostic_roberta.py - VÉRIFICATION COMPLÈTE

import sys
import os
import time

# Ajouter le chemin du projet
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_dependencies():
    """Vérifie les dépendances critiques"""
    print("=" * 60)
    print("🔍 VÉRIFICATION DES DÉPENDANCES")
    print("=" * 60)
    
    dependencies = {
        'flask': 'Flask',
        'transformers': 'Transformers (RoBERTa)',
        'torch': 'PyTorch',
        'textblob': 'TextBlob',
        'nltk': 'NLTK',
        'feedparser': 'Feedparser',
        'bs4': 'BeautifulSoup'
    }
    
    missing = []
    for package, name in dependencies.items():
        try:
            __import__(package)
            print(f"✅ {name}")
        except ImportError:
            print(f"❌ {name} - MANQUANT")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️ Dépendances manquantes: {', '.join(missing)}")
        print(f"💡 Installation: pip install {' '.join(missing)}")
        return False
    
    return True

def test_roberta():
    """Test RoBERTa avec 3 exemples"""
    print("\n" + "=" * 60)
    print("🤖 TEST RoBERTa")
    print("=" * 60)
    
    try:
        from Flask.sentiment_analyzer import SentimentAnalyzer
        
        analyzer = SentimentAnalyzer()
        
        # Attendre le chargement
        print("⏳ Chargement de RoBERTa (attente 10 secondes)...")
        time.sleep(10)
        
        test_cases = [
            ("This is absolutely fantastic and wonderful!", "positif attendu"),
            ("This is terrible and awful.", "négatif attendu"),
            ("The weather is normal today.", "neutre attendu")
        ]
        
        print("\n📝 Tests d'analyse:")
        for i, (text, expected) in enumerate(test_cases, 1):
            print(f"\n--- Test {i} ({expected}) ---")
            print(f"Texte: '{text}'")
            
            result = analyzer.analyze_sentiment_with_score(text)
            
            print(f"🔹 Modèle: {result['model']}")
            print(f"🔹 Type: {result['type']}")
            print(f"🔹 Score: {result['score']:.4f}")
            print(f"🔹 Confiance: {result['confidence']:.4f}")
            
            if result['model'] == 'roberta':
                print("✅ RoBERTa ACTIF!")
            else:
                print("⚠️ Mode fallback (traditionnel)")
        
        return analyzer.roberta_pipeline is not None
        
    except Exception as e:
        print(f"❌ Erreur test RoBERTa: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_database():
    """Vérifie la base de données"""
    print("\n" + "=" * 60)
    print("📊 VÉRIFICATION BASE DE DONNÉES")
    print("=" * 60)
    
    try:
        import sqlite3
        from Flask.config import DB_PATH
        
        if not os.path.exists(DB_PATH):
            print(f"❌ Base de données introuvable: {DB_PATH}")
            return False
        
        print(f"✅ Base de données: {DB_PATH}")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Vérifier les colonnes
        cursor.execute("PRAGMA table_info(articles)")
        columns = [col[1] for col in cursor.fetchall()]
        
        critical_columns = [
            'analysis_model',
            'detailed_sentiment',
            'sentiment_confidence',
            'roberta_score'
        ]
        
        print("\n🔹 Colonnes critiques:")
        for col in critical_columns:
            if col in columns:
                print(f"   ✅ {col}")
            else:
                print(f"   ❌ {col} - MANQUANTE")
        
        # Statistiques
        cursor.execute("SELECT COUNT(*) FROM articles")
        total = cursor.fetchone()[0]
        print(f"\n📊 Total articles: {total}")
        
        if 'analysis_model' in columns:
            cursor.execute("""
                SELECT 
                    analysis_model, 
                    COUNT(*) as count,
                    AVG(roberta_score) as avg_score
                FROM articles 
                WHERE analysis_model IS NOT NULL
                GROUP BY analysis_model
            """)
            
            print("\n🔹 Articles par modèle:")
            for row in cursor.fetchall():
                model, count, avg_score = row
                avg_score_str = f"{avg_score:.4f}" if avg_score else "N/A"
                print(f"   {model}: {count} articles (score moyen: {avg_score_str})")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur BD: {e}")
        return False

def check_app_factory():
    """Vérifie app_factory.py"""
    print("\n" + "=" * 60)
    print("🏭 VÉRIFICATION APP_FACTORY.PY")
    print("=" * 60)
    
    try:
        with open('Flask/app_factory.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = {
            'SentimentAnalyzer importé': 'from .sentiment_analyzer import SentimentAnalyzer' in content,
            'sentiment_analyzer créé': 'sentiment_analyzer = SentimentAnalyzer()' in content,
            'Passé à RSSManager': 'sentiment_analyzer=sentiment_analyzer' in content
        }
        
        for check, result in checks.items():
            status = "✅" if result else "❌"
            print(f"{status} {check}")
        
        return all(checks.values())
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def main():
    """Fonction principale"""
    print("\n" + "=" * 60)
    print("🚀 DIAGNOSTIC COMPLET GEOPOL - RoBERTa")
    print("=" * 60)
    
    results = {
        'Dépendances': check_dependencies(),
        'RoBERTa': test_roberta(),
        'Base de données': check_database(),
        'App Factory': check_app_factory()
    }
    
    print("\n" + "=" * 60)
    print("📋 RÉSUMÉ")
    print("=" * 60)
    
    for test, passed in results.items():
        status = "✅ OK" if passed else "❌ ÉCHEC"
        print(f"{status} - {test}")
    
    if all(results.values()):
        print("\n🎉 Tous les tests sont passés !")
        print("💡 RoBERTa devrait fonctionner correctement")
    else:
        print("\n⚠️ Certains tests ont échoué")
        print("💡 Consultez les détails ci-dessus")

if __name__ == "__main__":
    main()
