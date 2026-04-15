# api/football_data.py

import requests
from config import FOOTBALL_DATA_KEY

BASE_URL = "https://api.football-data.org/v4"
HEADERS  = {"X-Auth-Token": FOOTBALL_DATA_KEY}


def fetch_football_matches(league: str = "PL", status: str = "SCHEDULED") -> dict:
    """
    Retourne les matchs d'une compétition.

    Paramètres :
      - league : code compétition (PL = Premier League, FL1, BL1, SA, PD...)
      - status : SCHEDULED | LIVE | IN_PLAY | FINISHED

    Retourne un dict {"matches": [...]} au format football-data.org :
      - homeTeam  : {"name": str}
      - awayTeam  : {"name": str}
      - utcDate   : str (ISO 8601)
      - status    : str
    """
    try:
        resp = requests.get(
            f"{BASE_URL}/competitions/{league}/matches",
            headers=HEADERS,
            params={"status": status},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()          # {"matches": [...], "competition": {...}, ...}

    except Exception as e:
        print(f"[football_data] fetch_football_matches erreur : {e}")
        return {"matches": []}
