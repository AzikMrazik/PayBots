import logging
import json
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
import aiohttp
from datetime import datetime
import os

API_TOKEN = "7354054366:AAHDb7f5ggIJJMESBRscwVkw12oX2dRzfG0Т"
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

users_data = {}
orders_today = []

# Load and save user data functions
def save_api_keys():
    with open("api_keys.json", "w") as f:
        json.dump(users_data, f)

def load_api_keys():
    global users_data
    if os.path.exists("api_keys.json"):
        with open("api_keys.json", "r") as f:
            users_data = json.load(f)

def save_orders_today():
    with open("orders_today.json", "w") as f:
        json.dump(orders_today, f)

def load_orders_today():
    global orders_today
    if os.path.exists("orders_today.json"):
        with open("orders_today.json", "r") as f:
            orders_today = json.load(f)

load_api_keys()
load_orders_today()

# Main menu keyboard
main_menu_markup = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Создать платеж", callback_data="create_payment")],
    [InlineKeyboardButton(text="Баланс и Вывод", callback_data="balance_and_withdrawal")],
    [InlineKeyboardButton(text="История", callback_data="transaction_history")],
    [InlineKeyboardButton(text="Ключи", callback_data="api_keys")]
])

# Handlers
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id not in users_data:
        await message.answer("Введите ваш API ключ для работы с платежами:")
    else:
        await message.answer("Добро пожаловать! Выберите действие:", reply_markup=main_menu_markup)

@dp.message(lambda message: message.text and message.text.startswith("API_KEY:"))
async def handle_api_key(message: types.Message):
    user_id = str(message.from_user.id)
    api_key = message.text.split("API_KEY:")[1].strip()
    users_data[user_id] = api_key
    save_api_keys()
    await message.answer("Ваш API ключ сохранен. Выберите действие:", reply_markup=main_menu_markup)

@dp.callback_query(lambda c: c.data == 'create_payment')
async def create_payment(callback_query: CallbackQuery):
    await bot.send_message(callback_query.from_user.id, "Введите сумму заказа:")

@dp.message(lambda message: message.text and message.text.isdigit())
async def handle_payment_amount(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id in users_data:
        amount = message.text
        merchant_order_id = datetime.now().strftime("%d%m%H%M%S")
        orders_today.append(merchant_order_id)
        save_orders_today()
        api_key = users_data[user_id]

        async with aiohttp.ClientSession() as session:
            async with session.post("https://payment-api-url.com/create", json={
                "api_key": api_key,
                "amount": amount,
                "merchant_order_id": merchant_order_id
            }) as response:
                if response.status == 200:
                    await message.answer(
                        f"Платеж создан. ID заказа: {merchant_order_id}. Введите следующую сумму или нажмите В меню.",
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="В меню", callback_data="main_menu")]])
                    )
                else:
                    await message.answer("Ошибка создания платежа. Попробуйте еще раз.",
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="В меню", callback_data="main_menu")]]))

@dp.callback_query(lambda c: c.data == 'balance_and_withdrawal')
async def balance_and_withdrawal(callback_query: CallbackQuery):
    user_id = str(callback_query.from_user.id)
    if user_id in users_data:
        api_key = users_data[user_id]
        async with aiohttp.ClientSession() as session:
            async with session.post("https://payment-api-url.com/balance", json={"api_key": api_key}) as response:
                if response.status == 200:
                    data = await response.json()
                    balance = data.get("balance")
                    markup = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="Запросить выплату", callback_data="withdraw_request")],
                        [InlineKeyboardButton(text="В меню", callback_data="main_menu")]
                    ])
                    await bot.send_message(callback_query.from_user.id, f"Ваш баланс: {balance}", reply_markup=markup)
                else:
                    await bot.send_message(callback_query.from_user.id, "Ошибка получения баланса.",
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="В меню", callback_data="main_menu")]]))

@dp.callback_query(lambda c: c.data == 'withdraw_request')
async def withdraw_request(callback_query: CallbackQuery):
    await bot.send_message(callback_query.from_user.id, "Введите кошелек для вывода:")

@dp.message(lambda message: not message.text.isdigit())
async def handle_withdraw_wallet(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id in users_data:
        wallet = message.text
        users_data[user_id] = {"api_key": users_data[user_id], "wallet": wallet}
        save_api_keys()
        await message.answer("Введите сумму для вывода:")

@dp.message(lambda message: message.text.isdigit())
async def handle_withdraw_amount(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id in users_data and isinstance(users_data[user_id], dict) and "wallet" in users_data[user_id]:
        amount = message.text
        wallet = users_data[user_id]["wallet"]
        api_key = users_data[user_id]["api_key"]
        async with aiohttp.ClientSession() as session:
            async with session.post("https://payment-api-url.com/withdraw", json={
                "api_key": api_key,
                "amount": amount,
                "wallet": wallet,
                "method": "usdttrc"
            }) as response:
                if response.status == 200:
                    await message.answer("Выплата успешно запрошена.",
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="В меню", callback_data="main_menu")]]))
                else:
                    await message.answer("Ошибка при запросе выплаты.",
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="В меню", callback_data="main_menu")]]))

@dp.callback_query(lambda c: c.data == 'transaction_history')
async def transaction_history(callback_query: CallbackQuery):
    transactions = "\n".join([f"{order_id} / Сумма" for order_id in orders_today])
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Проверить платеж", callback_data="check_payment")],
        [InlineKeyboardButton(text="В меню", callback_data="main_menu")]
    ])
    await bot.send_message(callback_query.from_user.id, f"История транзакций за сегодня:\n{transactions}", reply_markup=markup)

@dp.callback_query(lambda c: c.data == 'check_payment')
async def check_payment(callback_query: CallbackQuery):
    await bot.send_message(callback_query.from_user.id, "Введите ID заявки для проверки:")

@dp.message(lambda message: True)
async def handle_check_payment(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id in users_data:
        order_id = message.text
        api_key = users_data[user_id]
        async with aiohttp.ClientSession() as session:
            async with session.post("https://payment-api-url.com/check", json={
                "api_key": api_key,
                "order_id": order_id
            }) as response:
                if response.status == 200:
                    payment_status = (await response.json()).get("status")
                    await message.answer(f"Статус платежа: {payment_status}",
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="transaction_history"), InlineKeyboardButton(text="В меню", callback_data="main_menu")]]))
                else:
                    await message.answer("Ошибка проверки статуса платежа.",
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="transaction_history"), InlineKeyboardButton(text="В меню", callback_data="main_menu")]]))

@dp.callback_query(lambda c: c.data == 'api_keys')
async def api_keys(callback_query: CallbackQuery):
    user_id = str(callback_query.from_user.id)
    if user_id in users_data:
        api_key = users_data[user_id]
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Изменить", callback_data="change_api_key")],
            [InlineKeyboardButton(text="В меню", callback_data="main_menu")]
        ])
        await bot.send_message(callback_query.from_user.id, f"Ваш текущий API ключ: {api_key}", reply_markup=markup)

@dp.callback_query(lambda c: c.data == 'change_api_key')
async def change_api_key(callback_query: CallbackQuery):
    await bot.send_message(callback_query.from_user.id, "Введите новый API ключ:")

# Run bot
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
