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
from config import BOT_TOKEN, DOMAIN, REPORT_CHAT_ID
from aiohttp import web 
from aiogram.webhook.aiohttp_server import setup_application
from urllib.parse import parse_qs
from datetime import datetime, timedelta
from openpyxl import Workbook
import pandas as pd
import aiosqlite
import os


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
    app.router.add_route('*', '/', handle_root)
    app.router.add_post('/cashinout', handle_cashinout)
    app.router.add_post('/epay', handle_epay)
    app.router.add_post('/crocopay', handle_crocopay)
    app.router.add_post('/p2p', handle_p2p)
    app.router.add_post('/apay', handle_apay)
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
                    await add_paid_order(float(amount), chat_id, "cashinout")
                except:
                    logger.info(f"Ошибка: {e}")
        except Exception as e:   
                logger.info(f"Ошибка: {e}")
        return web.Response(text="OK", status=200)
    except Exception as e:
        logger.error(f"Ошибка: {str(e)}")
        return web.Response(text="OK", status=200)

async def handle_corkpay(request: web.Request):
    bot: Bot = request.app['bot']
    system = "corkpay"
    try:
        data = await request.text()
        logger.info(f"Получен вебхук: {data}")
        cleaned_text = data.lstrip('✅ \n\t')
        parsed_data = parse_qs(cleaned_text)
        data = {k: v[0] for k, v in parsed_data.items()}
        try:
            order_id = data['merchant_order']
            chat_id, amount = await get_chat_id(order_id, system)
            if chat_id != None:
                chat_id = int(chat_id)
            else:
                return web.Response(text="OK")
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text=f"🟣CORKPAY:\n✅Заказ №{order_id} на сумму {amount}₽ успешно оплачен!"
                )
                await add_paid_order(float(amount), chat_id, "corkpay")
            except Exception as e:
                logger.info(f"Ошибка: {e}")
        except Exception as e:   
                logger.info(f"Ошибка: {e}")
        return web.Response(text="OK", status=200)
    except Exception as e:
        logger.error(f"Ошибка: {str(e)}")
        return web.Response(text="OK", status=200)

async def handle_epay(request: web.Request):
    bot: Bot = request.app['bot']
    system = "epay"
    try:
        data = await request.json()
        logger.info(f"Получен вебхук: {data}")
        order_id = data['transaction_id']
        chat_id, amount = await get_chat_id(order_id, system)
        if chat_id != None:
                chat_id = int(chat_id)
        else:
                return web.Response(text="OK")
        try:
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text=f"🟡E-PAY:\n✅Заказ №{order_id} на сумму {amount}₽ успешно оплачен!"
                )
                await add_paid_order(float(amount), chat_id, "epay")
            except Exception as e:
                logger.info(f"Ошибка №1: {e}")
        except Exception as e:   
                logger.info(f"Ошибка №2: {e}")

        return web.Response(text="OK", status=200)
    
    except Exception as e:
        logger.error(f"Ошибка: {str(e)}")
        return web.Response(text="OK", status=200)

async def handle_crocopay(request: web.Request):
    bot: Bot = request.app['bot']
    try:
        data = await request.json()
        chat_id = -1002486163462
        amount = data['total']
        try:
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text=f"🟢CrocoPay:\n✅Заказ на сумму {amount}₽ успешно оплачен!"
                )
                await add_paid_order(float(amount), chat_id, "crocopay")
            except:
                logger.info(f"Ошибка: {e}")
        except Exception as e:   
                logger.info(f"Ошибка: {e}")

        return web.Response(text="OK", status=200)
    
    except Exception as e:
        logger.error(f"Ошибка: {str(e)}")
        return web.Response(text="OK", status=200)

async def handle_p2p(request: web.Request):
    bot: Bot = request.app['bot']
    system = "p2p"
    try:
        data = await request.json()
        logger.info(f"Получен вебхук: {data}")
        order_id = data['client_order_id']
        amount = data['amount']
        status = data['status']
        chat_id = await get_chat_id(order_id, system)
        if chat_id != None:
                chat_id = int(chat_id)
        else:
                return web.Response(text="OK")
        try:
            try:
                if status == "PAID":
                    await bot.send_message(
                        chat_id=chat_id,
                        text=f"⚪P2P Express:\n✅Заказ №{order_id} на сумму {amount}₽ успешно оплачен!"
                    )
                    await add_paid_order(float(amount), chat_id, "p2p")
            except Exception as e:
                logger.info(f"Ошибка №1: {e}")
        except Exception as e:   
                logger.info(f"Ошибка №2: {e}")
        return web.Response(text="OK", status=200)
    except Exception as e:
        logger.error(f"Ошибка: {str(e)}")
        return web.Response(text="OK", status=200)

async def handle_crocopay(request: web.Request):
    bot: Bot = request.app['bot']
    try:
        data = await request.text()
        try:
            data = await request.text()
        except:
            pass
        chat_id = -1002486163462
        try:
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text=f"🅰️APay:\n✅Заказ успешно оплачен! {data}"
                )
            except:
                logger.info(f"Ошибка: {e}")
        except Exception as e:   
                logger.info(f"Ошибка: {e}")

        return web.Response(text="OK", status=200)
    
    except Exception as e:
        logger.error(f"Ошибка: {str(e)}")
        return web.Response(text="OK", status=200)

async def handle_all_other(request):
    return web.Response(text="Forbidden", status=403)

async def get_chat_id(order_id, system):
    if system == "corkpay":
        async with connect("/root/paybots/corkpay/orders_corkpay.db") as db:
            cursor = await db.execute(
                "SELECT chat_id, amount FROM orders_corkpay WHERE order_id = ?", 
                (order_id,)
            )
            result = await cursor.fetchone()
            return result
    elif system == "epay":
        async with connect("/root/paybots/epay/orders_epay.db") as db:
            cursor = await db.execute(
                "SELECT chat_id, amount FROM orders_epay WHERE order_id = ?", 
                (order_id,)
            )
            result = await cursor.fetchone()
            return result
    elif system == "p2p":
        async with connect("/root/paybots/p2pexpress/orders_p2p.db") as db:
            cursor = await db.execute(
                "SELECT chat_id, amount FROM orders_p2p WHERE order_id = ?", 
                (order_id,)
            )
            result = await cursor.fetchone()
            return result[0]

async def auto_cleanup():
    while True:
        try:
            systems = {
                "corkpay": "/root/paybots/corkpay/orders_corkpay.db",
                "epay": "/root/paybots/epay/orders_epay.db", 
                "p2p": "/root/paybots/p2pexpress/orders_p2p.db"
            }
            
            for system, db_path in systems.items():
                cutoff = (datetime.now() - timedelta(days=10)).isoformat()
                async with aiosqlite.connect(db_path) as db:
                    await db.execute(
                        "DELETE FROM orders WHERE created_at < ?",
                        (cutoff,))
                    await db.commit()
            
            logger.info("Автоочистка старых заказов выполнена")
        except Exception as e:
            logger.error(f"Ошибка автоочистки: {e}")
        await asyncio.sleep(86400)

@dp.message(Command("ping"))
async def start_command(message: Message):
    msg = await message.answer("🔔Notificator на связи✅")
    await asyncio.sleep(5)
    await msg.delete()

async def generate_report():
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        async with aiosqlite.connect("/root/paybots/paid_orders.db") as db:
            cursor = await db.execute(
                "SELECT date, amount, chat_id, system FROM paid_orders "
                "WHERE date BETWEEN ? AND ?",
                (start_date.isoformat(), end_date.isoformat()))
            rows = await cursor.fetchall()
        
        df = pd.DataFrame(rows, columns=['Дата', 'Сумма', 'id', 'Система'])
        report_path = "/tmp/weekly_report.xlsx"
        df.to_excel(report_path, index=False)
        
        return report_path
    except Exception as e:
        logger.error(f"Ошибка генерации отчета: {e}")
        return None

async def schedule_report():
    while True:
        now = datetime.now()
        
        # Рассчет времени до следующего воскресенья 23:59
        days_until_sunday = (6 - now.weekday()) % 7
        next_sunday = now + timedelta(days=days_until_sunday)
        next_sunday = next_sunday.replace(hour=23, minute=59, second=0, microsecond=0)
        
        if next_sunday < now:
            next_sunday += timedelta(weeks=1)
        
        wait_seconds = (next_sunday - now).total_seconds()
        await asyncio.sleep(wait_seconds)
        
        report_path = await generate_report()
        if report_path:
            try:
                with open(report_path, 'rb') as f:
                    await bot.send_document(
                        chat_id=REPORT_CHAT_ID,  # ID вашего чата
                        document=f,
                        caption="Еженедельный отчет об оплаченных заказах"
                    )
                os.remove(report_path)
            except Exception as e:
                logger.error(f"Ошибка отправки отчета: {e}")

async def create_paid_orders_table():
    async with aiosqlite.connect("/root/paybots/paid_orders.db") as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS paid_orders
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         date TEXT,
                         amount REAL,
                         chat_id INTEGER,
                         system TEXT)''')
        await db.commit()

async def add_paid_order(amount: float, chat_id: int, system: str):
    async with aiosqlite.connect("/root/paybots/paid_orders.db") as db:
        now = datetime.now().isoformat()
        await db.execute(
            'INSERT INTO paid_orders (date, amount, chat_id, system) VALUES (?, ?, ?, ?)',
            (now, amount, chat_id, system))
        await db.commit()

async def main():
    logger = logging.getLogger(__name__)
    asyncio.create_task(auto_cleanup())
    asyncio.create_task(schedule_report())
    await create_paid_orders_table()
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