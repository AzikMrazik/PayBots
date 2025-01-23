import logging
import asyncio
from aiohttp import ClientSession
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.formatting import *
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import API_TOKEN, ALLOWED_GROUPS, CHECK_URL

router = Router()

logging.basicConfig(level=logging.DEBUG)

orderlist = dict()

async def addorder(order_id, chat_id, amount):
    orderlist[order_id] = chat_id,amount

async def checklist(bot: Bot):
        while True:
            await check(bot)
            await asyncio.sleep(60)

async def check(bot: Bot):
    async with ClientSession() as session:
        for order_id in list(orderlist.keys()):
            async with session.post(
                CHECK_URL,
                json={"order_id": order_id, "api_key": API_TOKEN}
            ) as response:
                data = await response.json()
                status = data.get('status')

            if status == "payment_success":
                chat_id, amount = orderlist[order_id]
                await send_success(bot, [order_id, chat_id, amount])
                del orderlist[order_id]

            elif status == "payment_canceled":
                del orderlist[order_id]

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
        async with ClientSession() as session:
            async with session.post(
                CHECK_URL,
                json={"order_id": ordercheck_id, "api_key": API_TOKEN}
            ) as response:
                data = await response.json()
                status = data.get('status')
                if status == "payment_success":
                    await message.answer(f"✅Заказ №{ordercheck_id}, оплачен!")
                elif status == "payment_canceled":
                    await message.answer(f"⛔Заказ №{ordercheck_id}, отменен!")
                elif status == "payment_wait":
                    await message.answer(f"⚠️Заказ №{ordercheck_id}, ожидает оплаты!")
                else:
                    await message.answer(f"⚰️Заказ №{ordercheck_id}, умер!")
    except Exception as e:
        await message.answer("⚰️Бот умер!")

