from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from core.sofa_api import fetch_sofa_matches, format_matches_list
from core.analysis import build_auto_analysis


async def show_basket_menu(query):
    keyboard = [
        [InlineKeyboardButton("📅 Matchs du jour", callback_data="basket_today")],
        [InlineKeyboardButton("📈 Analyse & Prédictions", callback_data="basket_analysis")],
        [InlineKeyboardButton("🔔 Alertes Basket", callback_data="basket_alerts")],
        [InlineKeyboardButton("⬅️ Retour", callback_data="open_menu")],
    ]

    await query.edit_message_text(
        "🏀 **RADAR BASKET — MODULE PREMIUM**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Sélectionne une option :\n",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


async def basket_today(query):
    events = await fetch_sofa_matches(sport="basketball")
    body = format_matches_list(events)
    await query.edit_message_text(
        "📅 **Matchs du jour (Basket)**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"{body}",
        parse_mode="Markdown",
    )


async def basket_analysis(query):
    await query.edit_message_text(
        build_auto_analysis("Basketball"),
        parse_mode="Markdown",
    )


async def basket_alerts(query):
    await query.edit_message_text(
        "🔔 **Alertes Basket**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Module en préparation ⚙️",
        parse_mode="Markdown",
    )
