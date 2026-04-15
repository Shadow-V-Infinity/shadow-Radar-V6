import asyncio
from telegram import Bot

async def main():
    bot = Bot(token="8732193712:AAFhqteo75X4mUSZQ_jM0RfGV2qptUxyuYk")
    print("🔵 Tentative de connexion...")
    me = await bot.get_me()
    print(f"🟢 Connexion réussie ! Bot : {me.first_name}")

if __name__ == "__main__":
    asyncio.run(main())
