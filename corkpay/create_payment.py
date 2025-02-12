import asyncio
from aiosqlite import connect
from aiohttp import ClientSession
from aiogram import Bot, Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.formatting import *
from config import API_TOKEN, BASE_URL, MERCHANT_ID, MERCHANT_TOKEN
from checker import addorder
from datetime import datetime

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
        bot_msg = await message.reply("⌛️Ожидаем реквизиты...")
        checkout = await sendpost(amount, message.from_user.id, 1)
        await bot_msg.delete()
        if checkout == True:
            await message.reply("⛔Нет реквизитов!")
        else:
            await message.reply(checkout[0])
            await message.answer(checkout[1])
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
        print(result)
        return result[0]

async def get_domain():
    async with ClientSession() as session:
        async with session.get(
            f"{BASE_URL}/api/getPayApiDomain/{API_TOKEN}"
        ) as response:
            domain = await response.text()
            return domain

async def sendpost(amount, chat_id, counter):
    domain = await get_domain()
    order_id = datetime.now().strftime("%d%m%H%M")
    async with ClientSession() as session:
        async with session.post(
            f"https://{domain}/h2h/p2p",
            json={
                "merchant_id": MERCHANT_ID,
                "merchant_token": MERCHANT_TOKEN,
                "ip": order_id,
                "amount": amount,
                "merchant_order": order_id,
                "callback_url": "https://t.me/"
            }
        ) as response:
            try:
                data = await response.json()
                print(data, flush=True)
            except Exception as e:
                return (f"⚰️CorkPay отправил труп!", f"{e}")
            else:
                order_status = data['status']
                print(order_status, flush=True)
                if order_status == "success":
                    card = data['card']
                    sign = data['sign']
                    bin = card[:6]
                    if bin != "220220":
                        print("again non-ru")
                        await asyncio.sleep(3)
                        if counter < 5:
                            counter += 1
                            await asyncio.sleep(3)
                            return await sendpost(amount, chat_id, counter)
                        else:
                            return True
                    bank_status = await bank_check(bin)
                    bank_name = await check_name(bin)
                    if bank_status != "RIP":
                        await addorder(sign, chat_id, amount, order_id)
                        return (f"📄 Создан заказ: №<code>{order_id}</code>\n\n💳 Номер карты для оплаты: <code>{card}</code>\n💰Сумма платежа: <code>{amount}</code> рублей\n\n🕑 Время на оплату: 20 мин.", F"🏦Банк: {bank_name}")
                    else:
                        print("again RIP")
                        await asyncio.sleep(3)
                        if counter < 5:
                            counter += 1
                            await asyncio.sleep(3)
                            return await sendpost(amount, chat_id, counter)
                        else:
                            return True
                else:
                        print("again no")
                        print(counter)
                        print(data['reason'])
                        if counter < 5:
                            counter += 1
                            await asyncio.sleep(3)
                            return await sendpost(amount, chat_id, counter)
                        else:
                            return True                   


