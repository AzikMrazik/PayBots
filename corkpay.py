import asyncio
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
import time
import requests
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path='/root/paybots/api.env')
API_TOKEN = os.getenv("API_TOKEN_CORKPAY")
MERCHANT_TOKEN = os.getenv("MERCHANT_TOKEN_CORKPAY")
MERCHANT_ID = os.getenv("MERCHANT_ID_CORKPAY")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()

CALLBACK_URL = "https://t.me/"

def create_payment_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Проверить платеж", callback_data="check_payment")]
        ]
    )

@router.message(F.text == "/start")
async def start_command(message: Message):
    await message.answer("Введите сумму для оплаты:")

@router.message(F.text.regexp(r"^\d+(\.\d+)?$"))
async def create_payment(message: Message):
    try:
        amount = float(message.text.strip())
        merchant_order = str(int(time.time()))
        payload = {
            "merchant_id": MERCHANT_ID,
            "merchant_token": MERCHANT_TOKEN,
            "ip": merchant_order,
            "amount": f"{amount:.2f}",
            "merchant_order": merchant_order,
            "callback_url": CALLBACK_URL,
        }
        response = requests.post("https://oeiblas.shop/h2h/p2p", json=payload)
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get("status") == "success" and response_data.get("card"):
                card = response_data.get("card")
                end_time = response_data.get("endTimeOfPayment")
                await message.answer(
                    f"Платеж создан успешно!\nКарта: {card}\nДо: {end_time}\nВведите сумму для следующего платежа:",
                    reply_markup=create_payment_keyboard(),
                )
            else:
                await message.answer(
                    "Реквизиты не найдены. Попробуйте снова:",
                    reply_markup=create_payment_keyboard(),
                )
        else:
            await message.answer(f"Ошибка HTTP при создании платежа: {response.status_code}")
    except ValueError:
        await message.answer("Пожалуйста, введите корректную сумму.")
    except Exception as e:
        await message.answer(f"Неизвестная ошибка: {e}")

@router.callback_query(F.data == "check_payment")
async def check_payment(callback_query: CallbackQuery):
    await bot.send_message(callback_query.from_user.id, "Введите сумму для платежа:")

@router.message(F.text.regexp(r"^\d+(\.\d+)?$"))
async def verify_payment(message: Message):
    try:
        amount = message.text.strip()
        payload = {"amount": amount}
        response = requests.post("https://corkpay.cc/api/apiOrderStatus", json=payload)
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get("status") == "success":
                await message.answer(
                    f"Платеж подтвержден!\nКарта: {response_data.get('card')}\nВведите сумму для следующего платежа:"
                )
            else:
                await message.answer(f"Ошибка проверки платежа: {response_data.get('reason', 'Неизвестная ошибка')}")
        else:
            await message.answer(f"Ошибка HTTP при проверке платежа: {response.status_code}")
    except Exception as e:
        await message.answer(f"Неизвестная ошибка: {e}")

async def main():
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
