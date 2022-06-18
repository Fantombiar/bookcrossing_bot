from enum import unique
from unittest.util import _MAX_LENGTH
from attr import field
from tortoise import models
from tortoise import fields
from typing import List


class Library(models.Model):
    book: fields.ForeignKeyRelation = fields.ForeignKeyField(
        "bot.Book", related_name="books"
    )
    user: fields.ForeignKeyRelation = fields.ForeignKeyField(
        "bot.User", related_name="users"
    )
    swap_status = fields.BooleanField(default=False)


class Book(models.Model):
    # id = fields.IntField(pk=True, generated=True)
    book_author = fields.CharField(max_length=255)
    book_title = fields.TextField()
    isbn_code = fields.BigIntField(null=True, unique=True)
    users: fields.ReverseRelation['Library']
    # owners: fields.ManyToManyRelation["User"] = fields.ManyToManyField(
    # "models.Team", related_name="books", through="user_book")


class User(models.Model):
    user_id = fields.BigIntField(pk=True)
    username = fields.CharField(
        max_length=255, null=True, unique=False, description="Actual name of the client"
    )
    city = fields.CharField(max_length=255, null=True)
    is_active = fields.BooleanField(default=True)
    books: fields.ReverseRelation['Library']
