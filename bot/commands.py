from telegram.ext import CommandHandler, CallbackQueryHandler, CallbackContext
from telegram import Update

# === Commandes simples ===

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Bienvenue sur le Radar V6 !")

def help_cmd(update: Update, context: CallbackContext):
    update.message.reply_text("Liste des commandes disponibles : /start /help")

# === Handlers centralisés ===

def setup_handlers(dispatcher):
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_cmd))

    # Ajoute ici tes futurs handlers :
    # dispatcher.add_handler(CallbackQueryHandler(nba_today, pattern="^nba_today$"))
    # dispatcher.add_handler(CallbackQueryHandler(nba_prediction, pattern="^nba_prediction$"))

