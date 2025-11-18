# test_archiviste.py
import sys
import os

# Ajouter le dossier principal au path
main_path = os.path.dirname(os.path.abspath(__file__))
flask_path = os.path.join(main_path, 'Flask')
sys.path.insert(0, main_path)  # Ajouter le dossier principal
sys.path.insert(0, flask_path)

print("🔍 Chemin Python:", sys.path[:5])
print("🔍 Contenu du dossier Flask:", os.listdir(flask_path))

try:
    # Import avec le package Flask
    from Flask.archiviste_enhanced import EnhancedArchiviste
    print("✅ Import réussi")
    print("✅ Classe disponible:", EnhancedArchiviste.__name__ if hasattr(EnhancedArchiviste, '__name__') else "Non trouvé")
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
