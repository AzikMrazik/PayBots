import logging
import time
import requests
import json
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv
import os

# Загрузка переменных окружения
load_dotenv(dotenv_path='/root/paybots/api.env')

API_TOKEN = os.getenv("API_TOKEN_CORKPAY")
MERCHANT_TOKEN = os.getenv("MERCHANT_TOKEN_CORKPAY")
MERCHANT_ID = os.getenv("MERCHANT_ID_CORKPAY")
CALLBACK_URL = "https://t.me/"

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# FSM для управления состояниями
class PaymentStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_sign = State()

# Главное меню
main_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Создать платеж", callback_data="create_payment")],
        [InlineKeyboardButton(text="Проверить платеж", callback_data="check_payment")]
    ]
)

@dp.message(Command(commands=['start']))
async def send_welcome(message: types.Message):
    await message.answer("Добро пожаловать! Выберите действие:", reply_markup=main_menu)

@dp.callback_query(lambda call: call.data == "create_payment")
async def create_payment(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("Введите сумму для создания платежа:")
    await state.set_state(PaymentStates.waiting_for_amount)

@dp.message(PaymentStates.waiting_for_amount)
async def process_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
        merchant_order = str(int(time.time()))
        ip = str(int(time.time()))  # Укажите правильный IP при необходимости

        # Отправка POST-запроса
        url = "https://dejukal.shop/h2h/p2p"
        payload = {
            "merchant_id": str(MERCHANT_ID),
            "merchant_token": MERCHANT_TOKEN,
            "ip": ip,
            "amount": amount,
            "merchant_order": merchant_order,
            "callback_url": CALLBACK_URL
        }
        response = requests.post(url, json=payload)
        response_data = response.json()

        if response_data.get("status") == "success":
            card = response_data["card"]
            sign = response_data["sign"]
            await message.answer(f"К оплате ровно - {amount}\nНомер карты - {card}\n\nПосле оплаты отправьте, пожалуйста, скриншот чека.\nЗаявка на оплату действительна 15 минут.")
            await message.answer(f"SIGN для проверки отправлен следующим сообщением.")
            await message.answer(sign)
        else:
            reason = response_data.get("reason", "Неизвестная ошибка")
            await message.answer(f"Ошибка: {reason}")
    except Exception as e:
        await message.answer(f"Произошла ошибка: {str(e)}")
    finally:
        await state.clear()
        await message.answer("Выберите следующее действие:", reply_markup=main_menu)

@dp.callback_query(lambda call: call.data == "check_payment")
async def check_payment(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("Введите SIGN для проверки:")
    await state.set_state(PaymentStates.waiting_for_sign)

@dp.message(PaymentStates.waiting_for_sign)
async def process_sign(message: types.Message, state: FSMContext):
    try:
        sign = message.text

        # Отправка POST-запроса
        url = "https://corkpay.cc/api/apiOrderStatus"
        payload = {
            "merchant_token": MERCHANT_TOKEN,
            "sign": sign
        }
        response = requests.post(url, json=payload)
        response_data = response.json()

        status = response_data.get("status")
        if status == "wait":
            await message.answer("Заказ не оплачен.")
        elif status == "success":
            await message.answer("Заказ оплачен.")
        else:
            await message.answer("Неизвестный статус заказа.")

    except Exception as e:
        await message.answer(f"Произошла ошибка: {str(e)}")
    finally:
        await state.clear()
        await message.answer("Выберите следующее действие:", reply_markup=main_menu)

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
