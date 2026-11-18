from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔍 По продуктам"), KeyboardButton(text="🎲 Рандом"), KeyboardButton(text="🍰 Сладкое")],
        [KeyboardButton(text="💪 ПП"), KeyboardButton(text="⚡ Быстрое"), KeyboardButton(text="⭐ Избранное")],
        [KeyboardButton(text="📢 Рассылка"), KeyboardButton(text="🍳 По технике")]
    ],
    resize_keyboard=True,
)


def nav_kb(rid: str, fav: bool, has_prev: bool = False, has_next: bool = True) -> InlineKeyboardMarkup:
    nav_row = []
    if has_prev:
        nav_row.append(InlineKeyboardButton(text="⬅️ Назад", callback_data="nav:prev"))
    if has_next:
        nav_row.append(InlineKeyboardButton(text="➡️ Вперёд", callback_data="nav:next"))

    rows = []
    if nav_row:
        rows.append(nav_row)
    rows.append([
        InlineKeyboardButton(text="💔 Убрать" if fav else "⭐ В избранное", callback_data=f"fav:{rid}")
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)