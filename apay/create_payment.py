from aiohttp import ClientSession
from aiogram import Bot, Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.formatting import *
from config import SECRET_KEY, BASE_URL, CLIENT_ID
from datetime import datetime
from hashlib import md5
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
async def create_payment(message: Message, state: FSMContext):
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
        checkout = await sendpost(amount, message.from_user.id)
        await message.reply(checkout[0])
        await message.reply(checkout[1])
        await message.answer("Введите сумму для следующего платежа:", reply_markup=back_kb())
        await state.set_state(PaymentStates.WAITING_AMOUNT)

async def sendpost(amount, chat_id):
    order_id = datetime.now().strftime("%d%m%H%M%S")
    amount = amount * 100
    sign = f"{order_id}:{amount}:{SECRET_KEY}"
    sign = md5(sign.encode()).hexdigest()
    async with ClientSession() as session:
        async with session.get(
            f"{BASE_URL}/backend/create_order",
            params={
                "client_id": CLIENT_ID,
                "order_id": order_id,
                "amount": amount,
                "sign": sign
            }
        ) as response:
            data = await response.json()
            print(data, flush=True)
            URL = data['url']
            await addorder(chat_id, amount, order_id)
            return (f"📄Создан заказ №{order_id}!", f"{URL}")
