from aiogram import Router, F
from aiogram.types import Message
from aiogram.utils.formatting import *
from create_payment import sendpost
from config import ALLOWED_GROUPS
from aiogram.types import BufferedInputFile
from qr_utils import generate_qr

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
        typ = typ.replace("/", "")
        amount = int(message.text.split("_")[1])
        if amount < 300 and typ != "qr":
            await message.answer("Минимальная сумма: 300 RUB")
            return
        if amount < 2500 and typ == "qr":
            await message.answer("Минимальная сумма: 2500 RUB")
            return
        if typ == "zds":
            await message.answer("Метод отключен!")
            return
    except Exception:
        await message.answer("Неверный формат команды. Используйте: /pay_1000 /zds_1000 /qr_1000")
        return
    else:
        msg = await message.reply("⌛️Ожидаем реквизиты...")
        order = await sendpost(amount, message.chat.id, msg, 1, typ)
        await msg.delete()
        for i in order:
            if isinstance(i, dict) and 'photo' in i:
                await message.answer_photo(i['photo'], caption=i.get('caption'), parse_mode="HTML")
            else:
                await message.answer(i)
        
@router.message(F.chat.type.in_({"group", "supergroup"}), F.text.startswith("/gen_"))
async def gen_command(message: Message):
    if message.chat.id not in ALLOWED_GROUPS:
        await message.answer("Бот не активирован в этой группе!")
        return
    p = message.text.split("_")
    if len(p) < 3:
        await message.answer("Неверный формат команды. Используйте: /gen_сумма_ссылка")
        return
    link = p[2]
    amt = p[1]
    photo, caption = await generate_qr(link, amt)
    await message.answer_photo(photo=photo, caption=caption, parse_mode="HTML")
    return


@router.message(F.chat.type.in_({"group", "supergroup"}), F.text.startswith("/temp_"))
async def temp_command(message: Message):
        parts = message.text.split("_")
        if len(parts) < 3:
            await message.answer("Неверный формат команды. Используйте: /temp_сумма_карта")
            return
        
        card = parts[2]
        amount = parts[1]
        template = f"""
📄Создана заявка на оплату!

💳Номер карты для оплаты: <code>{card}</code>
💰Сумма платежа: <code>{amount}</code> рублей

🕑Время на оплату: 20 мин.
        """
        try:
            await message.answer(text=template)
        except Exception as e:
            await message.answer("Произошла ошибка: " + str(e))
    