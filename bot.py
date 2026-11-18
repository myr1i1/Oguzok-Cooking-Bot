# bot.py
import asyncio
import os
import random
from dotenv import load_dotenv

from models import load_recipes
from keyboards import main_menu, nav_kb
from storage import is_fav, toggle_fav, get_favs, remember_user, all_user_ids

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.exceptions import TelegramBadRequest


load_dotenv()
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

proxy = os.getenv("PROXY")
session = AiohttpSession(proxy=proxy) if proxy else None
bot = Bot(token=os.getenv("BOT_TOKEN"), session=session)

dp = Dispatcher()
recipes = load_recipes()
by_id = {r.id: r for r in recipes}


class Search(StatesGroup):
    waiting_ingredients = State()
    waiting_equipment = State()


class Broadcast(StatesGroup):
    waiting_text = State()


def get_category_pool(category: str) -> list[str]:
    if category == "pp":
        return [r.id for r in recipes if "пп" in r.tags or "белковое" in r.tags]
    if category == "sweet":
        return [r.id for r in recipes if "сладкое" in r.tags]
    if category == "fast":
        return [r.id for r in recipes if "быстрое" in r.tags]
    return [r.id for r in recipes]


def render_card(uid: int, data: dict):
    """Собирает текст и клавиатуру для текущего индекса в FSM."""
    mode = data.get("mode")
    history = data.get("history", [])
    idx = data.get("idx", 0)
    matches_map = data.get("matches", {})

    rid = history[idx]
    r = by_id[rid]
    text = r.beauty_text()

    if mode == "ingredients" and rid in matches_map:
        text = f"⊹ Совпало {matches_map[rid]} из {len(r.ingredients)}\n\n" + text

    has_prev = idx > 0
    if mode in ("random", "pp", "sweet", "fast"):
        # В категориях вперед можно листать всегда, пока есть больше 1 рецепта
        has_next = len(get_category_pool(mode)) > 1
    else:
        # В поиске и избранном идем по списку history
        has_next = idx < len(history) - 1

    kb = nav_kb(rid, is_fav(uid, rid), has_prev=has_prev, has_next=has_next)
    return text, kb


async def start_browsing(message: Message, state: FSMContext, mode: str, pool_ids: list[str], matches: dict | None = None):
    """Запускает просмотр раздела новым сообщением."""
    if mode in ("random", "pp", "sweet", "fast"):
        first_id = random.choice(pool_ids)
        history = [first_id]
    else:
        history = list(pool_ids)

    data = {
        "mode": mode,
        "history": history,
        "idx": 0,
        "matches": matches or {},
    }
    await state.set_state(None)
    await state.set_data(data)

    text, kb = render_card(message.from_user.id, data)
    await message.answer(text, reply_markup=kb)


@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    remember_user(message.from_user.id, message.from_user.first_name, message.from_user.username)
    await message.answer(
        f"Привет, огузок {message.from_user.first_name}. "
        "Это общажный бот для рецептов на любой вкус, даже ппшные, даже быстрые и даже без микроволновки.",
        reply_markup=main_menu,
    )


@dp.message(F.text == "🎲 Рандом")
async def random_recipe(message: Message, state: FSMContext):
    await start_browsing(message, state, "random", get_category_pool("random"))


@dp.message(F.text == "💪 ПП")
async def pp_recipe(message: Message, state: FSMContext):
    await start_browsing(message, state, "pp", get_category_pool("pp"))


@dp.message(F.text == "🍰 Сладкое")
async def sweet_recipe(message: Message, state: FSMContext):
    await start_browsing(message, state, "sweet", get_category_pool("sweet"))


@dp.message(F.text == "⚡ Быстрое")
async def fast_recipe(message: Message, state: FSMContext):
    await start_browsing(message, state, "fast", get_category_pool("fast"))


@dp.message(F.text == "⭐ Избранное")
async def show_favs(message: Message, state: FSMContext):
    ids = [rid for rid in get_favs(message.from_user.id) if rid in by_id]
    if not ids:
        return await message.answer("Пусто. Жми ⭐ под рецептом.")
    await start_browsing(message, state, "favs", ids)


@dp.message(F.text == "🔍 По продуктам")
async def ask_ingredients(message: Message, state: FSMContext):
    await state.set_state(Search.waiting_ingredients)
    await message.answer("Че у тебя есть? Пиши через запятую: яйца, сыр, помидоры...")


@dp.message(Search.waiting_ingredients, F.text)
async def find_by_ingredients(message: Message, state: FSMContext):
    user_ingredients = [i.strip().lower() for i in message.text.split(",") if i.strip()]
    found = []
    for recipe in recipes:
        count = recipe.match(user_ingredients)
        if count > 0:
            found.append((count, recipe))

    if not found:
        await state.clear()
        return await message.answer("Из этого даже я ничего не сварю. Сходи в магаз")

    found.sort(key=lambda pair: pair[0], reverse=True)
    pool_ids = [r.id for _, r in found]
    matches = {r.id: count for count, r in found}
    await start_browsing(message, state, "ingredients", pool_ids, matches=matches)


@dp.message(F.text == "🍳 По технике")
async def ask_equipment(message: Message, state: FSMContext):
    await state.set_state(Search.waiting_equipment)
    await message.answer(
        "Какие кухонные принадлежности в наличии? Пиши через запятую, выбирая из этих: "
        "сковородка, блендер, духовка, без готовки, микроволновка, кастрюля."
    )


@dp.message(Search.waiting_equipment, F.text)
async def find_by_equipment(message: Message, state: FSMContext):
    user_equipment = [i.strip().lower() for i in message.text.split(",") if i.strip()]
    found = [
        r for r in recipes
        if r.match_equipment(user_equipment) == len(r.equipment)
    ]

    if not found:
        await state.clear()
        return await message.answer("Ты чето борщишь. Не тот формат.")

    await start_browsing(message, state, "equipment", [r.id for r in found])


@dp.callback_query(F.data.startswith("nav:"))
async def on_navigate(cb: CallbackQuery, state: FSMContext):
    direction = cb.data.split(":", 1)[1]
    data = await state.get_data()
    mode = data.get("mode")
    history = list(data.get("history", []))
    idx = data.get("idx", 0)

    if not mode or not history:
        return await cb.answer("Список устарел, выбери раздел в меню заново", show_alert=True)

    if direction == "prev":
        if idx <= 0:
            return await cb.answer("Это первый рецепт")
        idx -= 1
    elif direction == "next":
        if idx < len(history) - 1:
            idx += 1
        elif mode in ("random", "pp", "sweet", "fast"):
            pool = get_category_pool(mode)
            unseen = [rid for rid in pool if rid not in history]
            if unseen:
                nxt = random.choice(unseen)
            else:
                candidates = [rid for rid in pool if rid != history[-1]] or pool
                nxt = random.choice(candidates)
            history.append(nxt)
            idx += 1
        else:
            return await cb.answer("Это последний рецепт")

    data["history"] = history
    data["idx"] = idx
    await state.set_data(data)

    text, kb = render_card(cb.from_user.id, data)
    try:
        await cb.message.edit_text(text, reply_markup=kb)
    except TelegramBadRequest:
        pass
    await cb.answer()


@dp.callback_query(F.data.startswith("fav:"))
async def on_fav(cb: CallbackQuery, state: FSMContext):
    rid = cb.data.split(":", 1)[1]
    added = toggle_fav(cb.from_user.id, rid)
    data = await state.get_data()
    mode = data.get("mode")
    history = list(data.get("history", []))
    idx = data.get("idx", 0)

    # Если удалили рецепт прямо внутри раздела «Избранное» — убираем его из текущего списка
    if mode == "favs" and not added and rid in history:
        history.remove(rid)
        if not history:
            await state.clear()
            await cb.message.edit_text("В избранном больше ничего не осталось. Жми ⭐ под рецептом.")
            return await cb.answer("Убрано")
        idx = min(idx, len(history) - 1)
        data["history"] = history
        data["idx"] = idx
        await state.set_data(data)
        text, kb = render_card(cb.from_user.id, data)
        await cb.message.edit_text(text, reply_markup=kb)
        return await cb.answer("Убрано")

    # В остальных режимах просто обновляем кнопку «В избранное» / «Убрать»
    if history and 0 <= idx < len(history) and history[idx] == rid:
        _, kb = render_card(cb.from_user.id, data)
        await cb.message.edit_reply_markup(reply_markup=kb)
    else:
        await cb.message.edit_reply_markup(reply_markup=nav_kb(rid, added, has_prev=False, has_next=False))

    await cb.answer("⭐ Добавлено" if added else "Убрано")


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