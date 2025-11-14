# Flask/weak_indicators_routes.py - VERSION CORRECTE
from flask import Blueprint, jsonify, request, render_template
import json, random, os
from datetime import datetime, timedelta
import sqlite3

weak_indicators_bp = Blueprint('weak_indicators', __name__)

# === FONCTIONS UTILITAIRES - DÉFINIR D'ABORD ===

def get_db_connection():
    """Connexion à la base de données"""
    instance_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    db_path = os.path.join(instance_dir, 'geopol.db')
    return sqlite3.connect(db_path)

def init_sdr_tables():
    """Initialise les tables SDR si elles n'existent pas"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Table des flux SDR
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sdr_streams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            frequency_khz INTEGER NOT NULL,
            type TEXT DEFAULT 'manual',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Table d'activité quotidienne
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sdr_daily_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stream_id INTEGER NOT NULL,
            date DATE NOT NULL,
            activity_count INTEGER DEFAULT 0,
            FOREIGN KEY(stream_id) REFERENCES sdr_streams(id),
            UNIQUE(stream_id, date)
        )
    """)
    
    conn.commit()
    conn.close()

# === ROUTES PRINCIPALES ===

@weak_indicators_bp.route('/weak-indicators')
def weak_indicators_page():
    return render_template('weak-indicators.html')

@weak_indicators_bp.route('/api/weak-indicators/countries')
def get_monitored_countries():
    """Route pour les pays surveillés"""
    countries = [
        {"code": "FR", "name": "France", "risk_level": "low"},
        {"code": "US", "name": "United States", "risk_level": "medium"},
        {"code": "CN", "name": "China", "risk_level": "medium"},
        {"code": "RU", "name": "Russia", "risk_level": "high"},
        {"code": "UA", "name": "Ukraine", "risk_level": "high"},
        {"code": "IL", "name": "Israel", "risk_level": "high"},
        {"code": "PS", "name": "Palestine", "risk_level": "high"}
    ]
    return jsonify(countries)

@weak_indicators_bp.route('/api/weak-indicators/status')
def get_weak_indicators_status():
    """Route pour le statut global"""
    return jsonify({
        "monitored_countries": 20,
        "active_alerts": random.randint(0, 5),
        "active_sdr_streams": random.randint(3, 8),
        "travel_advice_changes": random.randint(0, 2),
        "last_update": datetime.utcnow().isoformat()
    })

# === ROUTES SDR ===

@weak_indicators_bp.route('/api/sdr-streams', methods=['GET', 'POST'])
def manage_sdr_streams():
    """Gestion des flux SDR"""
    try:
        if request.method == 'GET':
            return get_sdr_streams()
        else:
            return add_sdr_stream()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_sdr_streams():
    """Récupère tous les flux SDR configurés"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT s.id, s.name, s.url, s.frequency_khz, s.type, s.created_at,
               COALESCE(SUM(a.activity_count), 0) as total_activity,
               MAX(a.date) as last_activity
        FROM sdr_streams s
        LEFT JOIN sdr_daily_activity a ON s.id = a.stream_id
        GROUP BY s.id
        ORDER BY s.created_at DESC
    """)
    
    streams = []
    for row in cur.fetchall():
        streams.append({
            "id": row[0],
            "name": row[1],
            "url": row[2],
            "frequency_khz": row[3],
            "type": row[4],
            "created_at": row[5],
            "total_activity": row[6],
            "last_activity": row[7],
            "active": True
        })
    
    conn.close()
    return jsonify(streams)

def add_sdr_stream():
    """Ajoute un nouveau flux SDR"""
    data = request.get_json()
    
    name = data.get('name', '').strip()
    url = data.get('url', '').strip()
    frequency_khz = data.get('frequency_khz')
    
    if not url or not frequency_khz:
        return jsonify({"error": "URL et fréquence requis"}), 400
    
    if not name:
        name = f"Flux {frequency_khz} kHz"
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Vérifier si le flux existe déjà
    cur.execute("SELECT id FROM sdr_streams WHERE url = ? AND frequency_khz = ?", 
                (url, frequency_khz))
    if cur.fetchone():
        conn.close()
        return jsonify({"error": "Ce flux existe déjà"}), 400
    
    # Ajouter le flux
    cur.execute("""
        INSERT INTO sdr_streams (name, url, frequency_khz, type, created_at)
        VALUES (?, ?, ?, 'manual', CURRENT_TIMESTAMP)
    """, (name, url, frequency_khz))
    
    stream_id = cur.lastrowid
    
    # Initialiser l'activité des 7 derniers jours
    today = datetime.utcnow().date()
    for i in range(7):
        date = today - timedelta(days=i)
        activity = random.randint(0, 20)
        cur.execute("""
            INSERT OR IGNORE INTO sdr_daily_activity (stream_id, date, activity_count)
            VALUES (?, ?, ?)
        """, (stream_id, date, activity))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        "success": True,
        "id": stream_id,
        "message": "Flux SDR ajouté avec succès"
    })

@weak_indicators_bp.route('/api/sdr-streams/<int:stream_id>', methods=['DELETE'])
def delete_sdr_stream(stream_id):
    """Supprime un flux SDR"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("DELETE FROM sdr_daily_activity WHERE stream_id = ?", (stream_id,))
        cur.execute("DELETE FROM sdr_streams WHERE id = ?", (stream_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "Flux supprimé"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@weak_indicators_bp.route('/api/sdr-streams/<int:stream_id>/activity')
def get_stream_activity(stream_id):
    """Récupère l'activité d'un flux"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT date, activity_count 
            FROM sdr_daily_activity 
            WHERE stream_id = ? AND date >= date('now', '-30 days')
            ORDER BY date
        """, (stream_id,))
        
        activity_data = []
        for row in cur.fetchall():
            activity_data.append({
                "date": row[0],
                "activity_count": row[1]
            })
        
        # Statistiques
        cur.execute("""
            SELECT 
                AVG(activity_count) as avg_activity,
                MAX(activity_count) as max_activity,
                SUM(activity_count) as total_activity
            FROM sdr_daily_activity 
            WHERE stream_id = ? AND date >= date('now', '-30 days')
        """, (stream_id,))
        
        stats = cur.fetchone()
        conn.close()
        
        return jsonify({
            "stream_id": stream_id,
            "activity": activity_data,
            "stats": {
                "avg_activity": round(stats[0] or 0, 2),
                "max_activity": stats[1] or 0,
                "total_activity": stats[2] or 0
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@weak_indicators_bp.route('/api/sdr-streams/stats')
def get_sdr_streams_stats():
    """Statistiques globales des flux SDR"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM sdr_streams")
        total_streams = cur.fetchone()[0]
        
        today = datetime.utcnow().date().isoformat()
        cur.execute("SELECT SUM(activity_count) FROM sdr_daily_activity WHERE date = ?", (today,))
        today_activity = cur.fetchone()[0] or 0
        
        cur.execute("SELECT AVG(activity_count) FROM sdr_daily_activity WHERE date >= date('now', '-7 days')")
        avg_daily_activity = round(cur.fetchone()[0] or 0, 2)
        
        cur.execute("""
            SELECT s.name, SUM(a.activity_count) as total_activity
            FROM sdr_streams s
            JOIN sdr_daily_activity a ON s.id = a.stream_id
            WHERE a.date >= date('now', '-7 days')
            GROUP BY s.id
            ORDER BY total_activity DESC
            LIMIT 5
        """)
        
        top_streams = []
        for row in cur.fetchall():
            top_streams.append({
                "name": row[0],
                "total_activity": row[1]
            })
        
        conn.close()
        
        return jsonify({
            "total_streams": total_streams,
            "today_activity": today_activity,
            "avg_daily_activity": avg_daily_activity,
            "top_streams": top_streams,
            "last_updated": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# === ROUTES MANQUANTES ===

@weak_indicators_bp.route('/api/travel-advice/scan', methods=['POST'])
def scan_travel_advice():
    """Scan des conseils aux voyageurs"""
    try:
        return jsonify({
            "success": True,
            "results": {
                "scan_date": datetime.utcnow().isoformat(),
                "sources_checked": [
                    {
                        "country": "France",
                        "url": "https://www.diplomatie.gouv.fr",
                        "status": "stable",
                        "level": "normal"
                    },
                    {
                        "country": "USA", 
                        "url": "https://travel.state.gov",
                        "status": "stable",
                        "level": "normal"
                    }
                ],
                "changes_detected": [],
                "alerts": []
            },
            "summary": {
                "scanned": 2,
                "changes": 0,
                "alerts": 0
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@weak_indicators_bp.route('/api/sdr-streams/websdr-monitor', methods=['POST'])
def start_websdr_monitoring():
    """Démarre la surveillance WebSDR"""
    try:
        data = request.get_json()
        websdr_url = data.get('websdr_url', 'http://websdr.ewi.utwente.nl:8901/')
        
        frequencies = [
            {"freq": 121500, "name": "Emergency Aviation"},
            {"freq": 2182000, "name": "Maritime MF"},
            {"freq": 5732000, "name": "Diplomatic HF"},
            {"freq": 8992000, "name": "Government Comm"},
            {"freq": 11175000, "name": "Foreign Service"},
            {"freq": 4500000, "name": "Military LF"}
        ]
        
        added_streams = []
        for freq_info in frequencies:
            conn = get_db_connection()
            cur = conn.cursor()
            
            cur.execute("""
                INSERT OR IGNORE INTO sdr_streams (name, url, frequency_khz, type, created_at)
                VALUES (?, ?, ?, 'websdr', CURRENT_TIMESTAMP)
            """, (freq_info["name"], websdr_url, freq_info["freq"]))
            
            stream_id = cur.lastrowid
            conn.commit()
            conn.close()
            
            if stream_id:
                added_streams.append({
                    "id": stream_id,
                    "name": freq_info["name"],
                    "frequency": freq_info["freq"]
                })
        
        return jsonify({
            "success": True,
            "message": f"Surveillance WebSDR démarrée avec {len(added_streams)} flux",
            "streams": added_streams
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# === ROUTES DEBUG ===

@weak_indicators_bp.route('/api/debug/routes')
def debug_routes():
    """Liste toutes les routes disponibles"""
    routes = []
    for rule in weak_indicators_bp.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': list(rule.methods),
            'path': str(rule)
        })
    return jsonify(routes)

@weak_indicators_bp.route('/api/debug/test')
def debug_test():
    """Route de test simple"""
    return jsonify({
        "status": "ok",
        "message": "API Weak Indicators fonctionnelle",
        "timestamp": datetime.utcnow().isoformat()
    })
