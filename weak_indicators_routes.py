# Flask/weak_indicators_routes.py
from flask import Blueprint, jsonify, request, render_template
import json, random, os
from datetime import datetime, timedelta
import sqlite3

weak_indicators_bp = Blueprint('weak_indicators', __name__)

# Route UI
@weak_indicators_bp.route('/weak-indicators')
def weak_indicators_page():
    return render_template('weak-indicators.html')

# Données de base (pays surveillés)
@weak_indicators_bp.route('/api/weak-indicators/countries')
def get_monitored_countries():
    default_countries = [
        {"code": "FR", "name": "France"},
        {"code": "US", "name": "United States"},
        {"code": "CN", "name": "China"},
        {"code": "DE", "name": "Germany"},
        {"code": "GB", "name": "United Kingdom"},
        {"code": "JP", "name": "Japan"},
        {"code": "RU", "name": "Russia"},
        {"code": "IN", "name": "India"},
        {"code": "BR", "name": "Brazil"},
        {"code": "CA", "name": "Canada"},
        {"code": "IT", "name": "Italy"},
        {"code": "ES", "name": "Spain"},
        {"code": "AU", "name": "Australia"},
        {"code": "MX", "name": "Mexico"},
        {"code": "KR", "name": "South Korea"},
        {"code": "ZA", "name": "South Africa"},
        {"code": "SA", "name": "Saudi Arabia"},
        {"code": "TR", "name": "Turkey"},
        {"code": "AR", "name": "Argentina"},
        {"code": "ID", "name": "Indonesia"},
    ]
    return jsonify(default_countries)

# Statut global pour les cartes du haut
@weak_indicators_bp.route('/api/weak-indicators/status')
def get_weak_indicators_status():
    # En production: SELECT COUNT(*) etc. Ici, valeurs simulées
    return jsonify({
        "monitored_countries": 20,
        "active_alerts": random.randint(0, 5),
        "active_sdr_streams": 0
    })

# Conseils aux voyageurs (mock + alerte si besoin)
@weak_indicators_bp.route('/api/travel-advice/<country>')
def get_travel_advice(country):
    statuses = ["normal", "vigilance", "deconseille", "formellement_deconseille"]
    weights = [0.7, 0.2, 0.08, 0.02]
    status = random.choices(statuses, weights=weights)[0]
    details = {
        "security": f"Situation {'calme' if status == 'normal' else 'tendue'}",
        "recommendations": {
            "normal": ["Vigilance normale dans les lieux touristiques"],
            "vigilance": ["Éviter les rassemblements", "Rester informé"],
            "deconseille": ["Voyage essentiel uniquement", "Éviter certaines régions"],
            "formellement_deconseille": ["Ne pas se rendre dans le pays", "Évacuation recommandée"]
        }[status]
    }
    resp = {
        "country": country.upper(),
        "status": status,
        "last_update": datetime.utcnow().isoformat(),
        "details": details
    }
    # Détection d'alertes (ex: changement brutal => flag "changes")
    if random.random() < 0.1:
        resp["changes"] = ["Changement de niveau de conseil détecté"]
    return jsonify(resp)

# Flux SDR: GET liste, POST ajout, DELETE suppression
@weak_indicators_bp.route('/api/sdr-streams', methods=['GET', 'POST'])
def manage_sdr_streams():
    # Créer l'instance dir si elle n'existe pas
    instance_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    db_path = os.path.join(instance_dir, 'geopol.db')
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sdr_streams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            frequency_khz INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
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

    if request.method == 'GET':
        cur.execute("SELECT id, name, url, frequency_khz, created_at FROM sdr_streams ORDER BY id DESC")
        rows = cur.fetchall()
        streams = []
        for r in rows:
            sid = r[0]
            cur.execute("SELECT SUM(activity_count) FROM sdr_daily_activity WHERE stream_id = ?", (sid,))
            total_activity = cur.fetchone()[0] or 0
            streams.append({
                "id": sid,
                "name": r[1],
                "url": r[2],
                "frequency_khz": r[3],
                "created_at": r[4],
                "total_activity": total_activity,
                "active": True
            })
        conn.close()
        return jsonify(streams)

    # POST: ajout d'un flux + initialisation activité vide
    data = request.get_json(force=True)
    name = data.get('name') or f"Flux {data.get('frequency_khz')} kHz"
    url = data.get('url')
    freq = int(data.get('frequency_khz'))
    if not url or not freq:
        conn.close()
        return jsonify({"error": "url et frequency_khz requis"}), 400
    cur.execute("INSERT INTO sdr_streams(name, url, frequency_khz) VALUES (?, ?, ?)", (name, url, freq))
    stream_id = cur.lastrowid
    # Initialiser l'activité des 7 derniers jours
    today = datetime.utcnow().date()
    for i in range(7):
        d = today - timedelta(days=i)
        cur.execute("INSERT OR IGNORE INTO sdr_daily_activity(stream_id, date, activity_count) VALUES (?, ?, ?)",
                    (stream_id, d, 0))
    conn.commit()
    conn.close()
    return jsonify({"status": "created", "id": stream_id})

@weak_indicators_bp.route('/api/sdr-streams/<int:stream_id>', methods=['DELETE'])
def delete_sdr_stream(stream_id):
    instance_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance')
    db_path = os.path.join(instance_dir, 'geopol.db')
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("DELETE FROM sdr_daily_activity WHERE stream_id = ?", (stream_id,))
    cur.execute("DELETE FROM sdr_streams WHERE id = ?", (stream_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted"})

# Mettre à jour l'activité d'un flux pour un jour donné
@weak_indicators_bp.route('/api/sdr-streams/<int:stream_id>/activity', methods=['POST'])
def update_sdr_stream_activity(stream_id):
    data = request.get_json(force=True)
    date_str = data.get('date')  # YYYY-MM-DD
    count = int(data.get('activity_count', 0))
    if not date_str:
        return jsonify({"error": "date (YYYY-MM-DD) requis"}), 400
    
    instance_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance')
    db_path = os.path.join(instance_dir, 'geopol.db')
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO sdr_daily_activity(stream_id, date, activity_count)
        VALUES (?, ?, ?)
        ON CONFLICT(stream_id, date) DO UPDATE SET activity_count = excluded.activity_count
    """, (stream_id, date_str, count))
    conn.commit()
    conn.close()
    return jsonify({"status": "updated"})

# Statistiques (moyenne quotidienne)
@weak_indicators_bp.route('/api/sdr-streams/<int:stream_id>/stats')
def sdr_stream_stats(stream_id):
    instance_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance')
    db_path = os.path.join(instance_dir, 'geopol.db')
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT AVG(activity_count) FROM sdr_daily_activity WHERE stream_id = ?", (stream_id,))
    avg = cur.fetchone()[0] or 0
    cur.execute("""
        SELECT date, activity_count FROM sdr_daily_activity
        WHERE stream_id = ?
        ORDER BY date DESC LIMIT 7
    """, (stream_id,))
    rows = cur.fetchall()
    series = [{"date": r[0], "activity_count": r[1]} for r in rows]
    conn.close()
    return jsonify({
        "stream_id": stream_id,
        "daily_average": round(avg, 2),
        "last_7_days": series
    })

# Données économiques (VIX) via yfinance - VERSION CORRIGÉE
@weak_indicators_bp.route('/api/economic-data/<country>/<indicator>')
def get_economic_data(country, indicator):
    period_map = {
        "1mo": "1mo",
        "3mo": "3mo", 
        "1y": "1y",
        "5y": "5y"
    }
    period = request.args.get("period", "1mo")
    
    # Mapper indicateurs courts
    symbol_map = {
        ("US", "VIX"): "^VIX",
        ("US", "GDP"): "SPY",      # Utiliser SPY comme proxy du PIB US
        ("US", "INFLATION"): "CPIAUCSL",
        ("US", "UNEMPLOYMENT"): "UNRATE",
        ("US", "TRADE_BALANCE"): "BOPGSTB"
    }
    symbol = symbol_map.get((country.upper(), indicator.upper()))
    if not symbol:
        return jsonify({"error": f"Indicateur non supporté: {country}/{indicator}"}), 400

    try:
        print(f"📊 Tentative de récupération VIX: {symbol} pour {period}")
        
        # Tentative avec yfinance
        import yfinance as yf
        
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period_map.get(period, "1mo"), interval="1d")
        
        if hist is None or hist.empty:
            print("⚠️ Aucune donnée reçue de yfinance")
            return _mock_economic_data(country, indicator)

        # Nettoyer les données et créer le résultat
        data = []
        for ts, row in hist.iterrows():
            close_value = row.get("Close")
            if close_value is not None and str(close_value) != "nan" and close_value != "":
                try:
                    value = float(close_value)
                    data.append({"date": ts.strftime("%Y-%m-%d"), "value": value})
                except (ValueError, TypeError):
                    continue

        if not data:
            print("⚠️ Données VIX vides après nettoyage")
            return _mock_economic_data(country, indicator)

        current = float(hist["Close"].iloc[-1]) if len(hist) > 0 else None
        # tendance naïve
        trend = "up" if len(hist) >= 2 and hist["Close"].iloc[-1] > hist["Close"].iloc[-2] else "down"
        
        print(f"✅ Données VIX reçues: {len(data)} points, valeur actuelle: {current}")
        
        return jsonify({
            "country": country,
            "indicator": indicator,
            "period": period,
            "data": data,
            "current": current,
            "trend": trend
        })
        
    except ImportError:
        print("❌ yfinance non installé")
        return _mock_economic_data(country, indicator)
    except Exception as e:
        print(f"❌ Erreur yfinance: {str(e)}")
        return _mock_economic_data(country, indicator)

def _mock_economic_data(country, indicator):
    """Retourne des données simulées en cas d'erreur yfinance"""
    import random
    from datetime import datetime, timedelta
    
    print(f"🟡 Utilisation de données simulées pour {indicator}")
    
    # Générer des données simulées réalistes pour VIX
    base_value = 20.0 if indicator.upper() == 'VIX' else 100.0
    data = []
    today = datetime.utcnow()
    
    for i in range(30):  # 30 jours
        date = today - timedelta(days=i)
        # Le VIX varie normalement entre 10 et 80
        value = base_value + random.uniform(-10, 10)
        if indicator.upper() == 'VIX':
            value = max(10, min(80, value))  # Limiter VIX entre 10 et 80
        
        data.append({
            "date": date.strftime("%Y-%m-%d"),
            "value": round(value, 2)
        })
    
    data.reverse()  # Du plus ancien au plus récent
    
    current = data[-1]["value"] if data else base_value
    trend = "up" if len(data) >= 2 and data[-1]["value"] > data[-2]["value"] else "down"
    
    return jsonify({
        "country": country,
        "period": request.args.get("period", "1mo"),
        "data": data,
        "current": current,
        "trend": trend,
        "mock": True  # Flag pour indiquer que c'est simulé
    })

# Collecteur SDR pour mise à jour automatique des activités
@weak_indicators_bp.route('/api/sdr-collect', methods=['POST'])
def collect_sdr_activity():
    instance_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance')
    db_path = os.path.join(instance_dir, 'geopol.db')
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT id, url, frequency_khz FROM sdr_streams")
    rows = cur.fetchall()
    today = datetime.utcnow().date().strftime("%Y-%m-%d")
    
    for (sid, url, freq) in rows:
        # TODO: ici faites l'appel serveur→WebSDR waterfall/spectrum
        # et comptez l'activité (nb de pics > seuil sur N secondes).
        # Pour l'exemple: nombre aléatoire
        activity = random.randint(0, 12)
        cur.execute("""
            INSERT INTO sdr_daily_activity(stream_id, date, activity_count)
            VALUES (?, ?, ?)
            ON CONFLICT(stream_id, date) DO UPDATE SET activity_count = excluded.activity_count
        """, (sid, today, activity))
    conn.commit()
    conn.close()
    return jsonify({"status": "collected"})
