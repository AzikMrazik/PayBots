import dotenv
import logging
import asyncio
from aiohttp import ClientSession
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.formatting import *
from aiogram.client.default import DefaultBotProperties
from config import RUB_ID, API_TOKEN, BASE_URL, PAY_URL

router = Router()

class PaymentStates(StatesGroup):
    WAITING_AMOUNT = State()

def back_kb():
    keyboard = [
        [InlineKeyboardButton(text="Назад в меню", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@router.callback_query(F.data == 'create_payment')
async def how_many(callback_query: CallbackQuery, bot: Bot, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.answer("Введите сумму платежа:", reply_markup=back_kb())
    await state.set_state(PaymentStates.WAITING_AMOUNT)

@router.message(PaymentStates.WAITING_AMOUNT)
async def create_payment(message: Message,  state: FSMContext):
    try:
        amount = int(message.text)
        if amount < 1000:
            await message.answer("Сумма платежа меньше 1000 RUB!")
            await message.answer("Отправьте новое значение:", reply_markup=back_kb())
            return   
    except:
        await message.answer("Вы отправили не числовое значение!")
        await message.answer("Отправьте новое значение:", reply_markup=back_kb())
        return
    else:
        async with ClientSession() as session:
            async with session.post(
                f"{BASE_URL}/merchant/createOneTimeInvoice",
                headers={"Authorization": API_TOKEN},
                json={
                    "amount": str(amount),
                    "currency": RUB_ID,
                    "currencies": [RUB_ID],
                    "durationSeconds": 86400,
                    "redirectUrl": "https://your-redirect-url.com"
                }
            ) as response:
                data = await response.json()
                id = data["data"]
                await message.answer(f"{PAY_URL}/{id}")

async def generate_payment_link(amount):
    async with ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/merchant/createOneTimeInvoice",
            headers={"Authorization": API_TOKEN},
            json={
                "amount": str(amount),
                "currency": RUB_ID,
                "currencies": [RUB_ID],
                "durationSeconds": 86400,
                "redirectUrl": "https://your-redirect-url.com"
            }
        ) as response:
            data = await response.json()
            return f"{PAY_URL}/{data['data']}"
