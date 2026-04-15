# api/weather_api.py
import requests

def fetch_weather(city="Paris", date="2026-04-15"):
    """Récupère les données météo pour une ville et une date."""
    # Remplace par l'URL et les paramètres de TON API météo
    url = "https://ton-api-météo.com/data"
    params = {
        "city": city,
        "date": date,
        "api_key": "TA_CLÉ_API_MÉTÉO"  # À mettre dans config.py
    }
    response = requests.get(url, params=params)
    return response.json()

def get_weather_condition(match_data):
    """Détermine la condition météo pour un match (ex: Roland-Garros = Paris)."""
    # Exemple : Associer un tournoi à une ville
    tournament_locations = {
        "Roland-Garros": "Paris",
        "Wimbledon": "Londres",
        "US Open": "New York",
        "Australian Open": "Melbourne"
    }
    city = tournament_locations.get(match_data.get("tournament"), "Paris")
    weather = fetch_weather(city, match_data["date"].split("T")[0])  # Extraire la date
    return weather["conditions"]  # Retourne "soleil", "pluie", etc.
