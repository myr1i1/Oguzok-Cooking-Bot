import asyncio
import os
import random
from dotenv import load_dotenv

from models import load_recipes
from keyboards import main_menu, recipe_kb, fav_kb, search_kb
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
    waiting_equipment = State()


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
    await message.answer(
        "Че у тебя есть? Пиши через запятую: яйца, сыр, помидоры..."
    )


@dp.message(Search.waiting_ingredients, F.text)
async def find_by_ingredients(message: Message, state: FSMContext):
    user_ingredients = [i.strip().lower() for i in message.text.split(",")]

    found = []
    for recipe in recipes:
        count = recipe.match(user_ingredients)
        if count > 0:
            found.append((count, recipe))

    if not found:
        await state.clear()
        return await message.answer("Из этого даже я ничего не сварю. Сходи в магаз")

    found.sort(key=lambda pair: pair[0], reverse=True)
    pool = [[count, r.id] for count, r in found]
    await state.update_data(pool=pool)
    await state.set_state(None)

    first = found[0]
    r = first[1]
    text = f"⊹ Совпало {first[0]} из {len(r.ingredients)}\n\n" + r.beauty_text()
    await message.answer(text, reply_markup=search_kb(r.id, is_fav(message.from_user.id, r.id)))


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
    if added:
        # добавление — оставляем кнопки, но перерисовываем «Добавить» → «Убрать»
        await cb.message.edit_reply_markup(reply_markup=recipe_kb(rid, True))
    else:
        # удаление — просто убираем кнопки, чтобы не путать с листанием
        await cb.message.edit_reply_markup(reply_markup=None)
    await cb.answer("⭐ Добавлено" if added else "Убрано")

@dp.callback_query(F.data == "next")
async def on_next(cb: CallbackQuery):
    recipe = random.choice(recipes)
    text, kb = with_kb(cb.from_user.id, recipe)
    await cb.message.edit_reply_markup(reply_markup=None)
    await cb.message.answer(text, reply_markup=kb)
    await cb.answer()


@dp.callback_query(F.data.startswith("favnext:"))
async def on_fav_next(cb: CallbackQuery):
    rid = cb.data.split(":", 1)[1]
    ids = get_favs(cb.from_user.id)
    if not ids:
        return await cb.answer("Пусто", show_alert=True)
    idx = ids.index(rid) if rid in ids else -1
    nxt = ids[(idx + 1) % len(ids)]   # зацикливание: после последнего — первый
    r = by_id.get(nxt)
    if not r:
        return await cb.answer("Рецепт не найден", show_alert=True)
    await cb.message.edit_reply_markup(reply_markup=None)   # убрать кнопки у старого
    await cb.message.answer(r.beauty_text(), reply_markup=fav_kb(nxt))
    await cb.answer()


@dp.message(F.text == "⭐ Избранное")
async def show_favs(message: Message):
    ids = get_favs(message.from_user.id)
    if not ids:
        return await message.answer("Пусто. Жми ⭐ под рецептом.")
    r = by_id.get(ids[0])
    if not r:
        return await message.answer("Что-то не нашлось, попробуй ещё раз.")
    await message.answer(r.beauty_text(), reply_markup=fav_kb(ids[0]))


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


@dp.message(F.text == "🍳 По технике")
async def ask_equipment(message: Message, state: FSMContext):
    await state.set_state(Search.waiting_equipment)
    await message.answer(
        "Какие кухонные принадлежности в наличии? Пиши через запятую, выбирая из этих: "
        "сковородка, блендер, духовка, без готовки, микроволновка, кастрюля."
    )


@dp.message(Search.waiting_equipment, F.text)
async def find_by_equipment(message: Message, state: FSMContext):
    user_equipment = [i.strip().lower() for i in message.text.split(",")]

    found = []
    for recipe in recipes:
        count = recipe.match_equipment(user_equipment)
        if count == len(recipe.equipment):
            found.append((count, recipe))

    if not found:
        await state.clear()
        return await message.answer("Ты чето борщишь. Не тот формат.")

    found.sort(key=lambda pair: pair[0], reverse=True)
    pool = [[count, r.id] for count, r in found]

    await state.update_data(pool=pool, search_type="equipment")
    await state.set_state(None)

    count, r = found[0]
    text = r.beauty_text()
    await message.answer(text, reply_markup=search_kb(r.id, is_fav(message.from_user.id, r.id)))


@dp.callback_query(F.data.startswith("srchnext:"))
async def on_srch_next(cb: CallbackQuery, state: FSMContext):
    rid = cb.data.split(":", 1)[1]
    data = await state.get_data()
    pool = data.get("pool", [])

    if not pool:
        return await cb.answer("Список устарел, начни поиск заново", show_alert=True)

    ids = [item[1] for item in pool]
    idx = ids.index(rid) if rid in ids else -1
    next_idx = (idx + 1) % len(pool)

    count, nxt = pool[next_idx]
    r = by_id.get(nxt)
    if not r:
        return await cb.answer("Рецепт не найден", show_alert=True)

    text = r.beauty_text()
    if data.get("search_type") != "equipment":
        text = f"⊹ Совпало {count} из {len(r.ingredients)}\n\n" + text

    await cb.message.edit_reply_markup(reply_markup=None)
    await cb.message.answer(text, reply_markup=search_kb(nxt, is_fav(cb.from_user.id, nxt)))
    await cb.answer()


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