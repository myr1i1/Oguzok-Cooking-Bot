import asyncio
import os
import random

from models import load_recipes
from keyboards import main_menu

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv


load_dotenv()
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()
recipes = load_recipes()
class Search(StatesGroup):
    waiting_ingredients = State()


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        f"Привет, огузок {message.from_user.first_name}. "
        "Это общажный бот для рецептов на любой вкус, даже ппшные, даже быстрые и даже без микроволновки.",
        reply_markup=main_menu,
        )


@dp.message(F.text == "🔍 По продуктам")
async def ask_ingredients(message: Message, state: FSMContext):
    await state.set_state(Search.waiting_ingredients)
    await message.answer("Че у тебя есть? Пиши через запятую: яйца, сыр, помидоры")


@dp.message(Search.waiting_ingredients, F.text)
async def find_by_ingredients(message: Message, state: FSMContext):
    await state.clear()

    user_ingredients = []
    for item in message.text.split(","):
        user_ingredients.append(item.strip().lower())

    found = []
    for recipe in recipes:
        count = recipe.match(user_ingredients)
        if count > 0:
            found.append((count, recipe))

    if not found:
        await message.answer("Из этого даже я ничего не сварю. Сходи в магаз")
        return

    found.sort(key=lambda pair: pair[0], reverse=True)

    for count, recipe in found[:3]:
        await message.answer(
            f"⊹ Совпало {count} из {len(recipe.ingredients)}\n\n"
            + recipe.beauty_text()
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