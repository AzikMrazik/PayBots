import asyncio
import aiogram
import aiosqlite
import logging
from aiohttp import web

from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, BotCommand, BotCommandScopeDefault
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.utils.formatting import Text, Bold, Italic, Code, Pre, Underline, Strikethrough

import config
from lexicon import get_text
import exceptions
import keyboards
import dbworker
import server

logging.basicConfig(level=logging.INFO, format='%(asctime)s (%(levelname)s) -- %(message)s')

bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Setting commands (left flyout menu in DM)
async def set_commands():
    commands = [
        BotCommand(command="/start", description="reStart"),
        BotCommand(command="/ping", description="Status"),
        BotCommand(command="/help", description="Help"),
        BotCommand(command="/lang", description="Language / Язык"),
        BotCommand(command="/menu", description="Menu")
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())

@dp.message(Command("start"))
@dp.message(Command("menu"))
@dp.callback_query(F.data == "main_menu")
async def main_menu_handler(message: Message | CallbackQuery, state: FSMContext):
    await state.clear()
    await bot.answer_callback_query(message.id) if isinstance(message, CallbackQuery) else None
    await message.answer(text=await get_text("main_menu", message.from_user.id), reply_markup=keyboards.main_kb())

@dp.message(Command("ping"))
async def ping_command(message: Message):
    await message.answer("🏓Pong")

@dp.message(Command("help"))
async def help_command(message: Message):
    await message.answer(text=await get_text("help", message.from_user.id), reply_markup=keyboards.help_kb())
    raise ValueError("This is a test error")  # Example of raising an error to test error handling

@dp.message(Command("lang"))
async def lang_command(message: Message):
    userinfo = await dbworker.get_userinfo(message.from_user.id)
    lang = userinfo.get('lang')
    if lang == 'ru':
        await dbworker.change_userinfo(message.from_user.id, lang='en')
    elif lang == 'en':
        await dbworker.change_userinfo(message.from_user.id, lang='ru')
    await message.answer(text=await get_text("lang_changed", message.from_user.id))

@dp.error()
async def error_handler(event):
    return await exceptions.handle_all_errors(event, event.exception)

async def main():
    await set_commands()
    await dbworker.init_db()
    logging.info("Bot is starting...")
    logging.info("Удаление старого вебхука...")
    await bot.delete_webhook()
    logging.info(f"Настройка вебхука: https://{config.DOMAIN}/tg_webhook")
    await bot.set_webhook(url=f"https://{config.DOMAIN}/tg_webhook")

    runner = await server.start_server(dp, bot)
    
    try:
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped by user.")