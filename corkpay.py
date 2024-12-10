import time
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path='/root/paybots/api.env')

API_TOKEN = os.getenv('API_TOKEN_CORKPAY')
MERCHANT_TOKEN = os.getenv('MERCHANT_TOKEN_CORKPAY')
MERCHANT_ID = os.getenv('MERCHANT_ID_CORKPAY')

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class PaymentState(StatesGroup):
    waiting_for_amount = State()
    waiting_for_sign = State()

async def create_payment(amount: str):
    url = "https://oeiblas.shop/h2h/p2p"
    merchant_order = str(int(time.time()))
    data = {
        "merchant_id": MERCHANT_ID,
        "merchant_token": MERCHANT_TOKEN,
        "ip": merchant_order,
        "amount": amount,
        "merchant_order": merchant_order,
        "callback_url": "https://t.me/"
    }
    response = requests.post(url, json=data)
    return response.json()

async def check_payment(sign: str):
    url = "https://corkpay.cc/api/apiOrderStatus"
    data = {
        "merchant_token": MERCHANT_TOKEN,
        "sign": sign
    }
    response = requests.post(url, json=data)
    return response.json()

@dp.message(Command("start"))
async def start_command(message: types.Message, state: FSMContext):
    await message.answer("Введите сумму для оплаты:")
    await state.set_state(PaymentState.waiting_for_amount)

@dp.message(PaymentState.waiting_for_amount)
async def handle_amount(message: types.Message, state: FSMContext):
    amount = message.text
    try:
        float(amount)
    except ValueError:
        await message.answer("Введите корректную сумму в формате числа.")
        return

    payment_response = await create_payment(amount)

    if payment_response.get("status") == "success":
        card = payment_response.get("card")
        sign = payment_response.get("sign")
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="Проверить платеж", callback_data="check_payment")
        keyboard.button(text="Создать платеж", callback_data="create_payment")
        keyboard = keyboard.as_markup()

        await message.answer(f"Платеж создан успешно!\nКарта для оплаты: {card}\nSign: {sign}", reply_markup=keyboard)
        await state.update_data(sign=sign)
    else:
        reason = payment_response.get("reason", "Неизвестная ошибка")
        await message.answer(f"Ошибка создания платежа: {reason}")

@dp.callback_query(lambda c: c.data == "check_payment")
async def check_payment_callback(callback_query: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    sign = user_data.get("sign")
    if not sign:
        await callback_query.message.answer("Сначала создайте платеж.")
        return

    payment_status = await check_payment(sign)
    await callback_query.message.answer(f"Результат проверки: {payment_status}")

@dp.callback_query(lambda c: c.data == "create_payment")
async def create_payment_callback(callback_query: types.CallbackQuery):
    await callback_query.message.answer("Введите сумму для оплаты:")
    await PaymentState.waiting_for_amount.set()

if __name__ == "__main__":
    dp.run_polling(bot)
