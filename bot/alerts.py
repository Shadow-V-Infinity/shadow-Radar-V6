# bot/alerts.py
def monitor_tennis_alerts():
    while True:
        # Récupérer les matchs de tennis en cours
        tennis_matches = fetch_tennis_matches()  # À implémenter
        for match in tennis_matches:
            # Récupérer les cotes
            odds = fetch_tennis_odds(match["id"])
            # Détecter les mouvements/surebets
            movements = detect_tennis_odd_movements(odds)
            surebets = detect_tennis_surebets(odds)
            # Envoyer les alertes
            for alert in movements + surebets:
                send_alert_to_users(alert)
        time.sleep(120)  # Toutes les 2 minutes

def detect_tennis_surebets():
    """Détecte les surebets pour les matchs de tennis."""
    # Exemple : Récupérer les cotes pour les matchs en cours
    tennis_matches = fetch_tennis_matches()
    surebets = []

    for match in tennis_matches:
        odds = fetch_tennis_odds(match["idEvent"])
        # Logique pour détecter les surebets (comme dans le football)
        # ...
        surebets.append({
            "match": f"{match['strHomeTeam']} vs {match['strAwayTeam']}",
            "profit": 5.2,  # Exemple
            "bookmakers": "Bet365 vs Winamax"
        })

    return surebets
