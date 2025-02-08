from aiohttp import web
from aiogram import Bot, Dispatcher
import logging
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from config import SECRET_KEY

logger = logging.getLogger(__name__)

async def handle_post(request: web.Request):
    bot: Bot = request.app['bot']
    try:
        logger.info("Handling POST request to /custom_webhook")
        data = await request.json()
        chat_id = data.get('chat_id')
        text = data.get('text')
        if chat_id and text:
            await bot.send_message(chat_id=chat_id, text=text)
        return web.Response(text="OK")
    except Exception as e:
        return web.Response(text=f"Error: {str(e)}", status=400)

async def start_web_app(dispatcher: Dispatcher, bot: Bot):
    app = web.Application()
    app['bot'] = bot  # Сохраняем бот в приложении
    
    app.router.add_get('/test', handle_test)

    SimpleRequestHandler(
        dispatcher=dispatcher, 
        bot=bot,
        secret_token=SECRET_KEY
    ).register(app, path="/tg_webhook")
    
    app.router.add_post('/custom_webhook', handle_post)
    return app

async def handle_test(request):
    return web.Response(text="OK")
