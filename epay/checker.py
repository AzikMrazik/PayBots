import asyncio
from aiosqlite import connect
from aiohttp import ClientSession
from aiogram import Bot, Router, F
from aiogram.types import Message
from aiogram.utils.formatting import *
from config import API_TOKEN, ALLOWED_GROUPS, BASE_URL

router = Router()

async def addorder(order_id, chat_id, amount):
    async with connect("orders_epay.db") as db:
        await db.execute(
            "INSERT INTO orders_epay (order_id, chat_id, amount) VALUES (?, ?, ?)",
            (order_id, chat_id, amount)
        )
        await db.commit()

async def checklist():
    async with connect("orders_epay.db") as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS orders_epay (
                order_id TEXT PRIMARY KEY,
                chat_id TEXT NOT NULL,
                amount TEXT NOT NULL
            )
        ''')
        await db.commit()

async def get_one_order(order_id):
    async with connect("orders_epay.db") as db:
        cursor = await db.execute(
            "SELECT amount FROM orders_epay WHERE order_id = ?", 
            (order_id,)
        )
        result = await cursor.fetchone()
        if result:
            return result[0]
        else:
            return None

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
        if amount == None:
            await message.answer("⭕Заказ не найден!")
        else:
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

