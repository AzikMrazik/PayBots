from decimal import Decimal
from typing import Any, Dict

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from api_client import RefeeApiClient, RefeeApiError
from database import Database
from utils import format_money, is_valid_tron_address, parse_decimal


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

