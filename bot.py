import asyncio
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from dotenv import load_dotenv

load_dotenv()
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        f"Привет, огузок {message.from_user.first_name}. "
        "Это общажный бот для рецептов на любой вкус, даже ппшные, даже быстрые и даже без микроволновки."
        )


@dp.message(F.text)
async def echo(message: Message):
    await message.answer(message.text)


@dp.message(F.sticker)
async def sticker_reply(message: Message):
    await message.answer("Нах мне твои стикеры чувак. Иди готовь.")


@dp.message(F.photo)
async def photo_reply(message: Message):
    await message.answer("Маме такое отправляй.")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())