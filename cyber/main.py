from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
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
    keyboard = [
        [InlineKeyboardButton(text="Баланс", callback_data='balance')],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@dp.message(lambda message: message.text.startswith("347"))
async def handle_balance_command(message: types.Message):
    chat_id = message.from_user.id
    await message.answer("Вы в главном меню, выберите действие:", reply_markup=balance_kb())
    return

@dp.message(commands=['ping'])
async def handle_ping_command(message: types.Message):
    msg = await message.answer("Cyber-Money:\n🏓Pong...")
    await asyncio.sleep(5)
    await msg.delete()
    return

async def main():
    await asyncio.gather(
        dp.start_polling(bot)
    )

if __name__ == "__main__":
    asyncio.run(main())