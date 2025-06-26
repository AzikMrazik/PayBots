import aiogram
import logging
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def main_kb():
    keyboard = [
        [InlineKeyboardButton(text="Создать платеж", callback_data='create_payment')],
        [InlineKeyboardButton(text="Баланс и вывод", callback_data='balance')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def help_kb():
    keyboard = [
        [InlineKeyboardButton(text="Помощь", callback_data='help')],
        [InlineKeyboardButton(text="Назад", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def lang_kb():
    keyboard = [
        [InlineKeyboardButton(text="Русский", callback_data='lang_ru'),
        InlineKeyboardButton(text="English", callback_data='lang_en')],
        [InlineKeyboardButton(text="Назад", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)