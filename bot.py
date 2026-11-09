import asyncio
import os
import random

from models import load_recipes
from keyboards import main_menu

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from dotenv import load_dotenv


load_dotenv()
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()
recipes = load_recipes()


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        f"Привет, огузок {message.from_user.first_name}. "
        "Это общажный бот для рецептов на любой вкус, даже ппшные, даже быстрые и даже без микроволновки.",
        reply_markup=main_menu,
        )



@dp.message(F.text == "🎲 Рандом")
async def random_recipe(message: Message):
    recipe = random.choice(recipes)
    await message.answer(recipe.beauty_text())


@dp.message(F.text == "💪 ПП")
async def pp_recipe(message: Message):
    pp_recipes = []
    for recipe in recipes:
        if "пп" in recipe.tags or "белковое" in recipe.tags:
            pp_recipes.append(recipe)

    recipe = random.choice(pp_recipes)
    await message.answer(recipe.beauty_text())


@dp.message(F.text == "⚡ Быстрое")
async def fast_recipe(message: Message):
    fast_recipes = []
    for recipe in recipes:
        if "быстрое" in recipe.tags:
            fast_recipes.append(recipe)

    recipe = random.choice(fast_recipes)
    await message.answer(recipe.beauty_text())


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