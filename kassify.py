import logging
import random
import requests
import io
from aiogram.types import InputFile
from aiogram import Bot, Dispatcher
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv
import os
import asyncio
from hashlib import md5

load_dotenv(dotenv_path='/root/paybots/api.env')
API_TOKEN = os.getenv('API_TOKEN_KASSIFY')
MERCHANT_ID = os.getenv('MERCHANT_ID_KASSIFY')
PASSWORD = os.getenv('PASSWORD_KASSIFY')

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

PAYMENT_URL = "https://payou.pro/sci/v1/"

def generate_id():
    return str(random.randint(1000000, 9999999))

user_data = {}

payment_methods = ["card_RUB", "card_RUB_MANUAL"]

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("Введите сумму платежа (без копеек):")
    user_data[message.chat.id] = {}

@dp.message(lambda msg: msg.text.isdigit())
async def get_sum(message: Message):
    amount = message.text + ".00"
    user_data[message.chat.id]['amount'] = amount
    keyboard = InlineKeyboardBuilder()
    for method in payment_methods:
        keyboard.add(InlineKeyboardButton(text=method, callback_data=method))
    keyboard.adjust(2)
    await message.answer("Выберите систему оплаты:", reply_markup=keyboard.as_markup())

@dp.callback_query(lambda call: call.data in payment_methods)
async def process_payment(callback_query: CallbackQuery):
    user_id = generate_id()
    order_id = generate_id()
    payment_system = callback_query.data
    amount = user_data[callback_query.message.chat.id]['amount']
    email = f"user_{user_id}@example.com"
    comment = "Test payment"
    hash_string = f"{MERCHANT_ID}:{amount}:{PASSWORD}:{payment_system}:{order_id}"
    signature = md5(hash_string.encode()).hexdigest()
    data = {
        "id": MERCHANT_ID,
        "sistems": payment_system,
        "summ": amount,
        "order_id": order_id,
        "Coments": comment,
        "hash": signature,
        "user_code": user_id,
        "user_email": email,
    }
    response = requests.get(PAYMENT_URL, params=data)
    if response.status_code == 200:
        if len(response.text) > 4000:
            log_file = io.BytesIO(response.text.encode('utf-8'))
            log_file.seek(0)
            await callback_query.message.answer_document(InputFile(log_file, filename="response.txt"))
        else:
            await callback_query.message.answer(f"Ответ сервера: {response.text}")
    else:
        await callback_query.message.answer(f"Ошибка: {response.status_code}. Ответ сервера: {response.reason}")
    await callback_query.message.answer("Введите сумму следующего платежа:")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
