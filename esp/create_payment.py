from aiosqlite import connect
from aiohttp import ClientSession
from aiogram import Bot, Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.formatting import *
from config import API_TOKEN, BASE_URL, DOMAIN, MERCHANT_ID
from datetime import datetime
import re

router = Router()

class PaymentStates(StatesGroup):
    WAITING_AMOUNT = State()
    WAITING_CHOOSE = State()

def back_kb():
    keyboard = [
        [InlineKeyboardButton(text="Назад в меню", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def choose_kb():
    keyboard = [
        [InlineKeyboardButton(text="Карта", callback_data='card')],
        [InlineKeyboardButton(text="СБП", callback_data='spb')],
        [InlineKeyboardButton(text="Назад в меню", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@router.callback_query(F.data == 'create_payment')
async def choose_method(callback_query: CallbackQuery, bot: Bot, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.answer("Введите сумму платежа:", reply_markup=choose_kb())
    await state.set_state(PaymentStates.WAITING_AMOUNT)

@router.message(PaymentStates.WAITING_CHOOSE)
async def how_many(callback_query: CallbackQuery, bot: Bot, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await state.update_data(payment_method=callback_query.data)
    await callback_query.message.answer("Введите сумму платежа:", reply_markup=back_kb())
    await state.set_state(PaymentStates.WAITING_AMOUNT)

@router.message(PaymentStates.WAITING_AMOUNT)
async def create_payment(message: Message,  state: FSMContext):
    user_data = await state.get_data()
    payment_method = user_data.get('payment_method')
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
        order = await sendpost(amount, message.from_user.id, payment_method)
        await msg.delete()
        for i in order:
            await message.answer(i)
        await message.answer("Выберите метод для следующего платежа:", reply_markup=choose_kb())
        await state.set_state(PaymentStates.WAITING_CHOOSE)
    
async def check_name(bin):
    async with connect("bins.db") as db:
        cursor = await db.execute(
            "SELECT bank_name FROM bins WHERE bin = ?", 
            (bin,)
        )
        result = await cursor.fetchone()
        return result[0]

async def sendpost(amount, chat_id, payment_method):
    order_id = datetime.now().strftime("%d%m%H%M%S")
    async with ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/create",
            json={
                "merchantId": int(MERCHANT_ID),
                "token": API_TOKEN,
                "orderId": order_id,
                "client": order_id, 
                "clientIp": "80.71.157.117", 
                "callback": f"https://{DOMAIN}/espay/{chat_id}",
                "amount": int(amount),
                "type": payment_method
            }
        ) as response:
            try:
                data = await response.json()
            except:
                data = await response.text()
                return (f"⚰️", f"ES-Pay отправил труп!", f"{data}", "Отправьте сообщение выше кодеру!")
            else:
                order_status = data['status']
                print(data, flush=True)
                if order_status == "success":
                    data = data['data']
                    order_id = data['id']
                    requisites = data['requisites']
                    try:
                        card = requisites['card_number']
                        sbp = False
                        card = re.sub(r'\s+', '', card)
                        bank_type = "карты"
                    except:
                        card = requisites['sbp_phone']
                        sbp = True
                        bank_type = "телефона"
                    bank_name = requisites['bank']
                    owner_name = requisites['name']
                    if not sbp:
                        bin = card[:6]
                        bank_name = await check_name(bin)
                    return (f"📄 Создана заявка: №<code>{order_id}</code>\n\n💳 Номер {bank_type} для оплаты: <code>{card}</code>\n💰Сумма платежа: <code>{amount}</code> рублей\n\n🕑 Время на оплату: 20 мин.", F"🏦Банк: {bank_name}\n🙍‍♂️Получатель: {owner_name}")
                else:
                    desc = data['message']
                    return ("❓Неизвестная ошибка", f"{desc}", "Отправьте сообщение выше кодеру!")                


