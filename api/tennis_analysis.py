# api/tennis_analysis.py

from api.weather_api import get_weather_condition, fetch_weather


# ---------------------------------------------------------------------------
# Profils joueurs (extensible)
# ---------------------------------------------------------------------------

PLAYER_PROFILES = {
    "Djokovic":           {"profil": "🎯 solide",   "age": 36},
    "Novak Djokovic":     {"profil": "🎯 solide",   "age": 36},
    "Nadal":              {"profil": "🔥 clutch",   "age": 37},
    "Rafael Nadal":       {"profil": "🔥 clutch",   "age": 37},
    "Federer":            {"profil": "🎯 solide",   "age": 42},
    "Roger Federer":      {"profil": "🎯 solide",   "age": 42},
    "Alcaraz":            {"profil": "🔥 clutch",   "age": 21},
    "Carlos Alcaraz":     {"profil": "🔥 clutch",   "age": 21},
    "Sinner":             {"profil": "🎯 solide",   "age": 22},
    "Jannik Sinner":      {"profil": "🎯 solide",   "age": 22},
    "Medvedev":           {"profil": "🧊 pressure", "age": 28},
    "Daniil Medvedev":    {"profil": "🧊 pressure", "age": 28},
    "Zverev":             {"profil": "🧊 pressure", "age": 27},
    "Alexander Zverev":   {"profil": "🧊 pressure", "age": 27},
    "Tsitsipas":          {"profil": "🔥 clutch",   "age": 25},
    "Stefanos Tsitsipas": {"profil": "🔥 clutch",   "age": 25},
}

DEFAULT_PROFILE = {"profil": "🎯 solide", "age": 25}


def _get_player_profile(name: str) -> dict:
    """Retourne le profil d'un joueur, avec fallback insensible à la casse."""
    if name in PLAYER_PROFILES:
        return PLAYER_PROFILES[name]
    name_lower = name.lower()
    for key, val in PLAYER_PROFILES.items():
        if name_lower in key.lower() or key.lower() in name_lower:
            return val
    return DEFAULT_PROFILE


# ---------------------------------------------------------------------------
# Données joueurs UTR
# ---------------------------------------------------------------------------

UTR_DATA = {
    "Novak Djokovic":     16.5,
    "Djokovic":           16.5,
    "Rafael Nadal":       16.0,
    "Nadal":              16.0,
    "Roger Federer":      15.8,
    "Federer":            15.8,
    "Carlos Alcaraz":     15.5,
    "Alcaraz":            15.5,
    "Jannik Sinner":      15.3,
    "Sinner":             15.3,
    "Daniil Medvedev":    15.0,
    "Medvedev":           15.0,
    "Alexander Zverev":   14.8,
    "Zverev":             14.8,
    "Stefanos Tsitsipas": 14.5,
    "Tsitsipas":          14.5,
}


# ---------------------------------------------------------------------------
# Helpers internes
# ---------------------------------------------------------------------------

def _score_forme(forme: str) -> float:
    """Convertit une séquence de résultats (ex: 'WWLLW') en score 0-1."""
    if not forme:
        return 0.5
    wins = forme.upper().count("W")
    return wins / len(forme)


def _proba_from_elo(elo_a: float, elo_b: float) -> tuple[float, float]:
    """Calcule les probabilités de victoire à partir des scores ELO."""
    diff = elo_a - elo_b
    proba_a = 1 / (1 + 10 ** (-diff / 400))
    return proba_a, 1 - proba_a


def _edge(proba: float, cote: float) -> float:
    """Edge simple : probabilité estimée moins probabilité implicite bookmaker."""
    return proba - (1 / cote)


# ---------------------------------------------------------------------------
# Ajustement météo avancé
# ---------------------------------------------------------------------------

def ajustement_meteo_avance(weather_data: dict, profil: str, age: int = 25) -> float:
    """
    Calcule un multiplicateur de probabilité selon la météo et le profil joueur.

    Profils reconnus :
      - '🧊 pressure' : joueurs qui craquent sous pression / conditions difficiles
      - '🎯 solide'   : joueurs réguliers, résistants
      - '🔥 clutch'   : joueurs qui brillent dans les moments clés

    weather_data doit contenir :
      - wind_speed   (km/h)
      - humidity     (%)
      - temperature  (°C)
    """
    ajustement = 1.0

    wind_speed  = weather_data.get("wind_speed", 0)
    humidity    = weather_data.get("humidity", 50)
    temperature = weather_data.get("temperature", 20)

    # Vent fort (> 15 km/h)
    if wind_speed > 15:
        if profil == "🧊 pressure":
            ajustement *= 0.95   # Joueurs "pressure" pénalisés par le vent
        elif profil == "🎯 solide":
            ajustement *= 1.03   # Joueurs solides avantagés
        elif profil == "🔥 clutch":
            ajustement *= 1.01   # Léger avantage clutch

    # Humidité élevée (> 70%)
    if humidity > 70:
        ajustement *= 1.02 if profil == "🔥 clutch" else 0.98

    # Chaleur extrême (> 30°C)
    if temperature > 30:
        ajustement *= 0.97 if age > 30 else 1.0   # Pénalité pour les joueurs âgés

    return ajustement


# ---------------------------------------------------------------------------
# Fonction principale d'analyse
# ---------------------------------------------------------------------------

def calcul_match_telegram(
    utr_a: float,
    utr_b: float,
    elo_a: float,
    elo_b: float,
    cote_a: float,
    cote_b: float,
    sets: int,
    surface: str,
    forme_a: str = "WWWWW",
    forme_b: str = "WWWWW",
    classement_a: int = 50,
    classement_b: int = 50,
    repos_a: int = 3,
    repos_b: int = 3,
    h2h_a: int = 0,
    service_won_a: float = 65.0,
    service_won_b: float = 65.0,
    type_tournoi: str = "ATP 250",
    # Nouveau : données match pour météo
    match_data: dict = None,
    # Noms joueurs pour récupérer profil
    nom_a: str = "",
    nom_b: str = "",
) -> str:
    """
    Analyse un match de tennis et retourne un message formaté pour Telegram.

    match_data (optionnel) : dict avec 'tournament', 'date', 'surface'
    nom_a / nom_b          : noms des joueurs pour récupérer profil et âge
    """

    # --- Profils joueurs ---
    profil_data_a = _get_player_profile(nom_a)
    profil_data_b = _get_player_profile(nom_b)
    profil_a = profil_data_a["profil"]
    profil_b = profil_data_b["profil"]
    age_a    = profil_data_a["age"]
    age_b    = profil_data_b["age"]

    # --- Météo ---
    weather_data = {}
    meteo_label  = "Inconnue"
    if match_data:
        try:
            meteo_label  = get_weather_condition(match_data)
            # fetch_weather pour avoir wind_speed, humidity, temperature
            tournament_locations = {
                "Roland-Garros":    "Paris",
                "Wimbledon":        "Londres",
                "US Open":          "New York",
                "Australian Open":  "Melbourne",
            }
            city = tournament_locations.get(
                match_data.get("tournament", ""), "Paris"
            )
            date_str    = match_data.get("date", "")[:10]
            weather_raw = fetch_weather(city, date_str)
            weather_data = {
                "wind_speed":  weather_raw.get("wind_speed", 0),
                "humidity":    weather_raw.get("humidity", 50),
                "temperature": weather_raw.get("temperature", 20),
            }
        except Exception as ex:
            print(f"[tennis_analysis] Erreur météo : {ex}")
            meteo_label  = "Inconnue"
            weather_data = {"wind_speed": 0, "humidity": 50, "temperature": 20}

    # --- Probabilités de base (ELO) ---
    proba_elo_a, proba_elo_b = _proba_from_elo(elo_a, elo_b)

    # --- Ajustements forme / UTR / service / repos / H2H ---
    forme_score_a  = _score_forme(forme_a)
    forme_score_b  = _score_forme(forme_b)
    utr_diff       = (utr_a - utr_b) / 20
    service_diff   = (service_won_a - service_won_b) / 100
    repos_diff     = (repos_b - repos_a) / 10
    h2h_factor     = h2h_a * 0.01

    ajustement_a = (
        (forme_score_a - forme_score_b) * 0.10
        + utr_diff        * 0.10
        + service_diff    * 0.05
        + repos_diff      * 0.03
        + h2h_factor
    )

    proba_a = max(0.05, min(0.95, proba_elo_a + ajustement_a))
    proba_b = 1 - proba_a

    # --- Ajustement météo avancé ---
    if weather_data:
        fact_a  = ajustement_meteo_avance(weather_data, profil_a, age_a)
        fact_b  = ajustement_meteo_avance(weather_data, profil_b, age_b)
        # Renormalisation pour que proba_a + proba_b = 1
        raw_a   = proba_a * fact_a
        raw_b   = proba_b * fact_b
        total   = raw_a + raw_b
        proba_a = max(0.05, min(0.95, raw_a / total))
        proba_b = 1 - proba_a

    # --- Edge ---
    edge_a = _edge(proba_a, cote_a)
    edge_b = _edge(proba_b, cote_b)

    # --- Volatilité ---
    diff_niveau = abs(elo_a - elo_b)
    if diff_niveau > 200:
        volatility = "Faible 🟢"
    elif diff_niveau > 100:
        volatility = "Moyenne 🟡"
    else:
        volatility = "Élevée 🔴"

    # --- Zone de jeux estimée ---
    avg_service = (service_won_a + service_won_b) / 2
    line  = round(avg_service / 10 + (sets * 3.5), 1)
    low   = round(line - 2.5, 1)
    high  = round(line + 2.5, 1)

    # --- Recommandation de pari ---
    EDGE_SEUIL = 0.05
    MISE_BASE  = 2.0

    if edge_a >= EDGE_SEUIL:
        bet_type  = "value bet"
        bet_side  = f"Joueur A ({nom_a or 'A'})"
        stake     = MISE_BASE + edge_a * 10
    elif edge_b >= EDGE_SEUIL:
        bet_type  = "value bet"
        bet_side  = f"Joueur B ({nom_b or 'B'})"
        stake     = MISE_BASE + edge_b * 10
    else:
        bet_type  = "none"
        bet_side  = ""
        stake     = 0.0

    # --- Météo résumé ---
    wind_str  = f"{weather_data.get('wind_speed', '?')} km/h"
    hum_str   = f"{weather_data.get('humidity', '?')}%"
    temp_str  = f"{weather_data.get('temperature', '?')}°C"

    # --- Message Telegram ---
    label_a = nom_a or "Joueur A"
    label_b = nom_b or "Joueur B"

    message = (
        f"🎾 *Analyse Match* ({'BO5' if sets == 5 else 'BO3'}) | {surface} | {type_tournoi}\n\n"
        f"🌡️ Météo : {meteo_label} | 💨 {wind_str} | 💧 {hum_str} | 🌡 {temp_str}\n"
        f"🏆 Classement : {label_a}={classement_a} | {label_b}={classement_b}\n"
        f"🔥 UTR : {label_a}={utr_a} | {label_b}={utr_b}\n"
        f"🎭 Profil : {label_a}={profil_a} | {label_b}={profil_b}\n"
        f"📊 ELO : {label_a}={elo_a} | {label_b}={elo_b}\n"
        f"💰 Cotes : {label_a}={cote_a} | {label_b}={cote_b}\n\n"
        f"📈 *Probas* : {label_a}={proba_a * 100:.1f}% | {label_b}={proba_b * 100:.1f}%\n"
        f"🎯 *Edge* : {label_a}={edge_a:.2%} | {label_b}={edge_b:.2%}\n"
        f"📊 *Volatilité* : {volatility}\n"
        f"🎯 *Zone de jeux* : {low}-{high} jeux | Ligne marché : {line}\n\n"
    )

    if bet_type != "none":
        message += f"💰 *Stratégie* : {bet_type} {bet_side} | Mise : {stake:.1f}%\n"
    else:
        message += "🚫 *Pas de pari recommandé*\n"

    return message
