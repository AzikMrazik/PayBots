import asyncio
import aiosqlite
import aiogram
import logging
from dbworker import get_chatinfo
import systems

async def get_text(key: str, chat_id: int, system=None) -> str:

    ret: str = ""

    if system:
        system = systems.ACTIVE_SYSTEMS.get(system, "777")

    chatinfo = await get_chatinfo(chat_id)
    lang = chatinfo.get('lang')
    if lang == 'ru':
        ret = LEXICON_RU.get(key, "Текст не найден")
    elif lang == 'en':
        ret = LEXICON_EN.get(key, "Key not found")
    else:
        ret = LEXICON_RU.get(key, "Текст не найден")

    return ret

LEXICON_RU = {
    "main_menu": "Главное меню",
    "help": "Помощь",
    "lang_changed": "Язык изменен на русский",
    "error_occurred": "Произошла ошибка. Пожалуйста, попробуйте позже.",
    "callback_received": "{system_name}:\nЗаказ №<code>{order_id}</code> на сумму <code>{amount}</code>₽ успешно оплачен."}

LEXICON_EN = {
    "main_menu": "Main menu",
    "help": "Help",
    "lang_changed": "Language changed to English",
    "error_occurred": "An error occurred. Please try again later.",
    "callback_received": "{system_name}:\nOrder №<code>{order_id}</code> for the amount of <code>{amount}</code>₽ has been paid."}
