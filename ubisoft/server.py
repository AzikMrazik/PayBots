import ssl
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
import config
import systems
import dbworker
from lexicon import get_text

async def handle_callback(req: web.Request):
    system = req.match_info.get('system')
    order_id = req.match_info.get('order_id')
    chat_id, amount = await dbworker.get_orderinfo(order_id)
    if not chat_id:
        logging.error(f"Order ID {order_id} not found in the database.")
        raise Exception(f"Order ID {order_id} not found in the database.")
    
    try:
        from main import bot
        await bot.send_message(chat_id, text=await get_text("callback_received", chat_id, system))
        logging.info(f"Callback processed for system: {system}, order ID: {order_id}, chat ID: {chat_id}")
    except Exception as e:
        logging.error(f"Error processing callback: {e}")
        raise

async def handle_all_other(req: web.Request):
    return web.Response(text="Forbidden", status=403)

async def create_app(dp: Dispatcher, bot: Bot):
    app = web.Application()
    app['bot'] = bot
    
    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    ).register(app, path="/tg_webhook")
    
    for sys in systems.ACTIVE_SYSTEMS:
        if systems.ACTIVE_SYSTEMS == {}:
            logging.warning("No active systems found. Please check your configuration.")
            continue
        app.router.add_route(f'/{systems}' + '/{order_id}', handle_callback)

    app.router.add_route('*', '/{path:.*}', handle_all_other)
    setup_application(app, dp, bot=bot)
    return app

async def start_server(dp: Dispatcher, bot: Bot):
    app = await create_app(dp, bot)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # SSL context для HTTPS
    ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_ctx.load_cert_chain(config.SSL_CERT, config.SSL_KEY)
    
    site = web.TCPSite(runner, '0.0.0.0', 8443, ssl_context=ssl_ctx)
    await site.start()
    logging.info("HTTPS сервер запущен на порту 8443")
    
    return runner