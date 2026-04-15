from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram import Update
from core.nba_history import nba_history_model
from core.loader import start, show_main_menu
from menus.tennis import show_tennis_menu, tennis_today, tennis_analysis, tennis_alerts
from menus.foot import show_foot_menu, foot_today, foot_analysis, foot_alerts
from menus.basket import show_basket_menu, basket_today, basket_analysis, basket_alerts
from menus.nba import show_nba_menu, nba_today, nba_analysis, nba_alerts
from menus.handball import show_handball_menu, handball_today, handball_analysis, handball_alerts
from menus.rugby import show_rugby_menu, rugby_today, rugby_analysis, rugby_alerts
from menus.hockey import show_hockey_menu, hockey_today, hockey_analysis, hockey_alerts

TELEGRAM_BOT_TOKEN = "TON_TOKEN_ICI"


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # MENU PRINCIPAL
    if data == "open_menu":
        await show_main_menu(query)

    # TENNIS
    elif data == "menu_tennis":
        await show_tennis_menu(query)
    elif data == "tennis_today":
        await tennis_today(query)
    elif data == "tennis_analysis":
        await tennis_analysis(query)
    elif data == "tennis_alerts":
        await tennis_alerts(query)

    # FOOT
    elif data == "menu_foot":
        await show_foot_menu(query)
    elif data == "foot_today":
        await foot_today(query)
    elif data == "foot_analysis":
        await foot_analysis(query)
    elif data == "foot_alerts":
        await foot_alerts(query)

    # BASKET
    elif data == "menu_basket":
        await show_basket_menu(query)
    elif data == "basket_today":
        await basket_today(query)
    elif data == "basket_analysis":
        await basket_analysis(query)
    elif data == "basket_alerts":
        await basket_alerts(query)

    # NBA
    elif data == "menu_nba":
        await show_nba_menu(query)
    elif data == "nba_today":
        await nba_today(query)
    elif data == "nba_analysis":
        await nba_analysis(query)
    elif data == "nba_alerts":
        await nba_alerts(query)

    # HANDBALL
    elif data == "menu_handball":
        await show_handball_menu(query)
    elif data == "handball_today":
        await handball_today(query)
    elif data == "handball_analysis":
        await handball_analysis(query)
    elif data == "handball_alerts":
        await handball_alerts(query)

    # RUGBY
    elif data == "menu_rugby":
        await show_rugby_menu(query)
    elif data == "rugby_today":
        await rugby_today(query)
    elif data == "rugby_analysis":
        await rugby_analysis(query)
    elif data == "rugby_alerts":
        await rugby_alerts(query)

    # HOCKEY
    elif data == "menu_hockey":
        await show_hockey_menu(query)
    elif data == "hockey_today":
        await hockey_today(query)
    elif data == "hockey_analysis":
        await hockey_analysis(query)
    elif data == "hockey_alerts":
        await hockey_alerts(query)

    # STATS
    elif data == "menu_stats":
        await query.edit_message_text(
            "📊 **STATISTIQUES GLOBALES — MODULE PREMIUM**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "Module en préparation ⚙️",
            parse_mode="Markdown",
        )

    # RETOUR / FERMETURE
    elif data == "back_home":
        await start(update, context)
    elif data == "menu_close":
        await query.edit_message_text("❌ **Menu fermé.**")


def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(menu_handler))

  async def nba_team(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage : /nba_team <team>")
        return
    team = " ".join(context.args)
    res = nba_history_model.get_team_summary(team)
    if not res:
        await update.message.reply_text("Équipe inconnue.")
        return
    await update.message.reply_text(res, parse_mode="Markdown")


async def nba_matchup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Usage : /nba_matchup <home> <away>")
        return
    home = context.args[0]
    away = context.args[1]
    res = nba_history_model.get_matchup_edge(home, away)
    if not res:
        await update.message.reply_text("Matchup introuvable.")
        return
    await update.message.reply_text(res, parse_mode="Markdown")
    
    app.add_handler(CommandHandler("nba_team", nba_team))
    app.add_handler(CommandHandler("nba_matchup", nba_matchup))

    print("Bot lancé…")
    app.run_polling()


if __name__ == "__main__":
    main()
