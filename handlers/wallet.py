from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database import Database
from utils import is_valid_tron_address, sanitize_label
from keyboards import wallets_manage_kb, wallets_select_kb, main_menu_kb
from states import AddWalletStates


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


# ===== Inline wallets management =====


@router.callback_query(lambda c: c.data == "menu:wallets")
async def cb_wallets_menu(call: CallbackQuery) -> None:
    await call.message.edit_text(
        "Управление кошельками:", reply_markup=wallets_manage_kb().as_markup()
    )
    await call.answer()


@router.callback_query(lambda c: c.data == "wallets:list")
async def cb_wallets_list(call: CallbackQuery) -> None:
    db: Database = call.message.bot.dispatcher.get("db")  # type: ignore[attr-defined]
    wallets = await db.list_wallets(call.from_user.id)  # type: ignore[union-attr]
    if not wallets:
        await call.message.edit_text(
            "У вас пока нет сохранённых адресов.", reply_markup=wallets_manage_kb().as_markup()
        )
    else:
        lines = [f"#{wid}: <code>{addr}</code> — {label or 'без метки'}" for (wid, addr, label) in wallets]
        await call.message.edit_text("\n".join(lines), reply_markup=wallets_manage_kb().as_markup())
    await call.answer()


@router.callback_query(lambda c: c.data == "wallets:add")
async def cb_wallets_add(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AddWalletStates.entering_address)
    await call.message.edit_text("Отправьте Tron-адрес для сохранения.")
    await call.answer()


@router.message(AddWalletStates.entering_address)
async def add_wallet_enter_address(message: Message, state: FSMContext) -> None:
    address = (message.text or "").strip()
    if not is_valid_tron_address(address):
        await message.answer("Адрес некорректен. Повторите ввод или нажмите Отмена.")
        return
    await state.update_data(address=address)
    await state.set_state(AddWalletStates.entering_label)
    await message.answer("Введите метку (необязательно). Отправьте текст или '-' чтобы пропустить.")


@router.message(AddWalletStates.entering_label)
async def add_wallet_enter_label(message: Message, state: FSMContext) -> None:
    db: Database = message.bot.dispatcher.get("db")  # type: ignore[attr-defined]
    data = await state.get_data()
    address = data.get("address", "")
    raw_label = (message.text or "").strip()
    label = None if raw_label in {"-", ""} else sanitize_label(raw_label)
    try:
        await db.add_wallet(message.from_user.id, address, label)  # type: ignore[union-attr]
        await message.answer(
            "Кошелёк сохранён ✅", reply_markup=main_menu_kb().as_markup()
        )
    except Exception as e:
        await message.answer(f"Не удалось сохранить адрес: {e}")
    await state.clear()


@router.callback_query(lambda c: c.data == "wallets:delete")
async def cb_wallets_delete(call: CallbackQuery) -> None:
    db: Database = call.message.bot.dispatcher.get("db")  # type: ignore[attr-defined]
    wallets = await db.list_wallets(call.from_user.id)  # type: ignore[union-attr]
    if not wallets:
        await call.message.edit_text(
            "Нет сохранённых кошельков.", reply_markup=wallets_manage_kb().as_markup()
        )
    else:
        await call.message.edit_text(
            "Выберите кошелёк для удаления:",
            reply_markup=wallets_select_kb(wallets, prefix="wallets:del").as_markup(),
        )
    await call.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("wallets:del:"))
async def cb_wallets_delete_pick(call: CallbackQuery) -> None:
    db: Database = call.message.bot.dispatcher.get("db")  # type: ignore[attr-defined]
    wallet_id = int(call.data.split(":")[-1])
    ok = await db.delete_wallet(call.from_user.id, wallet_id)  # type: ignore[union-attr]
    if ok:
        await call.message.edit_text("Кошелёк удалён ✅", reply_markup=wallets_manage_kb().as_markup())
    else:
        await call.message.edit_text("Не удалось удалить.", reply_markup=wallets_manage_kb().as_markup())
    await call.answer()

