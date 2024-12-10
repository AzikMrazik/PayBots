import asyncio
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
import time
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path='/root/paybots/api.env')
API_TOKEN = os.getenv("API_TOKEN_CORKPAY")
MERCHANT_TOKEN = os.getenv("MERCHANT_TOKEN_CORKPAY")
MERCHANT_ID = os.getenv("MERCHANT_ID_CORKPAY")

# Bot setup
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()

# Callback URL
CALLBACK_URL = "https://t.me/"

# Inline Keyboards
def create_payment_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Создать платеж", callback_data="create_payment")]
        ]
    )
    return keyboard

def create_check_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Проверить платеж", callback_data="check_payment")]
        ]
    )
    return keyboard

@router.message(F.text == "/start")
async def start_command(message: Message):
    await message.answer("Введите сумму для оплаты:", reply_markup=create_check_keyboard())

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
        response_data = response.json()
        if response_data.get("status") == "success":
            card = response_data.get("card")
            end_time = response_data.get("endTimeOfPayment")
            await message.answer(
                f"Платеж создан успешно!\nКарта: {card}\nДо: {end_time}\nВведите сумму для следующего платежа:",
                reply_markup=create_check_keyboard(),
            )
        else:
            reason = response_data.get("reason", "Неизвестная ошибка")
            await message.answer(f"Ошибка создания платежа: {reason}\nПопробуйте еще раз.")
    except ValueError:
        await message.answer("Пожалуйста, введите корректную сумму.")
    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}")

@router.callback_query(F.data == "check_payment")
async def check_payment(callback_query: CallbackQuery):
    await bot.send_message(callback_query.from_user.id, "Введите SIGN для проверки:")

@router.message(F.text.regexp(r"^[A-Za-z0-9]+$"))
async def verify_payment(message: Message):
    try:
        sign = message.text.strip()
        payload = {"sign": sign}
        response = requests.post("https://oeiblas.shop/h2h/p2p/verify", json=payload)
        response_data = response.json()
        if response_data.get("status") == "success":
            await message.answer(
                f"Платеж подтвержден!\nСтатус: {response_data.get('status')}\nВведите SIGN для следующей проверки:"
            )
        else:
            reason = response_data.get("reason", "Неизвестная ошибка")
            await message.answer(f"Ошибка проверки платежа: {reason}\nПопробуйте еще раз.")
    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}", reply_markup=create_check_keyboard())

async def main():
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
