from aiogram import Router, F
from aiogram.types import Message
from aiogram.utils.formatting import *
from create_payment import sendpost
from config import ALLOWED_GROUPS

router = Router()

@router.message(F.chat.type.in_({"group", "supergroup"}), F.text.startswith("/qr_"))
@router.message(F.chat.type.in_({"group", "supergroup"}), F.text.startswith("/zds_"))
@router.message(F.chat.type.in_({"group", "supergroup"}), F.text.startswith("/pay_"))
async def cash_command(message: Message):
    if message.chat.id not in ALLOWED_GROUPS:
        await message.answer("Бот не активирован в этой группе!")
        return
    try:
        typ = message.text.split("_")[0]
        amount = int(message.text.split("_")[1])
        if amount < 300:
            await message.answer("Минимальная сумма: 300 RUB")
            return
    except:
        await message.answer("Неверный формат команды. Используйте: /pay_1000 /zds_1000 /qr_1000")
        return
    else:
        msg = await message.reply("⌛️Ожидаем реквизиты...")
        order = await sendpost(amount, message.chat.id, msg, 1, typ)
        await msg.delete()
        for i in order:
            await message.answer(i)
        
