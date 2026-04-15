# api/tennis_api.py

import requests
from config import TENNIS_API_KEY

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE_URL = "https://tennis-live-data.p.rapidapi.com"
HEADERS  = {
    "X-RapidAPI-Key":  TENNIS_API_KEY,
    "X-RapidAPI-Host": "tennis-live-data.p.rapidapi.com",
}


# ---------------------------------------------------------------------------
# Matchs en direct
# ---------------------------------------------------------------------------

def fetch_tennis_matches() -> list[dict]:
    """
    Retourne la liste des matchs de tennis en direct.

    Chaque dict contient :
      - player1     (str)
      - player2     (str)
      - tournament  (str)
      - status      (str)
      - date        (str, ISO)
    """
    try:
        resp = requests.get(
            f"{BASE_URL}/matches/today",
            headers=HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        matches = []
        for m in data.get("results", []):
            if m.get("status") not in ("live", "in_progress", "LIVE"):
                continue
            matches.append({
                "player1":    m.get("home_team", m.get("player1", "Joueur 1")),
                "player2":    m.get("away_team", m.get("player2", "Joueur 2")),
                "tournament": m.get("tournament", m.get("league", "Tournoi inconnu")),
                "status":     m.get("score",  m.get("status", "")),
                "date":       m.get("date",   ""),
            })
        return matches

    except Exception as e:
        print(f"[tennis_api] fetch_tennis_matches erreur : {e}")
        return []


# ---------------------------------------------------------------------------
# Matchs programmés aujourd'hui
# ---------------------------------------------------------------------------

def fetch_tennis_matches_scheduled() -> list[dict]:
    """
    Retourne la liste des matchs de tennis programmés aujourd'hui.

    Même structure que fetch_tennis_matches().
    """
    try:
        resp = requests.get(
            f"{BASE_URL}/matches/today",
            headers=HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        matches = []
        for m in data.get("results", []):
            matches.append({
                "player1":    m.get("home_team", m.get("player1", "Joueur 1")),
                "player2":    m.get("away_team", m.get("player2", "Joueur 2")),
                "tournament": m.get("tournament", m.get("league", "Tournoi inconnu")),
                "status":     m.get("status", "Programmé"),
                "date":       m.get("date", ""),
            })
        return matches

    except Exception as e:
        print(f"[tennis_api] fetch_tennis_matches_scheduled erreur : {e}")
        return []


# ---------------------------------------------------------------------------
# UTR d'un joueur
# ---------------------------------------------------------------------------

# Données locales de secours (même base que tennis_analysis.py)
_UTR_FALLBACK = {
    "novak djokovic": 16.5,
    "djokovic":       16.5,
    "rafael nadal":   16.0,
    "nadal":          16.0,
    "roger federer":  15.8,
    "federer":        15.8,
    "carlos alcaraz": 15.5,
    "alcaraz":        15.5,
    "jannik sinner":  15.3,
    "sinner":         15.3,
    "daniil medvedev":15.0,
    "medvedev":       15.0,
    "alexander zverev":14.8,
    "zverev":         14.8,
    "stefanos tsitsipas":14.5,
    "tsitsipas":      14.5,
}


def fetch_player_utr(player_name: str) -> float:
    """
    Retourne le score UTR d'un joueur.
    Tente d'abord l'API ; repli sur la base locale si indisponible.
    """
    try:
        resp = requests.get(
            f"{BASE_URL}/player",
            headers=HEADERS,
            params={"name": player_name},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        utr = data.get("results", {}).get("utr")
        if utr is not None:
            return float(utr)
    except Exception as e:
        print(f"[tennis_api] fetch_player_utr({player_name}) erreur : {e}")

    # Repli local
    key = player_name.lower()
    for k, v in _UTR_FALLBACK.items():
        if key in k or k in key:
            return v
    return 10.0   # valeur par défaut joueur inconnu


# ---------------------------------------------------------------------------
# Classement ATP
# ---------------------------------------------------------------------------

def fetch_atp_rankings() -> list[dict]:
    """
    Retourne le classement ATP.

    Chaque dict contient :
      - rank    (int)
      - player  (str)
      - points  (int)
    """
    try:
        resp = requests.get(
            f"{BASE_URL}/rankings/atp",
            headers=HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        rankings = []
        for entry in data.get("results", []):
            rankings.append({
                "rank":   entry.get("ranking", entry.get("rank", 0)),
                "player": entry.get("player",  entry.get("name",  "Inconnu")),
                "points": entry.get("points",  0),
            })
        return rankings

    except Exception as e:
        print(f"[tennis_api] fetch_atp_rankings erreur : {e}")
        # Repli statique top 5 pour ne pas planter le bot
        return [
            {"rank": 1, "player": "Jannik Sinner",    "points": 11830},
            {"rank": 2, "player": "Carlos Alcaraz",   "points": 9255},
            {"rank": 3, "player": "Novak Djokovic",   "points": 8685},
            {"rank": 4, "player": "Alexander Zverev", "points": 6885},
            {"rank": 5, "player": "Daniil Medvedev",  "points": 6685},
        ]
