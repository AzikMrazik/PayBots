import logging
import time
import requests
from requests.exceptions import Timeout, RequestException
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
def main_menu():
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Создать платеж", callback_data="create_payment")],
        [InlineKeyboardButton(text="Проверить платеж", callback_data="check_payment")]
    ])
    return markup

@dp.message(Command(commands=['start']))
async def send_welcome(message: types.Message):
    await message.answer("Добро пожаловать! Выберите действие:", reply_markup=main_menu())

@dp.callback_query(lambda callback_query: callback_query.data == "create_payment")
async def create_payment(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Введите сумму для создания платежа:")
    await state.set_state(PaymentStates.waiting_for_amount)

@dp.message(PaymentStates.waiting_for_amount)
async def process_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
        merchant_order = str(int(time.time()))
        ip = str(int(time.time()))  # Укажите правильный IP при необходимости

        # Отправка POST-запроса с таймаутом
        url = "https://dejukal.shop/h2h/p2p"
        payload = {
            "merchant_id": str(MERCHANT_ID),
            "merchant_token": MERCHANT_TOKEN,
            "ip": ip,
            "amount": amount,
            "merchant_order": merchant_order,
            "callback_url": CALLBACK_URL
        }
        try:
            response = requests.post(url, json=payload, timeout=20)
            response.raise_for_status()
            response_data = response.json()
        except Timeout:
            await message.answer("Ошибка: сервер не отвечает в течение 20 секунд. Попробуйте позже.")
            return
        except RequestException as e:
            await message.answer(f"Ошибка при отправке запроса: {str(e)}")
            return

        if response_data.get("status") == "success":
            card = response_data["card"]
            sign = response_data["sign"]
            amount_str = int(amount) if amount.is_integer() else amount
            await message.answer(
                f"К оплате ровно - {amount_str}\nНомер карты - {card}\n\nПосле оплаты отправьте, пожалуйста, скриншот чека. Заявка на оплату действительна 15 минут."
            )
            await message.answer(f"SIGN для проверки:\n`{sign}`", parse_mode="Markdown")
            await message.answer("Введите сумму для следующего платежа:", 
                                 reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                     [InlineKeyboardButton(text="Главное меню", callback_data="main_menu")]
                                 ]))
            await state.set_state(PaymentStates.waiting_for_amount)  # Повтор запроса суммы
        else:
            reason = response_data.get("reason", "Неизвестная ошибка")
            await message.answer(f"Ошибка: {reason}", reply_markup=main_menu())
    except Exception as e:
        await message.answer(f"Произошла ошибка: {str(e)}", reply_markup=main_menu())

@dp.callback_query(lambda callback_query: callback_query.data == "check_payment")
async def check_payment(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Введите SIGN для проверки:")
    await state.set_state(PaymentStates.waiting_for_sign)

@dp.message(PaymentStates.waiting_for_sign)
async def process_sign(message: types.Message, state: FSMContext):
    try:
        sign = message.text

        # Отправка POST-запроса с таймаутом
        url = "https://corkpay.cc/api/apiOrderStatus"
        payload = {
            "merchant_token": MERCHANT_TOKEN,
            "sign": sign
        }
        try:
            response = requests.post(url, json=payload, timeout=20)
            response.raise_for_status()
            response_data = response.json()
        except Timeout:
            await message.answer("Ошибка: сервер не отвечает в течение 20 секунд. Попробуйте позже.")
            return
        except RequestException as e:
            await message.answer(f"Ошибка при отправке запроса: {str(e)}")
            return

        status = response_data.get("status")
        if status == "wait":
            await message.answer("Заказ не оплачен.")
        elif status == "success":
            await message.answer("Заказ оплачен.")
        else:
            await message.answer("Неизвестный статус заказа.")

        await message.answer("Введите SIGN для следующей проверки или вернитесь в главное меню.", 
                             reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                 [InlineKeyboardButton(text="Главное меню", callback_data="main_menu")]
                             ]))
    except Exception as e:
        await message.answer(f"Произошла ошибка: {str(e)}", reply_markup=main_menu())

@dp.callback_query(lambda callback_query: callback_query.data == "main_menu")
async def back_to_main_menu(callback_query: types.CallbackQuery):
    await callback_query.message.answer("Выберите действие:", reply_markup=main_menu())

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
