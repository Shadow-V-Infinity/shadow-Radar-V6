# api/tennis_api.py
import requests

def fetch_atp_rankings():
    url = "https://raw.githubusercontent.com/JetBrains-Research/tennis_api/master/data/atp_rankings.json"
    response = requests.get(url)
    return response.json()

def fetch_player_stats(player_name):
    # Exemple : Récupérer les stats d'un joueur depuis une API ou un dataset
    # (À adapter selon tes sources de données)
    url = f"https://api.tennis-data.org/players?name={player_name}"  # Exemple fictif
    response = requests.get(url)
    return response.json()

def fetch_player_utr(player_name):
    # Exemple avec un dataset public (à adapter)
    utr_data = {
        "Novak Djokovic": 16.5,
        "Rafael Nadal": 16.0,
        "Roger Federer": 15.8,
        # ... (ajoute d'autres joueurs)
    }
    return utr_data.get(player_name, 12.0)  # Valeur par défaut si inconnu

def calcul_match_telegram(
    utr_a, utr_b, elo_a, elo_b, cote_a, cote_b, sets, surface,
    forme_a="WWWWW", forme_b="WWWWW",
    classement_a=50, classement_b=50,
    repos_a=3, repos_b=3,
    h2h_a=0,
    meteo="soleil",
    service_won_a=65, service_won_b=65,
    type_tournoi="ATP 250"
):
    # ... (ton code existant pour calculer les probas, edges, etc.)

    # Formatage pour Telegram
    message = (
        f"🎾 **Analyse Match** ({'BO5' if sets == 5 else 'BO3'}) | {surface} | {type_tournoi}\n\n"
        f"🌡️ Météo : {météo}\n"
        f"🏆 Classement : A={classement_a} | B={classement_b}\n"
        f"🔥 UTR : A={utr_a} | B={utr_b}\n"
        f"📊 ELO : A={elo_a} | B={elo_b}\n"
        f"💰 Cotes : A={cote_a} | B={cote_b}\n\n"
        f"📈 **Probas** : A={proba_a*100:.1f}% | B={proba_b*100:.1f}%\n"
        f"🎯 **Edge** : A={edge_a:.2%} | B={edge_b:.2%}\n"
        f"📊 **Volatilité** : {volatility}\n"
        f"🎯 **Zone de jeux** : {low}-{high} jeux | Ligne marché : {line}\n\n"
    )

    if bet_type != "none":
        message += f"💰 **Stratégie** : {bet_type} {bet_side} | Mise : {stake:.1f}%\n"
    else:
        message += "🚫 **Pas de pari recommandé**\n"

    return message
