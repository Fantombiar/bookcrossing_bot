from genericpath import exists
from aiogram import Bot, Dispatcher, executor, types
from pprint import pprint
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext
from pprint import pprint
import database
import config
from models import User, Book, Library
from config import dp, bot
from keyboards.keyboard_list import keyboards
from fsmhandlers.book_search import register_book_handlers
from fsmhandlers.user_settings import register_settings_handlers
from fsmhandlers.createuser import ChooseUserName, register_user_handlers

user_data = {}


async def on_startup(_):
    await set_default_commands()
    await database.init()
    # Створюю хендлери у файлі create user, передаю туди dp, щоб не робити круговий імпорт.
    register_user_handlers()
    register_settings_handlers()
    register_book_handlers()


async def set_default_commands() -> None:
    await dp.bot.set_my_commands([types.BotCommand("start", "Запустити бота")])


@dp.message_handler(commands="start", state="*")
async def cmd_start(call_message) -> None:
    # I have to add an "if" statement so previous users wouldn't need to register again.
    if await database.check_user_existance(user_id=call_message.from_user.id):
        # Тут відбувається перехід в Finite State Machine, в якій збираються дані про юзера. Хендлери в папці fsmhandlers, createuser.py
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        await bot.send_message(
            call_message.from_user.id,
            "Вітаю! Будь ласка вибери, що саме тебе цікавить в меню знизу\nАбо ж якщо хочеш додати книгу через код ззаду, можеш одразу надіслати фото сюди.",
            reply_markup=keyboard.add(*keyboards["initial_menu"]),
        )
    else:
        await ChooseUserName(call_message)
    # await message.answer("Great, you've been registered!")


@dp.callback_query_handler(Text(startswith="reset"), state="*")
async def back_to_start_meny(call: types.CallbackQuery, state=FSMContext):
    await state.finish()
    await call.answer()
    await cmd_start(call)


async def shutdown(dispatcher: Dispatcher):
    await database.shutdown()


if __name__ == "__main__":
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
