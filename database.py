from array import array
from ast import And
from typing import Dict, List
from tortoise import Tortoise
from tortoise.models import Model
from tortoise.expressions import Q
from tortoise.query_utils import Prefetch
from config import DATABASE_CONFIG
from models import User, Library, Book


async def init():
    # Init database connectio
    await Tortoise.init(config=DATABASE_CONFIG)
    # Generate the Schemas
    await Tortoise.generate_schemas()
    print("Successfully connected")


async def shutdown():
    await Tortoise.connections.close_all()


async def get_book_to_user_data(book_id) -> list:
    book_instances: list = (
        await Library.all().prefetch_related("user", "book").filter(book=book_id)
    )
    # users_ids = await Library.filter(book=books)
    owners: list = []
    owner: dict = {}
    for book in range(len(book_instances)):
        if book_instances[book].user.is_active:
            print(book_instances[book].user.username)
            owner["username"] = book_instances[book].user.username
            owner["id"] = book_instances[book].user.user_id
            owner["city"] = book_instances[book].user.city
            owners.append(owner)
            owner = {}
    return owners


async def get_all_books(
    user_id,
) -> list:  # Тут окрім повернення всіх доступних книг є ще їх фільтрація по ознаці активності юзера, який нею володіє, та видалення власних книг зі списку видачі.
    whole_library: List = await Library.all().prefetch_related("user", "book")
    available_books_ids: List = []
    for book_instance in whole_library:
        if (
            not book_instance.user.is_active or book_instance.user.user_id == user_id
        ):  # if not book_instance.user.is_active or book_instance.user.user_id == user_id:
            whole_library.remove(book_instance)
        else:
            available_books_ids.append(book_instance.book.id)

    books = await Book.filter(Q(id__in=available_books_ids))
    print(books)
    return books


async def get_filterred_book_user_list(request_type, keyword) -> list:
    if request_type == "inauthor":
        book_list = await Book.filter(book_author__icontains=keyword)
    elif request_type == "intitle":
        book_list = await Book.filter(book_title__icontains=keyword)
    return book_list


async def change_usage_status(user_id: int) -> bool:
    user = await User.get(user_id=user_id)

    if user.is_active:
        user.is_active = False
    else:
        user.is_active = True

    await User.save(user, update_fields=["is_active"])
    user = await User.get(user_id=user_id)
    print("User status after:", user.is_active)
    return user.is_active


async def get_user_library(user_id: int) -> list:
    user_books: list = (
        await Library.all().prefetch_related("book", "user").filter(user=user_id)
    )
    books: list = []
    book: dict = {}

    for instance in user_books:
        book["id"] = instance.id
        book["title"] = instance.book.book_title
        book["author"] = instance.book.book_author
        if instance.swap_status:
            book["swap_status"] = "Обміняв(ла)"
        else:
            book["swap_status"] = "Книга в мене"
        books.append(book)
        book = {}
    return books


async def change_book_instance_status(book_instance_id: int) -> bool:
    book = await Library.get(id=book_instance_id)
    if book.swap_status:
        book.swap_status = False
    else:
        book.swap_status = True

    await Library.save(book, update_fields=["swap_status"])
    book = await Library.get(id=book_instance_id)
    print("Book status after:", book.swap_status)
    return book.swap_status


async def check_user_existance(user_id: int) -> bool:
    return await User.exists(user_id=user_id)
