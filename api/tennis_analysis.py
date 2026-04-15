# api/tennis_analysis.py

from api.weather_api import get_weather_condition, fetch_weather


# ---------------------------------------------------------------------------
# Profils joueurs
# ---------------------------------------------------------------------------

# Clés en minuscules pour simplifier la recherche insensible à la casse
_PLAYER_PROFILES: dict[str, dict] = {
    "djokovic":  {"profil": "🎯 solide",   "age": 36},
    "nadal":     {"profil": "🔥 clutch",   "age": 37},
    "federer":   {"profil": "🎯 solide",   "age": 42},
    "alcaraz":   {"profil": "🔥 clutch",   "age": 21},
    "sinner":    {"profil": "🎯 solide",   "age": 22},
    "medvedev":  {"profil": "🧊 pressure", "age": 28},
    "zverev":    {"profil": "🧊 pressure", "age": 27},
    "tsitsipas": {"profil": "🔥 clutch",   "age": 25},
}

_DEFAULT_PROFILE = {"profil": "🎯 solide", "age": 25}

# Correspondance tournoi → ville pour la météo
_TOURNAMENT_CITIES: dict[str, str] = {
    "Roland-Garros":   "Paris",
    "Wimbledon":       "Londres",
    "US Open":         "New York",
    "Australian Open": "Melbourne",
}


def _get_player_profile(name: str) -> dict:
    """Retourne le profil d'un joueur, insensible à la casse et aux noms partiels."""
    name_lower = name.lower()
    for key, val in _PLAYER_PROFILES.items():
        if key in name_lower or name_lower in key:
            return val
    return _DEFAULT_PROFILE


# ---------------------------------------------------------------------------
# Helpers calcul
# ---------------------------------------------------------------------------

def _score_forme(forme: str) -> float:
    """Convertit 'WWLLW' en score 0-1."""
    if not forme:
        return 0.5
    return forme.upper().count("W") / len(forme)


def _proba_from_elo(elo_a: float, elo_b: float) -> tuple[float, float]:
    """Probabilités de victoire par formule ELO standard."""
    proba_a = 1 / (1 + 10 ** (-(elo_a - elo_b) / 400))
    return proba_a, 1 - proba_a


def _edge(proba: float, cote: float) -> float:
    """Edge = proba estimée − proba implicite bookmaker."""
    return proba - (1 / cote)


def _clamp(value: float, low: float = 0.05, high: float = 0.95) -> float:
    return max(low, min(high, value))


# ---------------------------------------------------------------------------
# Ajustement météo
# ---------------------------------------------------------------------------

def ajustement_meteo_avance(weather_data: dict, profil: str, age: int = 25) -> float:
    """
    Multiplicateur de probabilité selon météo et profil joueur.

    Profils :
      '🧊 pressure' : pénalisé par conditions difficiles
      '🎯 solide'   : régulier, résistant
      '🔥 clutch'   : brille dans les moments difficiles
    """
    ajustement  = 1.0
    wind_speed  = weather_data.get("wind_speed", 0)
    humidity    = weather_data.get("humidity", 50)
    temperature = weather_data.get("temperature", 20)

    if wind_speed > 15:
        factors = {"🧊 pressure": 0.95, "🎯 solide": 1.03, "🔥 clutch": 1.01}
        ajustement *= factors.get(profil, 1.0)

    if humidity > 70:
        ajustement *= 1.02 if profil == "🔥 clutch" else 0.98

    if temperature > 30 and age > 30:
        ajustement *= 0.97

    return ajustement


# ---------------------------------------------------------------------------
# Fonction principale
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
    match_data: dict | None = None,
    nom_a: str = "",
    nom_b: str = "",
) -> str:
    """
    Analyse un match de tennis et retourne un message formaté pour Telegram.

    Paramètres optionnels
    ---------------------
    match_data : dict avec 'tournament', 'date', 'surface' pour la météo
    nom_a / nom_b : noms des joueurs pour profil et âge
    """

    label_a = nom_a or "Joueur A"
    label_b = nom_b or "Joueur B"

    # --- Profils joueurs ---
    profil_data_a = _get_player_profile(nom_a)
    profil_data_b = _get_player_profile(nom_b)
    profil_a = profil_data_a["profil"]
    profil_b = profil_data_b["profil"]
    age_a    = profil_data_a["age"]
    age_b    = profil_data_b["age"]

    # --- Météo ---
    weather_data: dict = {}
    meteo_label        = "Inconnue"

    if match_data:
        try:
            meteo_label  = get_weather_condition(match_data)
            city         = _TOURNAMENT_CITIES.get(match_data.get("tournament", ""), "Paris")
            date_str     = match_data.get("date", "")[:10]
            weather_raw  = fetch_weather(city, date_str)
            weather_data = {
                "wind_speed":  weather_raw.get("wind_speed", 0),
                "humidity":    weather_raw.get("humidity", 50),
                "temperature": weather_raw.get("temperature", 20),
            }
        except Exception as ex:
            print(f"[tennis_analysis] Erreur météo : {ex}")
            weather_data = {"wind_speed": 0, "humidity": 50, "temperature": 20}

    # --- Probabilités ELO ---
    proba_elo_a, _ = _proba_from_elo(elo_a, elo_b)

    # --- Ajustements forme / UTR / service / repos / H2H ---
    ajustement_a = (
        (_score_forme(forme_a) - _score_forme(forme_b)) * 0.10
        + ((utr_a - utr_b) / 20)                        * 0.10
        + ((service_won_a - service_won_b) / 100)        * 0.05
        + ((repos_b - repos_a) / 10)                    * 0.03
        + h2h_a * 0.01
    )

    proba_a = _clamp(proba_elo_a + ajustement_a)
    proba_b = 1 - proba_a

    # --- Ajustement météo ---
    if weather_data:
        raw_a   = proba_a * ajustement_meteo_avance(weather_data, profil_a, age_a)
        raw_b   = proba_b * ajustement_meteo_avance(weather_data, profil_b, age_b)
        total   = raw_a + raw_b or 1
        proba_a = _clamp(raw_a / total)
        proba_b = 1 - proba_a

    # --- Edge ---
    edge_a = _edge(proba_a, cote_a)
    edge_b = _edge(proba_b, cote_b)

    # --- Volatilité ---
    diff_niveau = abs(elo_a - elo_b)
    volatility  = (
        "Faible 🟢"  if diff_niveau > 200 else
        "Moyenne 🟡" if diff_niveau > 100 else
        "Élevée 🔴"
    )

    # --- Zone de jeux ---
    avg_service = (service_won_a + service_won_b) / 2
    line        = round(avg_service / 10 + sets * 3.5, 1)
    low         = round(line - 2.5, 1)
    high        = round(line + 2.5, 1)

    # --- Recommandation ---
    EDGE_SEUIL = 0.05
    MISE_BASE  = 2.0

    if edge_a >= EDGE_SEUIL:
        bet_type = "value bet"
        bet_side = label_a
        stake    = MISE_BASE + edge_a * 10
    elif edge_b >= EDGE_SEUIL:
        bet_type = "value bet"
        bet_side = label_b
        stake    = MISE_BASE + edge_b * 10
    else:
        bet_type = "none"
        bet_side = ""
        stake    = 0.0

    # --- Message Telegram ---
    wind_str = f"{weather_data.get('wind_speed', '?')} km/h"
    hum_str  = f"{weather_data.get('humidity', '?')}%"
    temp_str = f"{weather_data.get('temperature', '?')}°C"

    message = (
        f"🎾 *Analyse Match* ({'BO5' if sets == 5 else 'BO3'}) | {surface} | {type_tournoi}\n\n"
        f"🌡️ Météo : {meteo_label} | 💨 {wind_str} | 💧 {hum_str} | 🌡 {temp_str}\n"
        f"🏆 Classement : {label_a}=#{classement_a} | {label_b}=#{classement_b}\n"
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
        message += f"💰 *Stratégie* : {bet_type} — {bet_side} | Mise : {stake:.1f}%\n"
    else:
        message += "🚫 *Pas de pari recommandé*\n"

    return message
