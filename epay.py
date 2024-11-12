import asyncio
import logging
import base64
from datetime import datetime, timedelta  # Добавлено timedelta для увеличения времени на час
import json  # Добавлен для работы с файлом

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

# Файл для хранения данных пользователей
USER_DATA_FILE = "user_data.json"

# Функция для загрузки данных пользователей из файла
def load_user_data():
    try:
        with open(USER_DATA_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Функция для сохранения данных пользователей в файл
def save_user_data():
    with open(USER_DATA_FILE, "w") as f:
        json.dump(user_data, f)

# Загрузка данных при старте
user_data = load_user_data()

class PaymentStates(StatesGroup):
    waiting_for_case_number = State()
    waiting_for_amount = State()

@router.message(Command('start'))
        async def cmd_start(message: Message, state: FSMContext):
            user_id = str(message.from_user.id)
            if user_id not in user_data:
                await message.answer('Пожалуйста, введите ваш № личного дела (только цифры):')
                await state.set_state(PaymentStates.waiting_for_case_number)
            else:
                keyboard = InlineKeyboardBuilder()
                keyboard.row(keyboard.button(text='Создать платеж', callback_data='create_payment'))
                keyboard.row(keyboard.button(text='Изменить № личного дела', callback_data='change_case_number'))
                await message.answer(
                    'Добро пожаловать обратно! Нажмите кнопку ниже, чтобы создать платеж или изменить № личного дела.',
                    reply_markup=keyboard.as_markup()
                )

@router.message(PaymentStates.waiting_for_case_number)
async def process_case_number(message: Message, state: FSMContext):
    case_number = message.text.strip()
    if not case_number.isdigit():
        await message.answer('Пожалуйста, введите корректный № личного дела (только цифры).')
        return
    user_id = str(message.from_user.id)
    user_data[user_id] = case_number
    save_user_data()  # Сохранить данные в файл
    await message.answer('Ваш № личного дела сохранен.')
    # Показать кнопку для создания платежа
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='Создать платеж', callback_data='create_payment')
    keyboard.button(text='Изменить № личного дела', callback_data='change_case_number')
    await message.answer(
        'Теперь вы можете создать платеж. Нажмите кнопку ниже.',
        reply_markup=keyboard.as_markup()
    )
    await state.clear()

@router.callback_query(F.data == 'change_case_number')
async def process_change_case_number(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.answer('Пожалуйста, введите ваш новый № личного дела:')
    await callback_query.answer()
    await state.set_state(PaymentStates.waiting_for_case_number)

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
    user_id = str(message.from_user.id)
    case_number = user_data.get(user_id)
    if not case_number:
        await message.answer('№ личного дела не найден. Пожалуйста, начните сначала с команды /start.')
        await state.clear()
        return
    # Генерация номера заказа (order_number) из текущей даты и времени с увеличением на 1 час
    now = datetime.now() + timedelta(hours=1)
    order_number = now.strftime('%d%m%H%M%S')  # Форматирует дату и время в нужный формат

    # Формирование строки с использованием case_number, amount и order_number
    data_string = f'api_key={case_number}&amount={amount}&merch={order_number}'
    # Кодирование в BASE64
    encoded_bytes = base64.b64encode(data_string.encode('utf-8'))
    encoded_string = encoded_bytes.decode('utf-8')
    # Создание ссылки
    link = f'https://t.me/epayapibot?start={encoded_string}'
    # Отправка ссылки пользователю
    await message.answer(f'Ссылка для оплаты: {link}')
    # Предложить создать новый платеж
    await message.answer('Введите сумму для следующего платежа или нажмите /start для возврата в меню.')
    # Состояние остается 'waiting_for_amount' для приема новой суммы

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
