import asyncio
import os

from aiogram import Bot
from dotenv import load_dotenv


load_dotenv()


async def main():
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    await bot.set_webhook(
        url="https://myrlil.pythonanywhere.com/webhook",
        secret_token=os.getenv("WEBHOOK_SECRET"),
        drop_pending_updates=True,
        allowed_updates=["message", "callback_query"],
    )
    await bot.session.close()
    print("Вебхук установлен ✅")


asyncio.run(main())