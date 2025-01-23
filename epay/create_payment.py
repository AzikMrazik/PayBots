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
from config import API_TOKEN, BASE_URL
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
        bot_msg = await message.answer("⌛️Ожидаем реквизиты...")
        link = await sendpost(amount, message.from_user.id)
        await message.answer(link)
        await bot_msg.delete

async def sendpost(amount, chat_id):
    async with ClientSession() as session:
        async with session.post(
            f"{BASE_URL}",
            json={
                "api_key": API_TOKEN,
                "amount": amount,
                "merchant_order_id": "1691",
                "notice_url": "https://t.me/"
            }
        ) as response:
            data = await response.json()
            precise_amount = data['amount']
            card = data['card_number']
            order_id = data['order_id']
            await addorder(order_id, chat_id, precise_amount)
            return f"📄 Создан заказ: <b>№{order_id}</b>\n\n💳 Номер карты для оплаты: <code>{card}</code>\n💰 Сумма платежа: <code>{precise_amount}</code> рублей\n\n🕑 Время на оплату: 30 мин."
