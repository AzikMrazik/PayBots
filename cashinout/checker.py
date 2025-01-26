import logging
import asyncio
import json
from datetime import datetime
from aiohttp import ClientSession
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.formatting import *
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from config import API_TOKEN

router = Router()

class PaymentStates(StatesGroup):
    WAITING_STARTDATE = State()
    WAITING_ENDDATE = State()

def back_kb():
    keyboard = [
        [InlineKeyboardButton(text="Назад в меню", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def choose_kb():
    keyboard = [[InlineKeyboardButton(text="Оставить пустым", callback_data='empty')],
                [InlineKeyboardButton(text="Назад в меню", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@router.callback_query(F.data == 'check')
async def how_many(callback_query: CallbackQuery, bot: Bot, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.answer(
        "Введите дату начала поиска (ДД.ММ.ГГГГ):", 
        reply_markup=back_kb()
    )
    await state.set_state(PaymentStates.WAITING_STARTDATE)

@router.message(PaymentStates.WAITING_STARTDATE)
async def process_start_date(message: Message, state: FSMContext):
    try:
        date_obj = datetime.strptime(message.text, "%d.%m.%Y")
        await state.update_data(from_ts=int(date_obj.timestamp()))
        await message.answer(
            "Введите дату окончания (ДД.ММ.ГГГГ) или нажмите 'Оставить пустым':",
            reply_markup=choose_kb()
        )
        await state.set_state(PaymentStates.WAITING_ENDDATE)
    except ValueError:
        await message.answer("❌ Неверный формат даты!", reply_markup=back_kb())

@router.callback_query(F.data == 'empty', PaymentStates.WAITING_ENDDATE)
async def process_empty_end_date(callback: CallbackQuery, state: FSMContext):
    await state.update_data(to_ts=None)
    await process_final_request(callback.message, state)

@router.message(PaymentStates.WAITING_ENDDATE)
async def process_end_date(message: Message, state: FSMContext):
    try:
        date_obj = datetime.strptime(message.text, "%d.%m.%Y")
        await state.update_data(to_ts=int(date_obj.timestamp()))
        await process_final_request(message, state)
    except ValueError:
        await message.answer("❌ Неверный формат даты!", reply_markup=choose_kb())

async def process_final_request(message: Message, state: FSMContext):
    data = await state.get_data()
    filters = {}
    
    # Формируем фильтры с правильным форматом времени
    if 'from_ts' in data:
        filters['fromTimestampSeconds'] = int(data['from_ts'])
    if 'to_ts' in data and data['to_ts'] is not None:
        filters['toTimestampSeconds'] = int(data['to_ts'])
    
    # Формируем параметры с правильной сериализацией JSON
    params = {
        'offset': 0,
        'limit': 999,
        'filters': json.dumps(filters, separators=(',', ':'))  # Убираем пробелы в JSON
    }
    
    print("Отправляемые параметры:", params)  # Для отладки
    
    api_url = "https://example.com/merchant/invoices"
    async with ClientSession() as session:
        async with session.get(
            api_url, headers={"Authorization": API_TOKEN}, params=params
        ) as response:
            resp = await response.json()
            successful_orders = [
            entry for entry in resp['data']['entries'] 
            if entry.get('status') == 'succeeded'
        ]
        
        # Сохраняем заказы в хранилище состояний
        await state.update_data(orders=successful_orders)
        
        # Считаем суммы
        total_rub = sum(float(order['currentAmountCurrency']) for order in successful_orders)
        total_usdt = sum(float(order['currentAmountUsdt']) for order in successful_orders)
        
        # Формируем сообщение со сводкой
        summary = [
            Bold("📊 Сводка за период:"),
            f"Всего успешных заказов: {len(successful_orders)}",
            f"Сумма в RUB: {total_rub:.2f}",
            f"Сумма в USDT: {total_usdt:.2f}",
        ]
        
        # Создаем клавиатуру с кнопкой
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Показать все заказы", callback_data="show_all_orders")],
            [InlineKeyboardButton(text="Назад в меню", callback_data="main_menu")]
        ])
        
        await message.answer(**as_section(*summary), reply_markup=keyboard)
        await state.set_state(PaymentStates.SHOW_DETAILS)

# Обработчик для кнопки "Показать все заказы"
@router.callback_query(F.data == "show_all_orders", PaymentStates.SHOW_DETAILS)
async def show_all_orders(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    orders = data.get('orders', [])
    
    for order in orders:
        order_text = as_section(
            Bold("📝 Детали заказа:"),
            f"ID: {order['id']}",
            f"Сумма в RUB: {order['currentAmountCurrency']}",
            f"Сумма в USDT: {order['currentAmountUsdt']}",
            f"Дата: {datetime.fromtimestamp(order['createdTimestampSeconds']).strftime('%d.%m.%Y %H:%M')}",
            "-------------------------"
        )
        await callback.message.answer(**order_text)
    
    await callback.answer()
    await state.clear()