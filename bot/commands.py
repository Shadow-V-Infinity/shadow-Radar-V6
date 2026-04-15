# bot/commands.py

import sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler
from config import TELEGRAM_BOT_TOKEN
from api.tennis_api import fetch_tennis_matches, fetch_tennis_matches_scheduled, fetch_player_utr, fetch_atp_rankings
from api.tennis_analysis import calcul_match_telegram
from api.tennis_stats import get_player_stats
from api.football_data import fetch_football_matches


# ---------------------------------------------------------------------------
# Commandes de base
# ---------------------------------------------------------------------------

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "🎉 Bienvenue sur *Sports Alert Bot* !\n\n"
        "Utilise /help pour voir la liste des commandes disponibles.",
        parse_mode="Markdown"
    )


async def help_command(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "📌 *Commandes disponibles* :\n\n"
        "/start — Démarrer le bot\n"
        "/help — Afficher cette aide\n"
        "/football — Voir les matchs de football\n"
        "/tennis — Matchs de tennis en direct\n"
        "/tennis\\_today — Matchs de tennis programmés aujourd'hui\n"
        "/atp — Classement ATP\n"
        "/analyse — Analyser un match de tennis\n"
        "/basket — Voir les matchs de basket\n"
        "/alerts — Gérer les alertes\n"
        "/stats — Voir les statistiques\n"
        "/surebets — Voir les surebets",
        parse_mode="Markdown"
    )


# ---------------------------------------------------------------------------
# Football
# ---------------------------------------------------------------------------

async def football(update: Update, context: CallbackContext):
    try:
        matches = fetch_football_matches(league="PL", status="SCHEDULED")
    except Exception as ex:
        await update.message.reply_text(f"⚠️ Erreur lors de la récupération des matchs : {ex}")
        return

    if not matches.get("matches"):
        await update.message.reply_text("⚽ Aucun match de football programmé.")
        return

    message = "⚽ *Matchs de football (Premier League)* :\n\n"
    for match in matches["matches"][:5]:
        message += (
            f"🔹 {match['homeTeam']['name']} vs {match['awayTeam']['name']}\n"
            f"   📅 {match['utcDate']}\n"
            f"   🏟 {match['status']}\n\n"
        )
    await update.message.reply_text(message, parse_mode="Markdown")


# ---------------------------------------------------------------------------
# Tennis
# ---------------------------------------------------------------------------

async def tennis(update: Update, context: CallbackContext):
    """Matchs en direct."""
    matches = fetch_tennis_matches()
    if not matches:
        await update.message.reply_text(
            "🎾 Aucun match de tennis en direct pour le moment.\n"
            "Essaie /tennis\\_today pour les matchs programmés aujourd'hui.",
            parse_mode="Markdown"
        )
        return

    message = "🎾 *Matchs de tennis en direct* :\n\n"
    for match in matches[:8]:
        message += (
            f"🔹 {match.get('player1', '?')} vs {match.get('player2', '?')}\n"
            f"   🏆 {match.get('tournament', 'Tournoi inconnu')}\n"
            f"   📊 {match.get('status', '')}\n\n"
        )
    await update.message.reply_text(message, parse_mode="Markdown")


async def tennis_today(update: Update, context: CallbackContext):
    """Matchs programmés aujourd'hui."""
    matches = fetch_tennis_matches_scheduled()
    if not matches:
        await update.message.reply_text("🎾 Aucun match de tennis programmé aujourd'hui.")
        return

    message = "🎾 *Matchs de tennis aujourd'hui* :\n\n"
    for match in matches[:8]:
        message += (
            f"🔹 {match.get('player1', '?')} vs {match.get('player2', '?')}\n"
            f"   🏆 {match.get('tournament', 'Tournoi inconnu')}\n\n"
        )
    await update.message.reply_text(message, parse_mode="Markdown")


async def atp_rankings(update: Update, context: CallbackContext):
    """Classement ATP top 10."""
    rankings = fetch_atp_rankings()
    if not rankings:
        await update.message.reply_text("⚠️ Impossible de récupérer le classement ATP.")
        return

    message = "🏆 *Classement ATP (Top 10)* :\n\n"
    for r in rankings[:10]:
        message += f"#{r['rank']} — {r['player']} ({r['points']} pts)\n"
    await update.message.reply_text(message, parse_mode="Markdown")


# ---------------------------------------------------------------------------
# Analyse tennis (avec météo)
# ---------------------------------------------------------------------------

async def analyse_tennis(update: Update, context: CallbackContext):
    """
    Usage : /analyse <JoueurA> <JoueurB> <sets(3/5)> <surface> <coteA> <coteB> [tournoi] [date]
    Exemple : /analyse Djokovic Nadal 3 terre 1.8 2.1 Roland-Garros 2026-04-20
    """
    if not context.args or len(context.args) < 6:
        await update.message.reply_text(
            "⚠️ *Usage* :\n"
            "`/analyse <JoueurA> <JoueurB> <sets(3/5)> <surface> <coteA> <coteB> [tournoi] [date]`\n\n"
            "Exemple :\n"
            "`/analyse Djokovic Nadal 3 terre 1.8 2.1 Roland-Garros 2026-04-20`",
            parse_mode="Markdown"
        )
        return

    joueur_a, joueur_b, sets_str, surface, cote_a_str, cote_b_str = context.args[:6]

    try:
        sets   = int(sets_str)
        cote_a = float(cote_a_str)
        cote_b = float(cote_b_str)
    except ValueError:
        await update.message.reply_text(
            "⚠️ Paramètres invalides. Sets doit être 3 ou 5, cotes en décimal (ex: 1.85)."
        )
        return

    if sets not in (3, 5):
        await update.message.reply_text("⚠️ Le nombre de sets doit être 3 (BO3) ou 5 (BO5).")
        return

    # Paramètres optionnels
    tournoi  = context.args[6] if len(context.args) > 6 else "ATP 250"
    date_str = context.args[7] if len(context.args) > 7 else datetime.now().strftime("%Y-%m-%d")

    match_data = {
        "tournament": tournoi,
        "date":       f"{date_str}T00:00:00Z",
        "surface":    surface,
    }

    # Données joueurs — récupérées depuis Tennis Abstract (Sackmann)
    await update.message.reply_text("⏳ Chargement des stats joueurs...")

    stats_a = get_player_stats(joueur_a)
    stats_b = get_player_stats(joueur_b)

    utr_a = fetch_player_utr(joueur_a)
    utr_b = fetch_player_utr(joueur_b)

    elo_a         = stats_a["elo"]
    elo_b         = stats_b["elo"]
    classement_a  = stats_a["rank"]
    classement_b  = stats_b["rank"]
    forme_a       = stats_a["form"]
    forme_b       = stats_b["form"]
    service_won_a = stats_a["service_won"]
    service_won_b = stats_b["service_won"]
    repos_a, repos_b = 3, 3
    h2h_a            = 0

    result = calcul_match_telegram(
        utr_a, utr_b, elo_a, elo_b, cote_a, cote_b, sets, surface,
        forme_a, forme_b, classement_a, classement_b,
        repos_a, repos_b, h2h_a,
        service_won_a, service_won_b,
        type_tournoi=tournoi,
        match_data=match_data,
        nom_a=joueur_a,
        nom_b=joueur_b,
    )
    await update.message.reply_text(result, parse_mode="Markdown")


# ---------------------------------------------------------------------------
# Basket
# ---------------------------------------------------------------------------

async def basket(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "🏀 *Matchs de basket* :\n\n_Fonctionnalité en cours d'intégration..._",
        parse_mode="Markdown"
    )


# ---------------------------------------------------------------------------
# Alertes
# ---------------------------------------------------------------------------

def _init_db():
    """Crée la table user_alerts si elle n'existe pas encore."""
    conn = sqlite3.connect("sports_bot.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_alerts (
            chat_id          INTEGER PRIMARY KEY,
            football_alerts  BOOLEAN DEFAULT 0,
            tennis_alerts    BOOLEAN DEFAULT 0,
            basket_alerts    BOOLEAN DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


def _set_alert(chat_id: int, sport: str, enabled: bool):
    """Active ou désactive les alertes pour un sport donné."""
    allowed = {"football", "tennis", "basket"}
    if sport not in allowed:
        raise ValueError(f"Sport inconnu : {sport}")
    _init_db()
    conn = sqlite3.connect("sports_bot.db")
    cursor = conn.cursor()
    cursor.execute(
        f"""
        INSERT INTO user_alerts (chat_id, {sport}_alerts)
        VALUES (?, ?)
        ON CONFLICT(chat_id) DO UPDATE SET {sport}_alerts = excluded.{sport}_alerts
        """,
        (chat_id, enabled),
    )
    conn.commit()
    conn.close()


async def alerts(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("✅ Activer alertes football",   callback_data="enable_football")],
        [InlineKeyboardButton("❌ Désactiver alertes football", callback_data="disable_football")],
        [InlineKeyboardButton("✅ Activer alertes tennis",     callback_data="enable_tennis")],
        [InlineKeyboardButton("❌ Désactiver alertes tennis",   callback_data="disable_tennis")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🔔 *Gérer les alertes* :", reply_markup=reply_markup, parse_mode="Markdown"
    )


async def button_click(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id

    actions = {
        "enable_football":  ("football", True,  "✅ Alertes football *activées* !"),
        "disable_football": ("football", False, "❌ Alertes football *désactivées*."),
        "enable_tennis":    ("tennis",   True,  "✅ Alertes tennis *activées* !"),
        "disable_tennis":   ("tennis",   False, "❌ Alertes tennis *désactivées*."),
    }

    if query.data in actions:
        sport, enabled, msg = actions[query.data]
        try:
            _set_alert(chat_id, sport, enabled)
            await query.edit_message_text(msg, parse_mode="Markdown")
        except Exception as ex:
            await query.edit_message_text(f"⚠️ Erreur : {ex}")
    else:
        await query.edit_message_text("⚠️ Action inconnue.")


# ---------------------------------------------------------------------------
# Divers
# ---------------------------------------------------------------------------

async def stats(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "📊 *Statistiques* :\n\n_Fonctionnalité en cours d'intégration..._",
        parse_mode="Markdown"
    )


async def surebets(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "💰 *Surebets disponibles* :\n\n_Recherche en cours..._",
        parse_mode="Markdown"
    )


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------

def main():
    _init_db()
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start",        start))
    application.add_handler(CommandHandler("help",         help_command))
    application.add_handler(CommandHandler("football",     football))
    application.add_handler(CommandHandler("tennis",       tennis))
    application.add_handler(CommandHandler("tennis_today", tennis_today))
    application.add_handler(CommandHandler("atp",          atp_rankings))
    application.add_handler(CommandHandler("analyse",      analyse_tennis))
    application.add_handler(CommandHandler("basket",       basket))
    application.add_handler(CommandHandler("alerts",       alerts))
    application.add_handler(CommandHandler("stats",        stats))
    application.add_handler(CommandHandler("surebets",     surebets))
    application.add_handler(CallbackQueryHandler(button_click))

    print("🤖 Bot démarré — polling...")
    application.run_polling()


if __name__ == "__main__":
    main()
