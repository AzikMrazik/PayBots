from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from database import Database
from utils import is_valid_tron_address, sanitize_label


router = Router()


@router.message(Command("addwallet"))
async def cmd_add_wallet(message: Message) -> None:
    db: Database = message.bot.dispatcher.get("db")  # type: ignore[attr-defined]
    parts = (message.text or "").split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("Использование: /addwallet <метка> <адрес>")
        return
    label, address = sanitize_label(parts[1]), parts[2].strip()
    if not is_valid_tron_address(address):
        await message.answer("Некорректный Tron-адрес")
        return
    try:
        await db.add_wallet(message.from_user.id, address, label)  # type: ignore[union-attr]
        await message.answer("Адрес сохранён ✅")
    except Exception as e:
        await message.answer(f"Не удалось сохранить адрес: {e}")


@router.message(Command("mywallets"))
async def cmd_my_wallets(message: Message) -> None:
    db: Database = message.bot.dispatcher.get("db")  # type: ignore[attr-defined]
    wallets = await db.list_wallets(message.from_user.id)  # type: ignore[union-attr]
    if not wallets:
        await message.answer("У вас пока нет сохранённых адресов.")
        return
    lines = [
        f"#{wid}: <code>{addr}</code> — {label or 'без метки'}" for (wid, addr, label) in wallets
    ]
    await message.answer("\n".join(lines))

