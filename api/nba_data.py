import requests
import pandas as pd
from datetime import datetime, timedelta
from config import BALL_DONT_LIE_API_KEY, ESPN_HEADERS

def get_nba_schedule(date=None):
    """Récupère le calendrier NBA pour une date donnée (aujourd'hui par défaut)."""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    league_id = 0  # 0 = NBA
    # Note: ESPN API nécessite un cookie espn_s2 pour les requêtes authentifiées.
    # Pour simplifier, on utilise BallDontLie pour le calendrier aussi.
    url = f"https://www.balldontlie.io/api/v1/games?seasons[]=2025&start_date={date}&end_date={date}"
    headers = {"Authorization": f"{BALL_DONT_LIE_API_KEY}"}
    response = requests.get(url, headers=headers)
    return response.json()["data"]

def get_nba_stats(team_id, season=2025):
    """Récupère les stats d'une équipe pour la saison."""
    url = f"https://www.balldontlie.io/api/v1/season_averages?season={season}&team_ids[]={team_id}"
    headers = {"Authorization": f"{BALL_DONT_LIE_API_KEY}"}
    response = requests.get(url, headers=headers)
    return response.json()["data"]

def get_historical_data(n=100, season=2025):
    """Récupère n matchs historiques pour entraîner le modèle."""
    url = f"https://www.balldontlie.io/api/v1/games?seasons[]={season}&per_page={n}"
    headers = {"Authorization": f"{BALL_DONT_LIE_API_KEY}"}
    response = requests.get(url, headers=headers)
    games = response.json()["data"]

    data = []
    for game in games:
        if game["home_team_score"] is not None:  # Ignore les matchs non joués
            home_team = game["home_team"]
            away_team = game["away_team"]
            data.append({
                "home_off_rating": home_team.get("offensive_rating", 110),
                "away_def_rating": away_team.get("defensive_rating", 110),
                "home_pace": home_team.get("pace", 98),
                "away_pace": away_team.get("pace", 98),
                "home_last_5_win_pct": home_team.get("last_5_win_pct", 0.5),
                "away_last_5_win_pct": away_team.get("last_5_win_pct", 0.5),
                "home_rest_days": home_team.get("rest_days", 1),
                "away_rest_days": away_team.get("rest_days", 1),
                "home_injury_impact": -2 if "injuries" in home_team else 0,
                "is_home_game": 1,
                "point_diff": game["home_team_score"] - game["away_team_score"],
                "home_team_id": home_team["id"],
                "away_team_id": away_team["id"],
                "game_date": game["date"]
            })
    return pd.DataFrame(data)

def get_team_stats(team_id, season=2025):
    """Récupère les stats avancées d'une équipe."""
    url = f"https://www.balldontlie.io/api/v1/teams/{team_id}"
    headers = {"Authorization": f"{BALL_DONT_LIE_API_KEY}"}
    response = requests.get(url, headers=headers)
    team_data = response.json()

    # Récupère les stats de saison
    season_avg = get_nba_stats(team_id, season)
    if not season_avg:
        return None

    return {
        "offensive_rating": team_data.get("offensive_rating", 110),
        "defensive_rating": team_data.get("defensive_rating", 110),
        "pace": team_data.get("pace", 98),
        "last_5_win_pct": season_avg[0].get("win_pct", 0.5) if season_avg else 0.5,
        "rest_days": 1,  # À calculer en fonction du dernier match
        "injury_impact": 0  # À ajuster avec des données de blessures
    }
