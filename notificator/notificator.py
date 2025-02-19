import logging
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
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
from urllib.parse import parse_qs

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
    app.router.add_post('/corkpay', handle_corkpay)
    app.router.add_get('/', handle_root)
    app.router.add_post('/cashinout', handle_cashinout)
    app.router.add_post('/epay', handle_epay)
    app.router.add_post('/crocopay', handle_crocopay)
    app.router.add_post('/platega', handle_platega)
    SimpleRequestHandler(
        dispatcher=dispatcher,
        bot=bot,
    ).register(app, path="/tg_webhook")
    app.router.add_route('*', '/{path:.*}', handle_all_other)
    return app

async def handle_root(request):
    return web.Response(text="Forbidden", status=403)

async def handle_cashinout(request: web.Request):
    bot: Bot = request.app['bot']
    try:
        data = await request.json()
        logger.info(f"Получен вебхук: {data}")
        if 'externalText' not in data or not data['externalText']:
            return web.Response(text="Error: externalText is missing", status=400)
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
                    logger.info(f"Ошибка: {e}")
        except Exception as e:   
                logger.info(f"Ошибка: {e}")
        return web.Response(text="OK", status=200)
    except Exception as e:
        logger.error(f"Ошибка: {str(e)}")
        return web.Response(text=f"Error: {str(e)}", status=500)

async def handle_corkpay(request: web.Request):
    bot: Bot = request.app['bot']
    system = "corkpay"
    try:
        data = await request.text()
        logger.info(f"Получен вебхук: {data}")
        cleaned_text = data.lstrip('✅ \n\t')
        parsed_data = parse_qs(cleaned_text)
        data = {k: v[0] for k, v in parsed_data.items()}
        await bot.send_message(
                    chat_id=831055006,
                    text=f"🟣CORKPAY:\n✅{data}"
                )
        try:
            order_id = data['merchant_order']
            chat_id, amount = await get_chat_id(order_id, system)
            if chat_id != False:
                chat_id = int(chat_id)
            else:
                return web.Response(text="OK")
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text=f"🟣CORKPAY:\n✅Заказ №{order_id} на сумму {amount}₽ успешно оплачен!"
                )
                await delorder(order_id, system)
            except Exception as e:
                logger.info(f"Ошибка: {e}")
        except Exception as e:   
                logger.info(f"Ошибка: {e}")
        return web.Response(text="OK", status=200)
    except Exception as e:
        logger.error(f"Ошибка: {str(e)}")
        return web.Response(text=f"Error: {str(e)}", status=500)

async def handle_epay(request: web.Request):
    bot: Bot = request.app['bot']
    system = "epay"
    try:
        data = await request.json()
        logger.info(f"Получен вебхук: {data}")
        order_id = data['merchant_order_id']
        amount = data['amount'] 
        chat_id = await get_chat_id(order_id, system)
        if chat_id != False:
                chat_id = int(chat_id)
        else:
                return web.Response(text="OK")
        try:
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text=f"🟡E-PAY:\n✅Заказ №{order_id} на сумму {amount}₽ успешно оплачен!"
                )
                await delorder(order_id, system)
            except Exception as e:
                logger.info(f"Ошибка: {e}")
        except Exception as e:   
                logger.info(f"Ошибка: {e}")

        return web.Response(text="OK", status=200)
    
    except Exception as e:
        logger.error(f"Ошибка: {str(e)}")
        return web.Response(text=f"Error: {str(e)}", status=500)

async def handle_crocopay(request: web.Request):
    bot: Bot = request.app['bot']
    system = "crocopay"
    try:
        data = await request.text()
        await bot.send_message(
                    chat_id=831055006,
                    text=f"🟢CrocoPay:\n✅{data}"
                )
        try:
            data = await request.json()
            await bot.send_message(
                    chat_id=831055006,
                    text=f"🟢CrocoPay:\n✅{data}"
                )     
        except:
            pass
        chat_id = 831055006
        order_id = 10000
        amount = 10000
        if chat_id != False:
                chat_id = int(chat_id)
        else:
                return web.Response(text="OK")
        try:
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text=f"🟢CrocoPay:\n✅Заказ №{order_id} на сумму {amount}₽ успешно оплачен!"
                )
                await delorder(order_id, system)
            except:
                logger.info(f"Ошибка: {e}")
        except Exception as e:   
                logger.info(f"Ошибка: {e}")

        return web.Response(text="OK", status=200)
    
    except Exception as e:
        logger.error(f"Ошибка: {str(e)}")
        return web.Response(text=f"Error: {str(e)}", status=500)

async def handle_platega(request: web.Request):
    bot: Bot = request.app['bot']
    system = "platega"
    try:
        data = await request.json()
        status = data['status']
        if status == "CONFIRMED" or status == "PAID":
            pass   
        else:
            return web.Response(text="OK", status=200) 
        id = data['id']
        order_id, chat_id = await get_chat_id(id)
        amount = data['amount']
        if chat_id != False:
                chat_id = int(chat_id)
        else:
                return web.Response(text="OK")
        try:
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text=f"⚪Platega:\n✅Заказ №{order_id} на сумму {amount}₽ успешно оплачен!"
                )
            except:
                logger.info(f"Ошибка: {e}")
        except Exception as e:   
                logger.info(f"Ошибка: {e}")

        return web.Response(text="OK", status=200)
    
    except Exception as e:
        logger.error(f"Ошибка: {str(e)}")
        return web.Response(text=f"Error: {str(e)}", status=500)

async def handle_all_other(request):
    return web.Response(text="Forbidden", status=403)

async def get_chat_id(order_id, system):
    if system == "corkpay":
        async with connect(f"/root/paybots/corkpay/orders_corkpay.db") as db:
            cursor = await db.execute(
                "SELECT chat_id, amount FROM orders_corkpay WHERE order_id = ?", 
                (order_id,)
            )
            result = await cursor.fetchone()
            return result
    elif system == "epay":
        async with connect(f"/root/paybots/epay/orders_epay.db") as db:
            cursor = await db.execute(
                "SELECT chat_id FROM orders_epay WHERE order_id = ?", 
                (order_id,)
            )
            result = await cursor.fetchone()
            return result[0]
    elif system == "platega":
        async with connect(f"/root/paybots/platega/orders_platega.db") as db:
            cursor = await db.execute(
                "SELECT order_id, chat_id FROM orders_platega WHERE transaction_id = ?", 
                (order_id,)
            )
            result = await cursor.fetchone()
            return result

async def delorder(order_id, system):
    if system == "corkpay":
        async with connect("/root/paybots/corkpay/orders_corkpay.db.db") as db:
            await db.execute(
                "DELETE FROM orders_corkpay WHERE order_id = ?", 
                (order_id,)
            )
            await db.commit()
    if system =="epay":
        async with connect("/root/paybots/epay/orders_epay.db") as db:
            await db.execute(
                "DELETE FROM orders_epay WHERE order_id = ?", 
                (order_id,)
            )
            await db.commit()

@dp.message(Command("ping"))
async def start_command(message: Message):
    msg = await message.answer("🔔Notificator на связи✅")
    await asyncio.sleep(5)
    await msg.delete()

async def main():
    logger = logging.getLogger(__name__)
    try:
        logger.info("Удаление старого вебхука...")
        await bot.delete_webhook()
        logger.info(f"Настройка вебхука: https://{DOMAIN}/tg_webhook")
        await bot.set_webhook(
            url=f"https://{DOMAIN}/tg_webhook"
        )
        web_app = await start_web_app(dp, bot)
        setup_application(web_app, dp, bot=bot)
        runner = web.AppRunner(web_app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 8080) 
        await site.start()
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