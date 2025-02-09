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
    app['bot'] = bot
    
    # Добавляем кастомные обработчики ПЕРЕД регистрацией вебхука aiogram
    app.router.add_get('/test', handle_test)
    app.router.add_post('/custom_webhook', handle_post)
    app.router.add_get('/', handle_root)
    app.router.add_post('/payment_webhook', handle_payment_webhook)
    # Регистрируем обработчик aiogram
    SimpleRequestHandler(
        dispatcher=dispatcher,
        bot=bot,
        secret_token=SECRET_KEY
    ).register(app, path="/tg_webhook")
    
    return app

async def handle_test(request):
    return web.Response(text="OK")

async def handle_root(request):
    return web.Response(text="Bot is running")

async def handle_payment_webhook(request: web.Request):
    bot: Bot = request.app['bot']
    try:
        data = await request.json()
        logger.info(f"Получен вебхук: {data}")

        # Проверяем наличие externalText
        if 'externalText' not in data or not data['externalText']:
            return web.Response(text="Error: externalText is missing", status=400)

        # Парсим externalText (формат: "order_id,chat_id")
        external_text = data['externalText'].split(',')
        if len(external_text) != 2:
            return web.Response(text="Error: invalid externalText format", status=400)
        
        order_id, chat_id = external_text
        chat_id = int(chat_id)  # Преобразуем в число
        try:
            if data['type'] == 'payment':
                amount = data['amount']
                await bot.send_message(
                    chat_id=chat_id,
                    text=f"Заказ №{order_id} на сумму {amount} RUB успешно оплачен!"
                )
        except Exception as e:   
                await bot.send_message(
                    chat_id=831055006,
                    text=f"{e}"
                )

        return web.Response(text="OK")

    except Exception as e:
        logger.error(f"Ошибка: {str(e)}")
        return web.Response(text=f"Error: {str(e)}", status=500)