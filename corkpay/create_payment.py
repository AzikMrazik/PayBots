import asyncio
import re
from aiosqlite import connect
from aiohttp import ClientSession
from aiogram import Bot, Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.formatting import *
from config import API_TOKEN, BASE_URL, MERCHANT_ID, MERCHANT_TOKEN, DOMAIN
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
        if amount < 1000 or amount > 10000:
            await message.answer("Доступная сумма: 1000 - 10.000 RUB!")
            await message.answer("Отправьте новое значение:", reply_markup=back_kb())
            return   
    except:
        await message.answer("Вы отправили не числовое значение!")
        await message.answer("Отправьте новое значение:", reply_markup=back_kb())
        return
    else:
        msg = await message.reply("⌛️Ожидаем реквизиты...")
        order = await sendpost(amount, message.from_user.id, msg, 1)
        await msg.delete()
        for i in order:
            await message.answer(i)
        await message.answer("Введите сумму для следующего платежа:", reply_markup=back_kb())
        await state.set_state(PaymentStates.WAITING_AMOUNT)
    
async def check_name(bin):
    async with connect("bins.db") as db:
        cursor = await db.execute(
            "SELECT bank_name FROM bins WHERE bin = ?", 
            (bin,)
        )
        result = await cursor.fetchone()
        return result[0]

async def get_domain():
    async with ClientSession() as session:
        async with session.get(
            f"{BASE_URL}/api/getPayApiDomain/{API_TOKEN}"
        ) as response:
            domain = await response.text()
            return domain

async def sendpost(amount, chat_id, msg, counter):
    domain = await get_domain()
    order_id = datetime.now().strftime("%d%m%H%M%S")
    async with ClientSession() as session:
        async with session.post(
            f"https://{domain}/h2h/p2p",
            json={
                "merchant_id": MERCHANT_ID,
                "merchant_token": MERCHANT_TOKEN,
                "ip": order_id,
                "amount": amount,
                "merchant_order": order_id,
                "callback_url": f"https://{DOMAIN}/corkpay"
            }
        ) as response:
            try:
                data = await response.json()
                print(data, flush=True)
            except:
                data = await response.text()
                return ("⚰️CorkPay отправил труп!", f"{data}", "Отправьте сообщение выше кодеру!")
            else:
                order_status = data['status']
                if order_status == "success":
                    card = data['card']
                    card = re.sub(r'\s+', '', card)
                    sign = data['sign']
                    bin = card[:6]
                    if bin[:3] != "220":
                        if counter < 5:
                            counter += 1
                            await msg.edit_text(f"⌛️Ожидаем реквизиты...({counter}/5)")
                            await asyncio.sleep(3)
                            return await sendpost(amount, chat_id, msg, counter)
                        else:
                            return ("⛔Нет реквизитов!",)
                    bank_name = await check_name(bin)
                    await addorder(sign, chat_id, amount, order_id)
                    return (f"📄 Создана заявка: №<code>{order_id}</code>\n\n💳 Номер карты для оплаты: <code>{card}</code>\n💰Сумма платежа: <code>{amount}</code> рублей\n\n🕑 Время на оплату: 20 мин.", f"🏦Банк: {bank_name}")
                else:
                    desc = data['reason']
                    if desc:
                        return ("❓Неизвестная ошибка", f"{desc}", "Отправьте сообщение выше кодеру!")   
                    else:
                        if counter < 5:
                            counter += 1
                            await msg.edit_text(f"⌛️Ожидаем реквизиты...({counter}/5)")
                            await asyncio.sleep(3)
                            return await sendpost(amount, chat_id, msg, counter)
                        else:
                            return ("⛔Нет реквизитов!",)                


