from aiohttp import ClientSession
from aiogram import Bot, Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.formatting import *
from config import MERCHANT_ID, API_KEY, BASE_URL
from datetime import datetime
import uuid
import asyncio

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
        bot_msg = await message.reply(f"⌛️Ожидаем реквизиты...")
        checkout = await sendpost(amount, message.from_user.id)
        await bot_msg.delete()
        await message.reply(checkout[0])
        await message.reply(checkout[1])
        await message.answer("Введите сумму для следующего платежа:", reply_markup=back_kb())
        await state.set_state(PaymentStates.WAITING_AMOUNT)

async def sendpost(amount, chat_id, counter=1):
    if counter == 10:
        return (f"⛔Нет реквизитов", f"Запросите снова!")
    order_id = datetime.now().strftime("%d%m%H%M")
    external_text = f"{order_id},{chat_id}"
    ids = str(uuid.uuid4())
    payload = {
    "paymentMethod": 9,
    "id": ids,
    "paymentDetails": {
        "amount": amount,
        "currency": "RUB"
    },
    "description": "test",
    "return": "https://google.com"
    }
    async with ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/transaction/process",
            headers={"X-Secret": API_KEY, "X-MerchantId": MERCHANT_ID},
            json=payload
        ) as response:
            data = await response.json()
            print(data, flush=True)
            try:
                URL = data['redirect']
                return (f"📄Создан заказ №{order_id}!", f"{URL}")
            except:
                counter += 1
                await asyncio.sleep(3)
                return await sendpost(amount, chat_id, counter)