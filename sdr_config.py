# Flask/sdr_config.py
"""
Configuration des flux SDR réels
"""

SDR_STREAMS_CONFIG = [
    {
        'name': 'KiwiSDR Global Network',
        'url': 'http://kiwisdr.com/public/',
        'type': 'kiwisdr',
        'description': 'Réseau mondial KiwiSDR - surveillance générale'
    },
    {
        'name': 'WebSDR University Twente',
        'url': 'http://websdr.ewi.utwente.nl:8901/',
        'frequency_khz': 14300,
        'type': 'websdr', 
        'description': 'Station universitaire NL - bandes HF'
    },
    {
        'name': 'Maritime Monitoring',
        'url': 'http://kiwisdr.com/public/',
        'frequency_khz': 2182,
        'type': 'kiwisdr',
        'description': 'Surveillance fréquences maritimes de détresse'
    },
    {
        'name': 'Aviation Emergency',
        'url': 'http://kiwisdr.com/public/', 
        'frequency_khz': 121500,
        'type': 'kiwisdr',
        'description': 'Fréquence urgence aviation 121.5 MHz'
    },
    {
        'name': 'Military Communications',
        'url': 'http://kiwisdr.com/public/',
        'frequency_khz': 6998,
        'type': 'kiwisdr',
        'description': 'Communications militaires standard'
    }
]

def initialize_sdr_streams(db_manager):
    """Initialise les flux SDR dans la base de données"""
    conn = db_manager.get_connection()
    cur = conn.cursor()
    
    # Vérifier si la table existe, sinon la créer
    try:
        cur.execute("SELECT 1 FROM sdr_streams LIMIT 1")
    except:
        # Table n'existe pas, la créer
        print("🔄 Création de la table sdr_streams...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sdr_streams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                frequency_khz INTEGER DEFAULT 0,
                type TEXT DEFAULT 'kiwisdr',
                description TEXT,
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        print("✅ Table sdr_streams créée")
    
    added_count = 0
    for stream in SDR_STREAMS_CONFIG:
        try:
            # Vérifier si le flux existe déjà
            cur.execute("SELECT id FROM sdr_streams WHERE name = ?", (stream['name'],))
            existing = cur.fetchone()
            
            if not existing:
                cur.execute("""
                    INSERT INTO sdr_streams 
                    (name, url, frequency_khz, type, description, active)
                    VALUES (?, ?, ?, ?, ?, 1)
                """, (
                    stream['name'],
                    stream['url'],
                    stream.get('frequency_khz', 0),
                    stream['type'],
                    stream['description']
                ))
                added_count += 1
                print(f"✅ Flux SDR ajouté: {stream['name']}")
            else:
                print(f"⚠️ Flux SDR existe déjà: {stream['name']}")
                
        except Exception as e:
            print(f"❌ Erreur ajout flux SDR {stream['name']}: {e}")
    
    conn.commit()
    
    # Compter le total des flux
    cur.execute("SELECT COUNT(*) FROM sdr_streams")
    total_count = cur.fetchone()[0]
    conn.close()
    
    print(f"🎯 {added_count} nouveaux flux SDR ajoutés ({total_count} au total)")
    return total_count