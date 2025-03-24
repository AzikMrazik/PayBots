from aiosqlite import connect
from aiohttp import ClientSession
from aiogram import Router, F
from aiogram.types import Message
from aiogram.utils.formatting import *
from config import API_TOKEN, ALLOWED_GROUPS, BASE_URL
from datetime import datetime

router = Router()

async def addorder(order_id, chat_id, amount, payment_id):
    await checklist()
    now = datetime.now().isoformat()
    async with connect("orders_p2p.db") as db:
        await db.execute(
            "INSERT INTO orders_p2p (order_id, chat_id, amount, payment_id, timestamp) VALUES (?, ?, ?, ?, ?)",
            (order_id, chat_id, amount, payment_id, now)
        )
        await db.commit()

async def checklist():
    async with connect("orders_p2p.db") as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS orders_p2p (
                order_id TEXT PRIMARY KEY,
                chat_id TEXT NOT NULL,
                amount TEXT NOT NULL,
                payment_id TEXT NOT NULL,
                timestamp TEXT NOT NULL         
            )
        ''')
        await db.commit()

async def get_one_order(order_id):
    async with connect("orders_p2p.db") as db:
        cursor = await db.execute(
            "SELECT payment_id FROM orders_p2p WHERE order_id = ?", 
            (order_id,)
        )
        result = await cursor.fetchone()
        if result:
            return result[0]

@router.message(F.chat.type.in_({"group", "supergroup"}), F.text.startswith("/p2pc_"))
async def check_command(message: Message):
    if message.chat.id not in ALLOWED_GROUPS:
        await message.answer("Бот не активирован в этой группе!")
        return
    try:
        ordercheck_id = int(message.text.split("_")[1])
    except (IndexError, ValueError) as e:
        await message.answer("Неверный формат команды. Используйте: /check_1000")
        return
    await message.answer(f"❓ID заказа: <code>{payment_id}</code>")
    try:
        payment_id = await get_one_order(ordercheck_id)
        if payment_id == None:
            await message.answer("⭕Заказ не найден!")
        else:
            async with ClientSession() as session:
                async with session.get(
                    f"{BASE_URL}/v1/payment/status",
                    headers={'authorization': 'Bearer ' + API_TOKEN},
                    params={"id": payment_id}
                ) as response:
                    try:
                        data = await response.json()
                        print(data, flush=True)
                        try:
                            error = data['error']
                            if error == "Not Found":
                                await message.answer(f"⭕Статус не найден")
                            else:
                                await message.answer(f"⛔Ошибка")
                        except:
                            order_id = data['client_order_id']
                            amount = data['amount']
                            paid_amount = data['paid_amount']
                            status = data['status']
                            if status == "payment_success":
                                await message.answer(f"✅Заказ №{ordercheck_id} на сумму {amount} оплачен!")
                            elif status == "payment_canceled":
                                await message.answer(f"⛔Заказ №{ordercheck_id} на сумму {amount} отменен!")
                            elif status == "payment_wait":
                                await message.answer(f"⚠️Заказ №{ordercheck_id} на сумму {amount} ожидает оплаты!")
                            else:
                                await message.answer(f"🔔Заказ №{order_id} на сумму {amount}, оплачен на {paid_amount}, в статусе {status}")
                    except Exception as e:
                        await message.answer(f"⚰️P2P отправил труп! {e}")
    except Exception as e:
            await message.answer(f"⚰️Бот умер! because {e}")

