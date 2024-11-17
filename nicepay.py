import asyncio
import json
import aiohttp
import os
from dotenv import load_dotenv
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Router

load_dotenv()

API_TOKEN_NP = os.getenv('api.env')
API_TOKEN = API_TOKEN_NP

merchant_id = os.getenv('MERCHANT_ID_NP')
secret = os.getenv('SECRET_NP')
description = "test desc"
customer = "user@gmail.com"  # Убедитесь, что это корректный email или идентификатор пользователя
success_url = "https://telegram.org/"
fail_url = success_url
currency = "RUB"

print(f"Ваш токен: {API_TOKEN}, {merchant_id}, {secret}")

# Инициализация бота и диспетчера с FSM (Finite State Machine)
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Инициализация Router
router = Router()
dp.include_router(router)  # Подключение Router к Dispatcher

# Клавиатура для выбора метода оплаты (inline-кнопки)
def get_payment_methods_kb():
    buttons = [
        [InlineKeyboardButton(text="Сбербанк", callback_data="sberbank_rub"),
         InlineKeyboardButton(text="Тинькофф", callback_data="tinkoff_rub")],
        [InlineKeyboardButton(text="Альфа", callback_data="alfabank_rub"),
         InlineKeyboardButton(text="Райфайзен", callback_data="raiffeisen_rub")],
        [InlineKeyboardButton(text="ВТБ", callback_data="vtb_rub"),
         InlineKeyboardButton(text="РНКБ", callback_data="rnkbbank_rub")],
        [InlineKeyboardButton(text="ПочтаБанк", callback_data="postbank_rub"),
         InlineKeyboardButton(text="СБП", callback_data="sbp_rub")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Клавиатура с кнопкой "В меню"
def get_menu_kb():
    buttons = [[InlineKeyboardButton(text="В меню", callback_data="menu")]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Функция для создания order_id по текущей дате и времени
def generate_order_id():
    return datetime.now().strftime("%d%m%H%M%S")

# Обработчик команды /start
@router.message(Command("start"))
async def start(message: types.Message):
    buttons = [[InlineKeyboardButton(text="Создать платеж", callback_data="create_payment")]]
    await message.answer("Добро пожаловать! Нажмите 'Создать платеж' для начала.", 
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

# Обработчик нажатия на кнопку "Создать платеж"
@router.callback_query(F.data == "create_payment")
async def create_payment(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Пожалуйста, введите сумму платежа:", reply_markup=types.ReplyKeyboardRemove())

# Обработчик ввода суммы платежа
@router.message(F.text.func(lambda text: text.isdigit()))
async def handle_amount(message: types.Message):
    global amount
    amount = int(message.text) * 100  # Умножаем на 100
    await message.answer("Выберите метод оплаты:", reply_markup=get_payment_methods_kb())

# Обработчик выбора метода оплаты
@router.callback_query(F.data.in_({"sberbank_rub", "tinkoff_rub", "alfabank_rub", "raiffeisen_rub", "vtb_rub", "rnkbbank_rub", "postbank_rub", "sbp_rub"}))
async def handle_payment_method(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    order_id = generate_order_id()  # Используем текущую дату и время для order_id
    method_code = callback_query.data
    await process_payment(callback_query, method_code, order_id)

# Функция для обработки платежа
async def process_payment(callback_query: types.CallbackQuery, method: str, order_id: str):
    global amount
    url = "https://nicepay.io/public/api/payment"
    payload = {
        "merchant_id": merchant_id,
        "secret": secret,
        "order_id": order_id,
        "customer": customer,  # Заменено account на customer
        "amount": amount,
        "currency": currency,
        "description": description,
        "success_url": success_url,
        "fail_url": fail_url,
        "method": method
    }
    headers = {'Content-Type': 'application/json'}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as response:
            result = await response.json()
            if result.get('status') == 'success':
                payment_link = result['data']['link']
                await bot.send_message(callback_query.from_user.id, 
                                       f"Оплата успешно создана. Перейдите по ссылке для оплаты: {payment_link}", 
                                       reply_markup=get_menu_kb())
                await bot.send_message(callback_query.from_user.id, 
                                       "Введите сумму следующего платежа или нажмите 'В меню':")
            else:
                error_message = result['data'].get('message', 'Неизвестная ошибка')
                await bot.send_message(callback_query.from_user.id, 
                                       f"Ошибка при создании платежа: {error_message}", 
                                       reply_markup=get_menu_kb())

# Обработчик нажатия кнопки "В меню"
@router.callback_query(F.data == "menu")
async def go_to_menu(callback_query: types.CallbackQuery):
    buttons = [[InlineKeyboardButton(text="Создать платеж", callback_data="create_payment")]]
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, 
                           "Вы вернулись в меню.", 
                           reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
