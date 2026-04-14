# api/odds_api.py
import requests
from config import ODDS_API_KEY

def fetch_odds(sport, league):
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "eu",
        "markets": "h2h",
        "bookmakers": "bet365,winamax"
    }
    response = requests.get(url, params=params)
    return response.json()
