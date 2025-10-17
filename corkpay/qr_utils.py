import qrcode
import io
from PIL import Image, ImageDraw
import requests
from aiogram.types import BufferedInputFile


async def generate_qr(link, amt):
        qr = qrcode.QRCode(version=1, box_size=25, border=6)
        qr.add_data(link)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img = img.convert("RGBA")
        
        try:
            r = requests.get("https://i.otzovik.com/objects/b/2340000/2335986.png", timeout=5)
            logo = Image.open(io.BytesIO(r.content))
            logo = logo.convert("RGBA")
            logo = logo.resize((90, 90))
        except:
            logo = Image.new('RGBA', (90, 90), (255, 255, 255, 255))
            d = ImageDraw.Draw(logo)
            d.rectangle([5, 5, 85, 85], fill=(255, 0, 0, 255))
        
        pos = ((img.size[0] - logo.size[0]) // 2, (img.size[1] - logo.size[1]) // 2)
        img.paste(logo, pos, logo)
        
        bio = io.BytesIO()
        img.save(bio, format='PNG')
        bio.seek(0)
        
        photo = BufferedInputFile(bio.read(), filename="qr.png")
        caption = f"""
📄Оплата по QR-коду.

💰К оплате: <code>{amt}</code> рублей

<i>Если не работает QR👇</i>
🔗Ссылка - <a href="{link}">[КНОПКА]</a>"""
        return photo, caption


