from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔍 По продуктам"), KeyboardButton(text="🎲 Рандом"), KeyboardButton(text="🍰 Сладкое")],
        [KeyboardButton(text="💪 ПП"), KeyboardButton(text="⚡ Быстрое"), KeyboardButton(text="⭐ Избранное")],
        [KeyboardButton(text="📢 Рассылка")],
    ],
    resize_keyboard=True,
)


def recipe_kb(rid, fav):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="💔 Убрать" if fav else "⭐ В избранное", callback_data=f"fav:{rid}"),
        InlineKeyboardButton(text="➡️ Следующий", callback_data="next"),
    ]])


def fav_kb(rid):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="➡️ Следующий", callback_data=f"favnext:{rid}"),
        InlineKeyboardButton(text="💔 Убрать", callback_data=f"fav:{rid}"),
    ]])