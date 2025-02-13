import logging
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher
import logging
from aiosqlite import connect
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiogram import Bot, Dispatcher
from aiogram.utils.formatting import *
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN, DOMAIN
from aiohttp import web 
from aiogram.webhook.aiohttp_server import setup_application

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]  # Явное указание вывода в консоль
)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

async def start_web_app(dispatcher: Dispatcher, bot: Bot):
    app = web.Application()
    app['bot'] = bot
    
    # Добавляем кастомные обработчики ПЕРЕД регистрацией вебхука aiogram
    app.router.add_post('/corkpay', handle_corkpay)
    app.router.add_get('/', handle_root)
    app.router.add_post('/cashinout', handle_cashinout)
    app.router.add_post('/epay', handle_epay)
    app.router.add_get('/epay', handle_epay)
    # Регистрируем обработчик aiogram
    SimpleRequestHandler(
        dispatcher=dispatcher,
        bot=bot,
    ).register(app, path="/tg_webhook")
    
    return app

async def handle_root(request):
    return web.Response(text="Forbidden", status=403)

async def handle_cashinout(request: web.Request):
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
                try:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=f"🔵CASHINOUT:\n✅Заказ №{order_id} на сумму {amount}₽ успешно оплачен!"
                    )
                except:
                    pass
        except Exception as e:   
                pass

        return web.Response(text="OK")

    except Exception as e:
        logger.error(f"Ошибка: {str(e)}")
        return web.Response(text=f"Error: {str(e)}", status=500)

async def handle_corkpay(request: web.Request):
    bot: Bot = request.app['bot']
    try:
        data = await request.json()
        logger.info(f"Получен вебхук: {data}")
        
        try:
            amount = data['amount']
            order_id = data['merchant_order']
            chat_id = get_chat_id(order_id, "corkpay")
            if chat_id != False:
                chat_id = int(chat_id)
            else:
                return web.Response(text="OK")
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text=f"🟣CORKPAY:\n✅Заказ №{order_id} на сумму {amount}₽ успешно оплачен!"
                )
            except:
                pass
        except Exception as e:   
                pass

        return web.Response(text="OK")
    
    except Exception as e:
        logger.error(f"Ошибка: {str(e)}")
        return web.Response(text=f"Error: {str(e)}", status=500)

async def handle_epay(request: web.Request):
    bot: Bot = request.app['bot']
    try:
        data = await request.json()
        logger.info(f"{request}")
        logger.info(f"Получен вебхук: {data}") 
        try:
            try:
                await bot.send_message(
                    chat_id=831055006,
                    text=f"🟡E-PAY:\n{data}"
                )
            except:
                pass
        except Exception as e:   
                pass

        return web.Response(text="OK")
    
    except Exception as e:
        logger.error(f"Ошибка: {str(e)}")
        return web.Response(text=f"Error: {str(e)}", status=500)

async def get_chat_id(order_id, system):
    async with connect(f"/root/paybots/corkpay/orders_{system}.db") as db:
        cursor = await db.execute(
            "SELECT chat_id FROM orders_corkpay WHERE order_id = ?", 
            (order_id,)
        )
        result = await cursor.fetchone()
        if result:
            return result[0]
        else:
            return False

async def main():
    logger = logging.getLogger(__name__)
    try:
        logger.info("Удаление старого вебхука...")
        await bot.delete_webhook()
        
        logger.info(f"Настройка вебхука: https://{DOMAIN}/tg_webhook")
        await bot.set_webhook(
            url=f"https://{DOMAIN}/tg_webhook"
        )

        # Создание aiohttp-приложения
        web_app = await start_web_app(dp, bot)
        setup_application(web_app, dp, bot=bot)

        # Запуск веб-сервера
        runner = web.AppRunner(web_app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 8080)
        
        await site.start()

        # Бесконечное ожидание
        logger.info("Сервер запущен на порту 8080")
        while True:
            await asyncio.sleep(3600)
            
    except Exception as e:
        logger.error(f"Ошибка: {e}", exc_info=True)
    finally:
        await bot.session.close()
        if 'runner' in locals():
            await runner.cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass