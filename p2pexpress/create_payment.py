import asyncio
from aiosqlite import connect
from aiohttp import ClientSession
from aiogram import Bot, Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.formatting import *
from config import API_TOKEN, BASE_URL
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
        if amount < 2500 or amount > 10000:
            await message.answer("Доступная сумма платежа 2500 - 10000 RUB!")
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
        await message.answer("Введите сумму для следующего платежа:", reply_markup=back_kb())
        await state.set_state(PaymentStates.WAITING_AMOUNT)

async def check_bank(bin):
    async with connect("bins.db") as db:
        cursor = await db.execute(
            "SELECT bank_name FROM bins WHERE bin = ?", 
            (bin,)
        )
        result = await cursor.fetchone()
        return result[0]

async def sendpost(amount, chat_id, msg, counter):
    client_order_id = datetime.now().strftime("%d%m%H%M%S")
    async with ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/v1/payment/h2h",
            headers={'authorization': 'Bearer ' + API_TOKEN},
            json={
                "amount": str(amount),
                "currency": "rub",
                "method": "all",
                "client_order_id": client_order_id
            }
        ) as response:
            try:
                data = await response.json()
                print(data, flush=True)
            except:
                data = await response.text()    
                return ("⚰️P2PExpress отправил труп!", f"{data}", "Отправьте сообщение выше кодеру!")
            else:
                status = data['status']
                if status != "error":
                    data = data['data']
                    payment_id = data['payment_id']
                    type = data['type']
                    bank_name = data['bank']
                    card = data['credentials']
                    card = re.sub(r'\s+', '', card)
                    try:
                        card_name = data['account_owner_name']
                    except:
                        card_name = None
                    precise_amount = data['need_to_pay']
                    if type == "sbp":
                        bank_type = "телефона"
                    elif type == "card":
                        bank_type = "карты"
                        bin = card[:6]
                        if bin[:3] != "220":
                            if counter < 5:
                                counter += 1
                                await msg.edit_text(f"⌛️Ожидаем реквизиты...({counter}/5)")
                                await asyncio.sleep(3)
                                return await sendpost(amount, chat_id, msg, counter)
                            else:
                                return ("⛔Нет реквизитов!",)
                        try:
                            bank_name = await check_bank(bin)
                        except:
                            pass
                    else:
                        bank_type = "счёта"
                    await addorder(client_order_id, chat_id, precise_amount, payment_id)
                    if card_name:
                        return (f"📄Создана заявка: №<code>{client_order_id}</code>\n\n💳Номер {bank_type} для оплаты: <code>{card}</code>\n💰Сумма платежа: <code>{precise_amount}</code> рублей\n\n🕑 Время на оплату: 10 мин.",
                                f"🙍‍♂️Получатель: {card_name}\n🏦Банк: {bank_name}")
                    elif card_name == "none":
                        return (f"📄Создана заявка: №<code>{client_order_id}</code>\n\n💳Номер {bank_type} для оплаты: <code>{card}</code>\n💰Сумма платежа: <code>{precise_amount}</code> рублей\n\n🕑 Время на оплату: 10 мин.",
                                f"🏦Банк: {bank_name}")
                    else:
                        return (f"📄Создана заявка: №<code>{client_order_id}</code>\n\n💳Номер {bank_type} для оплаты: <code>{card}</code>\n💰Сумма платежа: <code>{precise_amount}</code> рублей\n\n🕑 Время на оплату: 10 мин.",
                                f"🏦Банк: {bank_name}")
                else:
                    desc = data['error']
                    if desc == "NO_PAYMENTS_AVAILABLE":
                        if counter < 5:
                                counter += 1
                                await msg.edit_text(f"⌛️Ожидаем реквизиты...({counter}/5)")
                                await asyncio.sleep(3)
                                return await sendpost(amount, chat_id, msg, counter)
                        else:
                            return ("⛔Нет реквизитов!",)
                    else:
                        return ("❓Неизвестная ошибка", f"{desc}", "Отправьте сообщение выше кодеру!")              


