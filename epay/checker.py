import logging
import asyncio
from aiosqlite import connect
from aiohttp import ClientSession
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.formatting import *
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import API_TOKEN, ALLOWED_GROUPS, BASE_URL

router = Router()

async def addorder(order_id, chat_id, amount):
    async with connect("orders.db") as db:
        await db.execute(
            "INSERT INTO orders (order_id, chat_id, amount) VALUES (?, ?, ?)",
            (order_id, chat_id, amount)
        )
        await db.commit()

async def delorder(order_id):
    async with connect("orders.db") as db:
        await db.execute(
            "DELETE FROM orders WHERE order_id = ?", 
            (order_id,)
        )
        await db.commit()

async def checklist(bot: Bot):
    async with connect("orders.db") as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                chat_id TEXT NOT NULL,
                amount TEXT NOT NULL
            )
        ''')
        await db.commit()
        while True:
            await check(bot)
            await asyncio.sleep(60)

async def get_all_orders():
    async with connect("orders.db") as db:
        cursor = await db.execute("SELECT * FROM orders")
        return await cursor.fetchall()
    
async def get_one_order(order_id):
    async with connect("orders.db") as db:
        cursor = await db.execute(
            "SELECT amount FROM orders WHERE order_id = ?", 
            (order_id,)
        )
        return await cursor.fetchone()

async def check(bot: Bot):
    async with ClientSession() as session:
        all_data = await get_all_orders()
        for order_id, chat_id, amount in all_data:
            try:
                async with session.post(
                    f"{BASE_URL}/request/order/info",
                    json={"order_id": order_id, "api_key": API_TOKEN}
                ) as response:
                    data = await response.json()
                    status = data.get('status')

                if status == "payment_wait":
                    await send_success(bot, [order_id, chat_id, amount])
                    await delorder(order_id)

                elif status == "payment_canceled":
                    await delorder(order_id)       

            except Exception as e:
                await bot.send_message(chat_id=chat_id, text=f"{data}")
                await bot.send_message(chat_id=chat_id, text=f"⚰️Заказ №{order_id} на сумму {amount} успешно умер! because {e}")

            await asyncio.sleep(3)

async def send_success(bot: Bot, target_chat):
    await bot.send_message(chat_id=target_chat[1], text=f"✅Заказ №{target_chat[0]} на сумму {target_chat[2]} успешно оплачен!")

@router.message(F.chat.type.in_({"group", "supergroup"}), F.text.startswith("/check_"))
async def check_command(message: Message):
    if message.chat.id not in ALLOWED_GROUPS:
        await message.answer("Бот не активирован в этой группе!")
        return
    try:
        ordercheck_id = int(message.text.split("_")[1])
    except (IndexError, ValueError) as e:
        await message.answer("Неверный формат команды. Используйте: /check_1000")
        return
    try:
        amount = await get_one_order(ordercheck_id)
        if not amount:
            amount = "[сумма не получена]"
        async with ClientSession() as session:
            async with session.post(
                f"{BASE_URL}/request/order/info",
                json={"order_id": ordercheck_id, "api_key": API_TOKEN}
            ) as response:
                data = await response.json()
                status = data.get('status')
                if status == "payment_success":
                    await message.answer(f"✅Заказ №{ordercheck_id} на сумму {amount} оплачен!")
                elif status == "payment_canceled":
                    await message.answer(f"⛔Заказ №{ordercheck_id} на сумму {amount} отменен!")
                elif status == "payment_wait":
                    await message.answer(f"⚠️Заказ №{ordercheck_id} на сумму {amount} ожидает оплаты!")
                else:
                    await message.answer(f"⚰️Заказ №{ordercheck_id} на сумму {amount} умер!")
    except Exception as e:
        await message.answer(f"⚰️Бот умер! because {e}")

