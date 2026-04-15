# bot/alerts.py

import time
import asyncio
import sqlite3

from telegram import Bot
from config import TELEGRAM_BOT_TOKEN
from api.tennis_api import fetch_tennis_matches
from api.odds_api import fetch_odds
from database import DB_PATH


# ---------------------------------------------------------------------------
# Utilitaires DB
# ---------------------------------------------------------------------------

def _get_subscribed_chat_ids(sport: str) -> list[int]:
    """Retourne les chat_id des utilisateurs abonnés aux alertes d'un sport."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f"SELECT chat_id FROM user_alerts WHERE {sport}_alerts = TRUE")
    ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    return ids


# ---------------------------------------------------------------------------
# Envoi d'alertes
# ---------------------------------------------------------------------------

async def _send_alert(chat_id: int, message: str):
    """Envoie un message Telegram à un utilisateur."""
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    try:
        await bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
    except Exception as e:
        print(f"❌ Erreur envoi alerte vers {chat_id} : {e}")


def send_alert_to_users(alert: dict, sport: str = "football"):
    """Envoie une alerte à tous les utilisateurs abonnés au sport concerné."""
    chat_ids = _get_subscribed_chat_ids(sport)
    message = _format_alert(alert)
    for chat_id in chat_ids:
        asyncio.run(_send_alert(chat_id, message))


def _format_alert(alert: dict) -> str:
    """Formate le message selon le type d'alerte."""
    if alert.get("type") == "movement":
        return (
            f"🚨 **Mouvement de cote détecté** 🚨\n\n"
            f"Match : {alert['match']}\n"
            f"Bookmaker : {alert['bookmaker']}\n"
            f"Issue : {alert['outcome']}\n"
            f"Variation : {alert['variation']:.2f}%\n"
            f"Nouvelle cote : {alert['current_price']}"
        )
    elif alert.get("type") == "surebet":
        return (
            f"💰 **Surebet détecté** 💰\n\n"
            f"Match : {alert['match']}\n"
            f"Profit garanti : {alert['profit']:.2f}%\n"
            f"Bookmakers : {alert['bookmakers']}"
        )
    return "⚠️ Alerte de type inconnu."


# ---------------------------------------------------------------------------
# Détection — Football
# ---------------------------------------------------------------------------

def detect_movements(sport: str = "soccer_epl", league: str = "Premier League") -> list[dict]:
    """
    Détecte les mouvements de cotes significatifs pour un sport donné.
    Retourne une liste d'alertes de type 'movement'.
    """
    odds_data = fetch_odds(sport, league)
    movements = []

    for event in odds_data:
        match_name = f"{event.get('home_team', '?')} vs {event.get('away_team', '?')}"
        bookmakers = event.get("bookmakers", [])

        # Comparer les cotes entre bookmakers pour détecter les écarts
        prices: dict[str, list[float]] = {}
        for bk in bookmakers:
            for market in bk.get("markets", []):
                if market.get("key") != "h2h":
                    continue
                for outcome in market.get("outcomes", []):
                    name = outcome.get("name")
                    price = outcome.get("price", 0)
                    prices.setdefault(name, []).append(price)

        for outcome_name, price_list in prices.items():
            if len(price_list) < 2:
                continue
            min_p, max_p = min(price_list), max(price_list)
            if min_p == 0:
                continue
            variation = (max_p - min_p) / min_p * 100
            if variation >= 5.0:  # seuil de 5%
                movements.append({
                    "type": "movement",
                    "match": match_name,
                    "bookmaker": "multi-bookmakers",
                    "outcome": outcome_name,
                    "variation": variation,
                    "current_price": max_p,
                })

    return movements


def detect_surebets(sport: str = "soccer_epl", league: str = "Premier League") -> list[dict]:
    """
    Détecte les surebets (arbitrage) sur les cotes bookmakers.
    Un surebet existe si la somme des probabilités implicites < 1.
    """
    odds_data = fetch_odds(sport, league)
    surebets = []

    for event in odds_data:
        match_name = f"{event.get('home_team', '?')} vs {event.get('away_team', '?')}"
        bookmakers = event.get("bookmakers", [])

        # Meilleure cote disponible par issue
        best_prices: dict[str, tuple[float, str]] = {}  # outcome → (price, bookmaker)
        for bk in bookmakers:
            bk_name = bk.get("key", "?")
            for market in bk.get("markets", []):
                if market.get("key") != "h2h":
                    continue
                for outcome in market.get("outcomes", []):
                    name = outcome.get("name")
                    price = outcome.get("price", 0)
                    if price > best_prices.get(name, (0, ""))[0]:
                        best_prices[name] = (price, bk_name)

        if len(best_prices) < 2:
            continue

        # Calcul de la marge implicite
        implied_sum = sum(1 / p for p, _ in best_prices.values())
        if implied_sum < 1.0:
            profit = (1 - implied_sum) * 100
            bk_names = ", ".join(bk for _, bk in best_prices.values())
            surebets.append({
                "type": "surebet",
                "match": match_name,
                "profit": profit,
                "bookmakers": bk_names,
            })

    return surebets


# ---------------------------------------------------------------------------
# Détection — Tennis
# ---------------------------------------------------------------------------

def _detect_tennis_odd_movements(odds: list[dict], match_name: str) -> list[dict]:
    """Détecte les mouvements de cotes sur un match de tennis."""
    movements = []
    prices: dict[str, list[float]] = {}

    for entry in odds:
        outcome = entry.get("outcome")
        price = entry.get("price", 0)
        if outcome and price:
            prices.setdefault(outcome, []).append(price)

    for outcome_name, price_list in prices.items():
        if len(price_list) < 2:
            continue
        min_p, max_p = min(price_list), max(price_list)
        if min_p == 0:
            continue
        variation = (max_p - min_p) / min_p * 100
        if variation >= 5.0:
            movements.append({
                "type": "movement",
                "match": match_name,
                "bookmaker": "multi-bookmakers",
                "outcome": outcome_name,
                "variation": variation,
                "current_price": max_p,
            })

    return movements


def _detect_tennis_surebets(odds: list[dict], match_name: str) -> list[dict]:
    """Détecte les surebets sur un match de tennis."""
    best_prices: dict[str, tuple[float, str]] = {}

    for entry in odds:
        outcome = entry.get("outcome")
        price = entry.get("price", 0)
        bookmaker = entry.get("bookmaker", "?")
        if outcome and price > best_prices.get(outcome, (0, ""))[0]:
            best_prices[outcome] = (price, bookmaker)

    if len(best_prices) < 2:
        return []

    implied_sum = sum(1 / p for p, _ in best_prices.values())
    if implied_sum < 1.0:
        profit = (1 - implied_sum) * 100
        bk_names = ", ".join(bk for _, bk in best_prices.values())
        return [{
            "type": "surebet",
            "match": match_name,
            "profit": profit,
            "bookmakers": bk_names,
        }]

    return []


def _fetch_tennis_odds(match_id) -> list[dict]:
    """
    Récupère les cotes d'un match de tennis.
    À connecter à ta source de données réelle.
    """
    # TODO : remplacer par un vrai appel API tennis
    return []


def monitor_tennis_alerts():
    """Boucle de surveillance des alertes tennis (thread dédié)."""
    print("🎾 Surveillance tennis démarrée.")
    while True:
        try:
            tennis_matches = fetch_tennis_matches()
            for match in tennis_matches:
                match_name = (
                    f"{match.get('player1', match.get('home', '?'))} vs "
                    f"{match.get('player2', match.get('away', '?'))}"
                )
                odds = _fetch_tennis_odds(match.get("id"))
                alerts = (
                    _detect_tennis_odd_movements(odds, match_name)
                    + _detect_tennis_surebets(odds, match_name)
                )
                for alert in alerts:
                    send_alert_to_users(alert, sport="tennis")
        except Exception as e:
            print(f"❌ Erreur monitor_tennis_alerts : {e}")

        time.sleep(120)
