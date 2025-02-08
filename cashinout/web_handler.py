from aiohttp import web
import json
from aiogram import Bot
from config import BOT_TOKEN

bot = Bot(token=BOT_TOKEN)

async def handle_post(request):
    try:
        data = await request.json()
        # Пример: отправка уведомления в чат
        chat_id = data.get('chat_id')
        text = data.get('text')
        if chat_id and text:
            await bot.send_message(chat_id=chat_id, text=text)
        return web.Response(text="OK")
    except Exception as e:
        return web.Response(text=f"Error: {str(e)}", status=400)

async def start_web_app():
    app = web.Application()
    app.router.add_post('/webhook', handle_post)  # Ваш кастомный эндпоинт
    return app