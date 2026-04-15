import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# api/odds.py

import requests
from config import ODDS_API_KEY, ODDS_API_IO_KEY
from database import save_odds   # réexporté pour que main.py puisse l'importer d'ici


# ---------------------------------------------------------------------------
# The Odds API  (odds-api.com)
# ---------------------------------------------------------------------------

ODDS_API_BASE = "https://api.the-odds-api.com/v4"

def fetch_odds(sport: str = "soccer_epl", league: str = "English Premier League") -> list:
    """
    Récupère les cotes depuis The Odds API.

    Paramètres :
      - sport  : clé sport (soccer_epl, soccer_ligue_1, tennis_atp...)
      - league : label lisible (utilisé en log uniquement)

    Retourne une liste de matchs au format odds-api :
      [{"id": ..., "bookmakers": [{"key": ..., "markets": [...]}], ...}]
    """
    try:
        resp = requests.get(
            f"{ODDS_API_BASE}/sports/{sport}/odds",
            params={
                "apiKey":  ODDS_API_KEY,
                "regions": "eu",
                "markets": "h2h",
                "oddsFormat": "decimal",
            },
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[odds] fetch_odds({league}) erreur : {e}")
        return []


# ---------------------------------------------------------------------------
# OddsAPI.io  (oddsapi.io)
# ---------------------------------------------------------------------------

ODDS_IO_BASE = "https://api.oddsapi.io/v4"

def fetch_odds_io(sport: str = "tennis", league: str = "ATP") -> list:
    """
    Récupère les cotes depuis OddsAPI.io.

    Retourne la même structure que fetch_odds() pour que save_odds()
    puisse traiter les deux sources de façon identique.
    """
    try:
        resp = requests.get(
            f"{ODDS_IO_BASE}/odds",
            params={
                "api_key": ODDS_API_IO_KEY,
                "sport":   sport,
                "league":  league,
                "format":  "decimal",
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        # Normalise vers le même format que The Odds API
        return data if isinstance(data, list) else data.get("data", [])
    except Exception as e:
        print(f"[odds] fetch_odds_io({league}) erreur : {e}")
        return []
