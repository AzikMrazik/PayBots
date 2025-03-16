from aiosqlite import connect
from aiogram import Router
from aiogram.utils.formatting import *
from datetime import datetime


router = Router()

async def addorder(chat_id, amount, order_id):
    await checklist()
    now = datetime.now().isoformat()
    async with connect("orders_crocopay.db") as db:
        await db.execute(
            "INSERT INTO orders_crocopay (chat_id, amount, order_id, timestamp) VALUES (?, ?, ?, ?)",
            (chat_id, amount, order_id, now)
        )
        await db.commit()

async def checklist():
    async with connect("orders_crocopay.db") as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS orders_crocopay (
                chat_id TEXT NOT NULL,
                amount TEXT NOT NULL,
                order_id TEXT NOT NULL,
                timestamp TEXT NOT NULL                  
            )
        ''')
        await db.commit()
