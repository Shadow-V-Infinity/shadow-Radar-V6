# bot/commands.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler
from config import TELEGRAM_BOT_TOKEN
from api.tennis_api import fetch_tennis_matches
from api.tennis_analysis import calcul_match_telegram
from api.tennis_api import fetch_player_utr, fetch_atp_rankings
from api.football_data import fetch_football_matches

# Commande /start
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "🎉 Bienvenue sur **Sports Alert Bot** !\n\n"
        "Utilise /help pour voir la liste des commandes disponibles."

from config import TELEGRAM_BOT_TOKEN
from telegram.ext import Application, CommandHandler, CallbackContext

async def start(update, context: CallbackContext):
    await update.message.reply_text("🎉 Bot démarré !")

async def help_command(update, context: CallbackContext):
    await update.message.reply_text(
        "📌 **Commandes disponibles** :\n\n"
        "/start - Démarrer le bot\n"
        "/help - Affiche cette aide\n"
        "/football - Voir les matchs de football\n"
        "/tennis - Voir les matchs de tennis\n"
        "/analyse - Analyser un match de tennis\n"
    )

# Commande /help
def help_command(update: Update, context: CallbackContext):
    update.message.reply_text(
        "📌 **Commandes disponibles** :\n\n"
        "/start - Démarrer le bot\n"
        "/help - Affiche cette aide\n"
        "/football - Voir les matchs de football\n"
        "/tennis - Voir les matchs de tennis\n"
        "/basket - Voir les matchs de basket\n"
        "/alerts - Gérer les alertes\n"
        "/stats - Voir les statistiques\n"
        "/surebets - Voir les surebets"
    )

# Commande /football
def football(update: Update, context: CallbackContext):
    matches = fetch_football_matches(league="PL", status="SCHEDULED")  # Premier League
    if not matches.get("matches"):
        update.message.reply_text("⚽ Aucun match de football en cours.")
        return

    message = "⚽ **Matchs de football (Premier League) :**\n\n"
    for match in matches["matches"][:5]:  # Affiche les 5 premiers matchs
        message += (
            f"🔹 {match['homeTeam']['name']} vs {match['awayTeam']['name']}\n"
            f"   📅 {match['utcDate']}\n"
            f"   🏟 {match['status']}\n\n"
        )

# Commande /tennis
def tennis(update: Update, context: CallbackContext):
    matches = fetch_tennis_matches()  # Récupère les matchs de tennis
    if not matches:
        update.message.reply_text("🎾 Aucun match de tennis en cours.")
        return

    message = "🎾 **Matchs de tennis :**\n\n"
    for match in matches[:5]:  # Affiche les 5 premiers matchs
        message += (
            f"🔹 {match.get('player1', match.get('home'))} vs {match.get('player2', match.get('away'))}\n"
            f"   📅 {match.get('date', 'Date inconnue')}\n"
            f"   🏟 {match.get('tournament', 'Tournoi inconnu')}\n\n"
        )
       
def analyse_tennis(update: Update, context: CallbackContext):
    # Exemple : /analyse Djokovic Nadal 3 terre 1.8 2.1
    if len(context.args) < 6:
        update.message.reply_text(
            "⚠️ **Usage** : /analyse <JoueurA> <JoueurB> <sets(3/5)> <surface> <coteA> <coteB>\n"
            "Exemple : /analyse Djokovic Nadal 3 terre 1.8 2.1"
        )
        return

    joueur_a, joueur_b, sets, surface, cote_a, cote_b = context.args[:6]
    sets = int(sets)
    cote_a = float(cote_a)
    cote_b = float(cote_b)

    # Récupérer les données joueurs (UTR, ELO, classement, etc.)
    utr_a = fetch_player_utr(joueur_a)
    utr_b = fetch_player_utr(joueur_b)

    # Valeurs par défaut (à remplacer par des appels API réels)
    elo_a, elo_b = 2100, 2050
    classement_a, classement_b = 8, 25
    forme_a, forme_b = "WWLLW", "LWLWW"
    repos_a, repos_b = 3, 1
    h2h_a = 3
    meteo = "soleil"
    service_won_a, service_won_b = 72, 65
    type_tournoi = "Grand Chelem"

    # Calculer l'analyse
    result = calcul_match_telegram(
        utr_a, utr_b, elo_a, elo_b, cote_a, cote_b, sets, surface,
        forme_a, forme_b, classement_a, classement_b,
        repos_a, repos_b, h2h_a, meteo, service_won_a, service_won_b, type_tournoi
    )

    update.message.reply_text(result)
    
# Commande /basket
def basket(update: Update, context: CallbackContext):
    update.message.reply_text("🏀 **Matchs de basket** :\n\n_Affichage des matchs en cours..._")

# Commande /alerts
def alerts(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("Activer les alertes", callback_data="enable_alerts")],
        [InlineKeyboardButton("Désactiver les alertes", callback_data="disable_alerts")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("🔔 **Gérer les alertes** :", reply_markup=reply_markup)

def enable_alerts(chat_id, sport):
    conn = sqlite3.connect("sports_bot.db")
    cursor = conn.cursor()
    cursor.execute(f"""
    INSERT OR IGNORE INTO user_alerts (chat_id, {sport}_alerts) VALUES (?, TRUE)
    ON CONFLICT(chat_id) DO UPDATE SET {sport}_alerts = TRUE
    """, (chat_id,))
    conn.commit()
    conn.close()

def disable_alerts(chat_id, sport):
    conn = sqlite3.connect("sports_bot.db")
    cursor = conn.cursor()
    cursor.execute(f"""
    INSERT OR IGNORE INTO user_alerts (chat_id, {sport}_alerts) VALUES (?, FALSE)
    ON CONFLICT(chat_id) DO UPDATE SET {sport}_alerts = FALSE
    """, (chat_id,))
    conn.commit()
    conn.close()

def button_click(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    chat_id = query.message.chat_id

        if query.data == "enable_alerts":
        enable_alerts(chat_id, "football")  # Active les alertes football par défaut
        query.edit_message_text("✅ Alertes **activées** pour le football !")
        elif query.data == "disable_alerts":
        disable_alerts(chat_id, "football")
        query.edit_message_text("❌ Alertes **désactivées** pour le football.")

def enable_alerts(chat_id, sport):
    conn = sqlite3.connect("sports_bot.db")
    cursor = conn.cursor()
    cursor.execute(f"""
    INSERT OR IGNORE INTO user_alerts (chat_id, {sport}_alerts) VALUES (?, TRUE)
    ON CONFLICT(chat_id) DO UPDATE SET {sport}_alerts = TRUE
    """, (chat_id,))
    conn.commit()
    conn.close()

def disable_alerts(chat_id, sport):
    conn = sqlite3.connect("sports_bot.db")
    cursor = conn.cursor()
    cursor.execute(f"""
    INSERT OR IGNORE INTO user_alerts (chat_id, {sport}_alerts) VALUES (?, FALSE)
    ON CONFLICT(chat_id) DO UPDATE SET {sport}_alerts = FALSE
    """, (chat_id,))
    conn.commit()
    conn.close()

def button_click(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    chat_id = query.message.chat_id

    if query.data == "enable_alerts":
        enable_alerts(chat_id, "football")  # Active les alertes football par défaut
        query.edit_message_text("✅ Alertes **activées** pour le football !")
    elif query.data == "disable_alerts":
        disable_alerts(chat_id, "football")
        query.edit_message_text("❌ Alertes **désactivées** pour le football.")

# Commande /stats
def stats(update: Update, context: CallbackContext):
    update.message.reply_text("📊 **Statistiques** :\n\n_Affichage des statistiques..._")

# Commande /surebets
def surebets(update: Update, context: CallbackContext):
    update.message.reply_text("💰 **Surebets disponibles** :\n\n_Recherche en cours..._")

# Fonction principale pour lancer le bot
def main():

    updater = Updater(TELEGRAM_BOT_TOKEN)
    dp = updater.dispatcher

    # Ajouter les handlers pour chaque commande
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("football", football))
    dp.add_handler(CommandHandler("tennis", tennis))
    dp.add_handler(CommandHandler("basket", basket))
    dp.add_handler(CommandHandler("alerts", alerts))
    dp.add_handler(CommandHandler("stats", stats))
    dp.add_handler(CommandHandler("surebets", surebets))

    # Handler pour les boutons
    dp.add_handler(CallbackQueryHandler(button_click))

    updater.start_polling()
    updater.idle()

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.run_polling()

if __name__ == "__main__":
    main()
