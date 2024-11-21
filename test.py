import aiohttp
import hmac
import hashlib
import os
from aiohttp.web import Application, Response, run_app
from aiogram import Bot, Dispatcher, types, Router
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from dotenv import load_dotenv
import logging

load_dotenv(dotenv_path="/root/paybots/api.env")

# Логирование
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
    try:
        async with aiohttp.ClientSession() as session:
            data = {
                "amount": amount,
                "currencies": [5],
                "durationSeconds": 86400,
                "callbackUrl": "https://t.me/amtest0170_bot",
                "redirectUrl": "https://yourwebsite.com/success",
            }
            data["signature"] = generate_signature(data, MERCHANT_TOKEN)

            headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
            logger.debug(f"Отправка запроса на создание платежа: {data}")

            async with session.post(f"{BASE_URL}/merchant/createOneTimeInvoice", json=data, headers=headers) as response:
                result = await response.json()
                logger.debug(f"Ответ API: {result}")
                if response.status == 200 and verify_signature(result, MERCHANT_TOKEN):
                    payment_url = result.get("url", "Не удалось получить URL")
                    await message.answer(f"Платёж создан! Перейдите по ссылке для оплаты: {payment_url}")
                else:
                    error_message = result.get("message", "Неизвестная ошибка")
                    await message.answer(f"Ошибка при создании платежа: {error_message}")
    except Exception as e:
        logger.error(f"Системная ошибка: {e}")
        await message.answer(f"Системная ошибка: {e}")


@router.callback_query(lambda c: c.data == "payment_history")
async def payment_history_handler(callback_query: types.CallbackQuery):
    try:
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
            async with session.get(f"{BASE_URL}/merchant/invoices", headers=headers) as response:
                result = await response.json()
                logger.debug(f"Ответ API для истории платежей: {result}")
                if response.status == 200:
                    invoices = result.get("data", [])
                    if invoices:
                        history = "\n".join(f"ID: {inv['id']}, Статус: {inv['status']}" for inv in invoices)
                        await callback_query.message.answer(f"История платежей:\n{history}")
                    else:
                        await callback_query.message.answer("Нет доступных записей.")
                else:
                    error_message = result.get("message", "Неизвестная ошибка")
                    await callback_query.message.answer(f"Ошибка при получении истории: {error_message}")
    except Exception as e:
        logger.error(f"Системная ошибка: {e}")
        await callback_query.message.answer(f"Системная ошибка: {e}")


@router.callback_query(lambda c: c.data == "withdraw_funds")
async def withdraw_funds_handler(callback_query: types.CallbackQuery):
    await callback_query.message.answer("Введите сумму для вывода:")
    router.message.register(process_withdraw_request)


async def process_withdraw_request(message: types.Message):
    amount = message.text
    try:
        async with aiohttp.ClientSession() as session:
            data = {
                "amount": amount,
                "currency": 5,
                "callbackUrl": "https://t.me/amtest0170_bot",
            }
            data["signature"] = generate_signature(data, MERCHANT_TOKEN)

            headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
            logger.debug(f"Отправка запроса на вывод: {data}")

            async with session.post(f"{BASE_URL}/withdraw", json=data, headers=headers) as response:
                result = await response.json()
                logger.debug(f"Ответ API для вывода: {result}")
                if response.status == 200 and verify_signature(result, MERCHANT_TOKEN):
                    await message.answer("Запрос на вывод создан успешно!")
                else:
                    error_message = result.get("message", "Неизвестная ошибка")
                    await message.answer(f"Ошибка при создании запроса на вывод: {error_message}")
    except Exception as e:
        logger.error(f"Системная ошибка: {e}")
        await message.answer(f"Системная ошибка: {e}")


async def handle_callback(request):
    try:
        data = await request.json()
        logger.debug(f"Получен callback: {data}")
        if verify_signature(data, MERCHANT_TOKEN):
            payment_id = data.get("invoiceId")
            status = data.get("status")
            await bot.send_message(chat_id=123456789, text=f"Платёж {payment_id} обновлён. Статус: {status}")
            return Response(text="OK")
        return Response(status=400, text="Invalid signature")
    except Exception as e:
        logger.error(f"Ошибка в обработке callback: {e}")
        return Response(status=500, text=f"Error: {e}")


app = Application()
app.router.add_post("/callback", handle_callback)

if __name__ == "__main__":
    dp.run_polling(bot)
    run_app(app, port=8080)
