import json
import requests
import cv2
import os
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram import types, Bot
from aiogram.types.message import ContentType
from models import Book, Library, User
from pyzbar import pyzbar
from pathlib import Path
from database import (
    get_all_books,
    get_book_to_user_data,
    get_filterred_book_user_list,
)
from pprint import pprint
from config import image_folder_path, bot, dp, list_limiter
from keyboards.keyboard_list import keyboards
from fsmhandlers.fsmachines import CreateBook, CreateOwnBook

user_data = {}


def register_book_handlers() -> None:
    dp.register_callback_query_handler(
        print_all_books, Text(startswith="list_books"), state="*"
    )
    dp.register_callback_query_handler(self_add_book, Text(startswith="book_self_add"))
    dp.register_callback_query_handler(book_search_choice, Text(startswith="book_"))
    dp.register_callback_query_handler(search_option_choice, Text(startswith="search_"))
    dp.register_message_handler(
        processing_book_name,
        state=CreateBook.wait_for_name,
    )
    dp.register_message_handler(
        processing_book_name,
        state=CreateBook.wait_for_name,
    )
    dp.register_message_handler(photo_code_scan, content_types=ContentType.PHOTO)
    dp.register_callback_query_handler(
        no_book_found,
        Text(startswith="search_failure"),
        state=CreateBook.wait_for_book_choice,
    )
    dp.register_callback_query_handler(
        add_book_to_database,
        state=CreateBook.wait_for_book_choice,
    )
    dp.register_message_handler(get_book_title, state=CreateOwnBook.wait_for_author)
    dp.register_message_handler(processing_own_book, state=CreateOwnBook.wait_for_name)


async def book_search_choice(call: types.CallbackQuery) -> None:
    action = call.data.split("_")[1]
    keyboard = types.InlineKeyboardMarkup(one_time_keyboard=True)
    keyboard.add(*keyboards["search_menu"])
    keyboard.add(*keyboards["book_self_add"])
    if action == "add":
        user_data[call.from_user.id, "search_goal"] = "add"
        await bot.send_message(
            call.from_user.id,
            f"Для того, щоб додати до своєї бібліотеки книгу можеш просто надіслати фото коду ззаду книги. Також доступний пошук по назві книги та автору.",
            reply_markup=keyboard,
        )
    elif action == "search":
        user_data[call.from_user.id, "search_goal"] = "search"
        await bot.send_message(
            call.from_user.id,
            f"Для того, щоб знайти книгу в нашій бібліотеці вибери критерій пошуку знизу. Також можеш подивитися список усіх доступних книг повернувшись до первинного меню.",
            reply_markup=keyboard,
        )
    await call.answer()


async def search_option_choice(call: types.CallbackQuery) -> None:
    action = call.data.split("_")[1]
    if user_data[call.from_user.id, "search_goal"] == "add":
        await CreateBook.wait_for_name.set()
    elif user_data[call.from_user.id, "search_goal"] == "search":
        await CreateBook.wait_for_name.set()
    if action == "author":
        user_data[call.from_user.id, "request_type"] = "inauthor"
        filler = "автора книги"
    elif action == "title":
        user_data[call.from_user.id, "request_type"] = "intitle"
        filler = "назву книги"
    await bot.send_message(
        call.from_user.id,
        f"Зрозумів, тепер будь ласка надішли мені {filler}:)",
    )
    await call.answer()


async def processing_book_name(message: types.Message, state: FSMContext) -> None:
    received_text: str = message.text
    if user_data[message.from_user.id, "request_type"]:
        if user_data[message.from_user.id, "search_goal"] == "add":
            book_data: json = await google_api_request(
                message.text, user_data[message.from_user.id, "request_type"]
            )
            await CreateBook.next()
            await state.update_data(books_list=book_data)
            await show_google_search_results(message, book_data)
        elif user_data[message.from_user.id, "search_goal"] == "search":
            await state.finish()
            book_data = await get_filterred_book_user_list(
                user_data[message.from_user.id, "request_type"], received_text
            )
            await print_books(message, book_data)
        user_data[message.from_user.id, "request_type"] = None
    else:
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(*keyboards["initial_menu"])
        await message.reply(
            f"Я отримав: <b>{received_text}</b>. Будь ласка вибери тип пошуку, бо я заплутався"
        )


async def google_api_request(request_data, request_type) -> json:
    response: requests.Response = requests.get(
        f"https://www.googleapis.com/books/v1/volumes?q={request_data}+{request_type}:{request_data}&key={os.environ.get('GOOGLE_BOOKS_API')}",
    )
    if response.status_code == 200:
        print("sucessfully fetched the data with parameters provided")
        # pprint(response.json())
        # pprint(response.json()["items"][0]["volumeInfo"]["title"])
    else:
        print(f"Hello person, there's a {response.status_code} error with your request")
    return response.json()


async def show_google_search_results(message, book_data: json):
    if book_data["totalItems"] == 0:
        await CreateBook.wait_for_name.set()  # Повертаємося до етапу пошуку книги
        user_data[message.from_user.id, "request_type"] = "title"
        await message.answer(
            f"На жаль цієї книги не знайшлося в нашій базі даних... Давай спробуємо знайти по назві...",
        )
    else:
        counter = 0
        keyboard = types.InlineKeyboardMarkup(one_time_keyboard=True, col=2)
        buttons: list = []
        message_text: str = ""
        for item in range(book_data["totalItems"]):
            counter += 1
            # Додаю кнопку для вибору конкретної книги зі списку до клавіатури
            buttons.append(
                types.InlineKeyboardButton(
                    text=f"{item + 1}", callback_data=f"book_item_{item}"
                )
            )
            # Просто виводжу назви книг
            if "authors" in book_data["items"][item]["volumeInfo"]:
                book_author: str = book_data["items"][item]["volumeInfo"]["authors"][0]
            else:
                book_author: str = "Автор не відомий"
            book_title: str = book_data["items"][item]["volumeInfo"]["title"]
            message_text = (
                message_text
                + f"\n\n{item+1}. Автор: {book_author} \nНазва книги: {book_title}"
            )
            if item + 1 == list_limiter:
                break
        pprint(book_data)
        await message.answer(message_text)
        keyboard.add(*buttons)
        keyboard.add(
            types.InlineKeyboardButton("Жодну", callback_data="search_failure")
        )
        await message.answer("Яку книгу додати до бібліотеки?", reply_markup=keyboard)
        print("Code is still executable after printing the books")


async def photo_code_scan(message: types.Message):
    user_data[message.from_user.id, "request_type"] = "isbn"
    print(type(message.photo[0]))

    # Завантажую картинку потрібного розміру на пк та отримую її адресу
    file = await bot.get_file(message.photo[3].file_id)
    file_path = file.file_path
    await bot.download_file(file_path, destination_dir=image_folder_path)

    # Виклик функції декодування картинки. На вхід отримує адресу картинки
    isbn_code: int = await isbn_decode(image_folder_path + "/" + file_path)
    if isbn_code:
        # await message.reply(f"Фоточку отримано! \n Код:{isbn_code}")
        book_data = await google_api_request(isbn_code, "isbn")
        user_data[message.from_user.id, "request_type"] = None
        await show_google_search_results(message, book_data)
    else:
        await message.reply(
            "На жаль, не вийшло розпізнати код, спробуйте будь ласка інше фото."
        )


async def isbn_decode(image: Path) -> int:
    # decodes all barcodes from an image
    im = cv2.imread(image)
    print("Image type:", image)
    print("Converted im type:", im)
    decoded_objects: list = pyzbar.decode(im)
    if decoded_objects:
        for obj in decoded_objects:
            # draw the barcode
            print("detected barcode:", obj)
            # print barcode type & data
            print("Type:", obj.type)
            print("Data:", obj.data)
            # Так як на фото може бути кілька barcode'ів, наказую програмі зупинитися на тому, що має код EAN13, бо такий притаманний книгам
            if obj.type == "EAN13":
                break
    # забираю усі нечисельні символи з рядка
    numeric_filter: str = filter(str.isdigit, str(obj.data))
    numeric_string: str = "".join(numeric_filter)
    return int(numeric_string)


async def add_book_to_database(call: types.CallbackQuery, state: FSMContext):
    print("Tried to add the book to database")
    books_list: json = await state.get_data()
    book_number: int = int(call.data.split("_")[2])
    pprint(books_list)
    await state.finish()
    isbn = None
    if "authors" in books_list["books_list"]["items"][book_number]["volumeInfo"]:
        author: str = books_list["books_list"]["items"][book_number]["volumeInfo"][
            "authors"
        ][0]
    else:
        author: str = "Автор не відомий"
    title: str = books_list["books_list"]["items"][book_number]["volumeInfo"]["title"]
    if (
        "industryIdentifiers"
        in books_list["books_list"]["items"][book_number]["volumeInfo"]
    ):
        # Sometimes isbn code consists of non-numerical values, so I have to filter these
        isbn_string = books_list["books_list"]["items"][book_number]["volumeInfo"][
            "industryIdentifiers"
        ][0]["identifier"]
        numeric_filter = filter(str.isdigit, isbn_string)
        isbn = int("".join(numeric_filter))

    book = await Book.create(book_author=author, book_title=title, isbn_code=isbn)
    await Library.create(book=book, user_id=call.from_user.id)
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(*keyboards["reset_button"])
    await bot.send_message(
        call.from_user.id, "Книжку додано до твоєї бібліотеки!", reply_markup=keyboard
    )
    await call.answer()


async def no_book_found(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    await bot.send_message(
        call.from_user.id,
        "Будь ласка спробуй ввести назву книги по-іншому",
        reply_markup=keyboard.add(*keyboards["search_menu"]),
    )


async def print_all_books(call: types.CallbackQuery):
    book_data = await get_all_books(call.from_user.id)
    await print_books(call, book_data)
    await call.answer()


async def print_books(message_call, book_data):
    message: str = "<b>Ось список усіх доступних книг на даний момент:</b>\n\n"
    amount_of_books: int = len(book_data)
    printed_books: int = 0
    iterations_counter: int = 0
    message_checker = False
    while printed_books < amount_of_books:
        # To avoid too long messages I've decided to split each of them by 10 books in each.
        for book in book_data[printed_books : printed_books + list_limiter]:
            owners = await get_book_to_user_data(book.id)
            message = (
                message + "<b>" + book.book_author + "</b>-  " + book.book_title + "\n"
            )
            for owner in owners:
                message = (
                    message
                    + "Власник: "
                    + owner["username"]
                    + "\nTag: @"
                    + message_call.from_user.username
                    + "\nЗ міста: "
                    + owner["city"]
                    + "\n"
                )
            iterations_counter = iterations_counter + 1
            print("Iteration: ", iterations_counter)
            if iterations_counter == list_limiter:
                break
        if message != "":
            await bot.send_message(message_call.from_user.id, message)
            message_checker = True
        message = ""
        printed_books = printed_books + iterations_counter
        iterations_counter = 0
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(*keyboards["reset_button"])
    if message_checker:
        await bot.send_message(
            message_call.from_user.id,
            "Нагадуємо, комунікація з власниками книг має відбуватися на паритетних умовах",
            reply_markup=keyboard,
        )
    else:
        await bot.send_message(
            message_call.from_user.id,
            "На жаль, зараз доступних книг немає. Запросіть своїх друзів, щоб вірогідність обміну була вища:)",
            reply_markup=keyboard,
        )


async def self_add_book(call):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(*keyboards["reset_button"])
    await CreateOwnBook.wait_for_author.set()
    await bot.send_message(
        call.from_user.id, "Будь ласка введи автора книги", reply_markup=keyboard
    )


async def get_book_title(message: types.Message, state: FSMContext):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(*keyboards["reset_button"])
    if message.text is None or any(map(str.isdigit, message.text)):
        await message.answer(
            "Будь ласка не залишай ім'я пустим та не використовуйте числа"
        )
        return
    await CreateOwnBook.next()
    await state.update_data(author=message.text.lower().capitalize())
    await message.reply("Тепер будь ласка надішли назву книги.", reply_markup=keyboard)


async def processing_own_book(message: types.Message, state: FSMContext):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(*keyboards["reset_button"])
    if message.text is None:
        await message.answer("Будь ласка не залишай назву книги пустою")
        return
    await state.update_data(title=message.text)
    book_init_data: dict = await state.get_data()
    book = await Book.create(
        book_author=book_init_data["author"],
        book_title=book_init_data["title"],
        isbn_code=None,
    )
    await Library.create(book=book, user_id=message.from_user.id)
    await message.answer(
        f"Чудово, книгу було додано до твоєї бібліотеки!\nАвтор книги: <b>{book_init_data['author']}</b> \nНазва:<b> {book_init_data['title']}</b>",
        reply_markup=keyboard,
    )
