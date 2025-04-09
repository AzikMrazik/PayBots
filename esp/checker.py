from aiohttp import ClientSession
from aiogram import Router, F
from aiogram.types import Message
from aiogram.utils.formatting import *
from config import API_TOKEN, ALLOWED_GROUPS, BASE_URL, MERCHANT_ID


router = Router()

@router.message(F.chat.type.in_({"group", "supergroup"}), F.text.startswith("/espc_"))
async def check_command(message: Message):
    if message.chat.id not in ALLOWED_GROUPS:
        await message.answer("Бот не активирован в этой группе!")
        return
    try:
        ordercheck_id = int(message.text.split("_")[1])
    except (IndexError, ValueError) as e:
        await message.answer("Неверный формат команды. Используйте: /epsc_1000")
        return
    try:
            async with ClientSession() as session:
                async with session.post(
                    f"{BASE_URL}/info",
                    json={
                            "merchantId": int(MERCHANT_ID),
                            "token": API_TOKEN,
                            "id": int(ordercheck_id)
                        }
                ) as response:
                    data = await response.json()
                    data = data['data']
                    status = data['status']
                    amount = data['amount']
                    await message.answer(f"✅Заказ №{ordercheck_id} на сумму {amount} в статусе {status}!")
    except Exception as e:
            await message.answer(f"⚰️Бот умер! because {e}")

