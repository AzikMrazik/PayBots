import asyncio
from aiosqlite import connect
from aiohttp import ClientSession
from aiogram import Bot, Router, F
from aiogram.types import Message
from aiogram.utils.formatting import *
from config import API_TOKEN, ALLOWED_GROUPS, BASE_URL

router = Router()

async def addorder(order_id, chat_id, amount):
    async with connect("orders_shaxta.db") as db:
        await db.execute(
            "INSERT INTO orders_shaxta (order_id, chat_id, amount) VALUES (?, ?, ?)",
            (order_id, chat_id, amount)
        )
        await db.commit()

async def delorder(order_id):
    async with connect("orders_shaxta.db") as db:
        await db.execute(
            "DELETE FROM orders_shaxta WHERE order_id = ?", 
            (order_id,)
        )
        await db.commit()

async def checklist(bot: Bot):
    async with connect("orders_shaxta.db") as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS orders_shaxta (
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
    async with connect("orders_shaxta.db") as db:
        cursor = await db.execute("SELECT * FROM orders_shaxta")
        return await cursor.fetchall()
    
async def get_one_order(order_id):
    async with connect("orders_shaxta.db") as db:
        cursor = await db.execute(
            "SELECT amount FROM orders_shaxta WHERE order_id = ?", 
            (order_id,)
        )
        result = await cursor.fetchone()
        resultend = result[0]
        return resultend

async def check(bot: Bot):
    async with ClientSession() as session:
        all_data = await get_all_orders()
        for order_id, chat_id, amount in all_data:
            try:
                async with session.post(
                    f"{BASE_URL}check-order",
                    params={
                        "apiKey": API_TOKEN,
                        "type_order": "buy",
                        "orderId": int(order_id)
                    }
                ) as response:
                    resp = await response.json(content_type=None)
                    data = resp['data']
                    status = data['status']

                if status == "confirmed":
                    await send_success(bot, [order_id, chat_id, amount])
                    await delorder(order_id)

                elif status == "declined":
                    await delorder(order_id)       

            except Exception as e:
              await bot.send_message(chat_id=chat_id, text=f"⚰️Заказ №{order_id} на сумму {amount} успешно умер! because {e}")

        await asyncio.sleep(3)

async def send_success(bot: Bot, target_chat):
    await bot.send_message(chat_id=target_chat[1], text=f"✅Заказ №{target_chat[0]} на сумму {target_chat[2]} успешно оплачен!")

@router.message(F.chat.type.in_({"group", "supergroup"}), F.text.startswith("/order_"))
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
                    f"{BASE_URL}check-order",
                    params={
                        "apiKey": API_TOKEN,
                        "type_order": "buy",
                        "orderId": int(ordercheck_id)
                    }
                ) as response:
                    resp = await response.json(content_type=None)
                    data = resp['data']
                    status = data['status']
                if status == "confirmed":
                    await message.answer(f"✅Заказ №{ordercheck_id} на сумму {amount} оплачен!")
                elif status == "declined":
                    await message.answer(f"⛔Заказ №{ordercheck_id} на сумму {amount} отменен!")
                elif status == "waiting":
                    await message.answer(f"⚠️Заказ №{ordercheck_id} на сумму {amount} ожидает оплаты!")
                else:
                    await message.answer(f"⚰️Заказ №{ordercheck_id} на сумму {amount} умер!")
    except Exception as e:
        await message.answer(f"⚰️Бот умер! because {e}")

