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
from config import BOT_TOKEN, DOMAIN, REPORT_CHAT_ID, ADMINS
from aiohttp import web 
from aiogram.webhook.aiohttp_server import setup_application
from urllib.parse import parse_qs
from datetime import datetime, timedelta
import pandas as pd
import aiosqlite
import os
from aiogram.types import FSInputFile
from datetime import time as dt_time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]  # Явное указание вывода в консоль
)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

COMMISSION_RATES = {
    "epay": lambda x: 0.32 if x < 10000 else 0.25,
    "corkpay": 0.30,
    "apay": 0.10,
    "crocopay": 0.15,
    "cashinout": 0.10,
    "p2p": 0.26
}

def calculate_net_amount(system: str, amount: float) -> float:
    rate = COMMISSION_RATES.get(system)
    if callable(rate):
        return amount * (1 - rate(amount))
    return amount * (1 - rate)

async def start_web_app(dispatcher: Dispatcher, bot: Bot):
    app = web.Application()
    app['bot'] = bot
    app.router.add_post('/corkpay', handle_corkpay)
    app.router.add_route('*', '/', handle_root)
    app.router.add_post('/cashinout', handle_cashinout)
    app.router.add_post('/epay', handle_epay)
    app.router.add_post('/crocopay/{order_id}', handle_crocopay)
    app.router.add_post('/p2p', handle_p2p)
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
    system = "crocopay"
    try:
        data = await request.json()
        order_id = int(request.match_info['order_id'])
        amount = data['total']
        chat_id = await get_chat_id(order_id, system)
        try:
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text=f"🟢CrocoPay:\n✅Заказ №{order_id} на сумму {amount}₽ успешно оплачен!"
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
    elif system == "crocopay":
        async with connect("/root/paybots/crocopay/orders_crocopay.db") as db:
            cursor = await db.execute(
                "SELECT chat_id, amount FROM orders_crocopay WHERE order_id = ?", 
                (order_id,)
            )
            result = await cursor.fetchone()
            return result[0]
    elif system == "apay":
        async with connect("/root/paybots/apay/orders_apay.db") as db:
            cursor = await db.execute(
                "SELECT chat_id, amount FROM orders_apay WHERE order_id = ?", 
                (order_id,)
            )
            result = await cursor.fetchone()
            return result    

async def auto_cleanup():
    while True:
        try:
            systems = {
                "corkpay": "/root/paybots/corkpay/orders_corkpay.db",
                "epay": "/root/paybots/epay/orders_epay.db", 
                "p2p": "/root/paybots/p2pexpress/orders_p2p.db",
                "crocopay": "/root/paybots/crocopay/orders_crocopay.db",
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
        
        formatted_rows = []
        for row in rows:
            raw_date, amount, chat_id, system = row
            # Парсим дату из строки
            dt = datetime.fromisoformat(raw_date)
            
            # Форматируем отдельно дату и время
            date_str = dt.strftime("%Y-%m-%d")
            time_str = dt.strftime("%H:%M:%S")
            
            # Преобразуем сумму в целое число
            formatted_amount = int(round(float(amount)))
            
            formatted_rows.append((
                date_str,
                time_str,
                formatted_amount,
                str(int(chat_id)),  # ID как строка
                system
            ))
        
        # Создаем DataFrame с новыми колонками
        df = pd.DataFrame(
            formatted_rows, 
            columns=['Дата', 'Время', 'Сумма', 'Chat ID', 'Платежная система']
        )
        
        report_path = "/tmp/weekly_report.xlsx"
        
        # Сохраняем с правильными форматами
        with pd.ExcelWriter(report_path, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
            
            worksheet = writer.sheets['Sheet1']
            
            # Формат для ID
            for cell in worksheet['D']:
                cell.number_format = '@'
                
            # Формат для сумм
            for cell in worksheet['C']:
                cell.number_format = '0'
        
        return report_path
    except Exception as e:
        logger.error(f"Ошибка генерации отчета: {e}")
        return None

async def schedule_report():
    while True:
        now = datetime.now()
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
                file = FSInputFile(report_path)
                await bot.send_document(
                    chat_id=REPORT_CHAT_ID,
                    document=file,
                    caption="Еженедельный отчет об оплаченных заказах"
                )
                os.remove(report_path)
            except Exception as e:
                logger.error(f"Ошибка отправки отчета: {e}")

@dp.message(Command("xls"))
async def handle_xls_command(message: Message):
    if message.from_user.id not in ADMINS:
        await message.answer("У вас нет доступа к этому!")
    else:
        try:
            report_path = await generate_report()
            if report_path:
                file = FSInputFile(report_path)
                await message.answer_document(
                    document=file,
                    caption="Отчет за последние 7 дней"
                )
                os.remove(report_path)
            else:
                await message.answer("❌ Не удалось сформировать отчет")
        except Exception as e:
            logger.error(f"Ошибка команды /xls: {e}")
            await message.answer("⚠️ Произошла ошибка при формировании отчета")

@dp.message(Command("today"))
async def handle_today(message: Message):
    if message.from_user.id not in ADMINS:
        await message.answer("У вас нет доступа к этому!")
        return
    
    try:
        now = datetime.now()
        if now.time() < dt_time(6, 0):
            start_date = now - timedelta(days=1)
        else:
            start_date = now
        
        start = start_date.replace(hour=6, minute=0, second=0, microsecond=0)
        end = start + timedelta(hours=20)
        
        async with aiosqlite.connect("/root/paybots/paid_orders.db") as db:
            cursor = await db.execute(
                "SELECT chat_id, amount, system FROM paid_orders "
                "WHERE date BETWEEN ? AND ?",
                (start.isoformat(), end.isoformat()))
            
            rows = await cursor.fetchall()
            
            # Группируем и считаем
            report = {}
            for chat_id, amount, system in rows:
                net_amount = calculate_net_amount(system, float(amount))
                
                if chat_id not in report:
                    report[chat_id] = {
                        'total': 0.0,
                        'count': 0,
                        'net_total': 0.0
                    }
                
                report[chat_id]['total'] += amount
                report[chat_id]['count'] += 1
                report[chat_id]['net_total'] += net_amount
            
            response = "📊 Отчет за сегодня (чистые суммы):\n"
            for chat_id, data in report.items():
                response += (
                    f"\n👤 Chat ID: {chat_id}\n"
                    f"💳 Общая сумма: {int(data['total'])}₽\n"
                    f"💵 Чистая сумма: {int(data['net_total'])}₽\n"
                    f"🧾 Чеков: {data['count']}\n"
                )
            
            await message.answer(response)
            
    except Exception as e:
        logger.error(f"Ошибка команды /today: {e}")
        await message.answer("⚠️ Ошибка формирования отчета")

@dp.message(Command("ago"))
async def handle_ago(message: Message):
    if message.from_user.id not in ADMINS:
        await message.answer("У вас нет доступа к этому!")
        return
    
    try:
        now = datetime.now() - timedelta(days=1)
        if now.time() < dt_time(6, 0):
            start_date = now - timedelta(days=1)
        else:
            start_date = now
        
        start = start_date.replace(hour=6, minute=0, second=0, microsecond=0)
        end = start + timedelta(hours=20)
        
        async with aiosqlite.connect("/root/paybots/paid_orders.db") as db:
            cursor = await db.execute(
                "SELECT chat_id, amount, system FROM paid_orders "
                "WHERE date BETWEEN ? AND ?",
                (start.isoformat(), end.isoformat()))
            
            rows = await cursor.fetchall()
            
            report = {}
            for chat_id, amount, system in rows:
                net_amount = calculate_net_amount(system, float(amount))
                
                if chat_id not in report:
                    report[chat_id] = {
                        'total': 0.0,
                        'count': 0,
                        'net_total': 0.0
                    }
                
                report[chat_id]['total'] += amount
                report[chat_id]['count'] += 1
                report[chat_id]['net_total'] += net_amount
            
            response = "📊 Отчет за вчера (чистые суммы):\n"
            for chat_id, data in report.items():
                response += (
                    f"\n👤 Chat ID: {chat_id}\n"
                    f"💳 Общая сумма: {int(data['total'])}₽\n"
                    f"💵 Чистая сумма: {int(data['net_total'])}₽\n"
                    f"🧾 Чеков: {data['count']}\n"
                )
            
            await message.answer(response)
            
    except Exception as e:
        logger.error(f"Ошибка команды /ago: {e}")
        await message.answer("⚠️ Ошибка формирования отчета")

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