from aiosqlite import connect
from aiogram import Router
from aiogram.utils.formatting import *

router = Router()

async def addorder(order_id, chat_id, amount):
    async with connect("orders_crocopay.db") as db:
        await db.execute(
            "INSERT INTO orders_crocopay (order_id, chat_id, amount) VALUES (?, ?, ?)",
            (order_id, chat_id, amount)
        )
        await db.commit()

async def checklist():
    async with connect("orders_crocopay.db") as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS orders_crocopay (
                order_id TEXT PRIMARY KEY,
                chat_id TEXT NOT NULL,
                amount TEXT NOT NULL
            )
        ''')
        await db.commit()
