from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from core.sofa_api import fetch_sofa_matches, format_matches_list
from core.analysis import build_auto_analysis


async def show_handball_menu(query):
    keyboard = [
        [InlineKeyboardButton("📅 Matchs du jour", callback_data="handball_today")],
        [InlineKeyboardButton("📈 Analyse & Prédictions", callback_data="handball_analysis")],
        [InlineKeyboardButton("🔔 Alertes Handball", callback_data="handball_alerts")],
        [InlineKeyboardButton("⬅️ Retour", callback_data="open_menu")],
    ]

    await query.edit_message_text(
        "🤾 **RADAR HANDBALL — MODULE PREMIUM**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Sélectionne une option :\n",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


async def handball_today(query):
    events = await fetch_sofa_matches(sport="handball")
    body = format_matches_list(events)
    await query.edit_message_text(
        "📅 **Matchs du jour (Handball)**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"{body}",
        parse_mode="Markdown",
    )


async def handball_analysis(query):
    await query.edit_message_text(
        build_auto_analysis("Handball"),
        parse_mode="Markdown",
    )


async def handball_alerts(query):
    await query.edit_message_text(
        "🔔 **Alertes Handball**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Module en préparation ⚙️",
        parse_mode="Markdown",
    )
