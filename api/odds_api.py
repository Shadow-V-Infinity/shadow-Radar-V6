# api/odds_api.py

import requests
from config import ODDS_API_KEY

BASE_URL = "https://api.the-odds-api.com/v4"


def fetch_odds(sport: str, league: str, regions: str = "eu", markets: str = "h2h") -> list:
    """
    Récupère les cotes pour un sport et une ligue donnés.

    Paramètres
    ----------
    sport   : identifiant sport ex. 'soccer_epl'
    league  : nom lisible pour les logs ex. 'English Premier League'
    regions : régions bookmakers (défaut : 'eu')
    markets : type de marché (défaut : 'h2h')
    """
    url = f"{BASE_URL}/sports/{sport}/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": regions,
        "markets": markets,
        "bookmakers": "bet365,winamax",
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        print(f"✅ [{league}] {len(data)} matchs récupérés.")
        return data
    except requests.exceptions.HTTPError as e:
        print(f"❌ Erreur HTTP fetch_odds({league}) : {e}")
    except requests.exceptions.ConnectionError:
        print(f"❌ Connexion impossible pour fetch_odds({league}).")
    except requests.exceptions.Timeout:
        print(f"⏱️ Timeout fetch_odds({league}).")
    except Exception as e:
        print(f"❌ Erreur inattendue fetch_odds({league}) : {e}")

    return []
