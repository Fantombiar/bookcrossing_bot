from aiogram.dispatcher.filters.state import State, StatesGroup


class CreateBook(StatesGroup):
    wait_for_name = State()
    wait_for_book_choice = State()


class SearchBook(StatesGroup):
    wait_for_name = State()
    wait_to_print = State()


class CreateOwnBook(StatesGroup):
    wait_for_author = State()
    wait_for_name = State()


class CreateUser(StatesGroup):
    waiting_for_full_name = State()
    waiting_for_city = State()
