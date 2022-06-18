from tomlkit import key
from config import bot, dp
from aiogram import types, Bot
from database import change_usage_status, get_user_library, change_book_instance_status
from aiogram.dispatcher.filters import Text
from keyboards.keyboard_list import keyboards


def register_settings_handlers() -> None:
    dp.register_callback_query_handler(show_settings_list, Text(startswith="settings"))
    dp.register_callback_query_handler(
        change_user_status, Text(startswith="change_user_status")
    )
    dp.register_callback_query_handler(show_users_library, Text(startswith="library"))
    dp.register_callback_query_handler(
        change_book_status, Text(startswith="change_book_")
    )


async def show_users_library(call: types.CallbackQuery):
    user_books: list = await get_user_library(call.from_user.id)
    message = ""

    if user_books:
        keyboard = types.InlineKeyboardMarkup(one_time_keyboard=True, col=2)
        buttons: list = []
        message = message + "Твої книги:\n"
        item = 0
        for book in user_books:
            message = (
                message
                + f"{item+1}.<b>"
                + book["author"]
                + "</b>: "
                + book["title"]
                + "\n<b>Статус:</b>"
                + book["swap_status"]
                + "\n\n"
            )
            buttons.append(
                types.InlineKeyboardButton(
                    text=f"{item + 1}", callback_data=f"change_book_{book['id']}"
                )
            )
            item = item + 1
        keyboard.add(*buttons)
        keyboard.add(*keyboards["reset_button"])
        message = (
            message
            + "Якщо ти вже обміняв(ла) якусь з книг, можеш змінити її статус за допомогою кнопок знизу."
        )
        await bot.send_message(call.from_user.id, message, reply_markup=keyboard)
    else:
        keyboard = types.InlineKeyboardMarkup(one_time_keyboard=True)
        keyboard.add(*keyboards["reset_button"])
        await bot.send_message(
            call.from_user.id, "В твоїй бібліотеці ще немає книг", reply_markup=keyboard
        )


async def show_settings_list(call: types.CallbackQuery):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(*keyboards["settings_menu"])
    await bot.send_message(
        call.from_user.id,
        "Для того, щоб перестати/почати з'являтись у списках видачі користувачів сервісу, натисніть кнопку під повідомленням",
        reply_markup=keyboard,
    )
    await call.answer()
    print("Zaglushka settings list")


async def change_user_status(call: types.CallbackQuery):
    keyboard = types.InlineKeyboardMarkup(one_time_keyboard=True)
    keyboard.add(*keyboards["reset_button"])
    result = await change_usage_status(call.from_user.id)
    if result:
        keyword = "Активний"
    else:
        keyword = "Не Активний"
    await bot.send_message(
        call.from_user.id,
        f"Чудово, твій статус було змінено на:<b> {keyword}</b>",
        reply_markup=keyboard,
    )


async def change_book_status(call: types.CallbackQuery):
    book_id: int = int(call.data.split("_")[2])
    swap_status: bool = await change_book_instance_status(book_id)
    keyboard = types.InlineKeyboardMarkup(one_time_keyboard=True)
    keyboard.add(*keyboards["reset_button"])
    if swap_status:
        keyword = "Обміняв(ла)"
    else:
        keyword = "Книга в мене"
    await bot.send_message(
        call.from_user.id,
        f"Чудово, статус книги було змінено на:<b> {keyword}</b>",
        reply_markup=keyboard,
    )
