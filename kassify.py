import logging
import random
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor
from dotenv import load_dotenv
import os

# Загрузка конфигурации
load_dotenv(dotenv_path='/root/paybots/api.env')
API_TOKEN = os.getenv('API_TOKEN_KASSIFY')
MERCHANT_ID = os.getenv('MERCHANT_ID_KASSIFY')
KEY_SHOP = os.getenv('KEY_SHOP_KASSIFY')

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# URL для отправки платежа
PAYMENT_URL = "https://kassify.com/sci/"

# Генерация 7-значного ID
def generate_id():
    return str(random.randint(1000000, 9999999))

# Inline-кнопки для выбора платежной системы
payment_methods = ["epaycoreRUB", "yoomoney", "yoomoney_HIYP", "P2P_pay"]
payment_keyboard = InlineKeyboardMarkup(row_width=2)
for method in payment_methods:
    payment_keyboard.add(InlineKeyboardButton(method, callback_data=method))

# Хранение данных пользователя
user_data = {}

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("Введите сумму платежа (без копеек):")
    user_data[message.chat.id] = {}

@dp.message_handler(lambda message: message.text.isdigit())
async def get_sum(message: types.Message):
    amount = message.text + ".00"
    user_data[message.chat.id]['amount'] = amount
    await message.answer("Выберите систему оплаты:", reply_markup=payment_keyboard)

@dp.callback_query_handler(lambda callback: callback.data in payment_methods)
async def process_payment(callback_query: types.CallbackQuery):
    user_id = generate_id()
    order_id = generate_id()
    payment_system = callback_query.data
    amount = user_data[callback_query.message.chat.id]['amount']

    # Формирование подписи
    hash_string = f"{MERCHANT_ID}:{amount}:{KEY_SHOP}:{order_id}"
    signature = requests.utils.quote(hash_string)  # md5 форматирование строки

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

    # Ответ пользователю
    if response.status_code == 200:
        await callback_query.message.answer(f"Ответ сервера: {response.text}")
    else:
        await callback_query.message.answer(f"Ошибка: {response.status_code}")

    # Спросить сумму для следующего платежа
    await callback_query.message.answer("Введите сумму следующего платежа:")

# Запуск бота
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
