# test_archiviste.py - Script de test du module Archiviste
"""
Script pour tester le module Archiviste
Usage: python test_archiviste.py
"""
import sys
import os

# Ajouter le chemin du projet
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Teste les imports nécessaires"""
    print("🔍 Test des imports...")
    
    try:
        import internetarchive
        print("  ✅ internetarchive installé")
    except ImportError:
        print("  ❌ internetarchive NON installé")
        print("     Installation: pip install internetarchive")
        return False
    
    try:
        from Flask.database import DatabaseManager
        print("  ✅ DatabaseManager disponible")
    except ImportError:
        print("  ⚠️ DatabaseManager non importable (normal si test isolé)")
    
    try:
        from Flask.archiviste import Archiviste, get_archiviste
        print("  ✅ Archiviste importable")
    except ImportError as e:
        print(f"  ❌ Erreur import Archiviste: {e}")
        return False
    
    return True


def test_archive_connection():
    """Teste la connexion à Archive.org"""
    print("\n🌐 Test de connexion Archive.org...")
    
    try:
        from internetarchive import search_items
        
        # Recherche simple
        results = search_items('collection:newspapers AND year:2000')
        
        # Récupérer le premier résultat
        first_result = None
        for item in results:
            first_result = item
            break
        
        if first_result:
            print(f"  ✅ Connexion OK - Item trouvé: {first_result.get('identifier', 'N/A')}")
            return True
        else:
            print("  ⚠️ Aucun résultat (normal, limite API)")
            return True
            
    except Exception as e:
        print(f"  ❌ Erreur connexion: {e}")
        return False


def test_archiviste_basic():
    """Teste les fonctionnalités de base d'Archiviste"""
    print("\n🧪 Test fonctionnalités Archiviste...")
    
    try:
        # Mock database manager pour le test
        class MockDatabaseManager:
            def get_connection(self):
                import sqlite3
                return sqlite3.connect(':memory:')
        
        from Flask.archiviste import Archiviste
        
        db_manager = MockDatabaseManager()
        archiviste = Archiviste(db_manager)
        
        print("  ✅ Instance Archiviste créée")
        
        # Vérifier les périodes
        periods = archiviste.historical_periods
        print(f"  ✅ {len(periods)} périodes historiques définies")
        
        # Vérifier les collections
        collections = archiviste.preferred_collections
        print(f"  ✅ {len(collections)} collections préférées")
        
        # Test extraction texte
        test_item = {
            'title': 'Test Title',
            'description': 'Test Description',
            'subject': ['politics', 'international']
        }
        text = archiviste.extract_text_from_item(test_item)
        print(f"  ✅ Extraction texte OK ({len(text)} caractères)")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Erreur test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_search_simulation():
    """Simule une recherche"""
    print("\n🔎 Test de recherche (simulation)...")
    
    try:
        from internetarchive import search_items
        
        query = 'collection:newspapers AND year:1990'
        print(f"  Requête: {query}")
        
        results = search_items(query)
        
        count = 0
        for i, item in enumerate(results):
            if i >= 5:  # Limiter à 5 pour le test
                break
            count += 1
            print(f"    {i+1}. {item.get('identifier', 'N/A')} - {item.get('title', 'N/A')[:50]}")
        
        if count > 0:
            print(f"  ✅ {count} résultats trouvés")
            return True
        else:
            print("  ⚠️ Aucun résultat (peut être normal)")
            return True
            
    except Exception as e:
        print(f"  ❌ Erreur recherche: {e}")
        return False


def main():
    """Fonction principale de test"""
    print("=" * 60)
    print("🧪 TEST MODULE ARCHIVISTE")
    print("=" * 60)
    
    results = []
    
    # Test 1: Imports
    results.append(("Imports", test_imports()))
    
    # Test 2: Connexion Archive.org
    results.append(("Connexion Archive.org", test_archive_connection()))
    
    # Test 3: Archiviste basic
    results.append(("Archiviste fonctionnalités", test_archiviste_basic()))
    
    # Test 4: Recherche
    results.append(("Recherche simulation", test_search_simulation()))
    
    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {passed}/{len(results)} tests réussis")
    
    if failed == 0:
        print("\n🎉 Tous les tests sont passés ! Le module Archiviste est prêt.")
        return 0
    else:
        print(f"\n⚠️ {failed} test(s) échoué(s). Vérifiez les erreurs ci-dessus.")
        return 1


if __name__ == '__main__':
    sys.exit(main())