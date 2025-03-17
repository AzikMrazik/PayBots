import asyncio
from aiosqlite import connect
from aiohttp import ClientSession
from aiogram import Bot, Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.formatting import *
from config import SECRET, ID, BASE_URL, DOMAIN
from datetime import datetime
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
    await state.clear()
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
        bot_msg = await message.reply(f"⌛️Ожидаем реквизиты...")
        checkout = await sendpost(amount, message.from_user.id)
        await bot_msg.delete()
        await message.reply(checkout[0])
        await message.answer(checkout[1])
        await message.answer("Введите сумму для следующего платежа:", reply_markup=back_kb())
        await state.set_state(PaymentStates.WAITING_AMOUNT)

async def sendpost(amount, chat_id, counter=1):
    order_id = datetime.now().strftime("%d%m%H%M%S")
    async with ClientSession() as session:
        async with session.post(
            f"{BASE_URL}",
            json={"client_id": ID,
                  "client_secret": SECRET,
                  "amount": amount,
                  "currency":"RUB",
                  "successUrl":"https://t.me/",
                  "cancelUrl":"https://t.me/",
                  "callbackUrl":f"https://{DOMAIN}/crocopay/{order_id}"}
        ) as response:
            data = await response.json()
            URL = data['redirect_url']
            await addorder(chat_id, amount, order_id)
            return (f"📄Создан заказ №{order_id}!", f"{URL}")

