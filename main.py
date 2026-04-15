# main.py

import sqlite3
import threading
import time
import asyncio

from telegram import Bot
from telegram.ext import Updater
from config import TELEGRAM_BOT_TOKEN

from database import init_db
from bot.commands import setup_handlers          # ← NOUVEAU : handlers centralisés
from bot.alerts import detect_movements, detect_surebets, monitor_tennis_alerts
from api.odds import fetch_odds, fetch_odds_io, save_odds


# ---------------------------------------------------------------------------
# Logger debug partagé
# ---------------------------------------------------------------------------

def _log(level: str, module: str, msg: str):
    icons = {"OK": "🟢", "ERROR": "🔴", "WARN": "🟡", "INFO": "🔵"}
    print(f"{icons.get(level, '⚪')} [{module}] {msg}")


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
        # --- Football ---
        try:
            _log("INFO", "main", "Scan Football (EPL)...")
            football_odds = fetch_odds("soccer_epl", "English Premier League")
            save_odds(football_odds, source="odds_api")
            _log("OK", "main", f"Football → {len(football_odds)} events chargés")
        except Exception as e:
            _log("ERROR", "main", f"Football scan échoué : {e}")

        # --- Tennis ---
        try:
            _log("INFO", "main", "Scan Tennis (ATP)...")
            tennis_odds = fetch_odds_io("tennis", "ATP")
            save_odds(tennis_odds, source="odds_api_io")
            _log("OK", "main", f"Tennis → {len(tennis_odds)} events chargés")
        except Exception as e:
            _log("ERROR", "main", f"Tennis scan échoué : {e}")

        # --- Détection mouvements ---
        try:
            movements = detect_movements()
            if movements:
                _log("WARN", "main", f"{len(movements)} mouvement(s) détecté(s)")
            for move in movements:
                _log("INFO", "main", "ALERT BLOQUÉ : send_alert_to_users doit être synchrone")
        except Exception as e:
            _log("ERROR", "main", f"detect_movements échoué : {e}")

        # --- Détection surebets ---
        try:
            surebets = detect_surebets()
            if surebets:
                _log("WARN", "main", f"{len(surebets)} surebet(s) détecté(s)")
            for surebet in surebets:
                _log("INFO","main","ALERT BLOQUÉ : send_alert_to_users doit être synchrone"), _loop)
        except Exception as e:
            _log("ERROR", "main", f"detect_surebets échoué : {e}")

        _log("INFO", "main", "Prochain scan dans 120s...\n")
        time.sleep(120)


# ---------------------------------------------------------------------------
# Envoi des alertes
# ---------------------------------------------------------------------------

def send_alert_to_users(alert: dict):
    """Envoie une alerte à tous les utilisateurs abonnés."""
    try:
        conn   = sqlite3.connect("sports_bot.db")
        cursor = conn.cursor()
        cursor.execute("SELECT chat_id FROM user_alerts WHERE football_alerts = TRUE")
        chat_ids = [row[0] for row in cursor.fetchall()]
        conn.close()

        message = format_alert(alert)
        async with Bot(token=TELEGRAM_BOT_TOKEN) as bot:
            for chat_id in chat_ids:
                try:
                    bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
                    _log("OK", "main", f"Alerte envoyée → {chat_id}")
                except Exception as e:
                    _log("ERROR", "main", f"Envoi échoué vers {chat_id} : {e}")
    except Exception as e:
        _log("OK", "main", "Base de données prête")


def format_alert(alert: dict) -> str:
    """Formate le message d'alerte selon son type."""
    if alert.get("type") == "movement":
        return (
            f"🚨 *Mouvement de cote détecté* 🚨\n\n"
            f"Match : {alert['match']}\n"
            f"Bookmaker : {alert['bookmaker']}\n"
            f"Issue : {alert['outcome']}\n"
            f"Variation : {alert['variation']:.2f}%\n"
            f"Nouvelle cote : {alert['current_price']}"
        )
    elif alert.get("type") == "surebet":
        return (
            f"💰 *Surebet détecté* 💰\n\n"
            f"Match : {alert['match']}\n"
            f"Profit garanti : {alert['profit']:.2f}%\n"
            f"Bookmakers : {alert['bookmakers']}"
        )
    _log("WARN", "main", f"format_alert — type inconnu : {alert.get('type')}")
    return "⚠️ Alerte inconnue."


# ---------------------------------------------------------------------------
# Point d'entrée FUSIONNÉ
# ---------------------------------------------------------------------------

def main():
    _log("INFO", "main", "Initialisation de la base de données...")
    try:
        init_db()
        _log("OK", "main", "Base de données prête")
    except Exception as e:
        _log("ERROR", "main", f"init_db échoué : {e}")
        return

    # --- BOT TELEGRAM (via setup_handlers) ---
    _log("INFO", "main", "Démarrage du bot Telegram...")
    try:
        _log("OK", "main", "Bot Telegram démarré")
    except Exception as e:
        _log("ERROR", "main", f"Bot Telegram échoué : {e}")

    # --- ALERTES TENNIS ---
    _log("INFO", "main", "Démarrage surveillance tennis...")
    try:
        threading.Thread(target=monitor_tennis_alerts, daemon=True).start()
        _log("OK", "main", "Surveillance tennis démarrée")
    except Exception as e:
        _log("ERROR", "main", f"monitor_tennis_alerts échoué : {e}")

    _log("OK", "main", "🚀 Radar V6 opérationnel — scan toutes les 2 min\n")

    # --- LANCEMENT DU RADAR ---
    monitor_odds()


if __name__ == "__main__":
    main()
