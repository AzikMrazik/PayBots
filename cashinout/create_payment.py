from aiohttp import ClientSession
from aiogram import Bot, Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.formatting import *
from datetime import datetime
from config import RUB_ID, API_TOKEN, BASE_URL, PAY_URL, DOMAIN

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
        link = await sendpost(amount, message.from_user.id)
        await message.reply(link)
        await message.answer("Введите сумму для следующего платежа:", reply_markup=back_kb())
        await state.set_state(PaymentStates.WAITING_AMOUNT)

async def sendpost(amount, chat_id):
    order_id = datetime.now().strftime("%d%m%H%M")
    external_text = f"{order_id},{chat_id}"
    async with ClientSession() as session:
        async with session.post(
            f"{BASE_URL}",
            headers={"Authorization": API_TOKEN},
            json={
                "amount": str(amount),
                "currency": RUB_ID,
                "currencies": [RUB_ID],
                "durationSeconds": 2700,
                "callbackUrl": f"https://{DOMAIN}/payment_webhook",
                "redirectUrl": "https://t.me/",
                "externalText": external_text
            }
        ) as response:
            data = await response.json()
            return (f"📄Создан заказ: №{order_id}!", f"{PAY_URL}{data['data']}")
