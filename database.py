# database.py
import sqlite3

def init_db():
    conn = sqlite3.connect("sports_bot.db")
    cursor = conn.cursor()

    # Table pour les matchs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS matches (
        id INTEGER PRIMARY KEY,
        api_id INTEGER UNIQUE,
        home_team TEXT,
        away_team TEXT,
        sport TEXT,
        league TEXT,
        date TEXT,
        status TEXT
    )
    """)

    # Table pour les cotes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS odds (
        id INTEGER PRIMARY KEY,
        match_id INTEGER,
        bookmaker TEXT,
        source TEXT,
        outcome_type TEXT,
        outcome_name TEXT,
        price REAL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (match_id) REFERENCES matches (id)
    )
    """)

    conn.commit()
    conn.close()

def save_match(match_data, sport):
    conn = sqlite3.connect("sports_bot.db")
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR IGNORE INTO matches (api_id, home_team, away_team, sport, league, date, status)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        match_data["id"],
        match_data.get("home_team", match_data.get("home", match_data.get("player1"))),
        match_data.get("away_team", match_data.get("away", match_data.get("player2"))),
        sport,
        match_data.get("league", match_data.get("tournament")),
        match_data["date"],
        match_data["status"]
    ))
    conn.commit()
    conn.close()

def init_db():
    conn = sqlite3.connect("sports_bot.db")
    cursor = conn.cursor()

    # ... (tables existantes)

    # Table pour les utilisateurs et leurs alertes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_alerts (
        id INTEGER PRIMARY KEY,
        chat_id INTEGER UNIQUE,
        football_alerts BOOLEAN DEFAULT FALSE,
        tennis_alerts BOOLEAN DEFAULT FALSE,
        basket_alerts BOOLEAN DEFAULT FALSE,
        min_odd_variation REAL DEFAULT 5.0  -- Seuil de variation pour les alertes (ex: 5%)
    )
    """)
    conn.commit()
    conn.close()
