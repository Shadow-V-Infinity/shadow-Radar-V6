import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("🤖 Initialisation du noyau IA…")

    frames = [
        "🤖 Initialisation du noyau IA…\n\n🔹 Boot du système quantique",
        "🤖 Initialisation du noyau IA…\n\n🔹 Boot du système quantique\n🔹 Calibration neuronale",
        "🤖 Initialisation du noyau IA…\n\n🔹 Boot du système quantique\n🔹 Calibration neuronale\n🔹 Synchronisation des modules",
        "🤖 Initialisation du noyau IA…\n\n🔹 Boot du système quantique\n🔹 Calibration neuronale\n🔹 Synchronisation des modules\n🔹 Activation du radar cognitif",
        "🤖 Initialisation du noyau IA…\n\n🔹 Boot du système quantique\n🔹 Calibration neuronale\n🔹 Synchronisation des modules\n🔹 Activation du radar cognitif\n🔹 Ouverture de l’interface holographique",
    ]

    for frame in frames:
        await msg.edit_text(frame)
        await asyncio.sleep(0.35)

    keyboard = [
        [InlineKeyboardButton("🚀 Entrer dans le Système", callback_data="open_menu")]
    ]

    await msg.edit_text(
        "🌑 **SHΛDOW RΛDΛR V6 — IA ONLINE**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Modules synchronisés.\n"
        "Interface holographique opérationnelle.\n"
        "Bienvenue Gaël.\n\n"
        "Prêt pour l’analyse prédictive ? 🔥",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


async def show_main_menu(query):
    keyboard = [
        [InlineKeyboardButton("🎾 Tennis", callback_data="menu_tennis")],
        [InlineKeyboardButton("⚽ Football", callback_data="menu_foot")],
        [InlineKeyboardButton("🏀 Basket", callback_data="menu_basket")],
        [InlineKeyboardButton("🟦 NBA", callback_data="menu_nba")],
        [InlineKeyboardButton("🤾 Handball", callback_data="menu_handball")],
        [InlineKeyboardButton("🏉 Rugby", callback_data="menu_rugby")],
        [InlineKeyboardButton("🏒 Hockey", callback_data="menu_hockey")],
        [InlineKeyboardButton("📊 Statistiques Globales", callback_data="menu_stats")],
        [InlineKeyboardButton("⬅️ Retour à l’Accueil", callback_data="back_home")],
        [InlineKeyboardButton("❌ Fermer le Menu", callback_data="menu_close")],
    ]

    await query.edit_message_text(
        "📟 **SHΛDOW MENU — MODE PREMIUM**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Sélectionne ton module :\n",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )
