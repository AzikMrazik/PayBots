from decimal import Decimal

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from aiogram.types import Message
from aiogram.filters import Command
from aiogram import Router
from database import Database
from utils import format_money, parse_decimal


router = Router()


@router.message(Command("balance"))
async def cmd_balance(message: Message) -> None:
    db: Database = message.bot.dispatcher.get("db")  # type: ignore[attr-defined]
    balance = await db.get_balance(message.from_user.id)  # type: ignore[union-attr]
    await message.answer(f"Ваш баланс: <b>{format_money(balance)}</b>")


@router.message(Command("refill"))
async def cmd_refill(message: Message) -> None:
    db: Database = message.bot.dispatcher.get("db")  # type: ignore[attr-defined]
    parts = (message.text or "").split()
    if len(parts) != 2:
        await message.answer("Использование: /refill <сумма>. Пример: /refill 10.5")
        return
    try:
        amount = parse_decimal(parts[1])
        new_balance = await db.add_balance(message.from_user.id, amount)  # type: ignore[union-attr]
        await message.answer(
            f"Пополнение успешно. Текущий баланс: <b>{format_money(new_balance)}</b>"
        )
    except Exception as e:
        await message.answer(f"Ошибка пополнения: {e}")

