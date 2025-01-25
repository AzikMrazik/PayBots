import dotenv
import logging
import asyncio
from aiohttp import ClientSession
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.formatting import *
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandObject
from create_payment import sendpost
from config import ALLOWED_GROUPS

router = Router()

@router.message(F.chat.type.in_({"group", "supergroup"}), F.text.startswith("/sbp_"))
async def cash_command(message: Message):
    if message.chat.id not in ALLOWED_GROUPS:
        await message.answer("Бот не активирован в этой группе!")
        return
    try:
        amount = int(message.text.split("_")[1])
        amount = amount / 1.21
        amount = round(amount)
        if amount < 1000:
            await message.answer("Минимальная сумма: 1000 RUB")
            return
    except Exception as e:
        print(e)
        await message.answer("Неверный формат команды. Используйте: /sbp_1000")
        return
    else:
        bot_msg = await message.reply("⌛️Ожидаем реквизиты...")
        checkout = await sendpost(amount, message.chat.id, "SBP")
        await bot_msg.delete()
        if checkout != True:
            await message.reply(checkout[0])
            await message.answer(checkout[1])
        else:
            await message.reply("⛔Нет реквизитов!")   

@router.message(F.chat.type.in_({"group", "supergroup"}), F.text.startswith("/card_"))
async def cash_command(message: Message):
    if message.chat.id not in ALLOWED_GROUPS:
        await message.answer("Бот не активирован в этой группе!")
        return
    try:
        amount = int(message.text.split("_")[1])
        amount = amount / 1.21
        amount = round(amount)
        if amount < 1000:
            await message.answer("Минимальная сумма: 1000 RUB")
            return
    except Exception as e:
        print(e)
        await message.answer("Неверный формат команды. Используйте: /card_1000")
        return
    else:
        bot_msg = await message.reply("⌛️Ожидаем реквизиты...")
        checkout = await sendpost(amount, message.chat.id, "CARD")
        await bot_msg.delete()
        if checkout != True:
            await message.reply(checkout[0])
            await message.answer(checkout[1])
        else:
            await message.reply("⛔Нет реквизитов!")   