from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from core.sofa_api import fetch_sofa_matches, format_matches_list
from core.analysis import build_auto_analysis


async def show_foot_menu(query):
    keyboard = [
        [InlineKeyboardButton("📅 Matchs du jour", callback_data="foot_today")],
        [InlineKeyboardButton("📈 Analyse & Prédictions", callback_data="foot_analysis")],
        [InlineKeyboardButton("🔔 Alertes Foot", callback_data="foot_alerts")],
        [InlineKeyboardButton("⬅️ Retour", callback_data="open_menu")],
    ]

    await query.edit_message_text(
        "⚽ **RADAR FOOT — MODULE PREMIUM**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Sélectionne une option :\n",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


async def foot_today(query):
    events = await fetch_sofa_matches(sport="football")
    body = format_matches_list(events)
    await query.edit_message_text(
        "📅 **Matchs du jour (Football)**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"{body}",
        parse_mode="Markdown",
    )


async def foot_analysis(query):
    await query.edit_message_text(
        build_auto_analysis("Football"),
        parse_mode="Markdown",
    )


async def foot_alerts(query):
    await query.edit_message_text(
        "🔔 **Alertes Football**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Module en préparation ⚙️",
        parse_mode="Markdown",
    )
