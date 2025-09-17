from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
import logging
import asyncio
from aiogram.client.default import DefaultBotProperties
import config, create_payment, commands

logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
dp.include_routers(create_payment.router, commands.router)

@dp.message(Command('ping'))
async def handle_ping_command(msg: types.Message):
    resp = await msg.answer("Amore Pay:\n🏓Pong...")
    await asyncio.sleep(5)
    await resp.delete()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())