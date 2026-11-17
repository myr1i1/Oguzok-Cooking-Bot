import asyncio
import os
import random
from dotenv import load_dotenv

from models import load_recipes
from keyboards import main_menu, recipe_kb
from storage import is_fav, toggle_fav, get_favs, remember_user, all_user_ids

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.client.session.aiohttp import AiohttpSession


load_dotenv()
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

proxy = os.getenv("PROXY")
if proxy:
    session = AiohttpSession(proxy=proxy)
else:
    session = None
bot = Bot(token=os.getenv("BOT_TOKEN"), session=session)

dp = Dispatcher()
recipes = load_recipes()

by_id = {r.id: r for r in recipes}
def with_kb(uid, recipe):
    return recipe.beauty_text(), recipe_kb(recipe.id, is_fav(uid, recipe.id))


class Search(StatesGroup):
    waiting_ingredients = State()


class Broadcast(StatesGroup):
    waiting_text = State()


@dp.message(CommandStart())
async def start(message: Message):
    remember_user(message.from_user.id, message.from_user.first_name, message.from_user.username)
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
        text, kb = with_kb(message.from_user.id, recipe)
        await message.answer(
        f"⊹ Совпало {count} из {len(recipe.ingredients)}\n\n" + text,
        reply_markup=kb,
    )


@dp.message(F.text == "🎲 Рандом")
async def random_recipe(message: Message):
    recipe = random.choice(recipes)
    text, kb = with_kb(message.from_user.id, recipe)
    await message.answer(text, reply_markup=kb)


@dp.message(F.text == "💪 ПП")
async def pp_recipe(message: Message):
    pp_recipes = []
    for recipe in recipes:
        if "пп" in recipe.tags or "белковое" in recipe.tags:
            pp_recipes.append(recipe)

    recipe = random.choice(pp_recipes)
    text, kb = with_kb(message.from_user.id, recipe)
    await message.answer(text, reply_markup=kb)


@dp.message(F.text == "🍰 Сладкое")
async def sweet_recipe(message: Message):
    sweet_recipes = []
    for recipe in recipes:
        if "сладкое" in recipe.tags:
            sweet_recipes.append(recipe)

    recipe = random.choice(sweet_recipes)
    text, kb = with_kb(message.from_user.id, recipe)
    await message.answer(text, reply_markup=kb)


@dp.message(F.text == "⚡ Быстрое")
async def fast_recipe(message: Message):
    fast_recipes = []
    for recipe in recipes:
        if "быстрое" in recipe.tags:
            fast_recipes.append(recipe)

    recipe = random.choice(fast_recipes)
    text, kb = with_kb(message.from_user.id, recipe)
    await message.answer(text, reply_markup=kb)


@dp.callback_query(F.data.startswith("fav:"))
async def on_fav(cb: CallbackQuery):
    rid = cb.data.split(":", 1)[1]
    added = toggle_fav(cb.from_user.id, rid)
    await cb.message.edit_reply_markup(reply_markup=recipe_kb(rid, is_fav(cb.from_user.id, rid)))
    await cb.answer("⭐ Добавлено" if added else "Убрано")

@dp.callback_query(F.data == "next")
async def on_next(cb: CallbackQuery):
    recipe = random.choice(recipes)
    text, kb = with_kb(cb.from_user.id, recipe)
    await cb.message.edit_reply_markup(reply_markup=None)
    await cb.message.answer(text, reply_markup=kb)
    await cb.answer()

@dp.message(F.text == "⭐ Избранное")
async def show_favs(message: Message):
    ids = get_favs(message.from_user.id)
    if not ids:
        return await message.answer("Пусто. Жми ⭐ под рецептом.")
    for rid in ids:
        r = by_id.get(rid)
        if r: await message.answer(r.beauty_text(), reply_markup=recipe_kb(rid, True))


@dp.message(F.text == "📢 Рассылка")
async def ask_broadcast(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("Тише, тише, братан. Эта кнопка не для тебя 👀")
    await state.set_state(Broadcast.waiting_text)
    await message.answer("Пиши текст рассылки. Он уйдёт всем, кто хоть раз делал /start.")


@dp.message(Broadcast.waiting_text, F.text)
async def do_broadcast(message: Message, state: FSMContext):
    await state.clear()
    text = message.text
    sent = failed = 0
    for uid in all_user_ids():
        try:
            await message.bot.send_message(int(uid), text)
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)
    await message.answer(f"✅ Отправлено: {sent}\n❌ Не дошло: {failed}")


@dp.message(F.text)
async def echo(message: Message):
    await message.answer("Эм, не понял. Жми кнопки в меню 👇", reply_markup=main_menu)


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