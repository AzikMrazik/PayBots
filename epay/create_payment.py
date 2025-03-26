import asyncio
from aiosqlite import connect
from aiohttp import ClientSession
from aiogram import Bot, Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.formatting import *
from config import API_TOKEN, BASE_URL, DOMAIN
from checker import addorder
from datetime import datetime
import re

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
        resultend = result[0]
        return resultend

async def sendpost(amount, chat_id, msg, counter):
    merchant_order_id = datetime.now().strftime("%d%m%H%M")
    async with ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/request/requisites",
            json={
                "api_key": API_TOKEN,
                "amount": amount,
                "merchant_order_id": merchant_order_id,
                "notice_url": f"https://{DOMAIN}/epay"
            }
        ) as response:
            try:
                data = await response.json()
            except:
                data = await response.text()
                return (f"⚰️", f"E-Pay отправил труп!", {data}, "Отправьте сообщение выше кодеру!")
            else:
                order_status = data['status']
                print(data, flush=True)
                if order_status != "error":
                    precise_amount = data['amount']
                    card = data['card_number']
                    card = re.sub(r'\s+', '', card)
                    order_id = data['order_id']
                    bank_name = data['bank']
                    if card[:1] == "+" or card[:1] == "8" or card[:1] == "7":
                        sbp = True
                    else:
                        sbp = False
                    if not sbp:
                        bin = card[:6]
                        bank_name = await check_name(bin)
                        bank_type = "карты"
                        if bin[:3] != "220":
                            await asyncio.sleep(3)
                            if counter < 6:
                                counter += 1
                                await msg.edit_text(f"⌛️Ожидаем реквизиты...({counter}/5)")
                                return await sendpost(amount, chat_id, msg, counter)
                            else:
                                return ("⛔Нет реквизитов",)
                    else:
                        bank_type = "телефона"
                    await addorder(order_id, chat_id, precise_amount)
                    return (f"📄 Создан заказ: №<code>{order_id}</code>\n\n💳 Номер {bank_type} для оплаты: <code>{card}</code>\n💰Сумма платежа: <code>{precise_amount}</code> рублей\n\n🕑 Время на оплату: 30 мин.", F"🏦Банк: {bank_name}")
                else:
                        if counter < 6:
                                counter += 1
                                await msg.edit_text(f"⌛️Ожидаем реквизиты...({counter}/5)")
                                return await sendpost(amount, chat_id, msg, counter)
                        else:
                            return ("⛔Нет реквизитов",)                


