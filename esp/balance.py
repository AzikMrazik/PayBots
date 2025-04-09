from aiohttp import ClientSession
from aiogram import Bot, Router, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.formatting import *
from config import API_TOKEN, MERCHANT_ID, ADMINS, BASE_URL

router = Router()

def menu_kb():
    keyboard = [
        [InlineKeyboardButton(text="Назад в меню", callback_data='main_menu')],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@router.callback_query(F.data == 'balance')
async def balance_menu(callback_query: CallbackQuery, bot: Bot):
    await bot.answer_callback_query(callback_query.id)
    if callback_query.from_user.id not in ADMINS:
        await callback_query.message.answer("У вас нет доступа к этому разделу!", reply_markup=menu_kb())
    else:
        balance = await check_balance()
        await callback_query.message.answer(f"{balance}", reply_markup=menu_kb())

async def check_balance():
    async with ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/merchant/info",
            json={
            "merchantId": int(MERCHANT_ID), 
            "token": API_TOKEN 
                } 
        ) as response:
            data = await response.json()
            balance = data['balance']
            return f"Ваш баланс: <b>{balance}₽</b>"
        