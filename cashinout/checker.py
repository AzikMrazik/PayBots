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
    
    if 'from_ts' in data:
        filters['fromTimestampSeconds'] = data['from_ts']
        print(filters)
    if 'to_ts' in data and data['to_ts'] is not None:
        filters['toTimestampSeconds'] = data['to_ts']
        print(filters)
    
    # Формируем параметры запроса
    params = {
        'offset': 0,
        'limit': 999,
        'filters': json.dumps(filters)
    }
    print(params)
    # Отправляем запрос к API (заглушка)
    api_url = "https://api.cashinout.io/merchant/invoices"
    async with ClientSession() as session:
        async with session.get(
            api_url, headers={"Authorization": API_TOKEN}, params=params
        ) as response:
            resp = await response.json()
            successful_orders = [
            entry for entry in resp['data']['entries'] 
            if entry.get('status') == 'succeeded'
        ]