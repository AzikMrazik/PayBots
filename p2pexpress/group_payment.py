from aiogram import Router, F
from aiogram.types import Message
from aiogram.utils.formatting import *
from create_payment import sendpost
from config import ALLOWED_GROUPS

router = Router()


@router.message(F.chat.type.in_({"group", "supergroup"}), F.text.startswith("/p2p_"))
async def cash_command(message: Message):
    if message.chat.id not in ALLOWED_GROUPS:
        await message.answer("Бот не активирован в этой группе!")
        return
    try:
        amount = int(message.text.split("_")[1])
        if amount < 2500 or amount > 10000:
            await message.answer("Доступная сумма платежа 2500 - 10000 RUB!")
            return
    except:
        await message.answer("Неверный формат команды. Используйте: /pay_1000")
        return
    else:
        msg = await message.reply("⌛️Ожидаем реквизиты...")
        order = await sendpost(amount, message.from_user.id, msg, 1)
        await msg.delete()
        for i in order:
            await message.answer(i)
        
