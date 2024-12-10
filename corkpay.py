import time
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv(dotenv_path='/root/paybots/api.env')

API_TOKEN = os.getenv("API_TOKEN_CORKPAY")
MERCHANT_TOKEN = os.getenv("MERCHANT_TOKEN_CORKPAY")
MERCHANT_ID = os.getenv("MERCHANT_ID_CORKPAY")
CALLBACK_URL = "https://t.me/"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

PAYMENT_URL = "https://oeiblas.shop/h2h/p2p"
CHECK_URL = "https://corkpay.cc/api/apiOrderStatus"

def create_payment(amount):
    unix_time = int(time.time())
    data = {
        "merchant_id": MERCHANT_ID,
        "merchant_token": MERCHANT_TOKEN,
        "ip": str(unix_time),
        "amount": f"{amount:.2f}",
        "merchant_order": str(unix_time),
        "callback_url": CALLBACK_URL,
    }
    response = requests.post(PAYMENT_URL, json=data)
    return response.json()

def check_payment(sign):
    data = {
        "merchant_token": MERCHANT_TOKEN,
        "sign": sign,
    }
    response = requests.post(CHECK_URL, json=data)
    return response.json()

@dp.message(Command("start"))
async def start_command(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Создать платеж", callback_data="create_payment")],
        [InlineKeyboardButton(text="Проверить платеж", callback_data="check_payment")],
    ])
    await message.answer("Добро пожаловать! Выберите действие:", reply_markup=keyboard)

@dp.callback_query(lambda callback: callback.data == "create_payment")
async def handle_create_payment(callback_query: types.CallbackQuery):
    await bot.send_message(callback_query.message.chat.id, "Введите сумму для нового платежа:")

    @dp.message(lambda message: message.text.replace('.', '', 1).isdigit())
    async def process_amount(message: types.Message):
        amount = float(message.text)
        payment_response = create_payment(amount)
        if payment_response.get("status") == "success":
            card = payment_response.get("card")
            end_time = payment_response.get("endTimeOfPayment")
            sign = payment_response.get("sign")
            await bot.send_message(
                message.chat.id,
                f"Платеж создан успешно:\nКарта: {card}\nСрок оплаты (UNIX): {end_time}\nSign: {sign}\nВведите следующую сумму или выберите действие."
            )
        else:
            await bot.send_message(
                message.chat.id,
                f"Ошибка создания платежа: {payment_response.get('reason')}\nПопробуйте снова."
            )
        dp.message_handlers.unregister(process_amount)

@dp.callback_query(lambda callback: callback.data == "check_payment")
async def handle_check_payment(callback_query: types.CallbackQuery):
    await bot.send_message(callback_query.message.chat.id, "Введите Sign для проверки платежа:")

    @dp.message()
    async def process_sign(message: types.Message):
        sign = message.text
        check_response = check_payment(sign)
        if check_response.get("status") in ["wait", "success"]:
            order_status = check_response.get("status")
            await bot.send_message(
                message.chat.id,
                f"Проверка платежа:\nСтатус: {order_status}\nSign: {check_response.get('sign')}"
            )
        else:
            await bot.send_message(
                message.chat.id,
                f"Ошибка проверки платежа: {check_response.get('reason')}\nПопробуйте снова."
            )
        dp.message_handlers.unregister(process_sign)

if __name__ == "__main__":
    dp.run_polling(bot)
