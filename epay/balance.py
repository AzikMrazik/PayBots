from aiohttp import ClientSession
from aiogram import Bot, Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.formatting import *
from config import API_TOKEN, BASE_URL, ADMINS

router = Router()

class PaymentStates(StatesGroup):
    WAITING_BALANCE = State()
    WAITING_WALLET = State()
    WAITING_NUMBER = State()

def choose_kb():
    keyboard = [
        [InlineKeyboardButton(text="Вывести", callback_data='cashout')],
        [InlineKeyboardButton(text="Проверить статус заявки", callback_data='check')],
        [InlineKeyboardButton(text="Назад в меню", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def back_kb():
    keyboard = [
        [InlineKeyboardButton(text="Назад", callback_data='balance')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def menu_kb():
    keyboard = [
        [InlineKeyboardButton(text="Назад в меню", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def last_kb():
    keyboard = [
        [InlineKeyboardButton(text="Назад", callback_data='balance')],
        [InlineKeyboardButton(text="Назад в меню", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@router.callback_query(F.data == 'balance')
async def balance_menu(callback_query: CallbackQuery, bot: Bot):
    await bot.answer_callback_query(callback_query.id)
    if callback_query.from_user.id not in ADMINS:
        await callback_query.message.answer("У вас нет доступа к этому разделу!", reply_markup=menu_kb())
    balance = await check_balance("standart")
    await callback_query.message.answer(text=balance, reply_markup=choose_kb())

@router.callback_query(F.data == 'cashout')
async def how_many(callback_query: CallbackQuery, bot: Bot, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.answer("Введите сумму для вывода:", reply_markup=back_kb())
    await state.set_state(PaymentStates.WAITING_BALANCE)

@router.message(PaymentStates.WAITING_BALANCE)
async def which_wallet(message: Message, bot: Bot, state: FSMContext):
    aval_balance = await check_balance("cashout")
    try:
        amount = int(message.text)
        if amount > aval_balance:
            await message.answer("Вы не можете вывести больше, чем у вас есть!")
            await message.answer(text="Введите сумму снова:", reply_markup=back_kb())
            return
    except:
        await message.answer("Вы ввели неверное значение!")
        await message.answer(text="Введите сумму снова:", reply_markup=back_kb())
        return
    await state.update_data(amount=amount)
    await message.answer(text="Введите адрес вашего кошелька:", reply_markup=back_kb())
    await state.set_state(PaymentStates.WAITING_WALLET)

@router.message(PaymentStates.WAITING_WALLET)
async def create_order(message: Message, state: FSMContext):
    wallet = message.text
    data = await state.get_data()
    amount = data.get("amount") 
    print(type(amount)) 
    async with ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/payout",
            json={
                "api_key": API_TOKEN,
                "amount": amount,
                "method": 3,
                "wallet": wallet
                  }
        ) as response:
            await message.answer(f"{response.url}")
            data = await response.json()
            try:
                await message.answer(f"✅Заявка №<code>{data['id']}</code> успешно создана!", reply_markup=last_kb())
            except:
                await message.answer(f"{data}")
                await message.answer("Произошла ошибка отправьте сообщение выше кодеру!")

async def check_balance(fromwho):
    async with ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/balances/get",
            json={
                "api_key": API_TOKEN
                  }
        ) as response:
            resp = await response.json()
            if fromwho == "cashout":
                return resp['balance_enable']
            else:
                return f"Ваш баланс: <b>{resp['balance']}₽</b>\nДоступный баланс для вывода: <b>{resp['balance_enable']}₽</b>"
        
@router.callback_query(F.data == 'check')
async def which_order(callback_query: CallbackQuery, bot: Bot, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.answer("Введите номер заявки:", reply_markup=back_kb())
    await state.set_state(PaymentStates.WAITING_NUMBER)

@router.message(PaymentStates.WAITING_NUMBER)
async def check_order(message: Message, state: FSMContext):
    await state.clear()
    try:
        order_id = message.text
    except:
        await message.answer("Вы ввели неверное значение!")
        await message.answer("Введите номер снова:", reply_markup=back_kb())
        return
    async with ClientSession() as session:
        async with session.get(
            f"{BASE_URL}/payout/{order_id}?api_key={API_TOKEN}"
        ) as response:
            data = await response.json()
            try:
                await message.answer(f"Заявка №<code>{data['id']}</code> находится в статусе {data['status']}.")
            except:
                await message.answer(f"{data}")
                await message.answer("Произошла ошибка отправьте сообщение выше кодеру!")