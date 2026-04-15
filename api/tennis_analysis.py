# api/tennis_analysis.py

import requests


# ---------------------------------------------------------------------------
# Données joueurs
# ---------------------------------------------------------------------------

UTR_DATA = {
    "Novak Djokovic": 16.5,
    "Rafael Nadal": 16.0,
    "Roger Federer": 15.8,
    # Ajoute d'autres joueurs ici
}


def fetch_atp_rankings() -> list:
    """Récupère le classement ATP depuis un dataset public."""
    url = "https://raw.githubusercontent.com/JetBrains-Research/tennis_api/master/data/atp_rankings.json"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


def fetch_player_stats(player_name: str) -> dict:
    """Récupère les stats d'un joueur depuis une API externe (à adapter)."""
    url = f"https://api.tennis-data.org/players?name={player_name}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Erreur fetch_player_stats({player_name}) : {e}")
        return {}


def fetch_player_utr(player_name: str) -> float:
    """Retourne l'UTR d'un joueur (valeur par défaut : 12.0 si inconnu)."""
    return UTR_DATA.get(player_name, 12.0)


# ---------------------------------------------------------------------------
# Calcul et analyse d'un match
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
    """Calcule l'edge (avantage) d'un pari : proba implicite vs proba estimée."""
    return proba - (1 / cote)


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
    meteo: str = "soleil",
    service_won_a: float = 65.0,
    service_won_b: float = 65.0,
    type_tournoi: str = "ATP 250",
) -> str:
    """
    Analyse un match de tennis et retourne un message formaté pour Telegram.

    Paramètres
    ----------
    utr_a / utr_b       : UTR des joueurs
    elo_a / elo_b       : scores ELO
    cote_a / cote_b     : cotes bookmaker
    sets                : 3 (BO3) ou 5 (BO5)
    surface             : terre / gazon / dur / indoor
    forme_a / forme_b   : 5 derniers résultats ex. 'WWLLW'
    classement_a/b      : classement ATP
    repos_a / repos_b   : jours de repos depuis le dernier match
    h2h_a               : victoires de A en head-to-head
    meteo               : conditions météo
    service_won_a/b     : % de points gagnés sur leur service
    type_tournoi        : ex. 'Grand Chelem', 'ATP 1000', etc.
    """

    # --- Probabilités de base (ELO) ---
    proba_elo_a, proba_elo_b = _proba_from_elo(elo_a, elo_b)

    # --- Ajustements ---
    forme_score_a = _score_forme(forme_a)
    forme_score_b = _score_forme(forme_b)
    utr_diff = (utr_a - utr_b) / 20          # normalisation ~[-1, 1]
    service_diff = (service_won_a - service_won_b) / 100
    repos_diff = (repos_b - repos_a) / 10    # plus de repos = avantage
    h2h_factor = h2h_a * 0.01               # léger bonus H2H

    ajustement_a = (
        (forme_score_a - forme_score_b) * 0.10
        + utr_diff * 0.10
        + service_diff * 0.05
        + repos_diff * 0.03
        + h2h_factor
    )

    proba_a = max(0.05, min(0.95, proba_elo_a + ajustement_a))
    proba_b = 1 - proba_a

    # --- Edge ---
    edge_a = _edge(proba_a, cote_a)
    edge_b = _edge(proba_b, cote_b)

    # --- Volatilité (écart de niveau) ---
    diff_niveau = abs(elo_a - elo_b)
    if diff_niveau > 200:
        volatility = "Faible 🟢"
    elif diff_niveau > 100:
        volatility = "Moyenne 🟡"
    else:
        volatility = "Élevée 🔴"

    # --- Zone de jeux estimée ---
    avg_service = (service_won_a + service_won_b) / 2
    line = round(avg_service / 10 + (sets * 3.5), 1)
    low = round(line - 2.5, 1)
    high = round(line + 2.5, 1)

    # --- Recommandation de pari ---
    EDGE_SEUIL = 0.05
    MISE_BASE = 2.0

    if edge_a >= EDGE_SEUIL:
        bet_type = "value bet"
        bet_side = "Joueur A"
        stake = MISE_BASE + edge_a * 10
    elif edge_b >= EDGE_SEUIL:
        bet_type = "value bet"
        bet_side = "Joueur B"
        stake = MISE_BASE + edge_b * 10
    else:
        bet_type = "none"
        bet_side = ""
        stake = 0.0

    # --- Message Telegram ---
    message = (
        f"🎾 **Analyse Match** ({'BO5' if sets == 5 else 'BO3'}) | {surface} | {type_tournoi}\n\n"
        f"🌡️ Météo : {meteo}\n"
        f"🏆 Classement : A={classement_a} | B={classement_b}\n"
        f"🔥 UTR : A={utr_a} | B={utr_b}\n"
        f"📊 ELO : A={elo_a} | B={elo_b}\n"
        f"💰 Cotes : A={cote_a} | B={cote_b}\n\n"
        f"📈 **Probas** : A={proba_a * 100:.1f}% | B={proba_b * 100:.1f}%\n"
        f"🎯 **Edge** : A={edge_a:.2%} | B={edge_b:.2%}\n"
        f"📊 **Volatilité** : {volatility}\n"
        f"🎯 **Zone de jeux** : {low}-{high} jeux | Ligne marché : {line}\n\n"
    )

    if bet_type != "none":
        message += f"💰 **Stratégie** : {bet_type} {bet_side} | Mise : {stake:.1f}%\n"
    else:
        message += "🚫 **Pas de pari recommandé**\n"

    return message
