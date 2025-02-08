from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from config import BOT_TOKEN, SECRET_KEY

bot = Bot(token=BOT_TOKEN)

async def handle_post(request):
    # Проверка секретного токена для кастомных запросов
    if request.headers.get("X-Secret-Token") != SECRET_KEY:
        return web.Response(status=403, text="Forbidden")
    
    try:
        data = await request.json()
        chat_id = data.get('chat_id')
        text = data.get('text')
        if chat_id and text:
            await bot.send_message(chat_id=chat_id, text=text)
        return web.Response(text="OK")
    except Exception as e:
        return web.Response(text=f"Error: {str(e)}", status=400)

async def start_web_app(dispatcher: Dispatcher):  # <- Добавлен аргумент
    app = web.Application()
    
    # Регистрация обработчика Telegram
    SimpleRequestHandler(
        dispatcher=dispatcher, 
        bot=bot,
        secret_token=SECRET_KEY
    ).register(app, path="/tg_webhook")  # Путь совпадает с вебхуком
    
    # Регистрация кастомного эндпоинта
    app.router.add_post('/custom_webhook', handle_post)
    
    return app