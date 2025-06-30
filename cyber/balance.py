from aiogram import Bot, types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging
import config
import aiohttp

router = Router()

class PaymentStates(StatesGroup):
    WAITING_AMOUNT = State()
    WAITING_WALLET = State()

@router.message(callback_query=F.data == 'balance')
async def show_balance(callback_query: types.CallbackQuery, bot: Bot, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.answer("Укажите сумму для вывода в TRX:")

@router.message(PaymentStates.WAITING_AMOUNT)
async def get_amount(message: types.Message, state: FSMContext):
    amount = message.text.strip()
    await state.update_data(amount=amount)
    await message.answer("Укажите кошелек для вывода:")

@router.message(PaymentStates.WAITING_WALLET)
async def get_wallet(message: types.Message, state: FSMContext):
    if len(message.text.strip()) != 34:
        await message.answer("⛔Ошибка! Неверный формат кошелька. Пожалуйста, введите корректный кошелек TRX.")
        return
    wallet = message.text.strip()
    amount = state.get_data().get("amount")
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{config.BASE_URL}/api/payout",
                                headers={"Authorization": f"Bearer {config.API_TOKEN}"},
                                json={"data": [{"sum": str(amount)}],
                                "wallet": wallet,
                                "method_id": "37"}) as response:
                data = await response.json()
                try:
                    status = data.get("status")
                    await message.answer("✅Выплата запрошена успешно!")
                    return
                except Exception as e:
                    for key, value in data.items():
                        await message.answer(f"⛔Ошибка!\n{key}: {value}")
                    return
                

