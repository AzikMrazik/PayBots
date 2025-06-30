from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
import logging
import asyncio
from aiogram.client.default import DefaultBotProperties
import config, create_payment, balance

logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
dp.include_routers(balance.router, create_payment.router)

def balance_kb():
    kb = [
        [InlineKeyboardButton(text="Баланс", callback_data='balance')],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

@dp.message(F.text.startswith("347"))
async def handle_balance_command(msg: types.Message):
    await msg.answer("Вы в главном меню, выберите действие:", reply_markup=balance_kb())

@dp.message(Command('ping'))
async def handle_ping_command(msg: types.Message):
    resp = await msg.answer("Cyber-Money:\n🏓Pong...")
    await asyncio.sleep(5)
    await resp.delete()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())