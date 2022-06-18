from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from emoji import emojize

keyboards = {
    "initial_menu": [
        InlineKeyboardButton(
            text=emojize("Додати в свою бібліотеку :blue_book:"),
            callback_data="book_add",
        ),
        InlineKeyboardButton(
            text=emojize("Знайти книгу в базі:books:"), callback_data="book_search"
        ),
        InlineKeyboardButton(
            text=emojize("Вивести усі :books:"), callback_data="list_books"
        ),
        InlineKeyboardButton(
            text=emojize("Мої налаштування :gear:"), callback_data="settings"
        ),
        InlineKeyboardButton(
            text=emojize("Моя біблотека :notebook_with_decorative_cover:"),
            callback_data="library",
        ),
    ],
    "search_menu": [
        InlineKeyboardButton(text="Шукати по назві", callback_data="search_title"),
        InlineKeyboardButton(text="Шукати по автору", callback_data="search_author"),
    ],
    "reset_button": [
        InlineKeyboardButton(text="Повернутись в початок", callback_data="reset")
    ],
    "settings_menu": [
        InlineKeyboardButton(
            text="Перестати/Почати отримувати пропозиції обміну",
            callback_data="change_user_status",
        )
    ],
    "book_self_add": [
        InlineKeyboardButton(text="Додати вручну", callback_data="book_self_add")
    ],
}
