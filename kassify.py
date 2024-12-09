import logging
import random
import requests
from aiogram import Bot, Dispatcher
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv
import os
import asyncio
from bs4 import BeautifulSoup

# Загрузка конфигурации
load_dotenv(dotenv_path='/root/paybots/api.env')
API_TOKEN = os.getenv('API_TOKEN_KASSIFY')
MERCHANT_ID = os.getenv('MERCHANT_ID_KASSIFY')
KEY_SHOP = os.getenv('KEY_SHOP_KASSIFY')

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# URL для отправки платежа
PAYMENT_URL = "https://kassify.com/sci/"

# Генерация 7-значного ID
def generate_id():
    return str(random.randint(1000000, 9999999))

# Хранение данных пользователя
user_data = {}

# Inline-кнопки для выбора платежной системы
payment_methods = ["epaycoreRUB", "yoomoney", "yoomoney_HIYP", "P2P_pay"]

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("Введите сумму платежа (без копеек):")
    user_data[message.chat.id] = {}

@dp.message(lambda msg: msg.text.isdigit())
async def get_sum(message: Message):
    amount = message.text + ".00"
    user_data[message.chat.id]['amount'] = amount

    # Создание клавиатуры с платёжными методами
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

    # Формирование подписи
    hash_string = f"{MERCHANT_ID}:{amount}:{KEY_SHOP}:{order_id}"
    signature = requests.utils.quote(hash_string)

    # Формирование данных для запроса
    data = {
        "ids": MERCHANT_ID,
        "summ": amount,
        "us_id": order_id,
        "user_code": user_id,
        "paysys": payment_system,
        "s": signature
    }

    # Отправка POST-запроса
    response = requests.post(PAYMENT_URL, data=data)

    if response.status_code == 200:
        # Проверка, если ответ в формате HTML
        if response.text.startswith("<!DOCTYPE html>"):
            soup = BeautifulSoup(response.text, "html.parser")
            error_message = soup.find("p", class_="errorText")
            if error_message:
                await callback_query.message.answer(f"Ошибка: {error_message.text.strip()}")
            else:
                await callback_query.message.answer("Неизвестная ошибка. Проверьте данные.")
         else:
            # Ограничить длину текста для Telegram
            if len(response_text) > 4000:
                logging.info(f"Полный ответ сервера: {response_text}")
                await callback_query.message.answer("Ответ сервера слишком длинный. Полный текст записан в логах.")
           else:
                await callback_query.message.answer(f"Ответ сервера: {response_text}")
    else:
        await callback_query.message.answer(f"Ошибка: {response.status_code}. Ответ сервера: {response.reason}")

    # Спросить сумму для следующего платежа
    await callback_query.message.answer("Введите сумму следующего платежа:")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
