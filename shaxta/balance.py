import logging
import asyncio
from aiohttp import ClientSession
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.formatting import *
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import API_TOKEN, BASE_URL

router = Router()

def back_kb():
    keyboard = [
        [InlineKeyboardButton(text="Назад в меню", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@router.callback_query(F.data == 'check_balance')
async def balance(callback_query: CallbackQuery, bot: Bot):
    await bot.answer_callback_query(callback_query.id)
    async with ClientSession() as session:
        async with session.post(
            f"{BASE__URL}balance",
            params={
                "apikey": API_TOKEN
            }
        ) as response:
            resp = response.json(content_type=None)
            data = resp['data']
            bal = data['balance']
            await callback_query.message.answer(f"Ваш баланс: {bal}", reply_markup=back_kb())