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
        if amount < 1000 or amount > 10000:
            await message.answer("Доступная сумма платежа 1000 - 10000 RUB!")
            return
    except:
        await message.answer("Неверный формат команды. Используйте: /pay_1000")
        return
    else:
        bot_msg = await message.reply("⌛️Ожидаем реквизиты...")
        checkout = await sendpost(amount, message.chat.id, 1)
        length = len(checkout) - 1
        counter = 1
        for sms in range(length):
            if counter == 1:
                await message.reply(checkout[sms])
                counter += 1
            else:
                await message.answer(checkout[sms])
        await bot_msg.delete()
        
