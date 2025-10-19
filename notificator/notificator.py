import logging
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN, DOMAIN, ADMINS
from aiogram.webhook.aiohttp_server import setup_application
from datetime import datetime, timedelta
import aiosqlite
from datetime import time as dt_time
from aiohttp.helpers import AccessLogger

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class FilteredAccessLogger(AccessLogger):
    def __init__(self, logger, log_format):
        super().__init__(logger, log_format)
        self.allowed_endpoints = [
            '/corkpay/',
            '/epay/', 
            '/crocopay/',
            '/cyber/',
            '/tg_webhook'
        ]
    
    def log(self, request, response, time):
        if any(request.path.startswith(endpoint) for endpoint in self.allowed_endpoints):
            super().log(request, response, time)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


COMMISSION_RATES = {
    "epay": 0.30, 
    "corkpay": 0.30,
    "cyber": 0.25,
    "crocopay": 0.15
}

DB_PATHS = {
    "crocopay": "/root/paybots/crocopay/orders_crocopay.db"
}

def calculate_net_amount(system: str, amount: float) -> float:
    rate = COMMISSION_RATES.get(system)
    if rate is None:
        return float(amount)
    if callable(rate):
        try:
            r = rate(float(amount))
        except Exception:
            return float(amount)
        return float(amount) * (1 - float(r))
    try:
        r = float(rate)
    except Exception:
        return float(amount)
    return float(amount) * (1 - r)

async def process_webhook(request: web.Request, system: str, message_template: str):
    bot: Bot = request.app['bot']
    try:
        data = await request.json() if system != "corkpay" else await request.text()
        logger.info(f"Получен вебхук для {system}: {data}")

        order_id = data.get('transaction_id') or data.get('merchant_order') or request.match_info.get('order_id') or request.match_info.get('transaction_id')
        amount = data.get('total') or data.get('amount')

        chat_id, amount = await get_chat_id(order_id, system)
        if chat_id is None:
            return web.Response(text="OK")

        await bot.send_message(
            chat_id=int(chat_id),
            text=message_template.format(order_id=order_id, amount=amount)
        )
        await add_paid_order(float(amount), int(chat_id), system)

        return web.Response(text="OK", status=200)
    except Exception as e:
        logger.error(f"Ошибка обработки вебхука для {system}: {e}")
        return web.Response(text="OK", status=200)

async def handle_corkpay(request: web.Request):
    bot: Bot = request.app['bot']
    logger.info(f"Получен вебхук для corkpay: {request.text()}")
    chat_id = request.match_info.get('chat_id')
    data = await request.json()
    logger.info(f"Получен вебхук для corkpay: {data}")
    order_id = data.get('external_uui')
    amount = data.get('amount')
    await bot.send_message(chat_id=chat_id, text=f"🟣CORKPAY:\n✅Заказ №{order_id} на сумму {amount}₽ успешно оплачен!")
    await add_paid_order(float(amount), int(chat_id), "corkpay")
    return web.Response(text="OK", status=200)

async def handle_cyber(request: web.Request):
    bot: Bot = request.app['bot']
    data = await request.json()
    logger.info(f"Получен вебхук для cyber: {data}")
    chat_id = request.match_info.get('chat_id')
    status = data.get('status')
    order_id = data.get('request_id')
    amount = data.get('sum')
    amount_float = float(amount)
    amount_int = int(amount_float)
    if status == "success":
        await bot.send_message(chat_id=chat_id, text=f"🟠CyberMoney:\n✅Заказ №{order_id} на сумму {amount_int}₽ успешно оплачен!")
        await add_paid_order(amount_float, int(chat_id), "cyber")
    else:
        pass 
    await add_paid_order(float(amount), int(chat_id), "cyber")
    return web.Response(text="OK", status=200)

async def handle_epay(request: web.Request):
    bot: Bot = request.app['bot']
    chat_id = request.match_info.get('chat_id')
    data = await request.json()
    order_id = data.get('transaction_id')
    amount = data.get('amount')
    await bot.send_message(chat_id=chat_id, text=f"🟡E-PAY:\n✅Заказ №{order_id} на сумму {amount}₽ успешно оплачен!")
    await add_paid_order(float(amount), int(chat_id), "epay")
    return web.Response(text="OK", status=200)

async def handle_crocopay(request: web.Request):
    return await process_webhook(request, "crocopay", "🟢CrocoPay:\n✅Заказ №{order_id} на сумму {amount}₽ успешно оплачен!")

async def start_web_app(dispatcher: Dispatcher, bot: Bot):
    app = web.Application()
    app['bot'] = bot
    
    # Настраиваем кастомный логгер доступа
    app['access_logger'] = FilteredAccessLogger(
        logger=logging.getLogger('aiohttp.access'),
        log_format='%a %t "%r" %s %b "%{Referer}i" "%{User-Agent}i"'
    )
    
    app.router.add_post('/corkpay/{chat_id}', handle_corkpay)
    app.router.add_route('*', '/', handle_root)
    app.router.add_post('/epay/{chat_id}', handle_epay)
    app.router.add_post('/crocopay/{order_id}', handle_crocopay)
    app.router.add_post('/cyber/{chat_id}', handle_cyber)
    SimpleRequestHandler(
        dispatcher=dispatcher,
        bot=bot,
    ).register(app, path="/tg_webhook")
    app.router.add_route('*', '/{path:.*}', handle_all_other)
    return app

async def handle_root(request):
    return web.Response(text="Forbidden", status=403)

async def handle_all_other(request):
    return web.Response(text="Forbidden", status=403)

async def get_chat_id(order_id, system):
    db_path = DB_PATHS.get(system)
    if not db_path:
        logger.error(f"Неизвестная система: {system}")
        return None, None

    async with aiosqlite.connect(db_path) as db:
        # Fix: Add f-string prefix to properly format the table name
        query = f"SELECT chat_id, amount FROM orders_{system} WHERE order_id = ?"
        cursor = await db.execute(query, (order_id,))
        result = await cursor.fetchone()

    if result:
        return (result[0], result[1]) if len(result) > 1 else (result[0], None)
    return None, None

async def auto_cleanup():
    while True:
        try:
            cutoff = (datetime.now() - timedelta(days=10)).isoformat()
            for system, db_path in DB_PATHS.items():
                async with aiosqlite.connect(db_path) as db:
                    await db.execute(
                        f"DELETE FROM orders_{system} WHERE timestamp < ?",
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

@dp.message(Command("ago"))
@dp.message(Command("today"))
async def handle_ago(message: Message):
    if message.from_user.id not in ADMINS:
        await message.answer("У вас нет доступа к этому!")
        return
    
    try:
        if message.text == "/ago":
            days = "вчера"
            now = datetime.now() - timedelta(days=1)
        else:
            days = "сегодня"
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
            
            report = {}
            for chat_id, amount, system in rows:
                if amount is None:
                    logger.warning(f"Пропущена запись с пустой суммой для chat_id={chat_id}, system={system}")
                    continue
                amt = float(amount)
                net_amount = calculate_net_amount(system, amt)

                if chat_id not in report:
                    report[chat_id] = {
                        'total': 0.0,
                        'count': 0,
                        'net_total': 0.0
                    }

                report[chat_id]['total'] += amt
                report[chat_id]['count'] += 1
                report[chat_id]['net_total'] += net_amount
            
            response = f"📊 Отчет за {days}:\n"
            for chat_id, data in report.items():
                response += (
                    f"\n👤 Chat ID: {chat_id}\n"
                    f"💳 Общая сумма: {int(data['total'])}₽\n"
                    f"💵 Чистая сумма: {int(data['net_total'])}₽\n"
                    f"🧾 Чеков: {data['count']}\n"
                )
            
            await message.answer(response)
            
    except Exception as e:
        logger.error(f"Ошибка команды: {e}")
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
    logger.info("Запуск задач автоочистки и отчетов")
    asyncio.gather(auto_cleanup())
    await create_paid_orders_table()
    try:
        logger.info("Удаление старого вебхука...")
        await bot.delete_webhook()
        logger.info(f"Настройка вебхука: https://{DOMAIN}/tg_webhook")
        await bot.set_webhook(url=f"https://{DOMAIN}/tg_webhook")

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