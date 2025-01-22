import dotenv
import logging
import asyncio
from datetime import datetime
from aiohttp import ClientSession
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.formatting import *
from aiogram.client.default import DefaultBotProperties
from config import RUB_ID, API_TOKEN, BASE_URL, PAY_URL, WEB_SERVER_IP, WEB_SERVER_PORT
from checker import addorder

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
        link = await sendpost(amount, message.from_user.id)
        await message.answer(link)

async def sendpost(amount, chat_id):
    externaltext = datetime.now().strftime("%d%m")
    async with ClientSession() as session:
        async with session.post(
            f"{BASE_URL}",
            headers={"Authorization": API_TOKEN},
            json={
                "amount": str(amount),
                "currency": RUB_ID,
                "currencies": [RUB_ID],
                "durationSeconds": 86400,
                "callbackUrl": f"https://{WEB_SERVER_IP}:{WEB_SERVER_PORT}/webhook",
                "redirectUrl": "https://t.me/",
                "externalText": externaltext
            }
        ) as response:
            data = await response.json()
            await addorder(externaltext, chat_id, amount)
            return f"{PAY_URL}{data}"
