from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from core.sofa_api import fetch_sofa_matches, format_matches_list
from core.analysis import build_auto_analysis


async def show_rugby_menu(query):
    keyboard = [
        [InlineKeyboardButton("📅 Matchs du jour", callback_data="rugby_today")],
        [InlineKeyboardButton("📈 Analyse & Prédictions", callback_data="rugby_analysis")],
        [InlineKeyboardButton("🔔 Alertes Rugby", callback_data="rugby_alerts")],
        [InlineKeyboardButton("⬅️ Retour", callback_data="open_menu")],
    ]

    await query.edit_message_text(
        "🏉 **RADAR RUGBY — MODULE PREMIUM**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Sélectionne une option :\n",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


async def rugby_today(query):
    events = await fetch_sofa_matches(sport="rugby")
    body = format_matches_list(events)
    await query.edit_message_text(
        "📅 **Matchs du jour (Rugby)**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"{body}",
        parse_mode="Markdown",
    )


async def rugby_analysis(query):
    await query.edit_message_text(
        build_auto_analysis("Rugby"),
        parse_mode="Markdown",
    )


async def rugby_alerts(query):
    await query.edit_message_text(
        "🔔 **Alertes Rugby**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Module en préparation ⚙️",
        parse_mode="Markdown",
    )
