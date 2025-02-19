import logging
import asyncio
from aiosqlite import connect
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.formatting import *
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
import create_payment, group_payment, checker
from config import BOT_TOKEN, ALLOWED_GROUPS
from checker import checklist

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
dp.include_routers(create_payment.router, group_payment.router, checker.router)

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
async def start_command(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Добро пожаловать!")
    await message.answer(text="Вы в главном меню, выберите действие:", reply_markup=main_kb())

@dp.message(F.chat.type.in_({"group", "supergroup"}), F.text.startswith("/ban_"))
async def cash_command(message: Message):
    if message.chat.id not in ALLOWED_GROUPS:
        await message.answer("Бот не активирован в этой группе!")
        return
    try:
        bin = message.text.split("_")[1]
        async with connect("bins.db") as db:
            await db.execute(
            "UPDATE bins SET note = 'RIP' WHERE bin = ?",
            (bin,)
            )
            await db.commit()
    except:
        await message.answer("Неверный формат команды. Используйте: /ban_220501")
        return
    else:
        bot_msg = await message.answer(f"⛔BIN {bin} успешно забанен!")
        await asyncio.sleep(10)
        await bot_msg.delete()

@dp.message(F.chat.type.in_({"group", "supergroup"}), F.text.startswith("/unban_"))
async def cash_command(message: Message):
    if message.chat.id not in ALLOWED_GROUPS:
        await message.answer("Бот не активирован в этой группе!")
        return
    try:
        bin = message.text.split("_")[1]
        print(bin)
        async with connect("bins.db") as db:
            await db.execute(
                "UPDATE bins SET note = '' WHERE bin = ?",
                (bin,)
                )             
            await db.commit()
    except Exception as e:
        await message.answer(f"{e}Неверный формат команды. Используйте: /unban_220501")
        return
    else:
        bot_msg = await message.answer(f"✅BIN {bin} успешно разбанен!")
        await asyncio.sleep(10)
        await bot_msg.delete()

@dp.message(Command("ping"))
async def start_command(message: Message):
    msg = await message.answer("🟣CorkPay на связи✅")
    await asyncio.sleep(5)
    await msg.delete()

async def main():
    await checklist()
    await asyncio.gather(
        dp.start_polling(bot)
    )

if __name__ == "__main__":
    asyncio.run(main())