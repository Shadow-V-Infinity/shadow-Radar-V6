from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from core.sofa_api import fetch_sofa_matches, format_matches_list
from core.analysis import build_auto_analysis


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
    await query.edit_message_text(
        build_auto_analysis("NBA"),
        parse_mode="Markdown",
    )


async def nba_alerts(query):
    await query.edit_message_text(
        "🔔 **Alertes NBA**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Module en préparation ⚙️",
        parse_mode="Markdown",
    )
