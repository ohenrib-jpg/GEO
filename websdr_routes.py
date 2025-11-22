# Flask/websdr_routes.py
from flask import Blueprint, jsonify, request
import requests
import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timedelta
import sqlite3
import os
import random
import numpy as np

websdr_bp = Blueprint('websdr', __name__)
logger = logging.getLogger(__name__)

# === GESTION DES STATIONS SDR ===

@websdr_bp.route('/api/sdr-streams', methods=['GET', 'POST'])
def manage_sdr_streams():
    """Gestion des flux SDR - COMPATIBLE AVEC L'EXISTANT"""
    try:
        if request.method == 'GET':
            return get_sdr_streams()
        else:
            return add_sdr_stream()
    except Exception as e:
        logger.error(f"Erreur gestion flux SDR: {e}")
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
        activity = random.randint(0, 20)  # Activité initiale simulée
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

@websdr_bp.route('/api/sdr-streams/<int:stream_id>', methods=['DELETE'])
def delete_sdr_stream(stream_id):
    """Supprime un flux SDR"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Supprimer l'activité associée
        cur.execute("DELETE FROM sdr_daily_activity WHERE stream_id = ?", (stream_id,))
        # Supprimer le flux
        cur.execute("DELETE FROM sdr_streams WHERE id = ?", (stream_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "Flux supprimé"})
    except Exception as e:
        logger.error(f"Erreur suppression flux SDR: {e}")
        return jsonify({"error": str(e)}), 500

@websdr_bp.route('/api/sdr-streams/<int:stream_id>/activity')
def get_stream_activity(stream_id):
    """Récupère l'activité d'un flux sur les 30 derniers jours"""
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
        logger.error(f"Erreur activité flux: {e}")
        return jsonify({"error": str(e)}), 500

@websdr_bp.route('/api/sdr-streams/stats')
def get_sdr_streams_stats():
    """Statistiques globales des flux SDR"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Nombre total de flux
        cur.execute("SELECT COUNT(*) FROM sdr_streams")
        total_streams = cur.fetchone()[0]
        
        # Activité totale aujourd'hui
        today = datetime.utcnow().date().isoformat()
        cur.execute("SELECT SUM(activity_count) FROM sdr_daily_activity WHERE date = ?", (today,))
        today_activity = cur.fetchone()[0] or 0
        
        # Activité moyenne par jour
        cur.execute("SELECT AVG(activity_count) FROM sdr_daily_activity WHERE date >= date('now', '-7 days')")
        avg_daily_activity = round(cur.fetchone()[0] or 0, 2)
        
        # Flux les plus actifs
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
        logger.error(f"Erreur statistiques SDR: {e}")
        return jsonify({"error": str(e)}), 500

# === SERVEURS WEBSDR PUBLICS ===

@websdr_bp.route('/api/websdr/servers')
def get_websdr_servers():
    """Retourne la liste des serveurs WebSDR publics"""
    servers = [
        {
            'id': 0,
            'name': 'University of Twente (NL)',
            'url': 'http://websdr.ewi.utwente.nl:8901/',
            'bands': ['LF', 'MF', 'HF', 'VHF'],
            'location': 'Netherlands',
            'status': 'online',
            'users_online': random.randint(5, 50)
        },
        {
            'id': 1, 
            'name': 'RTL-SDR Hong Kong',
            'url': 'http://sdr.rtl.hk:8901/',
            'bands': ['HF', 'VHF'],
            'location': 'Hong Kong',
            'status': 'online',
            'users_online': random.randint(2, 20)
        },
        {
            'id': 2,
            'name': 'WebSDR Germany',
            'url': 'http://websdr.fdmr.de:8901/',
            'bands': ['HF'],
            'location': 'Germany', 
            'status': 'online',
            'users_online': random.randint(3, 15)
        }
    ]
    
    return jsonify({
        "servers": servers,
        "total_online": len(servers)
    })

@websdr_bp.route('/api/websdr/emissions/recent')
def get_recent_emissions():
    """Émissions récentes détectées"""
    try:
        hours = int(request.args.get('hours', 24))
        
        # Pour l'instant, données simulées
        emissions = []
        base_time = datetime.utcnow()
        
        # Générer des émissions réalistes
        frequencies = [121500, 5732000, 8992000, 11175000, 4500000, 3023000]
        
        for i in range(random.randint(5, 15)):
            freq = random.choice(frequencies)
            emissions.append({
                'id': i,
                'frequency': freq,
                'strength': round(random.uniform(0.1, 0.9), 2),
                'bandwidth': random.choice([100, 500, 1000, 2500]),
                'type': random.choice(['aviation', 'maritime', 'military', 'diplomatic', 'emergency']),
                'server': f"Server {random.randint(0, 2)}",
                'timestamp': (base_time - timedelta(minutes=random.randint(0, hours*60))).isoformat(),
                'analysis': {
                    'modulation': random.choice(['AM', 'FM', 'SSB']),
                    'speech_detected': random.choice([True, False])
                }
            })
        
        # Trier par timestamp
        emissions.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify({
            "emissions": emissions[:20],  # Limiter à 20
            "timeframe_hours": hours,
            "total": len(emissions)
        })
        
    except Exception as e:
        logger.error(f"Erreur émissions récentes: {e}")
        return jsonify({"error": str(e)}), 500

# === FONCTIONS UTILITAIRES ===

def get_db_connection():
    """Connexion à la base de données"""
    instance_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    db_path = os.path.join(instance_dir, 'geopol.db')
    return sqlite3.connect(db_path)

def init_websdr_tables():
    """Initialise les tables WebSDR"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Table des flux SDR (compatible existant)
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
    
    # Table d'activité quotidienne (compatible existant)
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
    
    # Table des émissions détectées
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sdr_emissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            frequency INTEGER NOT NULL,
            strength REAL NOT NULL,
            bandwidth INTEGER,
            type TEXT,
            server TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            analysis TEXT
        )
    """)
    
    # Index pour performances
    cur.execute("CREATE INDEX IF NOT EXISTS idx_sdr_activity_stream ON sdr_daily_activity(stream_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_sdr_activity_date ON sdr_daily_activity(date)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_emissions_frequency ON sdr_emissions(frequency)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_emissions_time ON sdr_emissions(timestamp)")
    
    conn.commit()
    conn.close()

# Initialisation au chargement
init_websdr_tables()