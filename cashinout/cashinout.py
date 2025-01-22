import logging
import asyncio
from aiohttp import web
from aiohttp.web import middleware
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.formatting import *
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import create_payment, group_payment, checker
from aiogram.enums import ParseMode
from config import BOT_TOKEN, WEB_SERVER_IP, WEB_SERVER_PORT
from checker import send_success

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
dp.include_routers(checker.router, create_payment.router, group_payment.router)

def main_kb():
    keyboard = [
        [InlineKeyboardButton(text="Создать платеж", callback_data='create_payment')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@dp.callback_query(F.data == 'main_menu')
async def handle_main_menu_callback(callback_query: CallbackQuery, state: FSMContext):
    await state.clear()
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message("Вы в главном меню, выберите действие:", reply_markup=main_kb())

@dp.message(Command("start"))
async def start_command(message: Message):
    await message.answer("Добро пожаловать!")
    await message.answer("Вы в главном меню, выберите действие:", reply_markup=main_kb())

async def webhook_handler(request: web.Request):
    data = await request.json()
    await send_success(bot, data)
    return web.Response(text="OK", status=200)

@middleware
async def security_middleware(request, handler):
    return web.Response(status=200)

app = web.Application()
app.middlewares.append(security_middleware)

async def on_startup(dp):
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, WEB_SERVER_IP, WEB_SERVER_PORT)
    await site.start()
    logging.info(f"Webhook server started on {WEB_SERVER_IP}:{WEB_SERVER_PORT}")
    print(f"https://{WEB_SERVER_IP}:{WEB_SERVER_PORT}/webhook")

async def main():
    await asyncio.gather(
        dp.start_polling(bot),
        on_startup(dp))

if __name__ == "__main__":
    asyncio.run(main())