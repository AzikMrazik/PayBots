import logging
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.formatting import *
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
import create_payment, group_payment, checker
from config import BOT_TOKEN

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
dp.include_routers(checker.router, create_payment.router, group_payment.router)

def main_kb():
    keyboard = [
        [InlineKeyboardButton(text="Создать платеж", callback_data='create_payment')],
        [InlineKeyboardButton(text="Просмотреть заявки", callback_data='check')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@dp.callback_query(F.data == 'main_menu')
async def handle_main_menu_callback(callback_query: CallbackQuery, state: FSMContext):
    await state.clear()
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.answer(text="Вы в главном меню, выберите действие:", reply_markup=main_kb())

@dp.message(Command("start"))
async def start_command(message: Message):
    await message.answer("Добро пожаловать!")
    await message.answer("Вы в главном меню, выберите действие:", reply_markup=main_kb())

async def main():
    await asyncio.gather(
        dp.start_polling(bot),
        )

if __name__ == "__main__":
    asyncio.run(main())