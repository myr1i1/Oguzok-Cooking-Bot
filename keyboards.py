from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔍 По продуктам"), KeyboardButton(text="🎲 Рандом")],
        [KeyboardButton(text="💪 ПП"), KeyboardButton(text="⚡ Быстрое")],
    ],
    resize_keyboard=True,
)