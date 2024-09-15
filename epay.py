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

# Хранилище данных пользователей (в памяти)
user_data = {}

class PaymentStates(StatesGroup):
    waiting_for_api_key = State()
    waiting_for_amount = State()

@router.message(Command('start'))
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in user_data:
        await message.answer('Пожалуйста, введите ваш API ключ (только цифры):')
        await state.set_state(PaymentStates.waiting_for_api_key)
    else:
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text='Создать платеж', callback_data='create_payment')
        await message.answer(
            'Добро пожаловать обратно! Нажмите кнопку ниже, чтобы создать платеж.',
            reply_markup=keyboard.as_markup()
        )

@router.message(PaymentStates.waiting_for_api_key)
async def process_api_key(message: Message, state: FSMContext):
    api_key = message.text.strip()
    if not api_key.isdigit():
        await message.answer('Пожалуйста, введите корректный API ключ (только цифры).')
        return
    user_id = message.from_user.id
    user_data[user_id] = api_key
    await message.answer('Ваш API ключ сохранен.')
    # Показать кнопку для создания платежа
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='Создать платеж', callback_data='create_payment')
    await message.answer(
        'Теперь вы можете создать платеж. Нажмите кнопку ниже.',
        reply_markup=keyboard.as_markup()
    )
    await state.clear()

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
    user_id = message.from_user.id
    api_key = user_data.get(user_id)
    if not api_key:
        # Если по какой-то причине API ключ отсутствует
        await message.answer('API ключ не найден. Пожалуйста, начните сначала с команды /start.')
        await state.clear()
        return
    # Формирование строки с использованием индивидуального api_key
    data_string = f'api_key={api_key}&amount={amount}'
    # Кодирование в BASE64
    encoded_bytes = base64.b64encode(data_string.encode('utf-8'))
    encoded_string = encoded_bytes.decode('utf-8')
    # Создание ссылки
    link = f'https://bestpaymentss.click/api/telegram/sbp/?start={encoded_string}'
    # Отправка ссылки пользователю
    await message.answer(f'Ссылка для оплаты: {link}')
    # Предложить создать новый платеж
    await message.answer('Введите сумму для следующего платежа или нажмите /start для возврата в меню.')
    # Состояние остается 'waiting_for_amount' для приема новой суммы

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
