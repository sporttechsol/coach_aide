from aiogram import types

from app import text

PLAYER_DEFAULT = types.ReplyKeyboardMarkup(
    resize_keyboard=True, selective=True
)
PLAYER_DEFAULT.add(text.YOUR_PROFILE)

GENERAL_TRAINER_DEFAULT = types.ReplyKeyboardMarkup(
    resize_keyboard=True, selective=True
)
GENERAL_TRAINER_DEFAULT.add(text.YOUR_PROFILE)
GENERAL_TRAINER_DEFAULT.add(text.LIST_OF_PLAYERS)

YES_OR_NO = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
YES_OR_NO.add(text.YES, text.NO)

NEXT = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
NEXT.add(text.NEXT)

CHECK_PROFILE_WITH_YES = types.ReplyKeyboardMarkup(
    resize_keyboard=True, selective=True
)
CHECK_PROFILE_WITH_YES.add(
    text.YES,
    text.CORRECT_FIRSTNAME,
    text.CORRECT_LASTNAME,
    text.CORRECT_PHONE_NUMBER,
    text.CORRECT_BIRTHDAY,
)

CHECK_PROFILE_WITH_NO = types.ReplyKeyboardMarkup(
    resize_keyboard=True, selective=True
)
CHECK_PROFILE_WITH_NO.add(
    text.NO,
    text.CORRECT_FIRSTNAME,
    text.CORRECT_LASTNAME,
    text.CORRECT_PHONE_NUMBER,
    text.CORRECT_BIRTHDAY,
)

CHECK_PAYDAY = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
CHECK_PAYDAY.add(
    text.YES,
    text.CORRECT_DAY,
    text.CORRECT_TIME,
    text.CORRECT_MESSAGE,
)

SHOW_USERS = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
SHOW_USERS.add(text.BLOCK_PLAYERS)
SHOW_USERS.add(text.BACK)
