from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from keyboards import main_menu_kb


router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    text = (
        "👋 Добро пожаловать в <b>RF x TSA</b>!\n\n"
        "Выберите действие с помощью кнопок ниже."
    )
    await message.answer(text, reply_markup=main_menu_kb().as_markup())


@router.callback_query(lambda c: c.data == "back:main")
async def cb_back_main(call: CallbackQuery) -> None:
    await call.message.edit_text(
        "Главное меню. Выберите действие:", reply_markup=main_menu_kb().as_markup()
    )
    await call.answer()

