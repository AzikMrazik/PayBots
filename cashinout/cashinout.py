import logging
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.formatting import *
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
import create_payment, group_payment
from config import BOT_TOKEN, SECRET_KEY, DOMAIN
from aiohttp import web 
from aiogram.webhook.aiohttp_server import setup_application
from web_handler import start_web_app

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
dp.include_routers(create_payment.router, group_payment.router)

def main_kb():
    keyboard = [
        [InlineKeyboardButton(text="Создать платеж", callback_data='create_payment')]
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
    # Настройка вебхука
    await bot.set_webhook(
        url=f"https://{DOMAIN}/tg_webhook",
        secret_token=SECRET_KEY
    )

    # Создание aiohttp-приложения
    web_app = await start_web_app(dp, bot)
    setup_application(web_app, dp, bot=bot)

    # Запуск веб-сервера
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    
    try:
        await asyncio.gather(site.start())
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        pass
    finally:
        await bot.session.close()
        await runner.cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass