import asyncio
from aiosqlite import connect
from aiohttp import ClientSession
from aiogram import Bot, Router, F
from aiogram.types import Message
from aiogram.utils.formatting import *
from config import MERCHANT_TOKEN, ALLOWED_GROUPS, BASE_URL

router = Router()

async def addorder(sign, chat_id, amount, order_id):
    async with connect("orders_corkpay.db") as db:
        await db.execute(
            "INSERT INTO orders_corkpay (sign, chat_id, amount, order_id) VALUES (?, ?, ?, ?)",
            (sign, chat_id, amount, order_id)
        )
        await db.commit()

async def delorder(order_id):
    async with connect("orders_corkpay.db") as db:
        await db.execute(
            "DELETE FROM orders_corkpay WHERE order_id = ?", 
            (order_id,)
        )
        await db.commit()

async def checklist(bot: Bot):
    async with connect("orders_corkpay.db") as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS orders_corkpay (
                sign TEXT PRIMARY KEY,
                chat_id TEXT NOT NULL,
                amount TEXT NOT NULL,
                order_id TEXT NOT NULL         
            )
        ''')
        await db.commit()
        while True:
            await check(bot)
            await asyncio.sleep(60)

async def get_all_orders():
    async with connect("orders_corkpay.db") as db:
        cursor = await db.execute("SELECT * FROM orders_corkpay")
        return await cursor.fetchall()
    
async def get_one_order(order_id):
    async with connect("orders_corkpay.db") as db:
        cursor = await db.execute(
            "SELECT amount, sign FROM orders_corkpay WHERE order_id = ?", 
            (order_id,)
        )
        result = await cursor.fetchone()
        return result

async def check(bot: Bot):
    async with ClientSession() as session:
        all_data = await get_all_orders()
        try:
            for sign, chat_id, amount, order_id in all_data:
                try:
                    async with session.post(
                        f"{BASE_URL}/api/apiOrderStatus",
                        json={"merchant_token": MERCHANT_TOKEN, "sign": sign}
                    ) as response:
                        data = await response.json()
                        status = data.get('status')

                    if status == "success":
                        await send_success(bot, [chat_id, amount, order_id])
                        await delorder(order_id)

                    elif status == "canceled":
                        await delorder(order_id)       

                except Exception as e:
                    await bot.send_message(chat_id=chat_id, text=f"{e}")
                    await bot.send_message(chat_id=chat_id, text=f"⚰️Заказ №{order_id} на сумму {amount} успешно умер! because {e}")

                await asyncio.sleep(3)
        except Exception as e:
            print("no", e)
            await asyncio.sleep(30)

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
        if not amount:
            amount = "[сумма не получена]"
        async with ClientSession() as session:
            async with session.post(
                f"{BASE_URL}/api/apiOrderStatus",
                json={"merchant_token": MERCHANT_TOKEN, "sign": sign}
            ) as response:
                data = await response.json()
                status = data.get('status')
                print(data)
                if status == "success":
                    await message.answer(f"✅Заказ №{ordercheck_id} на сумму {amount} оплачен!")
                elif status == "canceled":
                    await message.answer(f"⛔Заказ №{ordercheck_id} на сумму {amount} отменен!")
                elif status == "wait":
                    await message.answer(f"⚠️Заказ №{ordercheck_id} на сумму {amount} ожидает оплаты!")
                else:
                    await message.answer(f"⚰️Заказ №{ordercheck_id} на сумму {amount} умер! по причине {status}")
    except Exception as e:
        await message.answer(f"⚰️Бот умер! because {e}")

