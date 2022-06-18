from aiogram import types
from models import User
from config import dp, bot
from fsmhandlers.fsmachines import CreateUser
from aiogram.dispatcher import FSMContext


def register_user_handlers() -> None:
    dp.register_message_handler(ChooseUserCity, state=CreateUser.waiting_for_full_name)
    dp.register_message_handler(UserCityChosen, state=CreateUser.waiting_for_city)


async def ChooseUserName(call_message) -> None:
    await CreateUser.waiting_for_full_name.set()
    await bot.send_message(
        call_message.from_user.id,
        f"Вітаю в боті для буккросингу! \nДля подальшого користування ботом потрібно зареєструватися \nБудь ласка введи своє ім'я",
    )


# @dp.message_handler(state=CreateUser.waiting_for_full_name)
async def ChooseUserCity(message: types.Message, state: FSMContext) -> None:
    # Перевіряю чи юзер не ввів пусте ім'я, або ім'я, яке містить цифри
    if message.text is None or any(map(str.isdigit, message.text)):
        await message.answer(
            "Будь ласка не залишайте ім'я пустим та не використовуйте числа"
        )
        return
    await state.update_data(chosen_name=message.text.lower().capitalize())

    # Переходжу в стан очікування на назву міста
    await CreateUser.next()
    await message.reply("Будь ласка введи назву свого міста")


# @dp.message_handler(state=CreateUser.waiting_for_city)
async def UserCityChosen(message: types.Message, state: FSMContext) -> None:
    if message.text is None or any(map(str.isdigit, message.text)):
        await message.answer(
            "Будь ласка не залишай назву міста пустим та не використовуй числа"
        )
        return
    await state.update_data(chosen_city=message.text.lower().capitalize())
    user_init_data = await state.get_data()
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(types.KeyboardButton(text="Повернутись до початку"))
    await message.answer(
        f"Твоє ім'я: <b>{user_init_data['chosen_name']}</b> , і ти з міста <b>{user_init_data['chosen_city']}</b>",
        reply_markup=keyboard,
    )
    await User.create(
        user_id=message.from_user.id,
        username=user_init_data["chosen_name"],
        city=user_init_data["chosen_city"],
    )
    await state.finish()
