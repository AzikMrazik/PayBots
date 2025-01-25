import asyncio
from aiohttp import ClientSession
from aiogram import Bot, Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.formatting import *
from config import API_TOKEN, BASE_URL
from checker import addorder

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
        [InlineKeyboardButton(text="СБП", callback_data='SBP')],
        [InlineKeyboardButton(text="КАРТА", callback_data='CARD')],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@router.callback_query(F.data == 'create_payment')
async def which_method(callback_query: CallbackQuery, bot: Bot, state: FSMContext):
    await state.clear()
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.answer("Выберите метод:", reply_markup=choose_kb())
    await state.set_state(PaymentStates.WAITING_CHOOSE)

@router.callback_query(PaymentStates.WAITING_CHOOSE)
async def how_many(callback_query: CallbackQuery, bot: Bot, state: FSMContext):
    await state.update_data(method=callback_query.data)
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.answer(text="Введите сумму платежа:", reply_markup=back_kb())
    await state.set_state(PaymentStates.WAITING_AMOUNT)

@router.message(PaymentStates.WAITING_AMOUNT)
async def create_payment(message: Message, bot: Bot, state: FSMContext):
    try:
        amount = int(message.text)
        amount = amount / 1.21
        amount = round(amount)
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
        data = await state.get_data()
        method = data.get("method")
        checkout = await sendpost(amount, message.from_user.id, method)
        await bot_msg.delete()
        if checkout != True:
            await message.reply(checkout[0])
            await message.answer(checkout[1])
        else:
            await message.reply("⛔Нет реквизитов!") 
        await state.clear()
        await message.answer("Выберет метод для следующего платежа:", reply_markup=choose_kb())  
        await state.set_state(PaymentStates.WAITING_CHOOSE)         

async def sendpost(amount, chat_id, method, counter=1):
    print(amount)
    async with ClientSession() as session:
        async with session.post(
            f"{BASE_URL}new-order",
            params={
                "apiKey": API_TOKEN,
                "amount": amount,
                "type_fiat": method
            }
        ) as response:
            resp = await response.json(content_type=None)
            status = resp['status']
            if status == "ok":
                data = resp['data']
                order_id = data['orderId']
                precise_amount = data['amountExc']
                card = data['paymentData']
                send_type = "карты"
                if method == "SBP":
                    card = "+" + card
                    send_type = "телефона"
                try:
                    bank = data['bank']
                except:
                    bank = "Не найден"
                await addorder(order_id, chat_id, precise_amount)
                return (f"📄 Создан заказ: №<code>{order_id}</code>\n\n💳Номер {send_type} для оплаты: <code>{card}</code>\n💰Сумма платежа: <code>{precise_amount}</code> рублей\n\n🕑 Время на оплату: 15 мин.", F"🏦Банк: {bank}")
            elif status == "error":
                if counter < 10:
                    counter += 1
                    print("again")
                    await asyncio.sleep(3)
                    return await sendpost(amount, chat_id, method, counter)   
                else:
                    return True
            else:
                print("Fuck")

