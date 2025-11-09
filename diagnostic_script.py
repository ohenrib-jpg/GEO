#!/usr/bin/env python3
"""
Script de diagnostic pour vérifier l'installation
"""

import os
import sys

def check_file(filepath, description):
    """Vérifie l'existence d'un fichier"""
    exists = os.path.exists(filepath)
    size = os.path.getsize(filepath) if exists else 0
    status = "✅" if exists else "❌"
    print(f"{status} {description}")
    if exists:
        print(f"   📁 {filepath} ({size} bytes)")
    else:
        print(f"   ⚠️  Fichier manquant: {filepath}")
    return exists

def main():
    print("=" * 60)
    print("🔍 DIAGNOSTIC DE L'ANALYSEUR RSS")
    print("=" * 60)
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("\n📂 Fichiers JavaScript:")
    js_files = [
        ("static/js/app.js", "Core JavaScript"),
        ("static/js/themes.js", "Gestion des thèmes"),
        ("static/js/themes-advanced.js", "Thèmes avancés"),
        ("static/js/articles.js", "Gestion des articles"),
        ("static/js/feeds.js", "Gestion des flux RSS"),
        ("static/js/filters.js", "Filtres avancés"),
        ("static/js/advanced-analysis.js", "⭐ ANALYSE AVANCÉE"),
        ("static/js/settings.js", "Paramètres"),
        ("static/js/dashboard.js", "Tableau de bord"),
    ]
    
    missing_js = []
    for filepath, description in js_files:
        full_path = os.path.join(base_dir, filepath)
        if not check_file(full_path, description):
            missing_js.append(filepath)
    
    print("\n📂 Fichiers Python:")
    py_files = [
        ("Flask/bayesian_analyzer.py", "Analyseur bayésien"),
        ("Flask/corroboration_engine.py", "Moteur de corroboration"),
        ("Flask/database_migrations.py", "Migrations"),
        ("Flask/routes_advanced.py", "Routes avancées"),
    ]
    
    missing_py = []
    for filepath, description in py_files:
        full_path = os.path.join(base_dir, filepath)
        if not check_file(full_path, description):
            missing_py.append(filepath)
    
    print("\n📂 Templates HTML:")
    html_files = [
        ("templates/base.html", "Template de base"),
        ("templates/index.html", "Page d'accueil"),
        ("templates/dashboard.html", "Tableau de bord"),
    ]
    
    for filepath, description in html_files:
        full_path = os.path.join(base_dir, filepath)
        check_file(full_path, description)
    
    print("\n📊 Base de données:")
    db_path = os.path.join(base_dir, "rss_analyzer.db")
    check_file(db_path, "Base de données SQLite")
    
    print("\n" + "=" * 60)
    
    if missing_js or missing_py:
        print("❌ PROBLÈMES DÉTECTÉS:")
        if missing_js:
            print("\n⚠️  Fichiers JavaScript manquants:")
            for f in missing_js:
                print(f"   - {f}")
        if missing_py:
            print("\n⚠️  Fichiers Python manquants:")
            for f in missing_py:
                print(f"   - {f}")
        
        print("\n💡 SOLUTION:")
        print("   Les fichiers doivent être créés manuellement.")
        print("   Consultez les artifacts fournis dans la conversation.")
        return False
    else:
        print("✅ TOUS LES FICHIERS SONT PRÉSENTS")
        print("\n🔍 Vérification de l'intégration dans base.html...")
        
        base_html_path = os.path.join(base_dir, "templates/base.html")
        if os.path.exists(base_html_path):
            with open(base_html_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            checks = {
                'advanced-analysis.js inclus': 'advanced-analysis.js' in content,
                'Bouton analyse avancée présent': 'nav-advanced' in content,
                'Gestionnaire événement présent': 'AdvancedAnalysisManager' in content,
            }
            
            print("\n📋 Vérifications base.html:")
            for check, result in checks.items():
                status = "✅" if result else "❌"
                print(f"{status} {check}")
                
            if not all(checks.values()):
                print("\n⚠️  Problème dans base.html détecté!")
                return False
        
        return True

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n✅ Diagnostic OK - Le système devrait fonctionner")
        print("\n🚀 Prochaines étapes:")
        print("   1. Redémarrez l'application: python run.py")
        print("   2. Ouvrez http://localhost:5000")
        print("   3. Ouvrez la console du navigateur (F12)")
        print("   4. Vérifiez les erreurs JavaScript")
    else:
        print("\n❌ Diagnostic ÉCHEC - Des fichiers manquent")
        print("\n💡 Veuillez créer les fichiers manquants")
    
    sys.exit(0 if success else 1)
