import time
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import F
from dotenv import load_dotenv
import os

# Загрузка переменных окружения
load_dotenv(dotenv_path='/root/paybots/api.env')

API_TOKEN = os.getenv("API_TOKEN_CORKPAY")
MERCHANT_TOKEN = os.getenv("MERCHANT_TOKEN_CORKPAY")
MERCHANT_ID = os.getenv("MERCHANT_ID_CORKPAY")
CALLBACK_URL = "https://t.me/"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

def create_payment(amount):
    unix_time = int(time.time())
    data = {
        "merchant_id": MERCHANT_ID,
        "merchant_token": MERCHANT_TOKEN,
        "ip": unix_time,
        "amount": f"{amount:.2f}",
        "merchant_order": unix_time,
        "callback_url": CALLBACK_URL,
    }
    response = requests.post("https://oeiblas.shop/h2h/p2p", json=data)
    return response.json()

def check_payment(sign):
    data = {"sign": sign}
    response = requests.post("https://oeiblas.shop/h2h/check", json=data)
    return response.json()

@dp.message(Command("start"))
async def start_command(message: types.Message):
    await ask_amount(message.chat.id)

async def ask_amount(chat_id):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Создать платеж", callback_data="create_payment")
    keyboard.button(text="Проверить платеж", callback_data="check_payment")
    await bot.send_message(chat_id, "Введите сумму для оплаты:", reply_markup=keyboard.as_markup())

@dp.callback_query(F.data == "create_payment")
async def handle_create_payment(callback_query: types.CallbackQuery):
    await bot.send_message(callback_query.message.chat.id, "Введите сумму для нового платежа:")
    @dp.message(F.text.regexp(r"^\d+(\.\d{1,2})?$"))
    async def process_amount(message: types.Message):
        amount = float(message.text)
        payment_response = create_payment(amount)
        if payment_response.get("status") == "success":
            card = payment_response.get("card")
            end_time = payment_response.get("endTimeOfPayment")
            sign = payment_response.get("sign")
            await bot.send_message(
                message.chat.id,
                f"Платеж создан успешно:\nКарта: {card}\nСрок оплаты (UNIX): {end_time}\nSign: {sign}\nВведите следующую сумму:",
            )
        else:
            await bot.send_message(
                message.chat.id,
                f"Ошибка создания платежа: {payment_response.get('reason')}\nПопробуйте снова."
            )
        await ask_amount(message.chat.id)

@dp.callback_query(F.data == "check_payment")
async def handle_check_payment(callback_query: types.CallbackQuery):
    await bot.send_message(callback_query.message.chat.id, "Введите Sign для проверки платежа:")
    @dp.message()
    async def process_sign(message: types.Message):
        sign = message.text
        check_response = check_payment(sign)
        if check_response.get("status") == "success":
            await bot.send_message(
                message.chat.id,
                f"Платеж найден:\nСтатус: {check_response.get('status')}\nДетали: {check_response}",
            )
        else:
            await bot.send_message(
                message.chat.id,
                f"Ошибка проверки платежа: {check_response.get('reason')}\nПопробуйте снова."
            )
        await ask_amount(message.chat.id)

if __name__ == "__main__":
    dp.run_polling(bot)
