import time
import requests
from aiogram import Bot, Dispatcher, Router, types
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
router = Router()

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
    print(f"Create Payment Request: {data}")  # Debug log
    print(f"Create Payment Response: {response.json()}")  # Debug log
    return response.json()

def check_payment(sign):
    data = {
        "merchant_token": MERCHANT_TOKEN,
        "sign": sign,
    }
    response = requests.post(CHECK_URL, json=data)
    print(f"Check Payment Request: {data}")  # Debug log
    print(f"Check Payment Response: {response.json()}")  # Debug log
    return response.json()

@router.message(Command("start"))
async def start_command(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Создать платеж", callback_data="create_payment")],
        [InlineKeyboardButton(text="Проверить платеж", callback_data="check_payment")],
    ])
    print(f"Start Command Triggered by User: {message.from_user.id}")  # Debug log
    await message.answer("Добро пожаловать! Выберите действие:", reply_markup=keyboard)

@router.callback_query(lambda callback: callback.data == "create_payment")
async def handle_create_payment(callback_query: types.CallbackQuery):
    print(f"Create Payment Triggered by User: {callback_query.from_user.id}")  # Debug log
    await bot.send_message(callback_query.message.chat.id, "Введите сумму для нового платежа:")

    @router.message(lambda message: message.text.replace('.', '', 1).isdigit())
    async def process_amount(message: types.Message):
        amount = float(message.text)
        print(f"User Input Amount: {amount}")  # Debug log
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
        router.message.handlers.remove(process_amount)

    dp.include_router(router)

@router.callback_query(lambda callback: callback.data == "check_payment")
async def handle_check_payment(callback_query: types.CallbackQuery):
    print(f"Check Payment Triggered by User: {callback_query.from_user.id}")  # Debug log
    await bot.send_message(callback_query.message.chat.id, "Введите Sign для проверки платежа:")

    @router.message()
    async def process_sign(message: types.Message):
        sign = message.text
        print(f"User Input Sign: {sign}")  # Debug log
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
        router.message.handlers.remove(process_sign)

    dp.include_router(router)

if __name__ == "__main__":
    print("Bot is starting...")  # Debug log
    dp.include_router(router)
    dp.run_polling(bot)
