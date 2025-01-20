import logging
import asyncio
from aiohttp import ClientSession as session
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.formatting import *
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import debuger, create_payment, group_payment
from config import TELEGRAM_BOT_TOKEN, UNIQUE_ID, UNIQUE_NAME, ADMIN_ID

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TELEGRAM_BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
dp.include_routers(debuger.router, create_payment.router, group_payment.router)

def main_kb():
    keyboard = [
        [InlineKeyboardButton(text="Создать платеж", callback_data='create_payment')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def send_welcome(user_id, username):
    if user_id == UNIQUE_ID:
        return f"Добро пожаловать, <b>{UNIQUE_NAME}</b>!"
    elif user_id in ADMIN_ID:  # Теперь сравниваем числа с числами
        return "Добро пожаловать, <b>admin</b>!"
    else:
        return f"Добро пожаловать, <b>{username}</b>!"

@dp.callback_query(F.data == 'main_menu')
async def handle_main_menu_callback(callback_query: CallbackQuery, state: FSMContext):
    await state.clear()
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    welcome_message = await send_welcome(user_id, callback_query.from_user.username)
    await bot.send_message(user_id, welcome_message, reply_markup=main_kb())

@dp.message(Command("start"))
async def start_command(message: Message):
    welcome_message = await send_welcome(message.from_user.id, message.from_user.username)
    await message.answer(welcome_message, reply_markup=main_kb())

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())