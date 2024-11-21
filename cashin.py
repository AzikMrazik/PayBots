import aiohttp
import hmac
import hashlib
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

load_dotenv(dotenv_path='/root/paybots/api.env')

API_TOKEN = os.getenv('API_TOKEN_CASHIN')
BASE_URL = "https://api.cashinout.io"
AUTH_TOKEN = os.getenv('AUTH_TOKEN_CASHIN')
router = Router()
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(router)

WUD_ID = 0
USDT_ID = 5
REDIRECT_URL = "https://telegram.org/"
MERCHANT_TOKEN = AUTH_TOKEN

def main_menu():
    keyboard = [
        [InlineKeyboardButton(text="Создать платеж", callback_data='create_payment')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def generate_signature(data: dict, merchant_token: str) -> str:
    if "signature" in data:
        del data["signature"]
    sorted_params = sorted(data.items())
    check_string = "\n".join([f"{k}={v}" for k, v in sorted_params])
    signature = hmac.new(
        merchant_token.encode('utf-8'),
        check_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature

def verify_signature(data: dict, merchant_token: str) -> bool:
    received_signature = data.get("signature", "")
    if not received_signature:
        return True
    expected_signature = generate_signature(data, merchant_token)
    return hmac.compare_digest(received_signature, expected_signature)

@router.message(Command(commands=['start']))
async def send_welcome(message: types.Message):
    await message.answer("Добро пожаловать! Выберите действие:", reply_markup=main_menu())

@router.callback_query(lambda c: c.data == 'create_payment')
async def create_payment(callback_query: types.CallbackQuery):
    await callback_query.message.answer("Введите сумму для создания платежа:")
    router.message.register(process_payment_amount, F.text)

async def process_payment_amount(message: types.Message):
    amount = message.text
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/merchant/createOneTimeInvoice",
            headers={"Authorization": AUTH_TOKEN},
            json={
                "amount": amount,
                "currency": WUD_ID,
                "currencies": [WUD_ID],
                "durationSeconds": 86400,
                "redirectUrl": REDIRECT_URL
            }
        ) as resp:
            data = await resp.json()
            if verify_signature(data, MERCHANT_TOKEN):
                payment_link = data.get("data")
                if payment_link:
                    payment_url = f"https://pay.cashinout.io/{payment_link}"
                    await message.answer(f"Ссылка для оплаты: {payment_url}")
                    await message.answer("Введите сумму для следующего платежа:", reply_markup=main_menu())
                else:
                    await message.answer("Не удалось получить ссылку для оплаты.", reply_markup=main_menu())
            else:
                await message.answer("Ошибка: неподтвержденная подпись данных.", reply_markup=main_menu())

@router.callback_query(lambda c: c.data == 'payment_history')
async def payment_history(callback_query: types.CallbackQuery):
    await callback_query.message.answer("Получаю историю платежей...")
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{BASE_URL}/merchant/invoices?offset=0&limit=10&filters={{}}",
            headers={"Authorization": AUTH_TOKEN}
        ) as resp:
            data = await resp.json()
            if verify_signature(data, MERCHANT_TOKEN):
                payments = data.get('data', {}).get('entries', [])
                if not payments:
                    await callback_query.message.answer("История платежей пуста.", reply_markup=main_menu())
                else:
                    history_message = "История платежей за последние 24 часа:\n\n"
                    for idx, payment in enumerate(payments, 1):
                        payment_url = f"https://pay.cashinout.io/{payment['id']}"
                        history_message += f"{idx}. Статус: {payment['status']}, Сумма: {payment['amount']} RUB, Ссылка: {payment_url}\n"
                    await callback_query.message.answer(history_message, reply_markup=main_menu())
            else:
                await callback_query.message.answer("Ошибка: неподтвержденная подпись данных.", reply_markup=main_menu())

if __name__ == '__main__':
    dp.run_polling(bot)
