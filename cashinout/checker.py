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
from aiogram.utils.formatting import Bold, Text, as_section
from config import API_TOKEN

router = Router()

class PaymentStates(StatesGroup):
    WAITING_STARTDATE = State()
    WAITING_ENDDATE = State()
    SHOW_DETAILS = State()

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

def last_kb():
        keyboard = [
            [InlineKeyboardButton(text="Показать все заказы", callback_data="show_all_orders")],
            [InlineKeyboardButton(text="Назад в меню", callback_data="main_menu")]
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
    print(data)
    # Формируем фильтры с правильным форматом времени
    if 'from_ts' in data:
        fromts = f"fromTimestampSeconds: {int(data['from_ts'])};"
    if 'to_ts' in data and data['to_ts'] is not None:
        tots = f"\ntoTimestampSeconds: {int(data['to_ts'])};"
    filters = "{\n" + fromts + tots + "\n}"
    
    api_url = "https://api.cashinout.io/merchant/invoices?offset=0&limit=999&filters=" + filters
    async with ClientSession() as session:
        async with session.get(
            api_url, headers={"Authorization": API_TOKEN}
        ) as response:
            print(response.url)
            resp = await response.json()
            successful_orders = [
            entry for entry in resp['data']['entries'] 
            if entry.get('status') == 'succeeded'
        ]
        
        # Сохраняем заказы в хранилище состояний
        await state.update_data(orders=successful_orders)
        
        total_rub = sum(float(order['currentAmountCurrency']) for order in successful_orders)
        total_usdt = sum(float(order['currentAmountUsdt']) for order in successful_orders)
        
        # Формируем текст правильно
        text = as_list(
            Bold("📊 Сводка за период:"),
            Text(f"Всего успешных заказов: {len(successful_orders)}"),
            Text(f"Сумма в RUB: {total_rub:.2f}"),
            Text(f"Сумма в USDT: {total_usdt:.2f}"),
        )

        await message.answer(**text.as_kwargs(), reply_markup=last_kb())
        await state.set_state(PaymentStates.SHOW_DETAILS)

# Обработчик для кнопки "Показать все заказы"
@router.callback_query(F.data == "show_all_orders", PaymentStates.SHOW_DETAILS)
@router.callback_query(F.data == "show_all_orders", PaymentStates.SHOW_DETAILS)
async def show_all_orders(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    orders = data.get('orders', [])
    
    for order in orders:
        order_text = as_list(
            Bold("📝 Детали заказа:"),
            Text(f"ID: {order['id']}"),
            Text(f"Сумма в RUB: {order['currentAmountCurrency']}"),
            Text(f"Сумма в USDT: {order['currentAmountUsdt']}"),
            Text(f"Дата: {datetime.fromtimestamp(order['createdTimestampSeconds']).strftime('%d.%m.%Y %H:%M')}"),
            Text("-------------------------")
        )
        await callback.message.answer(**order_text.as_kwargs())  # Добавлен .as_kwargs()
        await asyncio.sleep(0.33)
    
    await callback.answer()
    await state.clear()