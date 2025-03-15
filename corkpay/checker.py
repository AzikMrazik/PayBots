import asyncio
from aiosqlite import connect
from aiohttp import ClientSession
from aiogram import Bot, Router, F
from aiogram.types import Message
from aiogram.utils.formatting import *
from config import MERCHANT_TOKEN, ALLOWED_GROUPS, BASE_URL
from datetime import datetime


router = Router()

async def addorder(sign, chat_id, amount, order_id):
    await checklist()
    now = datetime.now().isoformat()
    async with connect("orders_corkpay.db") as db:
        await db.execute(
            "INSERT INTO orders_corkpay (sign, chat_id, amount, order_id, timestamp) VALUES (?, ?, ?, ?, ?)",
            (sign, chat_id, amount, order_id, now)
        )
        await db.commit()

async def delorder(order_id):
    async with connect("orders_corkpay.db") as db:
        await db.execute(
            "DELETE FROM orders_corkpay WHERE order_id = ?", 
            (order_id,)
        )
        await db.commit()

async def checklist():
    async with connect("orders_corkpay.db") as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS orders_corkpay (
                sign TEXT PRIMARY KEY,
                chat_id TEXT NOT NULL,
                amount TEXT NOT NULL,
                order_id TEXT NOT NULL,
                timestamp TEXT NOT NULL                  
            )
        ''')
        await db.commit()

    
async def get_one_order(order_id):
    async with connect("orders_corkpay.db") as db:
        cursor = await db.execute(
            "SELECT amount, sign FROM orders_corkpay WHERE order_id = ?", 
            (order_id,)
        )
        result = await cursor.fetchone()
        if result:
            return result
        else:
            return None, None

async def send_success(bot: Bot, target_chat):
    await bot.send_message(chat_id=target_chat[0], text=f"✅Заказ №{target_chat[2]} на сумму {target_chat[1]} успешно оплачен!")

@router.message(F.chat.type.in_({"group", "supergroup"}), F.text.startswith("/corkc_"))
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
        amount, sign = await get_one_order(ordercheck_id)
        if sign == None:
            await message.answer("⭕Заказ не найден!")
        else:
            async with ClientSession() as session:
                async with session.post(
                    f"{BASE_URL}/api/apiOrderStatus",
                    json={"merchant_token": MERCHANT_TOKEN, "sign": sign}
                ) as response:
                    data = await response.json()
                    status = data.get('status')
                    print(data, flush=True)
                    if status == "success":
                        await message.answer(f"✅Заказ №{ordercheck_id} на сумму {amount} оплачен!")
                    elif status == "fail":
                        await message.answer(f"⛔Заказ №{ordercheck_id} на сумму {amount} отменен!")
                    elif status == "wait":
                        await message.answer(f"⚠️Заказ №{ordercheck_id} на сумму {amount} ожидает оплаты!")
                    else:
                        await message.answer(f"⚰️Заказ №{ordercheck_id} на сумму {amount} умер! по причине {status}")
    except Exception as e:
            await message.answer(f"⚰️Бот умер! because {e}")

