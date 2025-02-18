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
from aiosqlite import connect
import re
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
        bot_msg = await message.reply(f"⌛️Ожидаем реквизиты...")
        checkout = await sendpost(amount, message.from_user.id)
        await bot_msg.delete()
        await message.reply(checkout[0])
        await message.reply(checkout[1])
        await message.answer("Введите сумму для следующего платежа:", reply_markup=back_kb())
        await state.set_state(PaymentStates.WAITING_AMOUNT)

async def bank_check(bin):
    async with connect("bins.db") as db:
        cursor = await db.execute(
            "SELECT note FROM bins WHERE bin = ?", 
            (bin,)
        )
        result = await cursor.fetchone()
        resultend = result[0]
        return resultend
    
async def check_name(bin):
    async with connect("bins.db") as db:
        cursor = await db.execute(
            "SELECT bank_name FROM bins WHERE bin = ?", 
            (bin,)
        )
        result = await cursor.fetchone()
        resultend = result[0]
        return resultend

async def sendpost(amount, chat_id, counter=1):
    if counter == 10:
        return (f"⛔Нет реквизитов", f"Запросите снова!")
    order_id = datetime.now().strftime("%d%m%H%M")
    ids = str(uuid.uuid4())
    payload = {
    "paymentMethod": 9,
    "id": ids,
    "paymentDetails": {
        "amount": amount,
        "currency": "RUB"
    },
    "description": order_id,
    "return": "https://t.me/"
    }
    async with ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/transaction/process",
            headers={"X-Secret": API_KEY, "X-MerchantId": MERCHANT_ID},
            json=payload
        ) as response:
            data = await response.json()
            print(data, flush=True)
            status_code = 200
            try:
                status_code = data['statusCode']
            except:
                pass
            if status_code == 200:
                transaction_id = data['transactionId']
                async with ClientSession() as session:
                    async with session.get(
                        f"{BASE_URL}/h2h/{transaction_id}",
                        headers={"X-Secret": API_KEY, "X-MerchantId": MERCHANT_ID},
                        json=payload
                    ) as response:
                        data = await response.json()
                        print(data, flush=True)
                        account_number = data['accountNumber']
                        sbp = ["+", "7", "8"]
                        if account_number not in sbp:
                            card = re.sub(r'\s+', '', card)
                            bin = card[:6]
                            method = await check_name(bin)
                            bank_status = await bank_check(bin)
                            if bank_status == "RIP":
                                counter += 1
                                await asyncio.sleep(1)
                                return await sendpost(amount, chat_id, counter)
                        account_name = data['accountName']
                        method = data['method']
                        all_method = ["ALL", "All", "all"]
                        if method in all_method:
                            method = "Любой банк"
                        amount = data['amount']
                        await addorder()
                        return (
                            f"📄 Создан заказ: №<code>{order_id}</code>\n\n💳 Номер для оплаты: {account_number}\n💰Сумма платежа: <code>{amount}</code> рублей\n\n🕑 Время на оплату: 15 мин.",
                            f"🏦Банк: {method}, получатель {account_name}"
                            )
            else:
                counter += 1
                await asyncio.sleep(1)
                return await sendpost(amount, chat_id, counter)