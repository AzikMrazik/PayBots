from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message


router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    text = (
        "👋 Добро пожаловать в <b>RF x TSA</b>!\n\n"
        "Этот бот помогает экономить на комиссиях в сети Tron с помощью сервиса re:fee.bot.\n\n"
        "Доступные команды:\n"
        "/balance — показать баланс\n"
        "/refill <сумма> — пополнить баланс (виртуально)\n"
        "/buyenergy <адрес> <энергия> — купить энергию\n"
        "/buybandwidth <адрес> <кол-во> — купить bandwidth\n"
        "/calculate — калькулятор энергии/стоимости\n"
        "/addwallet <метка> <адрес> — сохранить адрес Tron\n"
        "/mywallets — список моих адресов\n"
    )
    await message.answer(text)

