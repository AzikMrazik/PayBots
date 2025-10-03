from decimal import Decimal
from typing import Any, Dict

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from api_client import RefeeApiClient, RefeeApiError
from database import Database
from utils import format_money, is_valid_tron_address, parse_decimal
from keyboards import (
    main_menu_kb,
    refill_kb,
    wallets_select_kb,
    confirm_kb,
)
from states import RefillStates, BuyEnergyStates, BuyBandwidthStates


router = Router()


async def _ensure_args(message: Message, expected: int) -> list[str]:
    parts = (message.text or "").split()
    if len(parts) < expected:
        await message.answer("Недостаточно аргументов. Проверьте синтаксис команды.")
        return []
    return parts


@router.message(Command("calculate"))
async def cmd_calculate(message: Message) -> None:
    api: RefeeApiClient = message.bot.dispatcher.get("api")  # type: ignore[attr-defined]
    parts = (message.text or "").split()
    # For simplicity: /calculate <from> <to> <amount_TRX>
    if len(parts) != 4:
        await message.answer(
            "Использование: /calculate <откуда> <куда> <сумма_TRX>\n"
            "Пример: /calculate TL... TD... 100"
        )
        return
    from_addr, to_addr, amount_str = parts[1], parts[2], parts[3]
    if not is_valid_tron_address(from_addr) or not is_valid_tron_address(to_addr):
        await message.answer("Некорректный Tron-адрес. Проверьте ввод.")
        return
    try:
        amount_trx = parse_decimal(amount_str)
    except Exception:
        await message.answer("Некорректная сумма. Пример: 12.5")
        return
    payload = {
        "fromAddress": from_addr,
        "toAddress": to_addr,
        "amountTRX": str(amount_trx),
    }
    try:
        energy_info = await api.precount_order(payload)
        bandwidth_info = await api.precount_bandwidth(payload)
        await message.answer(
            "Предварительный расчёт:\n"
            f"Энергия: {energy_info}\n"
            f"Bandwidth: {bandwidth_info}"
        )
    except RefeeApiError as e:
        await message.answer(f"Ошибка API при расчёте: {e}")


# ===== Inline flows =====


@router.callback_query(lambda c: c.data == "menu:refill")
async def cb_refill_menu(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(RefillStates.waiting_amount)
    await call.message.edit_text(
        "Выберите сумму пополнения или введите свою:", reply_markup=refill_kb().as_markup()
    )
    await call.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("refill:amount:"))
async def cb_refill_amount(call: CallbackQuery, state: FSMContext) -> None:
    db: Database = call.message.bot.dispatcher.get("db")  # type: ignore[attr-defined]
    amount_str = call.data.split(":")[-1]
    try:
        amount = parse_decimal(amount_str)
        new_balance = await db.add_balance(call.from_user.id, amount)  # type: ignore[union-attr]
        await call.message.edit_text(
            f"Пополнение на {amount} USDT успешно. Баланс: <b>{format_money(new_balance)}</b>",
            reply_markup=main_menu_kb().as_markup(),
        )
        await state.clear()
    except Exception as e:
        await call.message.edit_text(f"Ошибка пополнения: {e}", reply_markup=main_menu_kb().as_markup())
        await state.clear()
    await call.answer()


@router.callback_query(lambda c: c.data == "refill:other")
async def cb_refill_other(call: CallbackQuery, state: FSMContext) -> None:
    await call.message.edit_text("Введите сумму (например, 12.5). Для отмены нажмите 'Отмена'.")
    await state.set_state(RefillStates.waiting_amount)
    await call.answer()


@router.message(RefillStates.waiting_amount)
async def refill_enter_amount(message: Message, state: FSMContext) -> None:
    db: Database = message.bot.dispatcher.get("db")  # type: ignore[attr-defined]
    try:
        amount = parse_decimal(message.text or "0")
        new_balance = await db.add_balance(message.from_user.id, amount)  # type: ignore[union-attr]
        await message.answer(
            f"Пополнение на {amount} USDT успешно. Баланс: <b>{format_money(new_balance)}</b>",
            reply_markup=main_menu_kb().as_markup(),
        )
        await state.clear()
    except Exception as e:
        await message.answer(f"Ошибка: {e}. Введите сумму повторно или нажмите Отмена.")


@router.callback_query(lambda c: c.data == "menu:buy_energy")
async def cb_buy_energy_start(call: CallbackQuery, state: FSMContext) -> None:
    db: Database = call.message.bot.dispatcher.get("db")  # type: ignore[attr-defined]
    wallets = await db.list_wallets(call.from_user.id)  # type: ignore[union-attr]
    await state.set_state(BuyEnergyStates.choosing_wallet)
    await call.message.edit_text(
        "Выберите кошелёк для покупки энергии:",
        reply_markup=wallets_select_kb(wallets, prefix="buyenergy:wallet").as_markup(),
    )
    await call.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("buyenergy:wallet:"))
async def cb_buy_energy_wallet(call: CallbackQuery, state: FSMContext) -> None:
    wallet_id = int(call.data.split(":")[-1])
    await state.update_data(wallet_id=wallet_id)
    await state.set_state(BuyEnergyStates.entering_amount)
    await call.message.edit_text("Введите количество энергии (число).")
    await call.answer()


@router.message(BuyEnergyStates.entering_amount)
async def buy_energy_enter_amount(message: Message, state: FSMContext) -> None:
    db: Database = message.bot.dispatcher.get("db")  # type: ignore[attr-defined]
    api: RefeeApiClient = message.bot.dispatcher.get("api")  # type: ignore[attr-defined]
    try:
        energy_amount = parse_decimal(message.text or "0")
    except Exception:
        await message.answer("Некорректное значение. Введите число, например 100.")
        return
    data = await state.get_data()
    wallet = await db.get_wallet(message.from_user.id, data.get("wallet_id", 0))  # type: ignore[union-attr]
    if not wallet:
        await message.answer("Кошелёк не найден.")
        await state.clear()
        return
    _, address, _ = wallet
    try:
        estimate = await api.precount_order({"ownerAddress": address, "energyAmount": str(energy_amount)})
    except RefeeApiError as e:
        await message.answer(f"Ошибка API при расчёте: {e}")
        await state.clear()
        return
    price = Decimal(str(estimate.get("priceUSDT") or estimate.get("price") or "0"))
    await state.update_data(energy_amount=str(energy_amount), price=str(price))
    await state.set_state(BuyEnergyStates.confirming)
    await message.answer(
        f"Адрес: <code>{address}</code>\nЭнергия: {energy_amount}\nСтоимость: {price} USDT",
        reply_markup=confirm_kb("buyenergy").as_markup(),
    )


@router.callback_query(lambda c: c.data == "buyenergy:confirm")
async def cb_buy_energy_confirm(call: CallbackQuery, state: FSMContext) -> None:
    db: Database = call.message.bot.dispatcher.get("db")  # type: ignore[attr-defined]
    api: RefeeApiClient = call.message.bot.dispatcher.get("api")  # type: ignore[attr-defined]
    data = await state.get_data()
    wallet_id = int(data.get("wallet_id", 0))
    energy_amount = Decimal(data.get("energy_amount", "0"))
    price = Decimal(data.get("price", "0"))
    wallet = await db.get_wallet(call.from_user.id, wallet_id)  # type: ignore[union-attr]
    if not wallet:
        await call.message.edit_text("Кошелёк не найден.", reply_markup=main_menu_kb().as_markup())
        await state.clear()
        await call.answer()
        return
    _, address, _ = wallet
    try:
        await db.subtract_balance(call.from_user.id, price)  # type: ignore[union-attr]
    except Exception as e:
        await call.message.edit_text(f"Оплата невозможна: {e}", reply_markup=main_menu_kb().as_markup())
        await state.clear()
        await call.answer()
        return
    try:
        result = await api.buy_energy({"ownerAddress": address, "energyAmount": str(energy_amount)})
        await call.message.edit_text(
            f"Заказ энергии оформлен ✅\nАдрес: <code>{address}</code>\nСписано: {price} USDT\nОтвет: {result}",
            reply_markup=main_menu_kb().as_markup(),
        )
    except RefeeApiError as e:
        await db.add_balance(call.from_user.id, price)  # type: ignore[union-attr]
        await call.message.edit_text(
            f"Ошибка оформления: {e}. Средства возвращены.", reply_markup=main_menu_kb().as_markup()
        )
    await state.clear()
    await call.answer()


@router.callback_query(lambda c: c.data == "menu:buy_bandwidth")
async def cb_buy_bw_start(call: CallbackQuery, state: FSMContext) -> None:
    db: Database = call.message.bot.dispatcher.get("db")  # type: ignore[attr-defined]
    wallets = await db.list_wallets(call.from_user.id)  # type: ignore[union-attr]
    await state.set_state(BuyBandwidthStates.choosing_wallet)
    await call.message.edit_text(
        "Выберите кошелёк для покупки bandwidth:",
        reply_markup=wallets_select_kb(wallets, prefix="buybw:wallet").as_markup(),
    )
    await call.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("buybw:wallet:"))
async def cb_buy_bw_wallet(call: CallbackQuery, state: FSMContext) -> None:
    wallet_id = int(call.data.split(":")[-1])
    await state.update_data(wallet_id=wallet_id)
    await state.set_state(BuyBandwidthStates.entering_amount)
    await call.message.edit_text("Введите количество bandwidth (число).")
    await call.answer()


@router.message(BuyBandwidthStates.entering_amount)
async def buy_bw_enter_amount(message: Message, state: FSMContext) -> None:
    db: Database = message.bot.dispatcher.get("db")  # type: ignore[attr-defined]
    api: RefeeApiClient = message.bot.dispatcher.get("api")  # type: ignore[attr-defined]
    try:
        amount = parse_decimal(message.text or "0")
    except Exception:
        await message.answer("Некорректное значение. Введите число, например 500.")
        return
    data = await state.get_data()
    wallet = await db.get_wallet(message.from_user.id, data.get("wallet_id", 0))  # type: ignore[union-attr]
    if not wallet:
        await message.answer("Кошелёк не найден.")
        await state.clear()
        return
    _, address, _ = wallet
    try:
        estimate = await api.precount_bandwidth({"ownerAddress": address, "bandwidthAmount": str(amount)})
    except RefeeApiError as e:
        await message.answer(f"Ошибка API при расчёте: {e}")
        await state.clear()
        return
    price = Decimal(str(estimate.get("priceUSDT") or estimate.get("price") or "0"))
    await state.update_data(amount=str(amount), price=str(price))
    await state.set_state(BuyBandwidthStates.confirming)
    await message.answer(
        f"Адрес: <code>{address}</code>\nBandwidth: {amount}\nСтоимость: {price} USDT",
        reply_markup=confirm_kb("buybw").as_markup(),
    )


@router.callback_query(lambda c: c.data == "buybw:confirm")
async def cb_buy_bw_confirm(call: CallbackQuery, state: FSMContext) -> None:
    db: Database = call.message.bot.dispatcher.get("db")  # type: ignore[attr-defined]
    api: RefeeApiClient = call.message.bot.dispatcher.get("api")  # type: ignore[attr-defined]
    data = await state.get_data()
    wallet_id = int(data.get("wallet_id", 0))
    amount = Decimal(data.get("amount", "0"))
    price = Decimal(data.get("price", "0"))
    wallet = await db.get_wallet(call.from_user.id, wallet_id)  # type: ignore[union-attr]
    if not wallet:
        await call.message.edit_text("Кошелёк не найден.", reply_markup=main_menu_kb().as_markup())
        await state.clear()
        await call.answer()
        return
    _, address, _ = wallet
    try:
        await db.subtract_balance(call.from_user.id, price)  # type: ignore[union-attr]
    except Exception as e:
        await call.message.edit_text(f"Оплата невозможна: {e}", reply_markup=main_menu_kb().as_markup())
        await state.clear()
        await call.answer()
        return
    try:
        result = await api.buy_bandwidth({"ownerAddress": address, "bandwidthAmount": str(amount)})
        await call.message.edit_text(
            f"Заказ bandwidth оформлен ✅\nАдрес: <code>{address}</code>\nСписано: {price} USDT\nОтвет: {result}",
            reply_markup=main_menu_kb().as_markup(),
        )
    except RefeeApiError as e:
        await db.add_balance(call.from_user.id, price)  # type: ignore[union-attr]
        await call.message.edit_text(
            f"Ошибка оформления: {e}. Средства возвращены.", reply_markup=main_menu_kb().as_markup()
        )
    await state.clear()
    await call.answer()


@router.message(Command("buyenergy"))
async def cmd_buy_energy(message: Message) -> None:
    db: Database = message.bot.dispatcher.get("db")  # type: ignore[attr-defined]
    api: RefeeApiClient = message.bot.dispatcher.get("api")  # type: ignore[attr-defined]

    parts = (message.text or "").split()
    if len(parts) != 3:
        await message.answer("Использование: /buyenergy <адрес> <энергия>")
        return
    address, energy_str = parts[1], parts[2]
    if not is_valid_tron_address(address):
        await message.answer("Некорректный Tron-адрес")
        return
    try:
        energy_amount = parse_decimal(energy_str)
    except Exception:
        await message.answer("Некорректное значение энергии")
        return

    # Ask API for cost estimate
    payload = {"ownerAddress": address, "energyAmount": str(energy_amount)}
    try:
        estimate = await api.precount_order({"ownerAddress": address, "energyAmount": str(energy_amount)})
    except RefeeApiError as e:
        await message.answer(f"Ошибка API при расчёте: {e}")
        return

    # Expect estimate contains 'priceUSDT' or 'price'
    price = Decimal(str(estimate.get("priceUSDT") or estimate.get("price") or "0"))
    if price <= 0:
        await message.answer("Не удалось определить стоимость заказа")
        return

    # Balance check and charge
    try:
        await db.subtract_balance(message.from_user.id, price)  # type: ignore[union-attr]
    except Exception as e:
        await message.answer(f"Оплата невозможна: {e}")
        return

    try:
        result = await api.buy_energy(payload)
        await message.answer(
            "Заказ энергии оформлен ✅\n"
            f"Адрес: <code>{address}</code>\n"
            f"Списано: {price} USDT\n"
            f"Ответ сервиса: {result}"
        )
    except RefeeApiError as e:
        # Refund on API failure
        await db.add_balance(message.from_user.id, price)  # type: ignore[union-attr]
        await message.answer(f"Ошибка оформления: {e}. Средства возвращены на баланс.")


@router.message(Command("buybandwidth"))
async def cmd_buy_bandwidth(message: Message) -> None:
    db: Database = message.bot.dispatcher.get("db")  # type: ignore[attr-defined]
    api: RefeeApiClient = message.bot.dispatcher.get("api")  # type: ignore[attr-defined]

    parts = (message.text or "").split()
    if len(parts) != 3:
        await message.answer("Использование: /buybandwidth <адрес> <кол-во>")
        return
    address, amount_str = parts[1], parts[2]
    if not is_valid_tron_address(address):
        await message.answer("Некорректный Tron-адрес")
        return
    try:
        amount = parse_decimal(amount_str)
    except Exception:
        await message.answer("Некорректное значение")
        return

    try:
        estimate = await api.precount_bandwidth({"ownerAddress": address, "bandwidthAmount": str(amount)})
    except RefeeApiError as e:
        await message.answer(f"Ошибка API при расчёте: {e}")
        return

    price = Decimal(str(estimate.get("priceUSDT") or estimate.get("price") or "0"))
    if price <= 0:
        await message.answer("Не удалось определить стоимость заказа")
        return

    try:
        await db.subtract_balance(message.from_user.id, price)  # type: ignore[union-attr]
    except Exception as e:
        await message.answer(f"Оплата невозможна: {e}")
        return

    payload = {"ownerAddress": address, "bandwidthAmount": str(amount)}
    try:
        result = await api.buy_bandwidth(payload)
        await message.answer(
            "Заказ bandwidth оформлен ✅\n"
            f"Адрес: <code>{address}</code>\n"
            f"Списано: {price} USDT\n"
            f"Ответ сервиса: {result}"
        )
    except RefeeApiError as e:
        await db.add_balance(message.from_user.id, price)  # type: ignore[union-attr]
        await message.answer(f"Ошибка оформления: {e}. Средства возвращены на баланс.")

