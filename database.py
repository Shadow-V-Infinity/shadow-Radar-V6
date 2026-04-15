# database.py

import sqlite3
from contextlib import contextmanager

DB_PATH = "sports_bot.db"


# ---------------------------------------------------------------------------
# Utilitaire de connexion
# ---------------------------------------------------------------------------

@contextmanager
def get_connection():
    """Context manager : ouvre une connexion et la ferme automatiquement."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # accès aux colonnes par nom
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

def init_db():
    """Crée toutes les tables si elles n'existent pas encore."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Matchs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                id       INTEGER PRIMARY KEY,
                api_id   INTEGER UNIQUE,
                home_team TEXT,
                away_team TEXT,
                sport    TEXT,
                league   TEXT,
                date     TEXT,
                status   TEXT
            )
        """)

        # Cotes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS odds (
                id           INTEGER PRIMARY KEY,
                match_id     INTEGER,
                bookmaker    TEXT,
                source       TEXT,
                outcome_type TEXT,
                outcome_name TEXT,
                price        REAL,
                timestamp    DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (match_id) REFERENCES matches (id)
            )
        """)

        # Alertes utilisateurs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_alerts (
                id                INTEGER PRIMARY KEY,
                chat_id           INTEGER UNIQUE,
                football_alerts   BOOLEAN DEFAULT FALSE,
                tennis_alerts     BOOLEAN DEFAULT FALSE,
                basket_alerts     BOOLEAN DEFAULT FALSE,
                min_odd_variation REAL DEFAULT 5.0
            )
        """)

        # Météo
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weather (
                id          INTEGER PRIMARY KEY,
                match_id    INTEGER,
                city        TEXT,
                date        TEXT,
                temperature REAL,
                humidity    REAL,
                wind_speed  REAL,
                conditions  TEXT,
                timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (match_id) REFERENCES matches (id)
            )
        """)

    print("✅ Base de données initialisée.")


# ---------------------------------------------------------------------------
# Matchs
# ---------------------------------------------------------------------------

def save_match(match_data: dict, sport: str):
    """Insère un match en base (ignoré si déjà présent via api_id)."""
    with get_connection() as conn:
        conn.execute("""
            INSERT OR IGNORE INTO matches
                (api_id, home_team, away_team, sport, league, date, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            match_data.get("id"),
            match_data.get("home_team") or match_data.get("home") or match_data.get("player1"),
            match_data.get("away_team") or match_data.get("away") or match_data.get("player2"),
            sport,
            match_data.get("league") or match_data.get("tournament"),
            match_data.get("date"),
            match_data.get("status"),
        ))


# ---------------------------------------------------------------------------
# Cotes
# ---------------------------------------------------------------------------

def save_odds(odds_data: list, source: str):
    """Insère une liste de cotes en base."""
    if not odds_data:
        return

    with get_connection() as conn:
        cursor = conn.cursor()
        for entry in odds_data:
            match_id = _get_match_id(cursor, entry.get("id"))
            if match_id is None:
                continue
            for bookmaker in entry.get("bookmakers", []):
                for market in bookmaker.get("markets", []):
                    for outcome in market.get("outcomes", []):
                        cursor.execute("""
                            INSERT INTO odds
                                (match_id, bookmaker, source, outcome_type, outcome_name, price)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            match_id,
                            bookmaker.get("key"),
                            source,
                            market.get("key"),
                            outcome.get("name"),
                            outcome.get("price"),
                        ))


# ---------------------------------------------------------------------------
# Météo
# ---------------------------------------------------------------------------

def save_weather(match_id: int, weather_data: dict):
    """Insère les données météo d'un match en base."""
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO weather
                (match_id, city, date, temperature, humidity, wind_speed, conditions)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            match_id,
            weather_data.get("city", "Paris"),
            weather_data["date"],
            weather_data["temperature"],
            weather_data["humidity"],
            weather_data["wind_speed"],
            weather_data["conditions"],
        ))


def _get_match_id(cursor: sqlite3.Cursor, api_id) -> int | None:
    """Retourne l'id interne d'un match à partir de son api_id."""
    row = cursor.execute(
        "SELECT id FROM matches WHERE api_id = ?", (api_id,)
    ).fetchone()
    return row["id"] if row else None
