import logging
import requests
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ParseMode
from aiogram.utils import exceptions
from aiogram.utils.executor import start_polling

logging.basicConfig(level=logging.INFO)

TELEGRAM_BOT_TOKEN = '7714027113:AAGNL1vKxe6lg0fN9BHbFLKVOlnp2s7T9DQ'
API_TOKEN = '832d6fcd0aba0b92bd0438872d6e7461'
BASE_URL = 'https://api.cashinout.io'

bot = Bot(token=TELEGRAM_BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Функция для генерации подписи
def generate_signature(body, merchant_token):
    import hmac
    import hashlib
    from urllib.parse import quote_plus
    body.pop('signature', None)
    sorted_params = sorted(body.items(), key=lambda item: item[0])
    check_string = '&'.join([f"{quote_plus(k)}={quote_plus(v)}" for k, v in sorted_params])
    signature = hmac.new(merchant_token.encode(), check_string.encode(), hashlib.sha256).hexdigest()
    return signature

# Команда /start
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Привет! Я бот для работы с API CashInOut. Используйте команды /create_one_time_invoice, /create_reusable_invoice, /find_invoice, /get_invoices, /close_invoice, /withdraw.")

# Команда /create_one_time_invoice
@dp.message_handler(commands=['create_one_time_invoice'])
async def create_one_time_invoice(message: types.Message):
    data = {
        "amount": "100",
        "currencies": [0, 1],
        "durationSeconds": 86400,
        "callbackUrl": "http://yourcallbackurl.com",
        "redirectUrl": "http://yourredirecturl.com",
        "externalText": "Test invoice"
    }
    headers = {'Authorization': f'Bearer {API_TOKEN}'}
    response = requests.post(f"{BASE_URL}/merchant/createOneTimeInvoice", json=data, headers=headers)
    if response.status_code == 200:
        await message.reply(f"Идентификатор созданного одноразового счета: {response.json()}")
    else:
        await message.reply(f"Ошибка при создании одноразового счета: {response.text}")

# Команда /create_reusable_invoice
@dp.message_handler(commands=['create_reusable_invoice'])
async def create_reusable_invoice(message: types.Message):
    data = {
        "currencies": [0, 1],
        "callbackUrl": "http://yourcallbackurl.com",
        "redirectUrl": "http://yourredirecturl.com",
        "externalText": "Test reusable invoice"
    }
    headers = {'Authorization': f'Bearer {API_TOKEN}'}
    response = requests.post(f"{BASE_URL}/merchant/createReusableInvoice", json=data, headers=headers)
    if response.status_code == 200:
        await message.reply(f"Идентификатор созданного многоразового счета: {response.json()}")
    else:
        await message.reply(f"Ошибка при создании многоразового счета: {response.text}")

# Команда /find_invoice
@dp.message_handler(commands=['find_invoice'])
async def find_invoice(message: types.Message):
    invoice_id = message.get_args()
    if not invoice_id:
        await message.reply("Пожалуйста, укажите идентификатор счета.")
        return
    headers = {'Authorization': f'Bearer {API_TOKEN}'}
    response = requests.get(f"{BASE_URL}/merchant/findInvoice/{invoice_id}", headers=headers)
    if response.status_code == 200:
        await message.reply(str(response.json()))
    else:
        await message.reply(f"Ошибка при получении информации о счете: {response.text}")

# Команда /get_invoices
@dp.message_handler(commands=['get_invoices'])
async def get_invoices(message: types.Message):
    offset = 0
    limit = 10
    headers = {'Authorization': f'Bearer {API_TOKEN}'}
    response = requests.get(f"{BASE_URL}/merchant/invoices?offset={offset}&limit={limit}", headers=headers)
    if response.status_code == 200:
        await message.reply(str(response.json()))
    else:
        await message.reply(f"Ошибка при получении истории счетов: {response.text}")

# Команда /close_invoice
@dp.message_handler(commands=['close_invoice'])
async def close_invoice(message: types.Message):
    invoice_id = message.get_args()
    if not invoice_id:
        await message.reply("Пожалуйста, укажите идентификатор счета.")
        return
    headers = {'Authorization': f'Bearer {API_TOKEN}'}
    response = requests.post(f"{BASE_URL}/merchant/closeInvoice/{invoice_id}", headers=headers)
    if response.status_code == 200:
        await message.reply("Счет успешно закрыт.")
    else:
        await message.reply(f"Ошибка при закрытии счета: {response.text}")

# Команда /withdraw
@dp.message_handler(commands=['withdraw'])
async def withdraw(message: types.Message):
    data = {
        "currencyFrom": "USDT",
        "toAmount": "100",
        "callbackUrl": "http://yourcallbackurl.com",
        "type": 0,
        "currencyTo": "BTC",
        "walletNumber": "your_wallet_number"
    }
    headers = {'Authorization': f'Bearer {API_TOKEN}'}
    response = requests.post(f"{BASE_URL}/withdraw", json=data, headers=headers)
    if response.status_code == 200:
        await message.reply(str(response.json()))
    else:
        await message.reply(f"Ошибка при выводе средств: {response.text}")

# Функция для обработки callbackов (пример)
async def process_callbacks():
    while True:
        # Здесь можно добавить логику для периодической проверки статуса счетов
        # или настройки webhook для приема уведомлений от API
        await asyncio.sleep(300)  # Проверка каждые 5 минут

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(process_callbacks())
    try:
        loop.run_until_complete(dp.start_polling())
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        loop.run_until_complete(dp.storage.close())
        loop.run_until_complete(dp.storage.wait_closed())
        loop.stop()