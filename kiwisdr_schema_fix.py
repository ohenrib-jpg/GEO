# Flask/kiwisdr_schema_fix.py
"""
Correctif du schéma KiwiSDR pour la colonne 'notes' manquante
"""

import sqlite3
import logging

logger = logging.getLogger(__name__)

def fix_kiwisdr_schema(db_manager):
    """Corrige le schéma KiwiSDR"""
    try:
        conn = db_manager.get_connection()
        cur = conn.cursor()
        
        # Vérifier si la colonne 'notes' existe dans kiwisdr_frequency_activity
        cur.execute("PRAGMA table_info(kiwisdr_frequency_activity)")
        columns = [row[1] for row in cur.fetchall()]
        
        if 'notes' not in columns:
            print("🔧 Ajout de la colonne 'notes' à kiwisdr_frequency_activity...")
            cur.execute("ALTER TABLE kiwisdr_frequency_activity ADD COLUMN notes TEXT")
            print("✅ Colonne 'notes' ajoutée")
        
        # Vérifier d'autres colonnes manquantes
        if 'observer' not in columns:
            print("🔧 Ajout de la colonne 'observer'...")
            cur.execute("ALTER TABLE kiwisdr_frequency_activity ADD COLUMN observer TEXT DEFAULT 'user'")
            print("✅ Colonne 'observer' ajoutée")
        
        conn.commit()
        conn.close()
        print("🎉 Schéma KiwiSDR corrigé avec succès")
        
    except Exception as e:
        print(f"❌ Erreur correction schéma: {e}")