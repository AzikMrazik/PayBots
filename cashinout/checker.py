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

router = Router()

logging.basicConfig(level=logging.DEBUG)

orderlist = dict()

async def addorder(order_id, chat_id, amount):
    orderlist[order_id] = chat_id,amount

async def send_success(bot: Bot, data):
    await bot.send_message(chat_id=831055006, text=str(data))