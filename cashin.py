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
        [InlineKeyboardButton(text="Создать платеж", callback_data='create_payment')],
        [InlineKeyboardButton(text="Баланс & Вывод", callback_data='balance_withdraw')]
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
        return False
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
                else:
                    await message.answer("Не удалось получить ссылку для оплаты.")
            else:
                await message.answer("Ошибка: неподтвержденная подпись данных.")
    await message.answer("Выберите дальнейшее действие:", reply_markup=main_menu())


@router.callback_query(lambda c: c.data == 'balance_withdraw')
async def balance_and_withdraw(callback_query: types.CallbackQuery):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{BASE_URL}/merchant/balance",
            headers={"Authorization": AUTH_TOKEN}
        ) as resp:
            data = await resp.json()
            if verify_signature(data, MERCHANT_TOKEN):
                balance = data.get("data", {}).get("balance", 0)
                await callback_query.message.answer(
                    f"Ваш текущий баланс: {balance} RUB\n\nДля вывода средств свяжитесь с поддержкой.",
                    reply_markup=main_menu()
                )
            else:
                await callback_query.message.answer("Ошибка: неподтвержденная подпись данных.", reply_markup=main_menu())


@router.message(lambda message: message.json.get("event") == "payment_notification")
async def handle_payment_notification(message: types.Message):
    data = message.json
    if verify_signature(data, MERCHANT_TOKEN):
        status = data.get("status")
        amount = data.get("amount")
        await message.answer(f"Платеж на сумму {amount} RUB получил статус: {status}.")
    else:
        await message.answer("Ошибка: неподтвержденная подпись уведомления.")


if __name__ == '__main__':
    dp.run_polling(bot)
