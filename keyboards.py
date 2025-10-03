from typing import Iterable, List, Optional, Tuple

from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_kb() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(text="💰 Баланс", callback_data="menu:balance")
    kb.button(text="➕ Пополнить", callback_data="menu:refill")
    kb.button(text="⚡ Купить энергию", callback_data="menu:buy_energy")
    kb.button(text="📶 Купить bandwidth", callback_data="menu:buy_bandwidth")
    kb.button(text="🧮 Калькулятор", callback_data="menu:calculate")
    kb.button(text="👛 Мои кошельки", callback_data="menu:wallets")
    kb.adjust(2, 2, 2)
    return kb


def back_main_kb() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ Назад", callback_data="back:main")
    kb.button(text="❌ Отмена", callback_data="cancel")
    kb.adjust(2)
    return kb


def refill_kb() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    for amount in ("5", "10", "25", "50"):
        kb.button(text=f"+{amount}", callback_data=f"refill:amount:{amount}")
    kb.button(text="Другая сумма", callback_data="refill:other")
    kb.button(text="⬅️ Назад", callback_data="back:main")
    kb.adjust(4, 1, 1)
    return kb


def wallets_manage_kb() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Добавить", callback_data="wallets:add")
    kb.button(text="🗑 Удалить", callback_data="wallets:delete")
    kb.button(text="📋 Список", callback_data="wallets:list")
    kb.button(text="⬅️ Назад", callback_data="back:main")
    kb.adjust(2, 2)
    return kb


def wallets_select_kb(wallets: Iterable[Tuple[int, str, Optional[str]]], prefix: str) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    for wid, address, label in wallets:
        show = label or address[-8:]
        kb.button(text=f"{show}", callback_data=f"{prefix}:{wid}")
    kb.button(text="➕ Добавить кошелёк", callback_data="wallets:add")
    kb.button(text="⬅️ Назад", callback_data="back:main")
    kb.adjust(1, 1, 1)
    return kb


def confirm_kb(prefix: str) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Подтвердить", callback_data=f"{prefix}:confirm")
    kb.button(text="❌ Отмена", callback_data="cancel")
    kb.adjust(2)
    return kb

