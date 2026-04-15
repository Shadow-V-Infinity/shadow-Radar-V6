from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from core.sofa_api import fetch_sofa_matches, format_matches_list
from core.analysis import build_auto_analysis


async def show_tennis_menu(query):
    keyboard = [
        [InlineKeyboardButton("📅 Matchs du jour", callback_data="tennis_today")],
        [InlineKeyboardButton("📈 Analyse & Prédictions", callback_data="tennis_analysis")],
        [InlineKeyboardButton("🔔 Alertes Tennis", callback_data="tennis_alerts")],
        [InlineKeyboardButton("⬅️ Retour", callback_data="open_menu")],
    ]

    await query.edit_message_text(
        "🎾 **RADAR TENNIS — MODULE PREMIUM**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Sélectionne une option :\n",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


async def tennis_today(query):
    events = await fetch_sofa_matches(sport="tennis")
    body = format_matches_list(events)
    await query.edit_message_text(
        "📅 **Matchs du jour (Tennis)**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"{body}",
        parse_mode="Markdown",
    )


async def tennis_analysis(query):
    await query.edit_message_text(
        build_auto_analysis("Tennis", surface="Dur / Terre / Gazon"),
        parse_mode="Markdown",
    )


async def tennis_alerts(query):
    await query.edit_message_text(
        "🔔 **Alertes Tennis**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Module en préparation ⚙️",
        parse_mode="Markdown",
    )
