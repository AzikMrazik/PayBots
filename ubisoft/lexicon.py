import asyncio
import aiosqlite
import aiogram
import logging
from dbworker import get_userinfo

async def get_text(key: str, user_id: int) -> str:

    ret: str = ""

    userinfo = await get_userinfo(user_id)
    lang = userinfo.get('lang')
    if lang == 'ru':
        ret = LEXICON_RU.get(key, "Key not found")
    elif lang == 'en':
        ret = LEXICON_EN.get(key, "Key not found")
    else:
        ret = LEXICON_RU.get(key, "Key not found")

    return ret

LEXICON_RU = {
    "main_menu": "Главное меню",
    "help": "Помощь",
    "lang_changed": "Язык изменен на русский",
    "error_occurred": "Произошла ошибка. Пожалуйста, попробуйте позже."}

LEXICON_EN = {
    "main_menu": "Main menu",
    "help": "Help",
    "lang_changed": "Language changed to English",
    "error_occurred": "An error occurred. Please try again later."}