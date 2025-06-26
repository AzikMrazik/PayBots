from aiogram import Router, F
from aiogram.types import Message
from aiogram.utils.formatting import *
from create_payment import sendpost
from config import ALLOWED_GROUPS
import qrcode
import io
from PIL import Image, ImageDraw
import requests
from aiogram.types import BufferedInputFile

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
            await message.answer(i)
        
@router.message(F.chat.type.in_({"group", "supergroup"}), F.text.startswith("/gen_"))
async def gen_command(message: Message):
    if message.chat.id not in ALLOWED_GROUPS:
        await message.answer("Бот не активирован в этой группе!")
        return
    try:
        p = message.text.split("_")
        if len(p) < 3:
            await message.answer("Неверный формат команды. Используйте: /gen_ссылка")
            return
        link = p[2]
        amt = p[1]
        
        qr = qrcode.QRCode(version=1, box_size=15, border=6)
        qr.add_data(link)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Загрузка лого из интернета
        try:
            resp = requests.get("https://avatars.mds.yandex.net/i?id=9e1c0e11c2266ea44a36ede9e88c1466a00a79a3-3193980-images-thumbs&n=13", timeout=5)
            logo = Image.open(io.BytesIO(resp.content))
            logo = logo.resize((60, 60))
        except:
            # Создаем простой лого если загрузка не удалась
            logo = Image.new('RGB', (60, 60), 'white')
            d = ImageDraw.Draw(logo)
            d.rectangle([10, 10, 50, 50], fill='blue')
        
        # Вставляем в центр
        pos = ((img.size[0] - logo.size[0]) // 2, (img.size[1] - logo.size[1]) // 2)
        img.paste(logo, pos)
        
        bio = io.BytesIO()
        img.save(bio, format='PNG')
        bio.seek(0)
        
        photo = BufferedInputFile(bio.read(), filename="qr.png")
        await message.answer_photo(photo, caption=f"""
📄Оплата по QR-коду.

💰К оплате: <code>{amt}</code> рублей

<i>Если не работает QR👇</i>
🔗Ссылка - <a href="{link}">[КНОПКА]</a>""", parse_mode="HTML")
        
    except IndexError:
        await message.answer("Неверный формат команды. Используйте: /gen_ссылка")
    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}")

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
    