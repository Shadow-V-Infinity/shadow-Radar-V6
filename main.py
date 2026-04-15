# main.py

import sqlite3
import threading
import time
import asyncio

from telegram import Bot
from config import TELEGRAM_BOT_TOKEN
from database import init_db
from bot.commands import main as bot_main
from bot.alerts import detect_movements, detect_surebets, monitor_tennis_alerts
from api.odds import fetch_odds, fetch_odds_io, save_odds


# ---------------------------------------------------------------------------
# Boucle asyncio partagée pour l'envoi des alertes
# ---------------------------------------------------------------------------

_loop = asyncio.new_event_loop()

def _start_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

threading.Thread(target=_start_loop, args=(_loop,), daemon=True).start()


# ---------------------------------------------------------------------------
# Surveillance des cotes
# ---------------------------------------------------------------------------

def monitor_odds():
    """Boucle principale : récupère les cotes, détecte les mouvements et surebets."""
    while True:
        football_odds = fetch_odds("soccer_epl", "English Premier League")
        save_odds(football_odds, source="odds_api")

        tennis_odds = fetch_odds_io("tennis", "ATP")
        save_odds(tennis_odds, source="odds_api_io")

        movements = detect_movements()
        surebets  = detect_surebets()

        for move    in movements: asyncio.run_coroutine_threadsafe(send_alert_to_users(move),    _loop)
        for surebet in surebets:  asyncio.run_coroutine_threadsafe(send_alert_to_users(surebet), _loop)

        time.sleep(120)


# ---------------------------------------------------------------------------
# Envoi des alertes
# ---------------------------------------------------------------------------

async def send_alert_to_users(alert: dict):
    """Envoie une alerte à tous les utilisateurs abonnés."""
    conn   = sqlite3.connect("sports_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM user_alerts WHERE football_alerts = TRUE")
    chat_ids = [row[0] for row in cursor.fetchall()]
    conn.close()

    message = format_alert(alert)
    async with Bot(token=TELEGRAM_BOT_TOKEN) as bot:   # v20 : context manager obligatoire
        for chat_id in chat_ids:
            try:
                await bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
            except Exception as e:
                print(f"Erreur envoi vers {chat_id} : {e}")


def format_alert(alert: dict) -> str:
    """Formate le message d'alerte selon son type."""
    if alert["type"] == "movement":
        return (
            f"🚨 *Mouvement de cote détecté* 🚨\n\n"
            f"Match : {alert['match']}\n"
            f"Bookmaker : {alert['bookmaker']}\n"
            f"Issue : {alert['outcome']}\n"
            f"Variation : {alert['variation']:.2f}%\n"
            f"Nouvelle cote : {alert['current_price']}"
        )
    elif alert["type"] == "surebet":
        return (
            f"💰 *Surebet détecté* 💰\n\n"
            f"Match : {alert['match']}\n"
            f"Profit garanti : {alert['profit']:.2f}%\n"
            f"Bookmakers : {alert['bookmakers']}"
        )
    return "⚠️ Alerte inconnue."


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------

def main():
    init_db()

    threading.Thread(target=bot_main,              daemon=True).start()
    threading.Thread(target=monitor_tennis_alerts, daemon=True).start()

    print("🚀 Radar V6 opérationnel. Scan en cours...")

    monitor_odds()


if __name__ == "__main__":
    main()
