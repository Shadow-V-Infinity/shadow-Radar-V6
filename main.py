# main.py
from database import init_db
from bot.commands import main as bot_main
from bot.alerts import detect_movements, detect_surebets
from telegram import Bot
from config import TELEGRAM_BOT_TOKEN
from bot.alerts import monitor_tennis_alerts
import threading
import time

def monitor_odds():
    while True:
        # 1. Récupérer les cotes pour le football
        football_odds = fetch_odds("soccer_epl", "English Premier League")
        save_odds(football_odds, source="odds_api")

        # 2. Récupérer les cotes pour le tennis
        tennis_odds = fetch_odds_io("tennis", "ATP")
        save_odds(tennis_odds, source="odds_api_io")

        # 3. Détecter les mouvements et surebets
        movements = detect_movements()
        surebets = detect_surebets()

        # 4. Envoyer les alertes aux utilisateurs abonnés
        for move in movements:
            send_alert_to_users(move)
        for surebet in surebets:
            send_alert_to_users(surebet)

        time.sleep(120)  # Attendre 2 minutes

def send_alert_to_users(alert):
    conn = sqlite3.connect("sports_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM user_alerts WHERE football_alerts = TRUE")
    chat_ids = [row[0] for row in cursor.fetchall()]
    conn.close()

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    for chat_id in chat_ids:
        try:
            bot.send_message(chat_id=chat_id, text=format_alert(alert), parse_mode='Markdown')
        except Exception as e:
            print(f"Erreur envoi : {e}")
            
def format_alert(alert):
    if alert["type"] == "movement":
        return (
            f"🚨 **Mouvement de cote détecté** 🚨\n\n"
            f"Match : {alert['match']}\n"
            f"Bookmaker : {alert['bookmaker']}\n"
            f"Issue : {alert['outcome']}\n"
            f"Variation : {alert['variation']:.2f}%\n"
            f"Nouvelle cote : {alert['current_price']}"
        )
    elif alert["type"] == "surebet":
        return (
            f"💰 **Surebet détecté** 💰\n\n"
            f"Match : {alert['match']}\n"
            f"Profit garanti : {alert['profit']:.2f}%\n"
            f"Bookmakers : {alert['bookmakers']}"
        )
        
def main():
    init_db()  # Initialise la DB SQLite avant de lancer le reste
    bot_thread = threading.Thread(target=bot_main)
    bot_thread.daemon = True
    bot_thread.start()

    
    # Lancer la boucle de surveillance des cotes
    monitor_odds() # Lance la boucle infinie de scan
    
    # Lancer la surveillance football + tennis
    threading.Thread(target=monitor_odds, daemon=True).start()  # Football
    threading.Thread(target=monitor_tennis_alerts, daemon=True).start()  # Tennis
   
    if __name__ == "__main__":
   
    main()
