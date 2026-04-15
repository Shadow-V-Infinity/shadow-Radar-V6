from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from core.sofa_api import fetch_sofa_matches, format_matches_list
from core.analysis import build_auto_analysis
from core.nba_history import nba_history_model


async def show_nba_menu(query):
    keyboard = [
        [InlineKeyboardButton("📅 Matchs NBA du jour", callback_data="nba_today")],
        [InlineKeyboardButton("📈 Analyse NBA", callback_data="nba_analysis")],
        [InlineKeyboardButton("🔔 Alertes NBA", callback_data="nba_alerts")],
        [InlineKeyboardButton("⬅️ Retour", callback_data="open_menu")],
    ]

    await query.edit_message_text(
        "🟦 **NBA — MODULE PREMIUM**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Sélectionne une option :\n",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


async def nba_today(query):
    events = await fetch_sofa_matches(tournament_id=132)
    body = format_matches_list(events)
    await query.edit_message_text(
        "📅 **Matchs du jour (NBA)**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"{body}",
        parse_mode="Markdown",
    )


async def nba_analysis(query):
    # Version simple : on affiche juste un texte générique + un rappel du modèle historique
    text = (
        "📈 **Analyse NBA — Mode Shadow‑Edge**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Ce module utilise :\n"
        "• Ton historique NBA (edge_calculated)\n"
        "• Des stats moyennes par équipe\n"
        "• Des edges moyens par matchup\n\n"
        "Pour une analyse ciblée, envoie par exemple :\n"
        "`/nba_matchup Lakers Suns`\n"
        "`/nba_team Lakers`\n"
    )
    await query.edit_message_text(text, parse_mode="Markdown")


async def nba_alerts(query):
    await query.edit_message_text(
        "🔔 **Alertes NBA**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Module en préparation ⚙️",
        parse_mode="Markdown",
    )
