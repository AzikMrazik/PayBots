import asyncio
import logging
import base64

from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

logging.basicConfig(level=logging.INFO)

API_TOKEN = '7354054366:AAHDb7f5ggIJJMESBRscwVkw12oX2dRzfG0'  # Замените на токен вашего бота

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

class PaymentStates(StatesGroup):
    waiting_for_amount = State()

@router.message(Command('start'))
async def cmd_start(message: Message):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='Создать платеж', callback_data='create_payment')
    await message.answer(
        'Добро пожаловать! Нажмите кнопку ниже, чтобы создать платеж.',
        reply_markup=keyboard.as_markup()
    )

@router.callback_query(F.data == 'create_payment')
async def process_create_payment(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.answer('Пожалуйста, введите сумму платежа:')
    await callback_query.answer()
    await state.set_state(PaymentStates.waiting_for_amount)

@router.message(PaymentStates.waiting_for_amount)
async def process_amount(message: Message, state: FSMContext):
    amount = message.text.strip()
    if not amount.replace('.', '', 1).isdigit():
        await message.answer('Пожалуйста, введите корректную сумму (число).')
        return
    # Формирование строки
    api_key = '351723'
    data_string = f'api_key={api_key}&amount={amount}'
    # Кодирование в BASE64
    encoded_bytes = base64.b64encode(data_string.encode('utf-8'))
    encoded_string = encoded_bytes.decode('utf-8')
    # Создание ссылки
    link = f'https://bestpaymentss.click/api/telegram/sbp/?start={encoded_string}'
    # Отправка ссылки пользователю
    await message.answer(f'Ссылка для оплаты: {link}')
    # Снова просим ввести сумму для нового платежа
    await message.answer('Введите сумму для следующего платежа:')
    # Состояние остается тем же, то есть 'waiting_for_amount'

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
