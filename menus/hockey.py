from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from core.sofa_api import fetch_sofa_matches, format_matches_list
from core.analysis import build_auto_analysis


async def show_hockey_menu(query):
    keyboard = [
        [InlineKeyboardButton("📅 Matchs du jour", callback_data="hockey_today")],
        [InlineKeyboardButton("📈 Analyse & Prédictions", callback_data="hockey_analysis")],
        [InlineKeyboardButton("🔔 Alertes Hockey", callback_data="hockey_alerts")],
        [InlineKeyboardButton("⬅️ Retour", callback_data="open_menu")],
    ]

    await query.edit_message_text(
        "🏒 **RADAR HOCKEY — MODULE PREMIUM**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Sélectionne une option :\n",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


async def hockey_today(query):
    events = await fetch_sofa_matches(sport="ice-hockey")
    body = format_matches_list(events)
    await query.edit_message_text(
        "📅 **Matchs du jour (Hockey)**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"{body}",
        parse_mode="Markdown",
    )


async def hockey_analysis(query):
    await query.edit_message_text(
        build_auto_analysis("Hockey sur glace"),
        parse_mode="Markdown",
    )


async def hockey_alerts(query):
    await query.edit_message_text(
        "🔔 **Alertes Hockey**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Module en préparation ⚙️",
        parse_mode="Markdown",
    )
