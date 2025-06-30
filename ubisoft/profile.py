from aiogram import Bot, types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging
import dbworker
import keyboards
import systems
from lexicon import get_text

router = Router()

class ProfileStates(StatesGroup):
    WAITING_FOR_API_KEY = State()
    WAITING_FOR_SYSTEM_SELECTION = State()
    WAITING_FOR_NEW_SYSTEM_SELECTION = State()

@router.callback_query(F.data == 'profile')
async def show_profile(callback_query: types.CallbackQuery, bot: Bot, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    chat_id = callback_query.from_user.id
    chat_info = await dbworker.get_chatinfo(chat_id)
    systems = chat_info.get('systems', await get_text("error_occured", chat_id))
    await callback_query.message.answer(text=await get_text("profile_info", chat_id), reply_markup=keyboards.profile_kb(chat_id))

@router.callback_query(F.data == 'user_systems')
async def user_systems(callback_query: types.CallbackQuery, bot: Bot, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    chat_id = callback_query.from_user.id
    chat_info = await dbworker.get_chatinfo(chat_id)
    systems = chat_info.get('systems')
    if systems == '[]':
        available_systems = {}
        for system in systems.ACTIVE_SYSTEMS:
            available_systems = systems.ACTIVE_SYSTEMS[system]['name']
        await callback_query.message.answer(text=await get_text("no_systems", chat_id), reply_markup=keyboards.choose_new_systems_kb(chat_id, available_systems))
        state.set_state(ProfileStates.WAITING_FOR_NEW_SYSTEM_SELECTION)
    else:
        await callback_query.message.answer(text=await get_text("user_systems", chat_id), reply_markup=keyboards.choose_user_systems_kb(chat_id, systems.keys()))
        state.set_state(ProfileStates.WAITING_FOR_SYSTEM_SELECTION)

@router.callback_query(ProfileStates.WAITING_FOR_SYSTEM_SELECTION)
async def select_system(callback_query: types.CallbackQuery, bot: Bot, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    system = callback_query.data
    chat_id = callback_query.from_user.id
    chat_info = await dbworker.get_chatinfo(chat_id)
    lang = chat_info.get('lang')
    if system in systems.ACTIVE_SYSTEMS:
        selected_system = systems.ACTIVE_SYSTEMS[system]
        secrets = systems.ACTIVE_SYSTEMS[system]['secrets']
        await callback_query.message.answer(text=await get_text("system_selected", chat_id), reply_markup=keyboards.system_selected_kb(chat_id, secrets.keys()))
    else:
        chat_info.get('systems').pop(system, None)
        await dbworker.change_chatinfo(chat_id, systems=chat_info.get('systems'))
        await callback_query.message.answer(text=await get_text("system_not_found", chat_id), reply_markup=keyboards.back_to_systems_kb(chat_id))

@router.callback_query(F.data.startswith('secrets_'))
async def handle_secrets(callback_query: types.CallbackQuery, bot: Bot, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    sys = callback_query.data.split('_')[1]
    sec_name = callback_query.data.split('_')[2]
    chat_id = callback_query.from_user.id
    
    # Сохраняем переменные в FSM
    await state.update_data(sys=sys, sec_name=sec_name)
    
    await callback_query.message.answer(text=await get_text("secret_info", chat_id), reply_markup=keyboards.change_secret_kb(chat_id))

@router.callback_query(F.data.startswith('secretsedit_'))
async def edit_secret(callback_query: types.CallbackQuery, bot: Bot, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    sys = callback_query.data.split('_')[1]
    sec_name = callback_query.data.split('_')[2]
    chat_id = callback_query.from_user.id
    
    # Сохраняем переменные в FSM
    await state.update_data(sys=sys, sec_name=sec_name)
    
    await callback_query.message.answer(text=await get_text("edit_secret_info", chat_id))
    await state.set_state(ProfileStates.WAITING_FOR_SECRET)

@router.message(ProfileStates.WAITING_FOR_SECRET)
async def handle_secret_edit(message: types.Message, bot: Bot, state: FSMContext):
    chat_id = message.from_user.id
    sec_val = message.text
    
    # Получаем переменные из FSM
    data = await state.get_data()
    sys = data.get('sys')
    sec_name = data.get('sec_name')
    
    chat_info = await dbworker.get_chatinfo(chat_id)
    systems = chat_info.get('systems')
    systems[sys]['secrets'][sec_name] = sec_val
    await dbworker.change_chatinfo(chat_id, systems=systems)
    
    await state.clear()

@router.callback_query(ProfileStates.WAITING_FOR_NEW_SYSTEM_SELECTION)
async def select_new_system(callback_query: types.CallbackQuery, bot: Bot, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    system = callback_query.data
    chat_id = callback_query.from_user.id
    secrets = systems.ACTIVE_SYSTEMS[system]['secrets']
    

