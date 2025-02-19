import asyncio
from aiosqlite import connect
from aiohttp import ClientSession
from aiogram import Bot, Router, F
from aiogram.types import Message
from aiogram.utils.formatting import *
from config import ALLOWED_GROUPS, BASE_URL, MERCHANT_ID, API_KEY

router = Router()

async def addorder(order_id, chat_id, amount, transaction_id):
    await checklist()
    async with connect("orders_platega.db") as db:
        await db.execute(
            "INSERT INTO orders_platega (order_id, chat_id, amount, transaction_id) VALUES (?, ?, ?, ?)",
            (order_id, chat_id, amount, transaction_id)
        )
        await db.commit()

async def delorder(order_id):
    async with connect("orders_platega.db") as db:
        await db.execute(
            "DELETE FROM orders_platega WHERE order_id = ?", 
            (order_id,)
        )
        await db.commit()

async def checklist():
    async with connect("orders_platega.db") as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS orders_platega (
                order_id TEXT PRIMARY KEY,
                chat_id TEXT NOT NULL,
                amount TEXT NOT NULL,
                transaction_id TEXT NOT NULL
            )
        ''')
        await db.commit()

    
async def get_one_order(order_id):
    async with connect("orders_platega.db") as db:
        cursor = await db.execute(
            "SELECT amount, transaction_id FROM orders_platega WHERE order_id = ?", 
            (order_id,)
        )
        result = await cursor.fetchone()
        if result:
            return result
        else:
            return None

async def send_success(bot: Bot, target_chat):
    await bot.send_message(chat_id=target_chat[1], text=f"✅Заказ №{target_chat[0]} на сумму {target_chat[2]} успешно оплачен!")

@router.message(F.chat.type.in_({"group", "supergroup"}), F.text.startswith("/platc_"))
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
        amount, id = await get_one_order(ordercheck_id)
        if amount == None:
            await message.answer("⭕Заказ не найден!")
        else:
            async with ClientSession() as session:
                async with session.get(
                    f"{BASE_URL}/transaction/{id}",
                    headers={"X-Secret": API_KEY, "X-MerchantId": MERCHANT_ID}
                ) as response:
                        data = await response.json()
                        try:
                            status = data['status']
                            if status == "CONFIRMED" or status == "PAID ":
                                await message.answer(f"✅Заказ №{ordercheck_id} на сумму {amount} оплачен!")
                            elif status == "CANCELED" or status == "FAILED" or status == "EXPIRED":
                                await message.answer(f"⛔Заказ №{ordercheck_id} на сумму {amount} отменен!")
                            elif status == "PENDING":
                                await message.answer(f"⚠️Заказ №{ordercheck_id} на сумму {amount} ожидает оплаты!")
                            else:
                                await message.answer(f"⚰️Заказ №{ordercheck_id} на сумму {amount} умер!")
                        except:
                            await message.answer(f"{data}")
    except Exception as e:
            await message.answer(f"⚰️Бот умер! because {e}")

