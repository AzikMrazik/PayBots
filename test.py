import aiohttp
import hmac
import hashlib
import os
from aiohttp.web import Application, Response, run_app
from aiogram import Bot, Dispatcher, types, Router
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from dotenv import load_dotenv

load_dotenv(dotenv_path=_'/root/paybots/api.env')

API_TOKEN = os.getenv("API_TOKEN_TEST")
AUTH_TOKEN = os.getenv("AUTH_TOKEN_CASHIN")
MERCHANT_TOKEN = AUTH_TOKEN
BASE_URL = "https://api.cashinout.io"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)


def generate_signature(data: dict, secret: str) -> str:
    sorted_params = sorted(data.items())
    message = "\n".join(f"{k}={v}" for k, v in sorted_params)
    return hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()


def verify_signature(data: dict, secret: str) -> bool:
    received_signature = data.pop("signature", None)
    expected_signature = generate_signature(data, secret)
    return hmac.compare_digest(received_signature, expected_signature)


def main_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Создать платёж", callback_data="create_payment")],
            [InlineKeyboardButton(text="История", callback_data="payment_history")],
            [InlineKeyboardButton(text="Вывод", callback_data="withdraw_funds")],
        ]
    )


@router.message(Command(commands=["start"]))
async def start_handler(message: types.Message):
    await message.answer("Добро пожаловать! Выберите действие:", reply_markup=main_menu())


@router.callback_query(lambda c: c.data == "create_payment")
async def create_payment_handler(callback_query: types.CallbackQuery):
    await callback_query.message.answer("Введите сумму для платежа:")
    router.message.register(process_payment_creation)


async def process_payment_creation(message: types.Message):
    amount = message.text
    async with aiohttp.ClientSession() as session:
        data = {
            "amount": amount,
            "currencies": [5],
            "durationSeconds": 86400,
            "callbackUrl": "https://t.me/amtest0170_bot",
            "redirectUrl": "https://yourwebsite.com/success",
        }
        data["signature"] = generate_signature(data, MERCHANT_TOKEN)

        async with session.post(f"{BASE_URL}/merchant/createOneTimeInvoice", json=data) as response:
            result = await response.json()
            if response.status == 200 and verify_signature(result, MERCHANT_TOKEN):
                payment_url = result.get("url", "Не удалось получить URL")
                await message.answer(f"Платёж создан! Перейдите по ссылке для оплаты: {payment_url}")
            else:
                await message.answer("Ошибка при создании платежа.")


@router.callback_query(lambda c: c.data == "payment_history")
async def payment_history_handler(callback_query: types.CallbackQuery):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/merchant/invoices", headers={"Authorization": f"Bearer {AUTH_TOKEN}"}) as response:
            result = await response.json()
            if response.status == 200:
                invoices = result.get("data", [])
                if invoices:
                    history = "\n".join(f"ID: {inv['id']}, Статус: {inv['status']}" for inv in invoices)
                    await callback_query.message.answer(f"История платежей:\n{history}")
                else:
                    await callback_query.message.answer("Нет доступных записей.")
            else:
                await callback_query.message.answer("Ошибка при получении истории.")


@router.callback_query(lambda c: c.data == "withdraw_funds")
async def withdraw_funds_handler(callback_query: types.CallbackQuery):
    await callback_query.message.answer("Введите сумму для вывода:")
    router.message.register(process_withdraw_request)


async def process_withdraw_request(message: types.Message):
    amount = message.text
    async with aiohttp.ClientSession() as session:
        data = {
            "amount": amount,
            "currency": 5,
            "callbackUrl": "https://t.me/amtest0170_bot",
        }
        data["signature"] = generate_signature(data, MERCHANT_TOKEN)

        async with session.post(f"{BASE_URL}/withdraw", json=data) as response:
            result = await response.json()
            if response.status == 200 and verify_signature(result, MERCHANT_TOKEN):
                await message.answer("Запрос на вывод создан успешно!")
            else:
                await message.answer("Ошибка при создании запроса на вывод.")


async def handle_callback(request):
    data = await request.json()
    if verify_signature(data, MERCHANT_TOKEN):
        payment_id = data.get("invoiceId")
        status = data.get("status")
        await bot.send_message(chat_id=123456789, text=f"Платёж {payment_id} обновлён. Статус: {status}")
        return Response(text="OK")
    return Response(status=400, text="Invalid signature")


app = Application()
app.router.add_post("/callback", handle_callback)

if __name__ == "__main__":
    dp.run_polling(bot)
    run_app(app, port=8080)
