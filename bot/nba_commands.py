# bot/nba_commands.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from api.nba_data import get_nba_schedule, get_team_stats
from api.nba_ml import predictor

# -----------------------------
# MENU NBA
# -----------------------------
async def nba_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("📅 Matchs du jour", callback_data="nba_today"),
            InlineKeyboardButton("📈 Prédiction ML", callback_data="nba_prediction"),
        ],
        [InlineKeyboardButton("🔙 Retour", callback_data="back_to_main")]
    ]
    await update.message.reply_text(
        "🏀 **Menu NBA** :",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# -----------------------------
# MATCHS NBA DU JOUR
# -----------------------------
async def nba_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    schedule = get_nba_schedule()
    if not schedule:
        await query.edit_message_text("Aucun match NBA aujourd'hui.")
        return

    matches = []
    for game in schedule:
        home_team = game["home_team"]["full_name"]
        away_team = game["away_team"]["full_name"]
        game_time = game["status"].split(" - ")[-1] if " - " in game["status"] else "TBD"
        matches.append(f"{home_team} vs {away_team} ({game_time})")

    await query.edit_message_text(
        "📅 **Matchs NBA du jour** :\n\n" +
        "\n".join(f"• {m}" for m in matches)
    )

# -----------------------------
# PRÉDICTION ML NBA
# -----------------------------
async def nba_prediction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    schedule = get_nba_schedule()
    if not schedule:
        await query.edit_message_text("Aucun match aujourd'hui.")
        return

    game = schedule[0]  # Premier match du jour
    home_team_id = game["home_team"]["id"]
    away_team_id = game["away_team"]["id"]

    home_stats = get_team_stats(home_team_id)
    away_stats = get_team_stats(away_team_id)

    if not home_stats or not away_stats:
        await query.edit_message_text("⚠️ Impossible de récupérer les stats pour ce match.")
        return

    prediction = predictor.predict(home_stats, away_stats)
    prediction.update({
        "home_team": game["home_team"]["full_name"],
        "away_team": game["away_team"]["full_name"],
        "game_time": game["status"].split(" - ")[-1] if " - " in game["status"] else "TBD"
    })

    await query.edit_message_text(
        f"📈 **Prédiction ML** : {prediction['home_team']} vs {prediction['away_team']}\n"
        f"🕒 Heure : {prediction['game_time']}\n"
        f"🔢 Score prédit : **{prediction['home_score']}** - {prediction['away_score']}\n"
        f"📊 Confiance : {prediction['confiance']}%\n"
        f"💡 Différence : {prediction['point_diff']} pts (avantage {prediction['home_team']})"
    )
