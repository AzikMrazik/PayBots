from aiohttp import ClientSession
from aiogram import Bot, Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.formatting import *
from config import API_TOKEN, ADMINS, BASE_URL

router = Router()

class PaymentStates(StatesGroup):
    WAITING_BALANCE = State()
    WAITING_WALLET = State()
    WAITING_NUMBER = State()

def choose_kb():
    keyboard = [
        [InlineKeyboardButton(text="Вывести", callback_data='cashout')],
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
    balance, rate = await check_balance()
    await callback_query.message.answer(text=f"💰Ваш баланс: {balance} RUB\n💱Курс: {rate} RUB за 1 USDT", reply_markup=choose_kb())

@router.callback_query(F.data == 'cashout')
async def how_many(callback_query: CallbackQuery, bot: Bot, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.answer("Введите сумму для вывода:", reply_markup=back_kb())
    await state.set_state(PaymentStates.WAITING_BALANCE)

@router.message(PaymentStates.WAITING_BALANCE)
async def which_wallet(message: Message, state: FSMContext):
    aval_balance = await check_balance()
    try:
        amount = int(message.text)
        if amount > int(aval_balance[0]):
            await message.answer("Вы не можете вывести больше, чем у вас есть!")
            await message.answer(text="Введите сумму снова:", reply_markup=back_kb())
            return
    except Exception as e:
        print(e, flush=True)
        await message.answer("Вы ввели неверное значение!")
        await message.answer(text="Введите сумму снова:", reply_markup=back_kb())
        return
    await state.update_data(amount=amount)
    await message.answer(text="Введите адрес вашего кошелька:", reply_markup=back_kb())
    await state.set_state(PaymentStates.WAITING_WALLET)

@router.message(PaymentStates.WAITING_WALLET)
async def create_order(message: Message, state: FSMContext):
    wallet = message.text
    if len(wallet) < 34:
            await message.answer("Неккоретный кошелёк")
            await message.answer(text="Введите сумму снова:", reply_markup=back_kb())
            return
    data = await state.get_data()
    amount = data.get("amount") 
    async with ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/v1/payout/payout",
            headers={'authorization': 'Bearer ' + API_TOKEN},
            json={
                "amount": str(amount),
                "wallet": wallet
                  }
        ):
            try:
                await message.answer(f"✅Заявка успешно создана!", reply_markup=last_kb())
            except:
                await message.answer(f"{data}")
                await message.answer("Произошла ошибка отправьте сообщение выше кодеру!")

async def check_balance():
    async with ClientSession() as session:
        async with session.get(
            f"{BASE_URL}/v1/payout/balance",
            headers={'authorization': 'Bearer ' + API_TOKEN}
        ) as response:
            data = await response.json()
            balance = data['balance']
            rate = data['rate']
            return (balance, rate)